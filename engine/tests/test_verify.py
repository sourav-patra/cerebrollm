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
        data["rule"] = [{"root": "fx", "glob": "**/*.md", "tier": "T2", "status": "current"}]
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

    def excluded_same_as_absent(self, rel, text, quote):
        f = Path(self.tmp.name) / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(text)
        with mock.patch.object(verify, "_indexed_sha", return_value=set()):
            with_quote = verify.run_verify(self.cfg, rel, quote)
            without = verify.run_verify(self.cfg, rel, "a sentence that is in no file")
        self.assertEqual(with_quote[0], "MISSING")
        self.assertEqual(with_quote, (without[0], without[1]))

    def test_excluded_same_code_with_or_without_quote(self):
        self.excluded_same_as_absent("evidence/secret.md", "The vault code is 4417.\n", "vault code is 4417")

    def test_secret_file_same_as_absent_quote(self):
        self.excluded_same_as_absent("keys.md", "token AKIA" + "X" * 16 + " here\n", "token AKIA")

    def test_no_rule_file_same_as_absent_quote(self):
        self.excluded_same_as_absent("notes.txt", "Plain text the rules do not match.\n", "Plain text")

    def test_excluded_path_is_not_read(self):
        (Path(self.tmp.name) / "logs").mkdir()
        (Path(self.tmp.name) / "logs" / "x.md").write_text("A change gets\n")
        with mock.patch.object(verify.corpus, "read_source", side_effect=AssertionError("read")):
            self.assertEqual(self.run_verify("logs/x.md", "A change gets", set()), "MISSING")
            self.assertEqual(self.run_verify("doc/../logs/x.md", "A change gets", set()), "MISSING")

    def test_symlink_out_of_root_refused(self):
        outside = tempfile.TemporaryDirectory(dir=SCRATCH)
        self.addCleanup(outside.cleanup)
        target = Path(outside.name) / "private.md"
        target.write_text("A change gets\n")
        link = Path(self.tmp.name) / "link.md"
        try:
            link.symlink_to(target)
        except OSError as exc:
            self.skipTest("cannot create a symlink here: %s" % exc)
        with mock.patch.object(verify.corpus, "read_source", side_effect=AssertionError("read")):
            self.assertEqual(self.run_verify("link.md", "A change gets", {self.sha}), "GONE")

    def test_symlink_to_excluded_file_inside_root(self):
        (Path(self.tmp.name) / "evidence").mkdir()
        (Path(self.tmp.name) / "evidence" / "e.md").write_text("A change gets\n")
        link = Path(self.tmp.name) / "alias.md"
        try:
            link.symlink_to(Path(self.tmp.name) / "evidence" / "e.md")
        except OSError as exc:
            self.skipTest("cannot create a symlink here: %s" % exc)
        self.assertEqual(self.run_verify("alias.md", "A change gets", set()), "MISSING")

    def test_outside_root_is_refused(self):
        with self.assertRaises(PermissionError):
            verify.corpus.read_source(self.cfg.roots["fx"], "../escape.md")


if __name__ == "__main__":
    unittest.main()
