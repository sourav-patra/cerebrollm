"""Chunking: table rows become nodes with their context, prose keeps the sentence splitter, and the
embedded text carries the title and heading path while the displayed text does not."""
import unittest

from llama_index.core import Document
from llama_index.core.node_parser import MarkdownNodeParser
from llama_index.core.schema import MetadataMode

from cerebrollm import config, indexer
from cerebrollm.glue import TableRows, table_pieces

PATH = "docs/specs/POLICY.md"
DOC = (
    "# Policy Update 9\n\n"
    "intro paragraph before the table.\n\n"
    "## Changes\n\n"
    "Some prose about changes.\n\n"
    "| Ref | Rule | Source |\n"
    "|---|---|---|\n"
    "| J1 | A unit PR stays a unit PR. | ruling |\n"
    "| J3 | A PR is ready when both checks pass. | ruling |\n\n"
    "After the table, more prose.\n"
)
ROW_J3 = "| J3 | A PR is ready when both checks pass. | ruling |"


def chunk(text, path=PATH):
    """(final nodes, document text) from the chunking steps, without the embedding model."""
    cfg = config.load()
    entry = {"domain": "org", "project": "example", "tier": "T1", "status": "locked", "path": path,
             "root": "example-repo", "ref": "origin/main", "sha256": "0" * 64,
             "mtime": "2026-10-26T10:00:00+05:30", "also_at": [], "text": text}
    docs = indexer.make_documents([entry])
    texts = {d.doc_id: d.text for d in docs}
    nodes = docs
    for step in indexer.chunk_steps(cfg, texts):
        nodes = step(nodes)
    return nodes, texts[docs[0].doc_id]


class TestTableRows(unittest.TestCase):
    def test_one_node_per_data_row(self):
        nodes, _ = chunk(DOC)
        j1 = [n for n in nodes if "| J1 |" in n.text]
        j3 = [n for n in nodes if "| J3 |" in n.text]
        self.assertEqual(len(j1), 1)
        self.assertEqual(len(j3), 1)
        self.assertIsNot(j1[0], j3[0])
        self.assertNotIn("| J3 |", j1[0].text)

    def test_row_text_has_title_section_header_and_separator(self):
        nodes, _ = chunk(DOC)
        j3 = next(n for n in nodes if ROW_J3 in n.text)
        self.assertEqual(j3.text.split("\n"), [
            "Document: Policy Update 9",
            "Section: Policy Update 9 > Changes",
            "| Ref | Rule | Source |",
            "|---|---|---|",
            ROW_J3,
        ])

    def test_prose_keeps_its_splitting(self):
        nodes, _ = chunk(DOC)
        self.assertTrue(any("intro paragraph before the table." in n.text for n in nodes))
        self.assertTrue(any(n.text.strip() == "Some prose about changes." or
                            "Some prose about changes." in n.text and "| J" not in n.text for n in nodes))
        self.assertTrue(any("After the table, more prose." in n.text and "| J" not in n.text for n in nodes))

    def test_long_row_split_by_the_splitter_is_still_located(self):
        long_row = "| L1 | " + " ".join("word%d" % i for i in range(900)) + " | ruling |"   # about 6,000 characters
        text = "# Long\n\n## Table\n\n| Ref | Text | Source |\n|---|---|---|\n" + long_row + "\n"
        nodes, doc = chunk(text, path="docs/specs/v2/long.md")
        pieces = [n for n in nodes if "word" in n.text]
        self.assertGreater(len(pieces), 1)                      # the splitter cut the row
        for n in pieces:
            start, end = n.metadata["char_start"], n.metadata["char_end"]
            self.assertGreaterEqual(start, 0, n.text[:80])
            self.assertIn(doc[start:end], long_row)           # the span lies inside the row, never the prefix
        covered = max(n.metadata["char_end"] for n in pieces) - min(n.metadata["char_start"] for n in pieces)
        self.assertGreaterEqual(covered, len(long_row) - 10)   # the pieces together cover the row

    def test_heading_and_rule_above_a_table_make_no_chunk_of_their_own(self):
        text = "# T\n\n## Changes\n\n---\n\n| a | b |\n|---|---|\n| 1 | 2 |\n\nFinal prose here.\n"
        nodes, _ = chunk(text, path="docs/specs/v2/h.md")
        self.assertFalse(any(n.text.strip() in ("## Changes", "---") for n in nodes))
        self.assertTrue(any("| 1 | 2 |" in n.text and "Section: T > Changes" in n.text for n in nodes))
        self.assertTrue(any("Final prose here." in n.text for n in nodes))

    def test_row_span_is_the_row_alone(self):
        nodes, doc = chunk(DOC)
        j3 = next(n for n in nodes if ROW_J3 in n.text)
        self.assertEqual(doc[j3.metadata["char_start"]:j3.metadata["char_end"]], ROW_J3)
        self.assertNotIn("span_text", j3.metadata)

    def test_sections_without_tables_pass_through(self):
        doc = Document(text="# T\n\nplain prose only.\n", doc_id="d")
        nodes = MarkdownNodeParser()([doc])
        out = TableRows(texts={"d": doc.text})(nodes)
        self.assertEqual([id(n) for n in out], [id(n) for n in nodes])

    def test_table_pieces(self):
        pieces = table_pieces("intro\n\n| a | b |\n|---|---|\n| 1 | 2 |\n| 3 | 4 |\n\nend\n")
        self.assertEqual([p[0] for p in pieces], ["prose", "row", "row", "prose"])
        self.assertEqual([p[5] for p in pieces if p[0] == "row"], ["| 1 | 2 |", "| 3 | 4 |"])

    def test_tables_inside_fenced_code_are_prose(self):
        text = "```\n| a | b |\n|---|---|\n| 1 | 2 |\n```\n"
        self.assertFalse([p for p in table_pieces(text) if p[0] == "row"])

    def test_table_without_data_rows_is_prose(self):
        self.assertFalse([p for p in table_pieces("| a | b |\n|---|---|\n\nafter\n") if p[0] == "row"])


class TestEmbeddedText(unittest.TestCase):
    def test_row_embeds_title_and_heading_and_displays_text_only(self):
        nodes, _ = chunk(DOC)
        j3 = next(n for n in nodes if ROW_J3 in n.text)
        embedded = j3.get_content(metadata_mode=MetadataMode.EMBED)
        self.assertIn("title: Policy Update 9", embedded)
        self.assertIn("heading_path: Policy Update 9 > Changes", embedded)
        self.assertNotIn("tier:", embedded)
        self.assertNotIn("sha256", embedded)
        self.assertEqual(j3.get_content(), j3.text)

    def test_prose_chunk_embeds_title_and_heading_and_displays_text_only(self):
        # the short intro section is merged into the section after it, so its chunk is filed under the title
        nodes, _ = chunk(DOC)
        prose = next(n for n in nodes if "intro paragraph before the table." in n.text)
        embedded = prose.get_content(metadata_mode=MetadataMode.EMBED)
        self.assertIn("title: Policy Update 9", embedded)
        self.assertIn("heading_path: Policy Update 9\n", embedded)
        self.assertNotIn("tier:", embedded)
        self.assertEqual(prose.get_content(), prose.text)


if __name__ == "__main__":
    unittest.main()
