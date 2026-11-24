"""Build small PDFs for the tests, with no PDF library: one page per list item, each a line of text
in the standard Helvetica font. A page given as None has no text layer (an empty content stream, as a
scanned page that holds only an image has none)."""


def make_pdf(pages):
    """The bytes of a PDF whose page n shows the lines of pages[n-1] (a list of lines), or no text for None."""
    objects = {}                      # object number -> body bytes
    page_ids = [3 + 2 * i for i in range(len(pages))]
    objects[1] = b"<< /Type /Catalog /Pages 2 0 R >>"
    kids = " ".join("%d 0 R" % n for n in page_ids)
    objects[2] = ("<< /Type /Pages /Kids [%s] /Count %d >>" % (kids, len(pages))).encode()
    font = 3 + 2 * len(pages)
    for page_id, lines in zip(page_ids, pages):
        stream_id = page_id + 1
        objects[page_id] = ("<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents %d 0 R "
                            "/Resources << /Font << /F1 %d 0 R >> >> >>" % (stream_id, font)).encode()
        ops = ""
        if lines:
            ops = "BT /F1 12 Tf 14 TL 72 720 Td " + " T* ".join(
                "(%s) Tj" % line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)") for line in lines) + " ET"
        body = ops.encode("latin-1")
        objects[stream_id] = b"<< /Length %d >>\nstream\n" % len(body) + body + b"\nendstream"
    objects[font] = b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>"
    out = bytearray(b"%PDF-1.4\n")
    offsets = {}
    for number in sorted(objects):
        offsets[number] = len(out)
        out += b"%d 0 obj\n" % number + objects[number] + b"\nendobj\n"
    xref = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objects) + 1)
    for number in sorted(objects):
        out += b"%010d 00000 n \n" % offsets[number]
    out += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objects) + 1, xref)
    return bytes(out)
