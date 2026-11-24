"""Recency multiplier and hit formatting. No database or model is needed."""
import datetime
import unittest
from types import SimpleNamespace

from llama_index.core.schema import TextNode

from cerebrollm import config, search
from cerebrollm.search import copy_key, distinct_by_text, expand_query, rrf_fuse

UTC = datetime.timezone.utc
NOW = datetime.datetime(2026, 10, 26, 12, 0, tzinfo=UTC)


class TestRecency(unittest.TestCase):
    W, HALF = 0.005, 30

    def mult(self, mtime):
        return search.recency_multiplier(mtime, NOW, self.W, self.HALF)

    def test_newest_gets_the_full_weight(self):
        self.assertAlmostEqual(self.mult("2026-10-26T12:00:00+00:00"), 1 + self.W)

    def test_boost_halves_every_half_life(self):
        self.assertAlmostEqual(self.mult("2026-09-26T12:00:00+00:00"), 1 + self.W / 2, places=4)

    def test_newer_scores_higher_and_stays_below_the_weight(self):
        newer, older = self.mult("2026-10-25T12:00:00+00:00"), self.mult("2026-10-01T12:00:00+00:00")
        self.assertGreater(newer, older)
        self.assertLessEqual(newer, 1 + self.W)
        self.assertGreater(older, 1.0)

    def test_offset_dates_are_compared_as_instants(self):
        # 2026-10-26 14:00 at +02:00 is 12:00 UTC, the same instant as NOW
        self.assertAlmostEqual(self.mult("2026-10-26T14:00:00+02:00"), 1 + self.W)

    def test_future_and_naive_dates(self):
        self.assertAlmostEqual(self.mult("2027-01-01T00:00:00+00:00"), 1 + self.W)   # clamped to age 0
        self.assertAlmostEqual(self.mult("2026-10-26T12:00:00"), 1 + self.W)         # naive: UTC

    def test_missing_or_bad_date_keeps_the_score(self):
        self.assertEqual(self.mult(None), 1.0)
        self.assertEqual(self.mult(""), 1.0)
        self.assertEqual(self.mult("not a date"), 1.0)

    def test_default_weight_is_configured(self):
        cfg = config.load()
        self.assertGreater(cfg.search["recency"]["weight"], 0)
        self.assertLessEqual(cfg.search["recency"]["weight"], 0.005)


class TestExcluded(unittest.TestCase):
    def test_excluded_path_not_returned(self):
        for meta in ({"root": "fx", "path": "notes/evidence/x.md", "ref": "file"},
                     {"root": "fx", "path": "notes/logs/y.md", "ref": "file"}):
            for mode, hits in self.search_all_modes(meta).items():
                self.assertEqual(hits, [], mode)
        for mode, hits in self.search_all_modes({"root": "fx", "path": "notes/ok.md", "ref": "file"}).items():
            self.assertEqual([h["path"] for h in hits], ["notes/ok.md"], mode)

    def search_all_modes(self, meta, cfg=None, all_status=False):
        from unittest import mock
        from llama_index.core.schema import NodeWithScore
        index = mock.Mock()
        index.as_retriever.return_value.retrieve.return_value = [
            NodeWithScore(node=TextNode(text="kept", metadata=meta), score=0.5)]
        hits = {}
        with mock.patch.object(search.VectorStoreIndex, "from_vector_store", return_value=index), \
                mock.patch.object(search.store, "vector_store"), mock.patch.object(search.store, "embed_model"):
            for mode in ("lexical", "vector", "hybrid"):
                hits[mode] = search.run_search(cfg or self.cfg(), "change", k=8, mode=mode, all_status=all_status)
        return hits

    def cfg(self):
        data = config.load().data
        data["root"] = [{"name": "fx", "kind": "dir", "path": "/nonexistent", "ref": "file"}]
        data["rule"] = [{"root": "fx", "glob": "**/*.md", "tier": "T2", "status": "current"}]
        return config.Config(data, "test")

    def test_excluded_primary_is_dropped_in_every_mode(self):
        meta = {"root": "fx", "path": "shared/logs/primary.md", "tier": "T1", "status": "current", "ref": "file",
                "also_at": ["fx:shared/ok.md"]}
        for mode, hits in self.search_all_modes(meta).items():
            self.assertEqual(hits, [], mode)

    def test_primary_without_a_root_or_tier_rule_is_dropped(self):
        for meta in ({"root": "gone", "path": "shared/ok.md", "ref": "file"},
                     {"root": "fx", "path": "shared/ok.txt", "ref": "file"}):
            for all_status in (False, True):
                for mode, hits in self.search_all_modes(meta, all_status=all_status).items():
                    self.assertEqual(hits, [], (meta["root"], mode, all_status))

    def test_also_at_keys_of_unknown_roots_or_excluded_paths_are_dropped(self):
        meta = {"root": "fx", "path": "shared/ok.md", "tier": "T2", "status": "current", "ref": "file",
                "also_at": ["fx:a/logs/b.md", "gone:a.md", "fx:a/c.md"]}
        for mode, hits in self.search_all_modes(meta).items():
            self.assertEqual(hits[0]["also_at"], ["fx:a/c.md"], mode)

    def test_root_name_with_a_colon_is_refused(self):
        data = config.load().data
        data["root"] = [{"name": "r:x", "kind": "dir", "path": "/nonexistent", "ref": "file"}]
        with self.assertRaises(ValueError):
            config.Config(data, "test")

    def test_excluded_copy_left_out_of_also_at(self):
        from unittest import mock
        from llama_index.core.schema import NodeWithScore
        meta = {"root": "fx", "path": "notes/ok.md", "also_at": ["fx:notes/copy.md", "fx:notes/logs/copy.md"]}
        index = mock.Mock()
        index.as_retriever.return_value.retrieve.return_value = [
            NodeWithScore(node=TextNode(text="kept", metadata=meta), score=0.5)]
        with mock.patch.object(search.VectorStoreIndex, "from_vector_store", return_value=index), \
                mock.patch.object(search.store, "vector_store"), mock.patch.object(search.store, "embed_model"):
            hits = search.run_search(self.cfg(), "change", k=8, mode="vector")
        self.assertEqual(hits[0]["also_at"], ["fx:notes/copy.md"])


def hit(rank, path, also_at=()):
    return {"rank": rank, "score": 0.0312, "tier": "T1", "status": "locked", "path": path,
            "line_start": 1, "line_end": 3, "ref": "origin/main", "project": "example",
            "heading_path": "Spec > Rules", "sha256": "ab" * 32, "source_unchanged": True,
            "also_at": list(also_at), "text": "text of %s" % path}


class TestFormat(unittest.TestCase):
    def test_also_at_is_shown_when_present(self):
        out = search.format_hits([hit(1, "docs/a/r5/N.md",
                                      ["example-repo:docs/a/r3/N.md"])])
        self.assertIn("also_at=[example-repo:docs/a/r3/N.md]", out.splitlines()[0])

    def test_also_at_is_absent_when_empty(self):
        out = search.format_hits([hit(1, "docs/a/r5/N.md")])
        self.assertNotIn("also_at", out)


SYN = config.load().synonyms


class TestSynonyms(unittest.TestCase):
    def test_configured_pairs(self):
        self.assertEqual(SYN["PR"], "pull request")
        self.assertEqual(SYN["PRD"], "product requirements")
        self.assertEqual(len(SYN), 6)

    def test_abbreviation_adds_its_phrase(self):
        q = expand_query("when is a PR ready to merge", SYN)
        self.assertTrue(q.startswith("when is a PR ready to merge "))
        self.assertIn("pull request", q)

    def test_phrase_adds_its_abbreviation(self):
        self.assertEqual(expand_query("who may merge pull requests", SYN).split()[-1], "PR")

    def test_no_match_leaves_the_query(self):
        self.assertEqual(expand_query("who is allowed to merge", SYN), "who is allowed to merge")

    def test_whole_words_only(self):
        self.assertEqual(expand_query("the prize is here", SYN), "the prize is here")


class FakeNode:
    def __init__(self, text):
        self.text = text

    def get_content(self):
        return self.text


def ranked_hit(text, path, also=()):
    return {"score": 1.0, "node": FakeNode(text), "meta": {"root": "notes", "path": path, "also_at": list(also)}}


class TestDistinctByText(unittest.TestCase):
    def test_duplicate_text_is_dropped_and_its_paths_join_also_at(self):
        ranked = [ranked_hit("A", "p1"), ranked_hit("A", "p2", also=["example-repo:p3"]), ranked_hit("B", "p4")]
        kept = distinct_by_text(ranked, 5)
        self.assertEqual([e["item"]["meta"]["path"] for e in kept], ["p1", "p4"])
        self.assertEqual(kept[0]["also_at"], ["notes:p2", "example-repo:p3"])
        self.assertEqual(kept[1]["also_at"], [])

    def test_k_is_filled_with_the_next_distinct_hits(self):
        ranked = [ranked_hit("A", "p1"), ranked_hit("A", "p2"), ranked_hit("B", "p3"), ranked_hit("C", "p4")]
        kept = distinct_by_text(ranked, 3)
        self.assertEqual([e["item"]["meta"]["path"] for e in kept], ["p1", "p3", "p4"])

    def test_copy_key_is_root_and_path(self):
        self.assertEqual(copy_key({"root": "notes", "path": "x.md"}), "notes:x.md")
        self.assertEqual(copy_key({"path": "x.md"}), "x.md")


class TestRRF(unittest.TestCase):
    def test_a_node_in_both_lists_ranks_first(self):
        a, b, c = (TextNode(text=t, id_=i) for t, i in [("a", "n1"), ("b", "n2"), ("c", "n3")])
        h = lambda node, score: SimpleNamespace(node=node, score=score)
        fused = rrf_fuse([[h(a, 0.9), h(b, 0.5)], [h(b, 0.8), h(c, 0.4)]])
        self.assertEqual(fused[0].node.node_id, "n2")
        self.assertAlmostEqual(fused[0].score, 1 / 61 + 1 / 60)   # rank 1 in one list, rank 0 in the other
        self.assertEqual(len(fused), 3)


class TestTieOrder(unittest.TestCase):
    """Equal scores must sort the same way whatever order the retriever returned them in, so that offset
    continuation neither repeats nor skips a hit."""

    def node(self, text, nid, path):
        return TextNode(text=text, id_=nid, metadata={"root": "fx", "path": path, "ref": "file"})

    def test_run_search_orders_equal_scores_by_path_then_chunk_id(self):
        from itertools import permutations
        from unittest import mock
        nodes = [self.node("one", "n9", "b/x.md"), self.node("two", "n2", "a/x.md"),
                 self.node("three", "n5", "a/x.md"), self.node("four", "n1", "c/x.md")]
        data = config.load().data
        data["root"] = [{"name": "fx", "kind": "dir", "path": "/nonexistent", "ref": "file"}]
        data["rule"] = [{"root": "fx", "glob": "**/*.md", "tier": "T2", "status": "current"}]
        cfg = config.Config(data, "test")
        seen = set()
        for order in permutations(nodes):
            index = mock.Mock()
            index.as_retriever.return_value.retrieve.return_value = [
                SimpleNamespace(node=n, score=0.5) for n in order]
            with mock.patch.object(search.VectorStoreIndex, "from_vector_store", return_value=index),                     mock.patch.object(search.store, "vector_store"), mock.patch.object(search.store, "embed_model"):
                hits = search.run_search(cfg, "change", k=8, mode="vector", all_status=True)
            seen.add(tuple(h["text"] for h in hits))
        self.assertEqual(seen, {("two", "three", "one", "four")})   # a/x.md n2, a/x.md n5, b/x.md, c/x.md

    def test_rrf_fuse_orders_equal_fused_scores_by_path_then_chunk_id(self):
        from itertools import permutations
        a, b, c = (self.node(t, i, p) for t, i, p in
                   [("a", "n7", "z.md"), ("b", "n3", "y.md"), ("c", "n4", "y.md")])
        h = lambda node, score: SimpleNamespace(node=node, score=score)
        seen = set()
        for order in permutations([a, b, c]):   # one list of three equal retrieval scores
            fused = rrf_fuse([[h(n, 0.5) for n in order]])
            seen.add(tuple(f.node.node_id for f in fused))
        self.assertEqual(seen, {("n3", "n4", "n7")})
        for first, second in ((a, b), (b, a)):   # two lists, each with one hit: fused scores are equal
            fused = rrf_fuse([[h(first, 0.9)], [h(second, 0.9)]])
            self.assertEqual([f.node.node_id for f in fused], ["n3", "n7"])


class TestSanitize(unittest.TestCase):
    def test_tsquery_operators_and_quotes_are_removed(self):
        out = search.sanitize("a & b | !c (d):* <e> 'f' \"g\" \\h")
        self.assertEqual(out, "a b c d e f g h")
        self.assertEqual(search.sanitize("a'; drop table x; --"), "a ; drop table x; --")   # harmless: a bound parameter


if __name__ == "__main__":
    unittest.main()
