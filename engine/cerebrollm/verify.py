"""cerebrollm verify: re-read the source and check the quote and the indexed sha256."""
import hashlib
import os
import posixpath

from . import corpus, rules, store


def _normalise(text):
    return " ".join(text.split())


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
        if rules.secret_hit(text) or _normalise(quote) not in _normalise(text):
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
