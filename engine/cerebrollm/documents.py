"""Bytes to text for every source file, in one place.

The corpus reader, `verify` and `search` all call read_text, so a quote is checked against exactly the
text that was indexed. A Markdown or plain-text file is its bytes decoded as UTF-8 (undecodable bytes
replaced). A PDF is its text layer, read page by page with pypdf (the optional extra `cerebrollm[pdf]`):
each page that has text becomes one section, a "## Page N" heading line and then the page's text, so the
chunker splits at page boundaries and a hit can name its page. A page with no text adds nothing."""
import bisect
import io
import re
from functools import lru_cache

PAGE_HEADING = "## Page %d"
# A line of page text that opens a Markdown code fence would make the parser read the next page's heading as
# code and join the pages into one section, so a backslash goes in front of it. The indexed text and the text
# `verify` checks both carry the backslash, so they still agree; only a quote that starts with a fence differs.
FENCE_LINE = re.compile(r"(?m)^([ \t]*)(```|~~~)")


class DocumentError(Exception):
    """A file that cannot be turned into text. `code` is the key counted in `status`."""
    code = "unreadable"


class NoTextLayer(DocumentError):
    code = "no_text_layer"


class Unreadable(DocumentError):
    code = "unreadable"


class ExtraMissing(DocumentError):
    code = "extra_missing"


def is_pdf(path):
    return str(path).lower().endswith(".pdf")


def read_text(data, path):
    """(text, pages) for the bytes of the file at `path`. `pages` is None for a file that is not a PDF,
    else a tuple of (page number, start, end) character offsets into the text, one per page with text.
    Raises DocumentError (NoTextLayer, Unreadable or ExtraMissing) for a PDF that gives no text."""
    if not is_pdf(path):
        return data.decode("utf-8", "replace"), None
    return _pdf_text(data)


def _page_texts(data):
    """The text of each page of the PDF, in order. One text per page, empty when the page has no text layer."""
    try:
        import pypdf
    except ImportError as exc:
        raise ExtraMissing("PDF support is not installed: pip install 'cerebrollm[pdf]'") from exc
    try:
        reader = pypdf.PdfReader(io.BytesIO(data))
        if reader.is_encrypted and not reader.decrypt(""):
            raise Unreadable("the PDF is password protected")
        return [(page.extract_text() or "") for page in reader.pages]
    except Unreadable:
        raise
    except Exception as exc:  # noqa: BLE001 - pypdf raises many types for damaged files; all mean "skip this file"
        raise Unreadable("the PDF could not be read: %s" % type(exc).__name__) from exc


@lru_cache(maxsize=4)   # a search names the page of up to 50 hits, often in the same PDF
def _pdf_text(data):
    parts, pages, pos = [], [], 0
    for number, raw in enumerate(_page_texts(data), 1):
        body = "\n".join(line.rstrip() for line in raw.replace("\r\n", "\n").replace("\r", "\n").split("\n")).strip()
        body = FENCE_LINE.sub(lambda m: m.group(1) + "\\" + m.group(2), body)
        if not body:
            continue
        section = PAGE_HEADING % number + "\n\n" + body
        pages.append((number, pos, pos + len(section)))
        parts.append(section)
        pos += len(section) + 2
    if not parts:
        raise NoTextLayer("the PDF has no text layer")
    return "\n\n".join(parts) + "\n", tuple(pages)


def page_bodies(text, pages):
    """The texts a quote may be matched against: one per page of a PDF, without the generated "## Page N"
    heading, so a quote can neither match a heading the PDF does not hold nor run across a page break; the
    whole text, as a one-item list, for a file that is not a PDF (`pages` is None)."""
    if pages is None:
        return [text]
    return [text[start + len(PAGE_HEADING % number) + 2:end] for number, start, end in pages]


def page_range(pages, start, end):
    """(first page, last page) holding the character span start..end of a PDF's text; (None, None) when
    `pages` is None or the span is unknown (start below 0)."""
    if not pages or start is None or start < 0:
        return None, None
    starts = [p[1] for p in pages]
    first = pages[max(bisect.bisect_right(starts, start) - 1, 0)][0]
    last = pages[max(bisect.bisect_right(starts, max(end - 1, start)) - 1, 0)][0]
    return first, last


def page_label(first, last):
    """"page 4" or "pages 4-5"; None when there is no page."""
    if first is None:
        return None
    return "page %d" % first if last in (None, first) else "pages %d-%d" % (first, last)


def pdf_lines(pdf):
    """The `status` lines for the PDF counts of one scan (corpus.enumerate_corpus): one line when the extra
    is missing, one line of counts when any PDF was indexed or skipped for another reason. [] when none."""
    lines = []
    if pdf.get("extra_missing"):
        lines.append("pdf files skipped: %d (the pdf extra is not installed: pip install 'cerebrollm[pdf]', then re-index)"
                     % pdf["extra_missing"])
    if pdf.get("indexed") or pdf.get("no_text_layer") or pdf.get("unreadable"):
        lines.append("pdf files: indexed %d  skipped without a text layer %d  skipped unreadable %d" % (
            pdf.get("indexed", 0), pdf.get("no_text_layer", 0), pdf.get("unreadable", 0)))
    return lines
