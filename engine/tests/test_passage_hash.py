"""Quotes that stay checkable after unrelated edits: each indexed passage carries the sha256 of its text, and
verify answers OK for a changed file while the passage that holds the quote still occurs in it unchanged.
The index format in state.json makes an older index warn and rebuild. The live tests run against the real
Postgres and Ollama on their own tables (cerebrollm_passagetest_ plus a random suffix per test, so two runs
against one database never share a table) and state directory, and are skipped with a message when either is
down, as in test_end_to_end."""
import contextlib
import copy
import hashlib
import io
import json
import os
import tempfile
import unittest
import uuid
from pathlib import Path
from unittest import mock

from cerebrollm import cli, config, store
from tests import SCRATCH
from tests.test_end_to_end import REASON

INTRO = ("## Intro\n\nThis handbook describes how the team works on the service. It covers reviews, releases and the "
         "limits that apply to every client, and it is kept in the repository next to the code it describes.\n\n")
REVIEW = ("## Review\n\nEvery change gets two review rounds before it merges. The first round checks the design and "
          "the second round checks the tests, and a reviewer never reviews a change that they wrote themselves.\n\n")
RELEASE = ("## Release\n\nA release is cut from the main branch on Mondays. The release notes list every change since "
           "the last release, and a release that fails its checks is withdrawn before anyone installs it.\n\n")
ROW = "| retries | Three retries with a five second pause. |"
LIMITS = "## Limits\n\n| Setting | Value |\n|---|---|\n| timeout | Thirty seconds per request. |\n" + ROW + "\n"
QUOTE = "Every change gets two review rounds before it merges."
ROW_QUOTE = "Three retries with a five second pause."


def handbook(*sections):
    return "# Handbook\n\n" + "".join(sections)


def make_cfg(root, state):
    """A config with root fx at root and a table name unique to this call."""
    data = copy.deepcopy(config.load().data)
    data["domain"] = "org"
    data["state_dir"] = str(state)
    data["postgres"]["table"] = "cerebrollm_passagetest_" + uuid.uuid4().hex[:12]
    data["root"] = [{"name": "fx", "kind": "dir", "path": str(root), "ref": "file"}]
    data["rule"] = [{"root": "fx", "glob": "**/*.md", "tier": "T2", "status": "current"}]
    return config.Config(data, Path("test"))


def drop_tables(cfg):
    for name in (cfg.data_table, cfg.next_data_table, "data_%s_old" % cfg.table):
        store.drop_table(cfg, name)


@unittest.skipIf(REASON, REASON or "")
class TestPassageHash(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=SCRATCH)
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "corpus"
        self.root.mkdir()
        self.doc = self.root / "handbook.md"
        self.doc.write_text(handbook(INTRO, REVIEW, RELEASE, LIMITS))
        self.cfg = make_cfg(self.root, Path(self.tmp.name) / "state")
        self.addCleanup(drop_tables, self.cfg)   # registered before the first index run
        from cerebrollm.indexer import run_index
        self.run_index = run_index
        self.run_index(self.cfg)

    def verify(self, quote, cfg=None, path="handbook.md"):
        from cerebrollm import verify
        return verify.run_verify(cfg or self.cfg, path, quote)[0]

    def rows(self):
        with store.sql(self.cfg) as cur:
            cur.execute("select text, metadata_->>'passage_sha256', (metadata_->>'char_end')::int - "
                        "(metadata_->>'char_start')::int from %s" % self.cfg.data_table)
            return cur.fetchall()

    def strip_to_format_1(self):
        """Rows as an index of format 1 left them: no passage_sha256."""
        with store.sql(self.cfg) as cur:
            cur.execute("update %s set metadata_ = (metadata_::jsonb - 'passage_sha256')::json" % self.cfg.data_table)

    def test_each_row_stores_the_hash_of_its_passage_text(self):
        rows = self.rows()
        self.assertGreaterEqual(len(rows), 4)   # intro, review, release, and one row per table row
        for text, sha, length in rows:
            self.assertEqual(sha, hashlib.sha256(text[-length:].encode("utf-8")).hexdigest())
        shas = {sha for _, sha, _ in rows}
        self.assertIn(hashlib.sha256(ROW.encode("utf-8")).hexdigest(), shas)   # a table row: the row alone
        self.assertEqual(store.read_state(self.cfg)["last_index"]["index_format"], store.INDEX_FORMAT)
        self.assertIsNone(store.format_warning(self.cfg))

    def test_an_edit_far_from_the_quote_keeps_ok(self):
        extra = "## News\n\nA new section above the quote moves every later passage further down the file.\n\n"
        self.doc.write_text(handbook(extra, INTRO.replace("the team", "our team"), REVIEW, RELEASE, LIMITS))
        self.assertEqual(self.verify(QUOTE), "OK")
        self.assertEqual(self.verify(ROW_QUOTE), "OK")

    def test_an_edit_inside_the_quoted_passage_is_changed(self):
        self.doc.write_text(handbook(INTRO, REVIEW.replace("the tests", "the docs"), RELEASE,
                                     LIMITS.replace("Thirty", "Sixty")))
        self.assertEqual(self.verify(QUOTE), "CHANGED")
        self.assertEqual(self.verify(ROW_QUOTE), "OK")   # its own row is unchanged
        self.doc.write_text(handbook(INTRO, REVIEW, RELEASE, LIMITS.replace("| retries |", "| retry count |")))
        self.assertEqual(self.verify(ROW_QUOTE), "CHANGED")

    def test_a_passage_moved_within_the_file_keeps_ok(self):
        self.doc.write_text(handbook(RELEASE, LIMITS, "\n", INTRO, REVIEW))
        self.assertEqual(self.verify(QUOTE), "OK")
        self.assertEqual(self.verify(ROW_QUOTE), "OK")

    def test_an_older_index_warns_and_changed_rebuilds_it(self):
        self.strip_to_format_1()   # rows and state as an index of format 1 left them
        state = store.read_state(self.cfg)
        del state["last_index"]["index_format"]
        self.cfg.state_path.write_text(json.dumps(state))
        self.assertIn("run `cerebrollm index` once", store.format_warning(self.cfg))
        self.doc.write_text(handbook(INTRO.replace("the team", "our team"), REVIEW, RELEASE, LIMITS))
        self.assertEqual(self.verify(QUOTE), "CHANGED")   # no passage hashes yet: the file hash decides
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            summary = self.run_index(self.cfg, changed=True)
        self.assertEqual(summary["mode"], "full")
        self.assertIn("running a full index to format %d" % store.INDEX_FORMAT, err.getvalue())
        self.assertIsNone(store.format_warning(self.cfg))
        self.assertTrue(all(sha for _, sha, _ in self.rows()))
        self.doc.write_text(handbook(INTRO.replace("the team", "a team"), REVIEW, RELEASE, LIMITS))
        self.assertEqual(self.verify(QUOTE), "OK")
        self.assertEqual(self.run_index(self.cfg, changed=True)["mode"], "changed")   # current format: no rebuild

    def test_changed_rebuilds_an_older_index_whose_state_file_is_gone(self):
        self.strip_to_format_1()
        self.cfg.state_path.unlink()
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(self.run_index(self.cfg, changed=True)["mode"], "full")
        self.assertTrue(all(sha for _, sha, _ in self.rows()))

    def test_a_passage_from_another_root_at_the_same_path_does_not_count(self):
        # Two roots holding the same path share a document id, so one index run keeps only one of them; the
        # other root's row is therefore written here directly: a copy of fx's review row under root fy, whose
        # passage is REVIEW. fx's own passage differs from REVIEW, and the edited fx file holds REVIEW.
        cut = "themselves, and a third round is added for a security change."
        self.doc.write_text(handbook(INTRO, REVIEW.replace("themselves.", cut), RELEASE, LIMITS))
        self.run_index(self.cfg)
        table = self.cfg.data_table
        with store.sql(self.cfg) as cur:
            cur.execute("select node_id, text, metadata_::text from %s where text like %%s" % table, ("%third round%",))
            node_id, text, meta = cur.fetchone()
            meta = json.loads(meta)
            passage = text[-(meta["char_end"] - meta["char_start"]):].replace(cut, "themselves.")
            meta.update(root="fy", char_end=meta["char_start"] + len(passage),
                        passage_sha256=hashlib.sha256(passage.encode("utf-8")).hexdigest())
            cur.execute("insert into %s (node_id, text, metadata_, embedding) select %%s, %%s, %%s::json, embedding "
                        "from %s where node_id = %%s" % (table, table),
                        (str(uuid.uuid4()), text.replace(cut, "themselves."), json.dumps(meta), node_id))
        self.doc.write_text(handbook(INTRO.replace("the team", "our team"), REVIEW, RELEASE, LIMITS))
        self.assertEqual(self.verify(QUOTE), "CHANGED")
        with store.sql(self.cfg) as cur:   # control: the same row under fx's own root does count
            cur.execute("update %s set metadata_ = jsonb_set(metadata_::jsonb, '{root}', '\"fx\"')::json "
                        "where metadata_->>'root' = 'fy'" % table)
        self.assertEqual(self.verify(QUOTE), "OK")

    def test_a_collapsed_copy_gives_no_passage_evidence(self):
        # two byte-identical files: b/ is kept (the folder that sorts last), a/ is recorded in its also_at
        (self.root / "a").mkdir()
        (self.root / "b").mkdir()
        for folder in ("a", "b"):
            (self.root / folder / "copy.md").write_text(handbook(INTRO, REVIEW, RELEASE))
        self.run_index(self.cfg)
        self.assertEqual(self.verify(QUOTE, path="a/copy.md"), "OK")   # whole-file hash through also_at
        edited = handbook(INTRO.replace("the team", "our team"), REVIEW, RELEASE)
        (self.root / "a" / "copy.md").write_text(edited)
        self.assertEqual(self.verify(QUOTE, path="a/copy.md"), "CHANGED")   # the copy's passages are not evidence
        (self.root / "b" / "copy.md").write_text(edited)
        self.assertEqual(self.verify(QUOTE, path="b/copy.md"), "OK")   # the kept file's own passage is

    def test_an_index_run_repairs_a_state_file_holding_null(self):
        self.cfg.state_path.write_text("null")
        self.assertIn("cannot be read", store.format_warning(self.cfg))
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(self.run_index(self.cfg, changed=True)["mode"], "full")
        self.assertEqual(store.read_state(self.cfg)["last_index"]["index_format"], store.INDEX_FORMAT)
        self.assertIsNone(store.format_warning(self.cfg))

    def test_a_marker_written_for_another_table_does_not_vouch_for_this_one(self):
        other = make_cfg(self.root, self.cfg.state_dir)   # same state folder, another table
        self.addCleanup(drop_tables, other)
        self.strip_to_format_1()   # this table now holds rows of format 1
        self.run_index(other)      # a format-2 run into the other table rewrites last_index
        self.assertIn("the index in %s has format unknown" % store.index_table(self.cfg),
                      store.format_warning(self.cfg))
        self.assertIsNone(store.format_warning(other))
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(self.run_index(self.cfg, changed=True)["mode"], "full")
        self.assertTrue(all(sha for _, sha, _ in self.rows()))

    def test_an_index_run_repairs_a_state_file_it_cannot_read(self):
        self.cfg.state_path.chmod(0)
        self.addCleanup(lambda: self.cfg.state_path.exists() and self.cfg.state_path.chmod(0o600))
        self.assertIn("cannot be read (PermissionError)", store.format_warning(self.cfg))
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(self.run_index(self.cfg, changed=True)["mode"], "full")
        self.assertTrue(os.access(self.cfg.state_path, os.R_OK))
        self.assertEqual(store.read_state(self.cfg)["last_index"]["index_format"], store.INDEX_FORMAT)
        self.assertIsNone(store.format_warning(self.cfg))

    def test_an_edit_between_invalid_bytes_inside_the_passage_is_changed(self):
        # \xff and \xfe both decode to U+FFFD, so the decoded passage text is the same before and after
        body = REVIEW.replace("two review rounds", "two review rounds (A\xffB)")
        head = handbook(INTRO, RELEASE, LIMITS, "\n").encode()
        self.doc.write_bytes(head + body.encode("latin-1"))
        self.run_index(self.cfg)
        self.doc.write_bytes(head + body.replace("\xff", "\xfe").encode("latin-1"))
        self.assertEqual(self.verify("Every change gets two review rounds"), "CHANGED")

    def test_ask_end_to_end_with_an_edited_file(self):
        from cerebrollm import answer
        generated = '"%s" [handbook.md]' % QUOTE

        def ask():
            return answer.ask(self.cfg, "how many review rounds does a change get", rerank_on=False,
                              generate=lambda prompt: generated, has=lambda term: True)
        self.doc.write_text(handbook(INTRO.replace("the team", "our team"), REVIEW, RELEASE, LIMITS))
        res = ask()
        self.assertFalse(res["abstained"])
        self.assertEqual([c["verify"] for c in res["citations"]], ["OK"])
        self.assertEqual(res["answer"], generated)
        self.doc.write_text(handbook(INTRO, REVIEW.replace("the tests", "the docs"), RELEASE, LIMITS))
        res = ask()
        self.assertTrue(res["abstained"])
        self.assertEqual([c["verify"] for c in res["citations"]], ["CHANGED"])


class TestFormatState(unittest.TestCase):
    """store.index_format and store.older_format on state.json contents, for table "db.data_t"."""

    def test_formats(self):
        t = "db.data_t"
        cases = [({}, None, False),
                 ({"last_index": {"mode": "full"}}, 1, True),                    # 0.2.0 and earlier
                 ({"last_index": {"mode": "full", "index_format": 2, "index_table": t}}, 2, False),
                 ({"last_index": {"mode": "full", "index_format": 2, "index_table": "db.data_u"}}, None, True),
                 ({"last_index": {"mode": "full", "index_format": 2}}, None, True),   # no table named
                 ({"last_index": {"mode": "full"}, "index_format": 2}, 1, True),  # a run by older code after this one
                 ({"last_index": {"mode": "full", "index_format": None, "index_table": t}}, None, True),
                 ({"last_index": {"mode": "full", "index_format": "2", "index_table": t}}, None, True),
                 ({"last_index": {"mode": "full", "index_format": True, "index_table": t}}, None, True)]
        for state, fmt, older in cases:
            self.assertEqual(store.index_format(state, t), fmt, state)
            self.assertEqual(store.older_format(state, t), older, state)


class TestFormatWarning(unittest.TestCase):
    """The warning line of status, search, verify and ask, from state.json alone (no Postgres or Ollama)."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=SCRATCH)
        self.addCleanup(self.tmp.cleanup)
        self.cfg = make_cfg(Path(self.tmp.name), Path(self.tmp.name) / "state")

    def write_raw(self, raw):
        self.cfg.state_dir.mkdir(parents=True, exist_ok=True)
        self.cfg.state_path.write_text(raw)

    def write_state(self, **state):
        self.write_raw(json.dumps(state))

    def run_cli(self, argv):
        out, err = io.StringIO(), io.StringIO()
        result = {"question": "q", "model": "m", "answer": answer_text(), "generator_text": "", "show_text": False,
                  "abstained": True, "absent_terms": [], "citations": [], "hits": [], "timings": {}}
        with mock.patch.object(config, "load", return_value=self.cfg), \
                mock.patch("cerebrollm.verify.run_verify", return_value=("OK", "detail")), \
                mock.patch("cerebrollm.search.run_search", return_value=[]), \
                mock.patch("cerebrollm.answer.ask", return_value=result), \
                mock.patch("cerebrollm.status.collect", return_value={}), \
                mock.patch("cerebrollm.status.format_status", return_value="status text"), \
                contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            cli.main(argv)
        return out.getvalue(), err.getvalue()

    COMMANDS = (["status"], ["search", "q", "--json"], ["verify", "a.md", "some quote"], ["ask", "q", "--json"])

    def test_an_older_index_prints_one_warning_line_on_stderr(self):
        self.write_state(last_index={"mode": "full"})   # 0.2.0 wrote no index_format
        for argv in self.COMMANDS:
            out, err = self.run_cli(argv)
            self.assertEqual(err.count("\n"), 1, argv)
            self.assertTrue(err.startswith("WARNING: the index in %s has format 1 and this cerebrollm needs 2;"
                                           % store.index_table(self.cfg)), argv)
            self.assertNotIn("WARNING", out, argv)
        out, _ = self.run_cli(["ask", "q", "--json"])
        self.assertTrue(json.loads(out)["abstained"])   # stdout still parses

    def test_a_current_index_or_no_index_prints_nothing(self):
        current = {"mode": "full", "index_format": store.INDEX_FORMAT, "index_table": store.index_table(self.cfg)}
        for state in ({"last_index": current}, {}):
            self.write_state(**state)
            for argv in self.COMMANDS:
                self.assertEqual(self.run_cli(argv)[1], "", (state, argv))

    def test_a_broken_state_file_warns_and_the_command_still_runs(self):
        for raw in ('{"last_index": {"mode": "fu', json.dumps({"last_index": {"mode": "full", "index_format": None}})):
            self.write_raw(raw)
            for argv in self.COMMANDS:
                out, err = self.run_cli(argv)
                self.assertEqual(err.count("\n"), 1, (raw, argv))
                self.assertTrue(err.startswith("WARNING:"), (raw, argv))
                self.assertTrue(out.strip(), (raw, argv))

    def test_a_state_file_that_is_not_an_object_warns_and_is_replaced_on_write(self):
        for raw in ("null", "[1, 2]"):
            self.write_raw(raw)
            self.assertIn("cannot be read", store.format_warning(self.cfg))
            with self.assertRaises(ValueError):
                store.read_state(self.cfg)
            store.write_state(self.cfg, last_index={"mode": "full", "index_format": store.INDEX_FORMAT,
                                                    "index_table": store.index_table(self.cfg)})
            self.assertEqual(store.read_state(self.cfg)["last_index"]["mode"], "full")
            self.assertIsNone(store.format_warning(self.cfg))

    def test_a_failing_check_still_runs_the_command(self):
        with mock.patch.object(store, "format_warning", side_effect=RuntimeError("boom")):
            out, err = self.run_cli(["verify", "a.md", "some quote"])
        self.assertEqual(out, "OK  detail\n")
        self.assertEqual(err, "WARNING: the index format check failed: RuntimeError\n")

    def test_index_prints_no_warning_line(self):
        self.write_state(last_index={"mode": "full"})
        with mock.patch("cerebrollm.indexer.run_index", return_value={"mode": "full"}):
            out, err = self.run_cli(["index", "--changed"])
        self.assertEqual(err, "")
        self.assertEqual(json.loads(out), {"mode": "full"})


def answer_text():
    from cerebrollm import answer
    return answer.ABSTAIN


if __name__ == "__main__":
    unittest.main()
