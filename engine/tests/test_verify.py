import copy
import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from cerebrollm import config, verify
from tests import SCRATCH


class TestVerify(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=SCRATCH)
        self.addCleanup(self.tmp.cleanup)
        data = copy.deepcopy(config.load().data)
        data["root"] = [{"name": "fx", "kind": "dir", "path": self.tmp.name, "ref": "file"}]
        self.cfg = config.Config(data, Path("test"))
        self.file = Path(self.tmp.name) / "doc.md"
        self.file.write_text("# Title\n\nA change gets  two review\nrounds before merge.\n")
        self.sha = hashlib.sha256(self.file.read_bytes()).hexdigest()

    def run_verify(self, path, quote, indexed):
        with mock.patch.object(verify, "_indexed_sha", return_value=indexed):
            return verify.run_verify(self.cfg, path, quote)[0]

    def test_ok_whitespace_normalised(self):
        self.assertEqual(self.run_verify("doc.md", "two review rounds before merge", {self.sha}), "OK")

    def test_ok_absolute_path(self):
        self.assertEqual(self.run_verify(str(self.file), "A change gets", {self.sha}), "OK")

    def test_missing(self):
        self.assertEqual(self.run_verify("doc.md", "a made-up sentence", {self.sha}), "MISSING")

    def test_changed(self):
        self.assertEqual(self.run_verify("doc.md", "A change gets", {"0" * 64}), "CHANGED")

    def test_gone(self):
        self.assertEqual(self.run_verify("nope.md", "A change gets", {self.sha}), "GONE")

    def test_unindexed(self):
        self.assertEqual(self.run_verify("doc.md", "A change gets", set()), "UNINDEXED")

    def test_outside_root_is_refused(self):
        with self.assertRaises(PermissionError):
            verify.corpus.read_source(self.cfg.roots["fx"], "../escape.md")


if __name__ == "__main__":
    unittest.main()
