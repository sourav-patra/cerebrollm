"""Replay the R1 sample from selection/snapshot-manifest.json (standard library only, no model, no database).

    python -m unittest test_selection_replay      (from research/model-study)

The sample is the first 150 chunks of random.Random(seed).sample(eligible rows in snapshot order) that
yielded a valid question; chunks recorded under skipped_after_five_attempts are passed over.
"""
import collections
import json
from pathlib import Path
import random
import unittest

SEL = Path(__file__).resolve().parent / 'selection'


def replay(manifest, protocol, skipped_ids):
    eligible = [r for r in manifest['rows'] if r[1] in protocol['statuses']]
    order = random.Random(protocol['seed']).sample(eligible, len(eligible))
    picked = [r for r in order if r[0] not in skipped_ids][:protocol['sample_size']]
    return order, picked


class TestReplay(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((SEL / 'snapshot-manifest.json').read_text())
        cls.protocol = json.loads((SEL / 'protocol.json').read_text())
        cls.set = json.loads((SEL / 'selection-set.json').read_text())
        cls.skipped = {s['node_id'] for s in cls.set['skipped_after_five_attempts']}
        cls.order, cls.picked = replay(cls.manifest, cls.protocol, cls.skipped)

    def test_manifest_belongs_to_the_snapshot_that_was_sampled(self):
        self.assertEqual(self.manifest['snapshot_sha256'], self.set['snapshot_sha256'])
        self.assertEqual(len(self.manifest['rows']), self.set['chunks_in_snapshot'])
        self.assertEqual(len([r for r in self.manifest['rows'] if r[1] in self.protocol['statuses']]),
                         self.set['eligible_chunks'])

    def test_replay_gives_the_150_selected_node_ids_in_order(self):
        self.assertEqual([r[0] for r in self.picked], [i['node_id'] for i in self.set['items']])
        self.assertEqual(len(self.picked), 150)

    def test_text_hashes_match(self):
        self.assertEqual([r[2] for r in self.picked], [i['text_sha256'] for i in self.set['items']])

    def test_the_two_replacements(self):
        self.assertEqual(len(self.skipped), 2)
        last = {r[0]: n for n, r in enumerate(self.order)}[self.picked[-1][0]]
        positions = {r[0]: n for n, r in enumerate(self.order)}
        for node_id in self.skipped:
            self.assertLess(positions[node_id], last, 'a skipped chunk must have been drawn before the last pick')

    def test_no_sampled_chunk_has_identical_text_under_another_id(self):
        counts = collections.Counter(r[2] for r in self.manifest['rows'])
        self.assertEqual([r[0] for r in self.picked if counts[r[2]] > 1], [])

    def test_another_seed_gives_another_sample(self):
        _, other = replay(self.manifest, dict(self.protocol, seed=28), self.skipped)
        self.assertNotEqual([r[0] for r in other], [r[0] for r in self.picked])


if __name__ == '__main__':
    unittest.main()
