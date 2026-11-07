"""cerebrollm verify: re-read the source and check the quote and the indexed sha256."""
import hashlib
import os
import posixpath
import re
import unicodedata

from . import corpus, rules, store

LINK = re.compile(r"\[([^\]]*)\]\([^)]*\)")
MARKER = re.compile(r"(?m)^\s*(?:[-+#>]+|\d+\.)\s+")
EMPHASIS = re.compile(r"(?<![\w*])(\*{1,3})(?=[^\s*])([^*\n]*?[^\s*])\1(?![\w*])")   # matched pairs only: 10**24 and FOO* stay


def _normalise(text):
    """Whitespace collapsed and Unicode in composed form (NFC), so "e" plus a combining accent equals "é"."""
    return " ".join(unicodedata.normalize("NFC", text).split())


def _plain(text):
    """Without Markdown markup, which a model drops or adds when it copies a line; the words must still match in order."""
    text = MARKER.sub("", LINK.sub(r"\1", text))
    return _normalise(EMPHASIS.sub(r"\2", text).replace("`", ""))   # underscores stay: FOO_ and _x are often content


def _word(c):
    """Part of a word: a letter or digit in any script, "_", or a combining mark that continues the letter before it."""
    return c.isalnum() or c == "_" or unicodedata.category(c).startswith("M")


def _bounded(needle, hay):
    """needle occurs in hay without cutting a word, identifier or number at either end: "port 80" is not in
    "port 8080", "require_auth" is not in "require_auth_extra", and "port 80." is not in "port 80.5"."""
    core = needle.rstrip(".,;:")   # sentence punctuation the model added or kept says nothing about the boundary
    if not core:
        return False
    start = hay.find(core)
    while start >= 0:
        end = start + len(core)
        before = hay[start - 1] if start else ""
        after = hay[end] if end < len(hay) else ""
        head_ok = not _word(core[0]) or not (before and (_word(before) or (
            before in ".," and start >= 2 and hay[start - 2].isdigit() and core[0].isdigit())))
        tail_ok = not _word(core[-1]) or not (after and (_word(after) or (
            after in ".," and end + 1 < len(hay) and hay[end + 1].isdigit() and core[-1].isdigit())))
        if head_ok and tail_ok and hay.startswith(needle, start):
            return True
        start = hay.find(core, start + 1)
    return False


def _found(quote, text):
    needle = _normalise(quote)
    if not needle:   # "" is inside every string
        return False
    if _bounded(needle, _normalise(text)):
        return True
    needle = _plain(quote).rstrip(".,;:")
    # the quote must end where the source's text ends: "port 80." must not match "port 8080", "10**24" or "10.5"
    return bool(needle) and re.search(r"(?:^|(?<=[\s(\[\"']))%s(?=$|\s|[.,;:!?)\]\"'](?:\s|$))" % re.escape(needle),
                                      _plain(text)) is not None


def _resolve(cfg, path, ref):
    """Candidate (root, relative path, ref) triples for a user-supplied path."""
    cands = []
    for root in cfg.roots.values():
        if ref and root["kind"] == "dir" and ref != "file":
            continue
        top = root["path"].rstrip("/") + "/"
        if os.path.isabs(path):
            if path.startswith(top):
                cands.append((root, path[len(top):], ref or root["ref"]))
        else:
            cands.append((root, path, ref or root["ref"]))
    return cands


def _requested(rel):
    """rel with "." and ".." removed lexically, before any link is followed; None when it leaves the root."""
    rel = posixpath.normpath(rel.replace(os.sep, "/"))
    return None if rel == ".." or rel.startswith("../") or rel.startswith("/") else rel


def _target(root, rel):
    """The path inside the root that rel reaches through links, in the form the indexer stores; None outside."""
    if root["kind"] == "git":
        return rel
    top = os.path.realpath(root["path"])
    full = os.path.realpath(os.path.join(top, rel))
    if os.path.commonpath([top, full]) != top:
        return None
    return os.path.relpath(full, top)


def _excluded(cfg, root, rel):
    """True when the index never holds this path: a never-index rule, or no tier rule."""
    return bool(rules.never_reason(rel, cfg.never)) or rules.classify(root["name"], rel, cfg.rules) is None


def _indexed_sha(cfg, root_name, rel, ref):
    """sha256 values indexed for this file: rows at this path and ref, plus rows whose also_at
    lists this file as a collapsed copy (also_at entries are "root:path")."""
    copy_of = "%s:%s" % (root_name, rel)
    with store.sql(cfg) as cur:
        cur.execute("select distinct metadata_->>'sha256' from %s where "
                    "(metadata_->>'path' = %%s and metadata_->>'ref' = %%s) or exists ("
                    "select 1 from jsonb_array_elements_text("
                    "coalesce((metadata_::jsonb)->'also_at', '[]'::jsonb)) as a(p) where a.p = %%s)"
                    % cfg.data_table, (rel, ref, copy_of))
        return {r[0] for r in cur.fetchall()}


def run_verify(cfg, path, quote, ref=None):
    """Return (code, detail); code is OK, CHANGED, MISSING, GONE or UNINDEXED."""
    seen_gone, absent = False, None
    for root, rel, rref in _resolve(cfg, path, ref):
        asked = _requested(rel)
        if asked is None:
            seen_gone = True
            continue
        # An excluded path answers exactly as an absent quote, decided before any link is followed or any
        # file is read: first the path as asked, then the file a link reaches. Later roots are still tried.
        if _excluded(cfg, root, asked):
            absent = absent or ("MISSING", "quote not found in %s@%s" % (asked, rref))
            continue
        rel = _target(root, asked)
        if rel is None:   # a link out of the root reads nothing and answers as a file that is not there
            seen_gone = True
            continue
        if _excluded(cfg, root, rel):
            absent = absent or ("MISSING", "quote not found in %s@%s" % (asked, rref))
            continue
        try:
            data = corpus.read_source(root, rel, rref)
        except (FileNotFoundError, IsADirectoryError, PermissionError):
            seen_gone = True
            continue
        text = data.decode("utf-8", "replace")
        if rules.secret_hit(text) or not _found(quote, text):
            return "MISSING", "quote not found in %s@%s" % (asked, rref)
        sha = hashlib.sha256(data).hexdigest()
        indexed = _indexed_sha(cfg, root["name"], rel, rref)
        if not indexed:
            return "UNINDEXED", "quote present but %s@%s is not in the index; sha256 %s" % (rel, rref, sha[:12])
        if sha in indexed:
            return "OK", "%s@%s sha256 %s" % (rel, rref, sha[:12])
        return "CHANGED", "quote present; %s@%s changed since indexing (now %s, indexed %s)" % (
            rel, rref, sha[:12], sorted(indexed)[0][:12])
    if absent:
        return absent
    if seen_gone:
        return "GONE", "source not found: " + path
    return "GONE", "no registered root matches: " + path
