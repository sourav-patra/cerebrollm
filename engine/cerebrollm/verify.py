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


def _canonical(root, rel):
    """The path inside the root that rel names, with links and ".." resolved, or None when it leaves the root."""
    if root["kind"] == "git":
        rel = posixpath.normpath(rel)
        return None if rel == ".." or rel.startswith("../") or rel.startswith("/") else rel
    top = os.path.realpath(root["path"])
    full = os.path.realpath(os.path.join(top, rel))
    if os.path.commonpath([top, full]) != top:
        return None
    return os.path.relpath(full, top).replace(os.sep, "/")


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
    seen_gone = False
    for root, rel, rref in _resolve(cfg, path, ref):
        rel = _canonical(root, rel)
        if rel is None:   # outside the root, also through a link: refused before any read
            seen_gone = True
            continue
        absent = ("MISSING", "quote not found in %s@%s" % (rel, rref))
        # An excluded file answers exactly as an absent quote, decided before the file is read.
        if _excluded(cfg, root, rel):
            return absent
        try:
            data = corpus.read_source(root, rel, rref)
        except (FileNotFoundError, IsADirectoryError, PermissionError):
            seen_gone = True
            continue
        text = data.decode("utf-8", "replace")
        if rules.secret_hit(text) or _normalise(quote) not in _normalise(text):
            return absent
        sha = hashlib.sha256(data).hexdigest()
        indexed = _indexed_sha(cfg, root["name"], rel, rref)
        if not indexed:
            return "UNINDEXED", "quote present but %s@%s is not in the index; sha256 %s" % (rel, rref, sha[:12])
        if sha in indexed:
            return "OK", "%s@%s sha256 %s" % (rel, rref, sha[:12])
        return "CHANGED", "quote present; %s@%s changed since indexing (now %s, indexed %s)" % (
            rel, rref, sha[:12], sorted(indexed)[0][:12])
    if seen_gone:
        return "GONE", "source not found: " + path
    return "GONE", "no registered root matches: " + path
