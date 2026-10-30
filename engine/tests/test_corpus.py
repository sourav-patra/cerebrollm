"""enumerate_corpus on a temp folder: never-index paths are skipped before any read, copies collapse,
JOURNAL files stay current. Reads are recorded through a wrapper around corpus.read_source."""
import copy
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from cerebrollm import config, corpus
from tests import SCRATCH

FILES = {
    "research/PLAN.md": "# Plan\n\nevaluation plan text.\n",
    "research/doc-x.md": "# Work order\n\nsteps.\n",
    "shared/drafts/other/keep.md": "# Draft\n\nan ordinary draft.\n",
    "shared/ok.md": "# Ok\n\nan ordinary top-level note.\n",
    "Project A/journal/JOURNAL_a-2026-10-20.md": "# Journal 20\n\nrecord one.\n",
    "Project A/journal/JOURNAL_a-2026-10-21.md": "# Journal 21\n\nrecord two.\n",
    "Project A/locked/r3/SPEC.md": "# Spec\n\nthe same bytes in two folders.\n",
    "Project A/locked/r5/SPEC.md": "# Spec\n\nthe same bytes in two folders.\n",
}
DRAFTS = "research/"


class TestEnumerate(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=SCRATCH)
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        for rel, text in FILES.items():
            (root / rel).parent.mkdir(parents=True, exist_ok=True)
            (root / rel).write_text(text)
        data = copy.deepcopy(config.load().data)
        data["root"] = [{"name": "notes", "kind": "dir", "path": str(root), "ref": "file"}]
        self.cfg = config.Config(data, Path("test"))

    def scan(self):
        reads = []
        real = corpus.read_source

        def recording(root, rel_path, ref=None):
            reads.append(rel_path)
            return real(root, rel_path, ref)

        with mock.patch.object(corpus, "read_source", side_effect=recording):
            entries, scan = corpus.enumerate_corpus(self.cfg)
        return entries, scan, reads

    def test_drafts_folder_is_never_read(self):
        entries, scan, reads = self.scan()
        self.assertFalse([r for r in reads if r.startswith(DRAFTS)], reads)
        self.assertFalse([e for e in entries if e["path"].startswith(DRAFTS)])
        self.assertEqual(scan["skipped_rule"]["path:" + DRAFTS], 2)

    def test_ordinary_drafts_and_notes_are_still_indexed(self):
        entries, _, _ = self.scan()
        paths = {e["path"] for e in entries}
        self.assertIn("shared/drafts/other/keep.md", paths)
        self.assertIn("shared/ok.md", paths)

    def test_journal_files_are_current(self):
        entries, _, _ = self.scan()
        journal = [e for e in entries if e["path"].split("/")[-1].startswith("JOURNAL")]
        self.assertEqual(len(journal), 2)
        self.assertEqual({e["status"] for e in journal}, {"current"})

    def test_identical_copies_are_indexed_once(self):
        entries, scan, _ = self.scan()
        spec = [e for e in entries if e["path"].endswith("SPEC.md")]
        self.assertEqual(len(spec), 1)
        self.assertEqual(spec[0]["path"], "Project A/locked/r5/SPEC.md")
        self.assertEqual(spec[0]["also_at"], ["notes:Project A/locked/r3/SPEC.md"])
        self.assertEqual(scan["counts"]["duplicates_collapsed"], 1)


if __name__ == "__main__":
    unittest.main()
