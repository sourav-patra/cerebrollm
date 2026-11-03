import copy
import hashlib
import os
import subprocess
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

    def link(self, name, target):
        path = Path(self.tmp.name) / name
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            path.symlink_to(target)
        except OSError as exc:
            self.skipTest("cannot create a symlink here: %s" % exc)

    def test_excluded_alias_to_eligible_file_is_not_read(self):
        self.link("evidence/alias.md", self.file)
        with mock.patch.object(verify.corpus, "read_source", side_effect=AssertionError("read")):
            self.assertEqual(self.run_verify("evidence/alias.md", "A change gets", set()), "MISSING")

    def test_excluded_alias_answers_the_same_whatever_its_target(self):
        outside = tempfile.TemporaryDirectory(dir=SCRATCH)
        self.addCleanup(outside.cleanup)
        (Path(outside.name) / "t.md").write_text("A change gets\n")
        self.link("evidence/out.md", Path(outside.name) / "t.md")
        self.link("evidence/dangling.md", Path(outside.name) / "nothing.md")
        with mock.patch.object(verify, "_indexed_sha", return_value=set()):
            results = {verify.run_verify(self.cfg, p, "A change gets")[0]
                       for p in ("evidence/out.md", "evidence/dangling.md", "evidence/none.md")}
        self.assertEqual(results, {"MISSING"})

    def test_linked_directory_into_excluded_folder(self):
        (Path(self.tmp.name) / "logs").mkdir()
        (Path(self.tmp.name) / "logs" / "x.md").write_text("A change gets\n")
        self.link("docs", Path(self.tmp.name) / "logs")
        self.assertEqual(self.run_verify("docs/x.md", "A change gets", set()), "MISSING")

    def test_a_later_root_is_still_tried(self):
        other = tempfile.TemporaryDirectory(dir=SCRATCH)
        self.addCleanup(other.cleanup)
        data = copy.deepcopy(self.cfg.data)
        data["root"] = [{"name": "first", "kind": "dir", "path": other.name, "ref": "file"}] + data["root"]
        cfg = config.Config(data, Path("test"))
        with mock.patch.object(verify, "_indexed_sha", return_value={self.sha}):
            self.assertEqual(verify.run_verify(cfg, "doc.md", "A change gets")[0], "OK")

    def test_outside_root_is_refused(self):
        with self.assertRaises(PermissionError):
            verify.corpus.read_source(self.cfg.roots["fx"], "../escape.md")


class TestGitRef(unittest.TestCase):
    """LLD I-03: a ref git could read as an option, or one that is not a commit, reads nothing."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=SCRATCH)
        self.addCleanup(self.tmp.cleanup)
        repo = self.tmp.name
        env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@example.com",
                   GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@example.com")
        git = lambda *a: subprocess.run(["git", "-C", repo, *a], check=True, capture_output=True, env=env).stdout
        git("init", "-q", "-b", "main")
        (Path(repo) / "docs").mkdir()
        (Path(repo) / "docs" / "a.md").write_text("A change gets two review rounds.\n")
        (Path(repo) / "evidence").mkdir()
        (Path(repo) / "evidence" / "a.md").write_text("The vault code is 4417.\n")
        git("add", "-A")
        git("commit", "-q", "-m", "fixture")
        self.tree = git("rev-parse", "main:evidence").decode().strip()
        data = copy.deepcopy(config.load().data)
        data["root"] = [{"name": "g", "kind": "git", "path": repo, "ref": "main"}]
        data["rule"] = [{"root": "g", "glob": "**/*.md", "tier": "T2", "status": "current"}]
        self.cfg = config.Config(data, Path("test"))
        self.repo = repo

    def run_verify(self, path, quote, ref):
        with mock.patch.object(verify, "_indexed_sha", return_value=set()):
            return verify.run_verify(self.cfg, path, quote, ref)[0]

    def test_valid_branch_still_verifies(self):
        self.assertEqual(self.run_verify("docs/a.md", "two review rounds", "main"), "UNINDEXED")

    def test_option_ref_reads_nothing(self):
        self.assertEqual(self.run_verify("docs/a.md", "two review rounds", "--output=out"), "GONE")
        self.assertEqual(self.run_verify("docs/a.md", "two review rounds", "--format=format:"), "GONE")
        self.assertFalse((Path(self.repo) / "out").exists())

    def test_tree_ref_cannot_reach_an_excluded_file(self):
        self.assertEqual(self.run_verify("a.md", "vault code is 4417", self.tree), "GONE")
        self.assertEqual(self.run_verify("a.md", "not in any file", self.tree), "GONE")


if __name__ == "__main__":
    unittest.main()
