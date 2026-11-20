"""A PDF through the whole pipeline against the real Postgres and Ollama: index, search, verify, ask, status.
Skipped with the cause when either is down or the pdf extra is missing. Own table (a new name each run, dropped afterwards) and state directory."""
import copy
import tempfile
import unittest
import uuid
from pathlib import Path

from cerebrollm import answer, config, search, status, store, verify
from cerebrollm.indexer import run_index
from tests import SCRATCH
from tests.pdf_fixture import make_pdf
from tests.test_end_to_end import REASON as SERVICES_DOWN

try:
    import pypdf  # noqa: F401
    NO_EXTRA = None
except ImportError:
    NO_EXTRA = "the pdf extra is not installed (pip install 'cerebrollm[pdf]')"

REASON = SERVICES_DOWN or NO_EXTRA
QUOTE = "The zephyrpdf retry limit is 3 attempts."


@unittest.skipIf(REASON, REASON or "")
class TestPdfEndToEnd(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(dir=SCRATCH)
        cls.root = Path(cls.tmp.name) / "corpus"
        cls.root.mkdir()
        (cls.root / "report.pdf").write_bytes(make_pdf([
            ["Release notes."],                                      # a short first page, not merged into page 2
            None,
            [QUOTE, "The default port is 8080."],
        ]))
        (cls.root / "scan.pdf").write_bytes(make_pdf([None, None]))
        (cls.root / "notes.md").write_text("# Notes\n\nA plain Markdown note about review rounds.\n")
        data = copy.deepcopy(config.load().data)
        data["domain"] = "org"
        data["state_dir"] = str(Path(cls.tmp.name) / "state")
        data["postgres"]["table"] = "cerebrollm_test_pdf_" + uuid.uuid4().hex[:12]   # unique per run: parallel runs share the database
        data["root"] = [{"name": "fx", "kind": "dir", "path": str(cls.root), "ref": "file"}]
        data["rule"] = [{"root": "fx", "glob": "**/*.md", "tier": "T2", "status": "current"},
                        {"root": "fx", "glob": "**/*.pdf", "tier": "T2", "status": "current"}]
        cls.cfg = config.Config(data, Path("test"))

    @classmethod
    def tearDownClass(cls):
        with store.sql(cls.cfg) as cur:
            cur.execute("drop table if exists %s" % cls.cfg.data_table)
            cur.execute("drop table if exists %s" % cls.cfg.next_data_table)
        cls.tmp.cleanup()

    def test_flow(self):
        cfg = self.cfg
        summary = run_index(cfg)
        self.assertEqual(summary["documents"], 2)                    # notes.md and report.pdf; scan.pdf is skipped
        self.assertEqual(summary["pdf"], {"indexed": 1, "no_text_layer": 1})
        self.assertEqual(summary["chunks_located"], summary["chunks_embedded"])

        hits = search.run_search(cfg, "zephyrpdf retry limit attempts", k=5, mode="lexical")
        pdf_hits = [h for h in hits if h["path"] == "report.pdf"]
        self.assertTrue(pdf_hits)
        self.assertEqual((pdf_hits[0]["page_start"], pdf_hits[0]["page_end"]), (3, 3))
        self.assertIn("report.pdf (page 3)@file", search.format_hits(pdf_hits[:1]).splitlines()[0])
        self.assertIn(QUOTE, pdf_hits[0]["text"])
        page_one = search.run_search(cfg, "Release notes", k=5, mode="lexical")
        self.assertEqual([(h["page_start"], h["page_end"]) for h in page_one if h["path"] == "report.pdf"
                          and "Release notes." in h["text"]], [(1, 1)])
        md = [h for h in search.run_search(cfg, "plain Markdown note", k=5, mode="lexical") if h["path"] == "notes.md"]
        self.assertEqual((md[0]["page_start"], md[0]["page_end"]), (None, None))

        self.assertEqual(verify.run_verify(cfg, "report.pdf", QUOTE)[0], "OK")
        self.assertEqual(verify.run_verify(cfg, "report.pdf", "The zephyrpdf retry limit is 9 attempts.")[0], "MISSING")
        self.assertEqual(verify.run_verify(cfg, "scan.pdf", "anything at all here")[0], "MISSING")

        result = answer.ask(cfg, "What is the zephyrpdf retry limit?", rerank_on=False,
                            generate=lambda prompt: '"%s" [report.pdf]' % QUOTE, has=lambda term: True)
        self.assertFalse(result["abstained"])
        self.assertEqual(result["answer"], '"%s" [report.pdf (page 3)]' % QUOTE)
        self.assertEqual(result["citations"][0]["page"], "page 3")

        text = status.format_status(cfg, status.collect(cfg))
        self.assertIn("pdf files: indexed 1  skipped without a text layer 1  skipped unreadable 0", text)

        # the file changes on disk: the quote is still on the page, the bytes are not the indexed bytes
        (self.root / "report.pdf").write_bytes(make_pdf([["Release notes."], None, [QUOTE, "The default port is 9090."]]))
        self.assertEqual(verify.run_verify(cfg, "report.pdf", QUOTE)[0], "CHANGED")


@unittest.skipIf(REASON, REASON or "")
class TestPdfRollback(unittest.TestCase):
    """Stop indexing PDFs when they are more than half of the live index: the full index refuses the swap, the
    live index stays, and the documented procedure (drop the live table, index again) replaces it."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(dir=SCRATCH)
        root = Path(cls.tmp.name) / "corpus"
        root.mkdir()
        for name in ("a.pdf", "b.pdf", "c.pdf"):
            (root / name).write_bytes(make_pdf([["The zephyrpdf rollback marker %s is here." % name], ["Page two of %s." % name]]))
        (root / "notes.md").write_text("# Notes\n\nA plain Markdown note about review rounds.\n")
        data = copy.deepcopy(config.load().data)
        data["domain"] = "org"
        data["state_dir"] = str(Path(cls.tmp.name) / "state")
        data["postgres"]["table"] = "cerebrollm_test_pdf_" + uuid.uuid4().hex[:12]
        data["root"] = [{"name": "fx", "kind": "dir", "path": str(root), "ref": "file"}]
        rules = [{"root": "fx", "glob": "**/*.md", "tier": "T2", "status": "current"}]
        cls.with_pdf = config.Config(copy.deepcopy(dict(data, rule=rules + [
            {"root": "fx", "glob": "**/*.pdf", "tier": "T2", "status": "current"}])), Path("test"))
        cls.without_pdf = config.Config(copy.deepcopy(dict(data, rule=rules)), Path("test"))

    @classmethod
    def tearDownClass(cls):
        with store.sql(cls.with_pdf) as cur:
            cur.execute("drop table if exists %s" % cls.with_pdf.data_table)
            cur.execute("drop table if exists %s" % cls.with_pdf.next_data_table)
        cls.tmp.cleanup()

    def test_procedure(self):
        index = run_index(self.with_pdf)
        self.assertEqual(index["pdf"]["indexed"], 3)
        self.assertTrue(search.run_search(self.with_pdf, "zephyrpdf rollback marker", mode="lexical"))

        live = store.row_count(self.with_pdf, self.with_pdf.data_table)
        with self.assertRaises(SystemExit) as refused:                 # the PDFs are more than half of the live rows
            run_index(self.without_pdf)
        self.assertIn("refusing to swap", str(refused.exception))
        self.assertEqual(store.row_count(self.without_pdf, self.without_pdf.data_table), live)   # the live index is as it was
        # search already hides rows of a path that no rule admits; only the rebuild removes them
        self.assertFalse(search.run_search(self.without_pdf, "zephyrpdf rollback marker", mode="lexical"))

        store.drop_table(self.without_pdf, self.without_pdf.data_table)    # the documented step
        again = run_index(self.without_pdf)
        self.assertEqual(again["documents"], 1)
        self.assertLess(store.row_count(self.without_pdf, self.without_pdf.data_table), live)   # the PDF rows are gone
        self.assertEqual(verify.run_verify(self.without_pdf, "a.pdf", "The zephyrpdf rollback marker a.pdf is here.")[0],
                         "MISSING")                                    # no rule, so no index and no answer


if __name__ == "__main__":
    unittest.main()
