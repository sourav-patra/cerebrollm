"""Thin LlamaIndex glue: a Document whose hash ignores mtime, and two small transformations
that run around the stock Markdown parser and sentence splitter."""
import hashlib
import re
from pathlib import PurePosixPath

from llama_index.core import Document
from llama_index.core.schema import TextNode, TransformComponent

HEADING = re.compile(r"^(#{1,6})[ \t]+(.+?)[ \t#]*$")
FENCE = re.compile(r"^\s*(```|~~~)")
TABLE_SEPARATOR = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(?:\|\s*:?-{3,}:?\s*)*\|?\s*$")
HRULE = re.compile(r"^\s*([-*_])(\s*\1){2,}\s*$")
# Metadata that is part of the embedded text. Every other metadata key is excluded from it.
EMBED_KEYS = ("path", "title", "heading_path")


class SourceDoc(Document):
    """Re-embed only when the bytes or the classification change, not when mtime changes."""

    @property
    def hash(self):
        m = self.metadata
        ident = "|".join(str(m[k]) for k in ("sha256", "tier", "status", "project", "path", "ref"))
        ident += "|" + ",".join(m.get("also_at") or [])
        return hashlib.sha256(ident.encode()).hexdigest()


def headings(text):
    """[(char offset, level, title)] for ATX headings outside fenced code."""
    out, pos, fenced = [], 0, False
    for line in text.splitlines(keepends=True):
        if FENCE.match(line):
            fenced = not fenced
        elif not fenced:
            m = HEADING.match(line.rstrip("\r\n"))
            if m:
                out.append((pos, len(m[1]), m[2].strip()))
        pos += len(line)
    return out


def body_offset(chunk, start):
    """Offset of the first line of a chunk that is neither blank nor a heading, so a chunk that
    opens with a bare heading is filed under the heading its text belongs to."""
    pos = 0
    for line in chunk.splitlines(keepends=True):
        if line.strip() and not HEADING.match(line.rstrip("\r\n")):
            return start + pos
        pos += len(line)
    return start


def heading_path(heads, offset):
    stack = []
    for pos, level, title in heads:
        if pos > offset:
            break
        stack = [h for h in stack if h[0] < level] + [(level, title)]
    return " > ".join(t for _, t in stack)


def doc_title(text, path):
    """The first level-1 heading of the document, else the file name without its extension."""
    for _, level, title in headings(text):
        if level == 1:
            return title
    return PurePosixPath(path).stem


def table_pieces(text):
    """Split a section's text into ("prose", start, end) and ("row", start, end, header, separator, row)
    pieces. A table is a line starting with "|", then a separator line of dashes, then the lines that
    start with "|". Tables inside fenced code are prose. A table with no data rows is prose."""
    lines = text.splitlines(keepends=True)
    offs, pos = [], 0
    for line in lines:
        offs.append(pos)
        pos += len(line)
    offs.append(pos)
    pieces, prose_start, fenced, i = [], 0, False, 0
    while i < len(lines):
        line = lines[i].rstrip("\r\n")
        if FENCE.match(line):
            fenced = not fenced
            i += 1
            continue
        is_table = (not fenced and line.lstrip().startswith("|") and i + 1 < len(lines)
                    and lines[i + 1].lstrip().startswith("|")
                    and TABLE_SEPARATOR.match(lines[i + 1].rstrip("\r\n")))
        j = i + 2
        while is_table and j < len(lines) and lines[j].lstrip().startswith("|"):
            j += 1
        if not is_table or j == i + 2:
            i += 1
            continue
        if offs[i] > prose_start:
            pieces.append(("prose", prose_start, offs[i]))
        header, sep = line, lines[i + 1].rstrip("\r\n")
        for r in range(i + 2, j):
            row = lines[r].rstrip("\r\n")
            pieces.append(("row", offs[r], offs[r] + len(row), header, sep, row))
        prose_start = offs[j]
        i = j
    if prose_start < len(text):
        pieces.append(("prose", prose_start, len(text)))
    return pieces


def _heading_or_rule_only(text):
    """True when every non-blank line is a heading or a horizontal rule (no content of its own)."""
    lines = [ln for ln in text.splitlines() if ln.strip()]
    return all(HEADING.match(ln.rstrip()) or HRULE.match(ln) for ln in lines)


def _child(node, text, start, end):
    """A new text node with the metadata, exclusions and source relationship of `node`."""
    return TextNode(text=text, metadata=dict(node.metadata),
                    excluded_embed_metadata_keys=list(node.excluded_embed_metadata_keys),
                    excluded_llm_metadata_keys=list(node.excluded_llm_metadata_keys),
                    relationships=dict(node.relationships),
                    start_char_idx=start, end_char_idx=end)


class MergeSmall(TransformComponent):
    """After MarkdownNodeParser: a section shorter than min_chars absorbs the section after it,
    so a bare heading is not a chunk of its own. Merged text is the original slice."""

    texts: dict
    min_chars: int = 200

    def __call__(self, nodes, **kwargs):
        out = []
        for n in nodes:
            prev = out[-1] if out else None
            if (prev is not None and prev.ref_doc_id == n.ref_doc_id
                    and len(prev.text) < self.min_chars
                    and prev.start_char_idx is not None and n.end_char_idx is not None):
                src = self.texts[n.ref_doc_id]
                prev.set_content(src[prev.start_char_idx:n.end_char_idx])
                prev.end_char_idx = n.end_char_idx
            else:
                out.append(n)
        return out


class TableRows(TransformComponent):
    """Before the sentence splitter: a Markdown table becomes one node per data row. The row's text is
    the document title, the section (heading path), the table's header row and separator, then the
    row. Prose between tables is kept as it is. A row node carries `row_prefix` (the lines before the
    row), which LocateChunks strips to find the row's own character span, also when the splitter has
    cut a long row into pieces. Sections without tables pass through."""

    texts: dict

    def __call__(self, nodes, **kwargs):
        out = []
        for n in nodes:
            src = self.texts.get(n.ref_doc_id)
            pieces = table_pieces(n.text) if src is not None and "|" in n.text else []
            if not any(p[0] == "row" for p in pieces):
                out.append(n)
                continue
            base = n.start_char_idx if n.start_char_idx is not None else max(src.find(n.text), 0)
            heads = headings(src)
            title = doc_title(src, n.metadata.get("path", ""))
            for p in pieces:
                if p[0] == "prose":
                    seg = n.text[p[1]:p[2]]
                    # a heading or rule above a table has no content of its own: the row's
                    # "Section:" line carries the heading, so no chunk is made for it
                    if seg.strip() and not _heading_or_rule_only(seg):
                        out.append(_child(n, seg, base + p[1], base + p[2]))
                    continue
                _, s, e, header, sep, row = p
                section = heading_path(heads, base + s)
                lines = ["Document: " + title]
                if section:
                    lines.append("Section: " + section)
                lines += [header, sep]
                prefix = "".join(line + "\n" for line in lines)
                child = _child(n, prefix + row, base + s, base + e)
                child.metadata["row_prefix"] = prefix
                child.excluded_embed_metadata_keys.append("row_prefix")
                child.excluded_llm_metadata_keys.append("row_prefix")
                out.append(child)
        return out


class LocateChunks(TransformComponent):
    """After SentenceSplitter: set heading_path, title and the character span of each chunk in its
    document (the splitter's own spans are relative to the section, not the document). A table row's
    span is the row alone, without the prefix lines. Only path, title and heading_path are part of the
    embedded text; the displayed text is the node text and never includes metadata."""

    texts: dict

    def __call__(self, nodes, **kwargs):
        cursor, heads, titles = {}, {}, {}
        for n in nodes:
            doc = n.ref_doc_id
            text = self.texts[doc]
            if doc not in heads:
                heads[doc] = headings(text)
                titles[doc] = doc_title(text, n.metadata.get("path", ""))
            prefix = n.metadata.pop("row_prefix", None)
            target = n.text
            if prefix and n.text.startswith(prefix) and n.text[len(prefix):].strip():
                target = n.text[len(prefix):]          # a table row, or the first piece of a split row
            start = text.find(target, cursor.get(doc, 0))
            if start < 0:
                start = text.find(target)
            n.metadata["char_start"] = start
            n.metadata["char_end"] = start + len(target) if start >= 0 else -1
            n.metadata["heading_path"] = heading_path(
                heads[doc], body_offset(target, start) if start >= 0 else 0)
            n.metadata["title"] = titles[doc]
            n.excluded_embed_metadata_keys = [k for k in n.metadata if k not in EMBED_KEYS]
            n.excluded_llm_metadata_keys = list(n.excluded_embed_metadata_keys)
            if start >= 0:
                cursor[doc] = start
        return nodes
