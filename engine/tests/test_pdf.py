"""PDF documents: one bytes-to-text function (documents.read_text) shared by the corpus reader, `verify`
and `search`; each page is its own section; hits and citations name the page; a PDF without a text layer
is skipped and counted. No database. The tests that read a real PDF need the extra `cerebrollm[pdf]`."""
import copy
import datetime
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from cerebrollm import answer, config, corpus, documents, indexer, search, status, verify
from tests import SCRATCH
from tests.pdf_fixture import make_pdf

try:
    import pypdf  # noqa: F401
    NEEDS_EXTRA = None
except ImportError:
    NEEDS_EXTRA = "the pdf extra is not installed (pip install 'cerebrollm[pdf]')"

PAGES = [
    ["Release notes 1.0", "The default port is 8080."],
    None,                                                  # a page with no text layer
    ["The retry limit is 3 attempts.", "Set the flag (see the guide) to enable it."],
]


@unittest.skipIf(NEEDS_EXTRA, NEEDS_EXTRA or "")
class TestReadText(unittest.TestCase):
    def setUp(self):
        documents._pdf_text.cache_clear()

    def test_each_page_with_text_is_a_section_and_keeps_its_number(self):
        text, pages = documents.read_text(make_pdf(PAGES), "r.pdf")
        self.assertEqual(text, "## Page 1\n\nRelease notes 1.0\nThe default port is 8080.\n\n"
                               "## Page 3\n\nThe retry limit is 3 attempts.\nSet the flag (see the guide) to enable it.\n")
        self.assertEqual([p[0] for p in pages], [1, 3])          # page 2 has no text and adds nothing
        for number, start, end in pages:
            self.assertTrue(text[start:end].startswith("## Page %d\n" % number))

    def test_page_range_names_the_page_holding_a_span(self):
        text, pages = documents.read_text(make_pdf(PAGES), "r.pdf")
        at = text.index("retry limit")
        self.assertEqual(documents.page_range(pages, at, at + 20), (3, 3))
        self.assertEqual(documents.page_range(pages, 0, len(text)), (1, 3))
        self.assertEqual(documents.page_range(None, 0, 5), (None, None))
        self.assertEqual(documents.page_range(pages, -1, -1), (None, None))
        self.assertEqual(documents.page_label(3, 3), "page 3")
        self.assertEqual(documents.page_label(1, 3), "pages 1-3")
        self.assertIsNone(documents.page_label(None, None))

    def test_extraction_is_repeatable(self):
        data = make_pdf(PAGES)
        first = documents.read_text(data, "r.pdf")
        documents._pdf_text.cache_clear()
        self.assertEqual(documents.read_text(data, "r.pdf"), first)

    def test_a_pdf_without_any_text_is_refused(self):
        with self.assertRaises(documents.NoTextLayer):
            documents.read_text(make_pdf([None, None]), "scan.pdf")

    def test_damaged_bytes_are_refused(self):
        with self.assertRaises(documents.Unreadable):
            documents.read_text(b"%PDF-1.4\nnot a pdf at all", "bad.pdf")
        with self.assertRaises(documents.Unreadable):
            documents.read_text(b"", "empty.pdf")

    def test_a_markdown_file_is_its_decoded_bytes(self):
        self.assertEqual(documents.read_text("# T\n\n\xe9 caf\xe9\n".encode(), "a.md"), ("# T\n\n\xe9 caf\xe9\n", None))
        self.assertEqual(documents.read_text(b"a\xffb", "a.md")[0], "a�b")


class TestExtraMissing(unittest.TestCase):
    def test_a_pdf_is_refused_with_the_install_line_when_pypdf_is_absent(self):
        documents._pdf_text.cache_clear()
        with mock.patch.dict(sys.modules, {"pypdf": None}):   # an import of None raises ImportError
            with self.assertRaises(documents.ExtraMissing) as raised:
                documents.read_text(make_pdf(PAGES), "r.pdf")
        self.assertIn("cerebrollm[pdf]", str(raised.exception))
        self.assertEqual(raised.exception.code, "extra_missing")

    def test_other_files_never_need_the_extra(self):
        with mock.patch.dict(sys.modules, {"pypdf": None}):
            self.assertEqual(documents.read_text(b"# Plain\n", "a.md")[0], "# Plain\n")


class Fixture(unittest.TestCase):
    """A folder with one Markdown file and PDFs, and a config that adds a *.pdf rule."""
    PDFS = {"docs/report.pdf": PAGES, "docs/scan.pdf": [None, None]}

    def setUp(self):
        documents._pdf_text.cache_clear()
        self.tmp = tempfile.TemporaryDirectory(dir=SCRATCH)
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "docs").mkdir()
        (self.root / "docs/notes.md").write_text("# Notes\n\nPlain notes about the port 8080 setting.\n")
        for rel, pages in self.PDFS.items():
            (self.root / rel).write_bytes(make_pdf(pages))
        (self.root / "docs/broken.pdf").write_bytes(b"%PDF-1.4\ngarbage")
        data = copy.deepcopy(config.load().data)
        data["root"] = [{"name": "fx", "kind": "dir", "path": str(self.root), "ref": "file"}]
        data["rule"] = [{"root": "fx", "glob": "**/*.md", "tier": "T2", "status": "current"},
                        {"root": "fx", "glob": "**/*.pdf", "tier": "T2", "status": "current"}]
        self.cfg = config.Config(data, Path("test"))

    def verify_ok(self, path, quote):
        with mock.patch.object(verify, "_indexed_sha", side_effect=lambda cfg, root, rel, ref: {
                hashlib.sha256(corpus.read_source(cfg.roots[root], rel, ref)).hexdigest()}):
            return verify.run_verify(self.cfg, path, quote)[0]


@unittest.skipIf(NEEDS_EXTRA, NEEDS_EXTRA or "")
class TestCorpus(Fixture):
    def test_pdf_is_read_per_page_and_skips_are_counted(self):
        entries, scan = corpus.enumerate_corpus(self.cfg)
        paths = {e["path"] for e in entries}
        self.assertEqual(paths, {"docs/notes.md", "docs/report.pdf"})
        self.assertEqual(scan["pdf"], {"indexed": 1, "no_text_layer": 1, "unreadable": 1})
        report = next(e for e in entries if e["path"] == "docs/report.pdf")
        self.assertIn("## Page 3\n\nThe retry limit is 3 attempts.", report["text"])
        raw = (self.root / "docs/report.pdf").read_bytes()
        self.assertEqual(report["sha256"], hashlib.sha256(raw).hexdigest())   # the hash stays over the file's bytes

    def test_indexed_text_is_exactly_the_text_verify_reads(self):
        entries, _ = corpus.enumerate_corpus(self.cfg)
        report = next(e for e in entries if e["path"] == "docs/report.pdf")
        data = corpus.read_source(self.cfg.roots["fx"], "docs/report.pdf")
        self.assertEqual(documents.read_text(data, "docs/report.pdf")[0], report["text"])
        self.assertEqual(self.verify_ok("docs/report.pdf", "The retry limit is 3 attempts."), "OK")
        self.assertEqual(self.verify_ok("docs/report.pdf", "The retry limit is 9 attempts."), "MISSING")
        self.assertEqual(self.verify_ok("docs/report.pdf", "Set the flag (see the guide) to enable it."), "OK")
        # the "## Page N" line is indexed text but not text of the PDF, so a quote is never checked against it
        self.assertEqual(self.verify_ok("docs/report.pdf", "## Page 3"), "MISSING")
        self.assertEqual(self.verify_ok("docs/report.pdf", "## Page 2"), "MISSING")

    def test_a_quote_across_a_page_break_does_not_verify(self):
        self.assertEqual(self.verify_ok("docs/report.pdf", "The default port is 8080. The retry limit is 3 attempts."),
                         "MISSING")

    def test_a_pdf_the_index_skipped_answers_as_absent(self):
        self.assertEqual(self.verify_ok("docs/scan.pdf", "anything at all here"), "MISSING")
        self.assertEqual(self.verify_ok("docs/broken.pdf", "anything at all here"), "MISSING")

    def test_the_default_rules_do_not_admit_pdfs(self):
        data = copy.deepcopy(self.cfg.data)
        data["rule"] = [r for r in config.load().data["rule"]]
        data["root"] = [{"name": "notes", "kind": "dir", "path": str(self.root), "ref": "file"}]
        entries, _ = corpus.enumerate_corpus(config.Config(data, Path("test")))
        self.assertFalse([e for e in entries if e["path"].endswith(".pdf")])
        self.assertFalse(any(".pdf" in r.get("glob", "") for r in config.load().data["rule"]))


class TestCorpusWithoutExtra(Fixture):
    def test_pdfs_are_skipped_and_status_has_one_line(self):
        with mock.patch.dict(sys.modules, {"pypdf": None}):
            entries, scan = corpus.enumerate_corpus(self.cfg)
        self.assertEqual({e["path"] for e in entries}, {"docs/notes.md"})
        self.assertEqual(scan["pdf"], {"extra_missing": 3})
        text = self.status_text(scan["pdf"])
        lines = [ln for ln in text.splitlines() if ln.startswith("pdf files")]
        self.assertEqual(len(lines), 1)
        self.assertIn("pip install 'cerebrollm[pdf]'", lines[0])
        self.assertIn("3", lines[0])

    def status_text(self, pdf):
        state = {"last_index": {"pdf": pdf}}
        with mock.patch("cerebrollm.store.read_state", lambda c: state), \
                mock.patch("cerebrollm.store.table_exists", lambda c: False):
            return status.format_status(self.cfg, status.collect(self.cfg))

    def test_status_counts_for_an_indexed_set(self):
        text = self.status_text({"indexed": 2, "no_text_layer": 1, "unreadable": 1})
        self.assertIn("pdf files: indexed 2  skipped without a text layer 1  skipped unreadable 1", text)
        self.assertNotIn("pip install", text)
        self.assertNotIn("pdf files", self.status_text({}))


@unittest.skipIf(NEEDS_EXTRA, NEEDS_EXTRA or "")
class TestChunks(unittest.TestCase):
    def chunks(self, pages):
        documents._pdf_text.cache_clear()
        text, page_map = documents.read_text(make_pdf(pages), "r.pdf")
        entry = {"domain": "org", "project": "example", "tier": "T2", "status": "current", "path": "r.pdf",
                 "root": "fx", "ref": "file", "sha256": "0" * 64, "mtime": "2026-11-01T00:00:00+00:00",
                 "also_at": [], "text": text}
        docs = indexer.make_documents([entry])
        texts = {d.doc_id: d.text for d in docs}
        nodes = docs
        for step in indexer.chunk_steps(config.load(), texts):
            nodes = step(nodes)
        return nodes, text, page_map

    def test_every_page_is_its_own_section_even_when_short(self):
        nodes, text, page_map = self.chunks([["Short one."], ["Short two."], ["Short three."]])
        self.assertEqual(len(nodes), 3)            # without the rule, MergeSmall would join these three
        for node, expected in zip(nodes, (1, 2, 3)):
            self.assertEqual(documents.page_range(page_map, node.metadata["char_start"], node.metadata["char_end"]),
                             (expected, expected))
            self.assertEqual(node.metadata["heading_path"], "Page %d" % expected)
        self.assertIn("Short two.", nodes[1].text)
        self.assertNotIn("Short one.", nodes[1].text)

    def test_a_long_page_splits_inside_its_page(self):
        long_page = ["Sentence number %d describes one setting of the tool in some detail." % i for i in range(1, 60)]
        nodes, text, page_map = self.chunks([long_page, ["Last page."]])
        spans = [documents.page_range(page_map, n.metadata["char_start"], n.metadata["char_end"]) for n in nodes]
        self.assertGreater(len(nodes), 2)
        self.assertEqual(spans[-1], (2, 2))
        self.assertTrue(all(s == (1, 1) for s in spans[:-1]), spans)

    def test_a_markdown_file_named_like_a_page_is_still_merged(self):
        entry = {"domain": "org", "project": "example", "tier": "T2", "status": "current", "path": "a.md",
                 "root": "fx", "ref": "file", "sha256": "0" * 64, "mtime": "2026-11-01T00:00:00+00:00",
                 "also_at": [], "text": "## Page 1\n\nShort.\n\n## Page 2\n\nAlso short.\n"}
        docs = indexer.make_documents([entry])
        nodes = docs
        for step in indexer.chunk_steps(config.load(), {docs[0].doc_id: docs[0].text}):
            nodes = step(nodes)
        self.assertEqual(len(nodes), 1)


@unittest.skipIf(NEEDS_EXTRA, NEEDS_EXTRA or "")
class TestHitsAndCitations(Fixture):
    def hit(self, text, page_start, page_end, path="docs/report.pdf"):
        return {"rank": 1, "score": 0.5, "tier": "T2", "status": "current", "path": path, "line_start": 1,
                "line_end": 3, "page_start": page_start, "page_end": page_end, "ref": "file", "project": "p",
                "heading_path": "Page %s" % page_start, "sha256": "ab" * 32, "source_unchanged": True,
                "also_at": [], "text": text}

    def test_line_span_returns_the_pages_of_a_pdf_passage(self):
        entries, _ = corpus.enumerate_corpus(self.cfg)
        report = next(e for e in entries if e["path"] == "docs/report.pdf")
        start = report["text"].index("The retry limit")
        meta = {"char_start": start, "char_end": start + 30, "ref": "file", "path": "docs/report.pdf",
                "sha256": report["sha256"]}
        first, last, fresh, page_first, page_last = search._line_span(self.cfg, meta)
        self.assertEqual((page_first, page_last, fresh), (3, 3, True))
        self.assertEqual(first, report["text"].count("\n", 0, start) + 1)
        md = {"char_start": 0, "char_end": 9, "ref": "file", "path": "docs/notes.md",
              "sha256": next(e for e in entries if e["path"] == "docs/notes.md")["sha256"]}
        self.assertEqual(search._line_span(self.cfg, md)[3:], (None, None))

    def test_a_hit_prints_its_page(self):
        line = search.format_hits([self.hit("The retry limit is 3 attempts.", 3, 3)]).splitlines()[0]
        self.assertIn(" docs/report.pdf (page 3)@file ", line)
        self.assertNotIn(" L1-3@", line)
        spanning = search.format_hits([self.hit("x", 1, 2)]).splitlines()[0]
        self.assertIn("docs/report.pdf (pages 1-2)@file", spanning)
        plain = dict(self.hit("x", None, None, path="docs/notes.md"))
        self.assertIn("docs/notes.md L1-3@file", search.format_hits([plain]))

    def test_the_prompt_names_the_page_and_a_cited_page_label_is_dropped_from_the_path(self):
        self.assertTrue(answer.format_hit(self.hit("body", 3, 3)).startswith("Source: docs/report.pdf (page 3) > Page 3\n"))
        self.assertTrue(answer.format_hit(self.hit("body", None, None, "a.md")).startswith("Source: a.md (lines 1-3)"))
        for cited in ("docs/report.pdf (page 3)", "docs/report.pdf (pages 1-2)", "docs/report.pdf"):
            self.assertEqual(answer.extract_citations('"The retry limit is 3 attempts." [%s]' % cited),
                             [("docs/report.pdf", "The retry limit is 3 attempts.")])

    def test_ask_prints_the_page_of_a_verified_pdf_quote(self):
        hits = [self.hit("The default port is 8080.", 1, 1), self.hit("The retry limit is 3 attempts.", 3, 3)]
        raw = '"The retry limit is 3 attempts." [docs/report.pdf]'
        with mock.patch.object(answer, "check_quote", return_value=("OK", "fine", "ab" * 32)):
            citations = answer.check_citations(self.cfg, raw, {"docs/report.pdf"}, hits)
        self.assertEqual(citations[0]["page"], "page 3")
        self.assertEqual(answer.verified_quotes(citations), '"The retry limit is 3 attempts." [docs/report.pdf (page 3)]')

    def test_a_quote_no_single_passage_holds_prints_without_a_page(self):
        hits = [self.hit("The default port is 8080.", 1, 1)]
        raw = '"The retry limit is 3 attempts." [docs/report.pdf]'
        with mock.patch.object(answer, "check_quote", return_value=("OK", "fine", "ab" * 32)):
            citations = answer.check_citations(self.cfg, raw, {"docs/report.pdf"}, hits)
        self.assertIsNone(citations[0]["page"])
        self.assertEqual(answer.verified_quotes(citations), '"The retry limit is 3 attempts." [docs/report.pdf]')

    def test_a_page_is_named_only_for_the_version_that_verified(self):
        # the passage was indexed from a file whose quote sat on page 1; the file was then replaced and
        # re-indexed with the quote on page 2, so verify answers OK for the new bytes
        old = make_pdf([["The retry limit is 3 attempts."], ["Other text."]])
        new = make_pdf([["Other text."], ["The retry limit is 3 attempts."]])
        (self.root / "docs/report.pdf").write_bytes(new)
        documents._pdf_text.cache_clear()
        raw = '"The retry limit is 3 attempts." [docs/report.pdf]'
        stale = dict(self.hit("The retry limit is 3 attempts.", 1, 1), sha256=hashlib.sha256(old).hexdigest())
        with mock.patch.object(verify, "_indexed_sha", return_value={hashlib.sha256(new).hexdigest()}):
            citations = answer.check_citations(self.cfg, raw, {"docs/report.pdf"}, [stale])
            self.assertEqual(citations[0]["verify"], "OK")
            self.assertIsNone(citations[0]["page"])
            self.assertEqual(answer.verified_quotes(citations), '"The retry limit is 3 attempts." [docs/report.pdf]')
            current = dict(stale, sha256=hashlib.sha256(new).hexdigest(), page_start=2, page_end=2)
            citations = answer.check_citations(self.cfg, raw, {"docs/report.pdf"}, [current])
            self.assertEqual(citations[0]["page"], "page 2")

    def test_a_generated_heading_does_not_give_a_page_to_a_quote_found_on_another_page(self):
        # only page 2 holds the text "## Page 1"; the passage of page 1 has that line only as its generated heading
        data = make_pdf([["alpha"], ["## Page 1"]])
        (self.root / "docs/report.pdf").write_bytes(data)
        documents._pdf_text.cache_clear()
        sha = hashlib.sha256(data).hexdigest()
        hits = [dict(self.hit("## Page 1\n\nalpha", 1, 1), sha256=sha), dict(self.hit("## Page 2\n\n## Page 1", 2, 2), sha256=sha)]
        with mock.patch.object(verify, "_indexed_sha", return_value={sha}):
            citations = answer.check_citations(self.cfg, '"## Page 1" [docs/report.pdf]', {"docs/report.pdf"}, hits)
        self.assertEqual(citations[0]["verify"], "OK")
        self.assertNotEqual(citations[0]["page"], "page 1")
        self.assertEqual(documents.without_page_headings("## Page 2\n\nbody\n## Page 3\n\nmore"), "\n\nbody\n\n\nmore")

    def test_markdown_citations_are_unchanged(self):
        raw = '"Plain notes about the port 8080 setting." [docs/notes.md]'
        with mock.patch.object(answer, "check_quote", return_value=("OK", "fine", "ab" * 32)):
            citations = answer.check_citations(self.cfg, raw, {"docs/notes.md"}, [self.hit("x", None, None, "docs/notes.md")])
        self.assertNotIn("page", citations[0])
        self.assertEqual(answer.verified_quotes(citations), '"Plain notes about the port 8080 setting." [docs/notes.md]')


class TestCitationNames(unittest.TestCase):
    def path_of(self, cited):
        return answer.extract_citations('"The retry limit is 3 attempts." [%s]' % cited)[0][0]

    def test_a_file_named_like_an_annotated_pdf_citation_is_kept(self):
        # the bracket text is exactly a retrieved path, or ends like a page label without being one
        raw = '"The retry limit is 3 attempts." [%s]'
        for name in ("manual.pdf (page 2).md", "manual.pdf (page 2).pdf", "manual (lines 3-9).md"):
            self.assertEqual(answer.extract_citations(raw % name, {name}), [(name, "The retry limit is 3 attempts.")], name)
        self.assertEqual(self.path_of("manual.pdf (page 2).md"), "manual.pdf (page 2).md")
        self.assertEqual(self.path_of("manual.pdf (page 2).pdf (page 3)"), "manual.pdf (page 2).pdf")
        self.assertEqual(answer.extract_citations(raw % "manual.pdf (page 2).pdf (page 3)", {"manual.pdf (page 2).pdf"}),
                         [("manual.pdf (page 2).pdf", "The retry limit is 3 attempts.")])

    def test_a_page_label_comes_off_only_after_a_pdf_name(self):
        self.assertEqual(self.path_of("Budget (page 2).md"), "Budget (page 2).md")
        self.assertEqual(self.path_of("Budget (page 2).md (lines 3-9) > Heading"), "Budget (page 2).md")
        self.assertEqual(self.path_of("Budget (page 2).pdf (page 3)"), "Budget (page 2).pdf")
        self.assertEqual(self.path_of("Budget (page 2).pdf"), "Budget (page 2).pdf")
        self.assertEqual(self.path_of("docs/REPORT.PDF (pages 1-2) > Page 1"), "docs/REPORT.PDF")


@unittest.skipIf(NEEDS_EXTRA, NEEDS_EXTRA or "")
class TestSourceOfAHit(Fixture):
    """search._line_span names a page only for the root and the bytes the passage was indexed from."""

    def meta(self, root_name, rel="docs/report.pdf"):
        root = self.cfg.roots[root_name]
        data = corpus.read_source(root, rel)
        text, _ = documents.read_text(data, rel)
        start = text.index("The retry limit")
        return {"char_start": start, "char_end": start + 30, "ref": "file", "path": rel, "root": root_name,
                "sha256": hashlib.sha256(data).hexdigest()}

    def test_the_second_root_is_read_for_a_hit_from_the_second_root(self):
        other = Path(self.tmp.name) / "other"
        (other / "docs").mkdir(parents=True)
        (other / "docs/report.pdf").write_bytes(make_pdf([["The retry limit is 3 attempts."]]))
        data = copy.deepcopy(self.cfg.data)
        data["root"].append({"name": "other", "kind": "dir", "path": str(other), "ref": "file"})
        self.cfg = config.Config(data, Path("test"))
        # the same relative path and ref in both roots: the quote is on page 3 in one and page 1 in the other
        self.assertEqual(search._line_span(self.cfg, self.meta("fx"))[2:], (True, 3, 3))
        self.assertEqual(search._line_span(self.cfg, self.meta("other"))[2:], (True, 1, 1))

    def test_a_changed_pdf_gets_no_page_and_is_flagged(self):
        meta = self.meta("fx")
        (self.root / "docs/report.pdf").write_bytes(make_pdf([["Another page."], None, ["The retry limit is 5 attempts."]]))
        documents._pdf_text.cache_clear()
        first, last, fresh, page_first, page_last = search._line_span(self.cfg, meta)
        self.assertEqual((fresh, page_first, page_last), (False, None, None))
        self.assertIn("SOURCE-CHANGED", search.format_hits([dict(
            rank=1, score=1.0, tier="T2", status="current", project="p", path="docs/report.pdf", ref="file",
            heading_path="", sha256=meta["sha256"], also_at=[], text="t", line_start=first, line_end=last,
            page_start=page_first, page_end=page_last, source_unchanged=fresh)]))

    def test_a_pdf_that_changed_into_unreadable_bytes_is_still_a_changed_source(self):
        meta = self.meta("fx")
        (self.root / "docs/report.pdf").write_bytes(b"%PDF-1.4 damaged")
        documents._pdf_text.cache_clear()
        self.assertEqual(search._line_span(self.cfg, meta), (None, None, False, None, None))


@unittest.skipIf(NEEDS_EXTRA, NEEDS_EXTRA or "")
class TestPdfQuoteMatching(Fixture):
    """verify matches a quote against one page's own text: not the generated page headings, not across a break."""
    PDFS = {"docs/one.pdf": [["alpha"]], "docs/two.pdf": [["alpha"], ["beta"]],
            "docs/lit.pdf": [["See Page 7 for the retry limit."]]}

    def test_a_quote_inside_one_page_verifies(self):
        self.assertEqual(self.verify_ok("docs/two.pdf", "alpha"), "OK")
        self.assertEqual(self.verify_ok("docs/two.pdf", "beta"), "OK")
        self.assertEqual(self.verify_ok("docs/lit.pdf", "See Page 7 for the retry limit."), "OK")
        self.assertEqual(self.verify_ok("docs/lit.pdf", "Page 7 for the retry"), "OK")

    def test_a_generated_page_heading_is_not_in_the_pdf(self):
        self.assertEqual(self.verify_ok("docs/one.pdf", "Page 1"), "MISSING")
        self.assertEqual(self.verify_ok("docs/one.pdf", "## Page 1"), "MISSING")
        self.assertEqual(self.verify_ok("docs/lit.pdf", "Page 1"), "MISSING")

    def test_a_quote_across_a_page_break_does_not_verify(self):
        self.assertEqual(self.verify_ok("docs/two.pdf", "alpha ## Page 2 beta"), "MISSING")
        self.assertEqual(self.verify_ok("docs/two.pdf", "alpha beta"), "MISSING")

    def test_page_bodies_are_the_text_after_each_heading(self):
        text, pages = documents.read_text(make_pdf([["alpha", "gamma"], None, ["beta"]]), "r.pdf")
        self.assertEqual(documents.page_bodies(text, pages), ["alpha\ngamma", "beta"])
        self.assertEqual(documents.page_bodies("# plain\n", None), ["# plain\n"])


@unittest.skipIf(NEEDS_EXTRA, NEEDS_EXTRA or "")
class TestPageSections(unittest.TestCase):
    def test_an_open_code_fence_on_one_page_does_not_swallow_the_next_page(self):
        documents._pdf_text.cache_clear()
        data = make_pdf([["```python", "print(1)"], ["Second page text."], ["~~~", "Third page text."]])
        text, pages = documents.read_text(data, "r.pdf")
        self.assertIn('\n\\```python\n', text)
        self.assertIn('\n\\~~~\n', text)
        entry = {"domain": "org", "project": "example", "tier": "T2", "status": "current", "path": "r.pdf",
                 "root": "fx", "ref": "file", "sha256": "0" * 64, "mtime": "2026-11-01T00:00:00+00:00",
                 "also_at": [], "text": text}
        docs = indexer.make_documents([entry])
        nodes = docs
        for step in indexer.chunk_steps(config.load(), {docs[0].doc_id: docs[0].text}):
            nodes = step(nodes)
        self.assertEqual([n.metadata["heading_path"] for n in nodes], ["Page 1", "Page 2", "Page 3"])
        self.assertEqual([documents.page_range(pages, n.metadata["char_start"], n.metadata["char_end"]) for n in nodes],
                         [(1, 1), (2, 2), (3, 3)])


@unittest.skipIf(NEEDS_EXTRA, NEEDS_EXTRA or "")
class TestRepeatedRows(unittest.TestCase):
    """The same table row on two pages (or in two sections) is two passages, each at its own place."""
    ROWS = ["| Name | Value |", "|---|---|", "| port | 8080 |"]

    def located(self, text):
        entry = {"domain": "org", "project": "example", "tier": "T2", "status": "current", "path": "r.pdf" if text.startswith("## Page") else "r.md",
                 "root": "fx", "ref": "file", "sha256": "0" * 64, "mtime": "2026-11-01T00:00:00+00:00",
                 "also_at": [], "text": text}
        docs = indexer.make_documents([entry])
        nodes = docs
        for step in indexer.chunk_steps(config.load(), {docs[0].doc_id: docs[0].text}):
            nodes = step(nodes)
        return [n for n in nodes if "| port | 8080 |" in n.text]

    def test_the_same_row_on_two_pdf_pages_gets_two_pages(self):
        documents._pdf_text.cache_clear()
        text, pages = documents.read_text(make_pdf([self.ROWS, self.ROWS]), "r.pdf")
        rows = self.located(text)
        self.assertEqual(len(rows), 2)
        self.assertEqual([documents.page_range(pages, n.metadata["char_start"], n.metadata["char_end"]) for n in rows],
                         [(1, 1), (2, 2)])
        self.assertEqual([n.metadata["char_start"] for n in rows], [text.index("| port"), text.index("| port", text.index("| port") + 1)])

    def test_the_same_row_in_two_markdown_sections_gets_two_spans(self):
        text = "# A\n\n" + "\n".join(self.ROWS) + "\n\n# B\n\n" + "\n".join(self.ROWS) + "\n"
        rows = self.located(text)
        self.assertEqual(len(rows), 2)
        self.assertEqual(len({n.metadata["char_start"] for n in rows}), 2)
        self.assertEqual([text[n.metadata["char_start"]:n.metadata["char_end"]] for n in rows], ["| port | 8080 |"] * 2)


class OnlyPdfs(unittest.TestCase):
    """A corpus whose only admitted files are PDFs: the scan builds nothing, so the index refuses, and the
    reason has to reach the user, not only the last successful index."""

    def setUp(self):
        documents._pdf_text.cache_clear()
        self.tmp = tempfile.TemporaryDirectory(dir=SCRATCH)
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "corpus"
        self.root.mkdir()
        data = copy.deepcopy(config.load().data)
        data["state_dir"] = str(Path(self.tmp.name) / "state")
        data["root"] = [{"name": "fx", "kind": "dir", "path": str(self.root), "ref": "file"}]
        data["rule"] = [{"root": "fx", "glob": "**/*.pdf", "tier": "T2", "status": "current"}]
        self.cfg = config.Config(data, Path("test"))

    def refused(self):
        with self.assertRaises(SystemExit) as raised:
            indexer.run_index(self.cfg)
        with mock.patch("cerebrollm.store.table_exists", lambda c: False):
            return str(raised.exception), status.format_status(self.cfg, status.collect(self.cfg))

    def test_without_the_extra_the_refusal_and_status_name_the_install_command(self):
        (self.root / "a.pdf").write_bytes(make_pdf(PAGES))
        with mock.patch.dict(sys.modules, {"pypdf": None}):
            message, text = self.refused()
        self.assertIn("pip install 'cerebrollm[pdf]'", message)
        self.assertIn("found no files to index", text)
        self.assertIn("  pdf files skipped: 1 (the pdf extra is not installed", text)

    @unittest.skipIf(NEEDS_EXTRA, NEEDS_EXTRA or "")
    def test_with_only_scans_the_refusal_and_status_count_them(self):
        (self.root / "scan.pdf").write_bytes(make_pdf([None, None]))
        message, text = self.refused()
        self.assertIn("skipped without a text layer 1", message)
        self.assertIn("  pdf files: indexed 0  skipped without a text layer 1  skipped unreadable 0", text)


class TestRefusalRecord(unittest.TestCase):
    """What an index attempt that finds no files may write, and where."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=SCRATCH)
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.root = self.base / "corpus"
        self.root.mkdir()

    def cfg(self, state_dir, rule="**/*.md"):
        data = copy.deepcopy(config.load().data)
        data["state_dir"] = str(state_dir)
        data["root"] = [{"name": "fx", "kind": "dir", "path": str(self.root), "ref": "file"}]
        data["rule"] = [{"root": "fx", "glob": rule, "tier": "T2", "status": "current"}]
        return config.Config(data, Path("test"))

    def test_an_empty_root_gives_the_plain_refusal(self):
        cfg = self.cfg(self.base / "state")
        with self.assertRaises(SystemExit) as raised:
            indexer.run_index(cfg)
        self.assertEqual(str(raised.exception), "refusing to index: the corpus scan found no files (would delete everything).")
        import json
        self.assertEqual(json.loads(cfg.refused_path.read_text())["files_seen"], 0)

    def test_nothing_is_written_when_the_state_folder_is_inside_a_root(self):
        for state in (self.root / "state", self.root, self.root / "a" / "b"):
            cfg = self.cfg(state)
            before = sorted(p.name for p in self.root.rglob("*"))
            with self.assertRaises(SystemExit):
                indexer.run_index(cfg)
            self.assertEqual(sorted(p.name for p in self.root.rglob("*")), before, state)
            self.assertFalse(indexer.record_refusal(cfg, {"counts": {}, "pdf": {}}))
        self.assertTrue(indexer.state_dir_in_a_root(self.cfg(self.root / "state")))
        self.assertFalse(indexer.state_dir_in_a_root(self.cfg(self.base / "state")))
        link = self.base / "link"   # a link into the root is the root
        link.symlink_to(self.root)
        self.assertTrue(indexer.state_dir_in_a_root(self.cfg(link / "state")))

    def test_the_record_is_its_own_file_and_state_json_is_untouched(self):
        cfg = self.cfg(self.base / "state")
        cfg.state_dir.mkdir()
        cfg.state_path.write_text('{"last_index": {"documents": 7}, "last_index_time": "2026-11-01T00:00:00+0000"}')
        before = cfg.state_path.read_bytes()
        with self.assertRaises(SystemExit):
            indexer.run_index(cfg)
        self.assertEqual(cfg.state_path.read_bytes(), before)
        self.assertEqual(sorted(p.name for p in cfg.state_dir.iterdir()), ["last_refused.json", "state.json"])

    def test_a_refusal_record_that_cannot_be_written_does_not_hide_the_refusal(self):
        state = self.base / "state"
        state.write_text("a file where the state folder should be")   # mkdir on it raises FileExistsError
        cfg = self.cfg(state)
        logged = []
        with self.assertRaises(SystemExit) as raised:
            indexer.run_index(cfg, log=logged.append)
        self.assertEqual(str(raised.exception), "refusing to index: the corpus scan found no files (would delete everything).")
        self.assertEqual(len(logged), 1)
        self.assertIn("could not record", logged[0])

    def test_a_file_that_a_rule_names_but_the_secret_scan_skips_does_not_make_the_corpus_rebuildable(self):
        (self.root / "a.md").write_text("# Notes\n\npassword: " + "a1" * 14 + "\n")   # long enough for the scan's password rule
        cfg = self.cfg(self.base / "state")
        entries, scan = corpus.enumerate_corpus(cfg)
        self.assertEqual((entries, scan["skipped_secret"]), ([], ["fx:a.md"]))
        with self.assertRaises(SystemExit) as raised:
            indexer.run_index(cfg)
        self.assertTrue(str(raised.exception).startswith("refusing to index: the corpus scan found no files"))

    def test_a_failed_replacement_leaves_no_temporary_record(self):
        cfg = self.cfg(self.base / "state")
        with mock.patch("cerebrollm.indexer.os.replace", side_effect=OSError("disk full")):
            with self.assertRaises(OSError):
                indexer.record_refusal(cfg, {"counts": {}, "pdf": {}})
        self.assertEqual(list(cfg.state_dir.iterdir()), [])

    def test_a_refusal_and_an_index_in_the_same_second_are_ordered_by_their_epochs(self):
        cfg = self.cfg(self.base / "state")
        cfg.state_dir.mkdir()
        cfg.refused_path.write_text('{"epoch": 1800000000.1, "time": "t", "files_seen": 2, "pdf": {}}')
        # the index finished at 1800000000.9; its time string is cut to whole seconds (1800000000)
        after = {"last_index_time": "2027-01-15T08:00:00+0000", "last_index_epoch": 1800000000.9}
        before = {"last_index_time": "2027-01-15T08:00:00+0000", "last_index_epoch": 1799999999.5}
        self.assertEqual(datetime.datetime.strptime(after["last_index_time"], "%Y-%m-%dT%H:%M:%S%z").timestamp(),
                         1800000000.0)
        self.assertIsNone(status.newer_refusal(cfg, after))
        self.assertEqual(status.newer_refusal(cfg, before)["files_seen"], 2)

    def test_status_shows_the_record_only_when_it_is_newer_than_the_last_index(self):
        cfg = self.cfg(self.base / "state")
        cfg.state_dir.mkdir()
        cfg.refused_path.write_text('{"epoch": 1800000000, "time": "t", "files_seen": 2, "pdf": {"extra_missing": 2}}')
        older = {"last_index_time": "2026-11-01T00:00:00+0000"}      # 2026-11-01 is before epoch 1800000000
        newer = {"last_index_time": "2030-01-01T00:00:00+0000"}
        self.assertEqual(status.newer_refusal(cfg, older)["files_seen"], 2)
        self.assertEqual(status.newer_refusal(cfg, {})["files_seen"], 2)
        self.assertIsNone(status.newer_refusal(cfg, newer))
        self.assertIsNone(status.newer_refusal(cfg, {"last_index_time": "garbage"}))
        cfg.refused_path.write_text("not json")
        self.assertIsNone(status.newer_refusal(cfg, older))


@unittest.skipIf(NEEDS_EXTRA, NEEDS_EXTRA or "")
class TestCopies(Fixture):
    def test_identical_pdfs_count_once(self):
        (self.root / "docs/copy-of-report.pdf").write_bytes((self.root / "docs/report.pdf").read_bytes())
        entries, scan = corpus.enumerate_corpus(self.cfg)
        self.assertEqual(len([e for e in entries if e["path"].endswith(".pdf")]), 1)
        self.assertEqual(scan["pdf"]["indexed"], 1)


if __name__ == "__main__":
    unittest.main()
