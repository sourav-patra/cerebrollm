#!/usr/bin/env python3
"""Check the v2 item set (development step N5). Stdlib only. eval/check_items.py and eval/items.jsonl stay frozen.

Public part (always): eval/items-v2.jsonl, group 2 (post-cutoff public documents, quotes in eval/v2-sources/) and
group 3 (unanswerable, each absent_terms entry must occur in neither eval/v2-sources/ nor the corpus).
Private part (only with --private): items.json of group 1 (own project docs) outside the repo, quotes checked against
the projects folder, plus the sha256 and line range recorded at pick time. The projects folder, the never-open list and
the skip patterns come from a SOURCES.txt (lines projects_folder:, never_open:, skip:), by default the one beside the
private items file; --sources picks another file and --notes-root overrides projects_folder.
Every path is normalised and checked against the root and the exclusion lists before any file is opened.

The corpus root comes from --corpus, else from [corpus] path in research/model-study/study.toml ($HOME and ~ expanded).

Usage: python3 eval/check_items_v2.py [--corpus ROOT] [--private ITEMS_JSON [--sources SOURCES_TXT] [--notes-root DIR]]
Prints OK <public> [<private>] or one line per failure and exits 1.
"""
import argparse
import fnmatch
import hashlib
import json
import os
import posixpath
import sys
import tomllib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import check_items as V1  # noqa: E402  (check_quote is reused, not copied)

PUBLIC = os.path.join(HERE, "items-v2.jsonl")
SOURCES = os.path.join(HERE, "v2-sources")
STUDY = os.path.join(os.path.dirname(HERE), "research", "model-study", "study.toml")
KINDS = {"exact", "paraphrase", "stale", "unanswerable"}
WANT_PUBLIC = {(2, "exact"): 10, (2, "paraphrase"): 7, (2, "stale"): 3, (3, "unanswerable"): 15}
CUTOFF = "2026-07-01"  # group 2 sources must be published on or after this date


def read_sources(path):
    """key: value lines of SOURCES.txt; list values are split on commas."""
    kv = {}
    with open(path, encoding="utf-8") as f:
        for l in f:
            if ":" in l and not l.lstrip().startswith("#"):
                k, v = l.split(":", 1)
                kv[k.strip()] = v.strip()
    return {"projects_folder": kv.get("projects_folder", ""),
            "never_open": [x.strip() for x in kv.get("never_open", "").split(",") if x.strip()],
            "skip": [x.strip() for x in kv.get("skip", "").split(",") if x.strip()]}


def corpus_from_study(path=STUDY):
    """[corpus] path of study.toml with $HOME and ~ expanded. Raises ValueError naming the missing key."""
    with open(path, "rb") as f:
        cfg = tomllib.load(f)
    try:
        p = cfg["corpus"]["path"]
    except KeyError:
        raise ValueError("%s has no [corpus] path" % path)
    return os.path.expanduser(os.path.expandvars(p))


def _excluded(top, never, skip):
    t = top.lower()
    return t in {x.lower() for x in never} or any(fnmatch.fnmatch(t, g.lower()) for g in skip)


def safe_rel(root, rel, never=(), skip=()):
    """(normalised relative path, None) or (None, reason). Touches no file: only normpath and realpath (lstat)."""
    if not isinstance(rel, str) or not rel or rel.startswith("/") or "\\" in rel or ":" in rel.split("/")[0]:
        return None, "path is not a relative posix path"
    n = posixpath.normpath(rel)
    if n in (".", "..") or n.startswith("../"):
        return None, "path escapes the root"
    if _excluded(n.split("/")[0], never, skip):
        return None, "path is in an excluded folder"
    base = os.path.realpath(root)
    real = os.path.realpath(os.path.join(root, n))
    if os.path.commonpath([real, base]) != base:
        return None, "path escapes the root through a link"
    top = os.path.relpath(real, base).split(os.sep)[0]
    if _excluded(top, never, skip):
        return None, "path is in an excluded folder (through a link)"
    return n, None


def _ref(root, q, label, cache, fails, never=(), skip=()):
    """Check one quote after the path checks. Returns the normalised path, or None when the path was rejected."""
    n, err = safe_rel(root, q.get("path"), never, skip)
    if err:
        fails.append("%s: %s: %s" % (label, q.get("path"), err))
        return None
    V1.check_quote(root, dict(q, path=n), label, cache, fails)
    return n


def _common(d, fails, seen):
    iid = d.get("id", "?")
    for k in ("id", "set", "group", "kind", "source", "question", "key_facts", "quotes"):
        if k not in d:
            fails.append("%s: missing field %s" % (iid, k))
    if iid in seen:
        fails.append("%s: duplicate id" % iid)
    seen.add(iid)
    if d.get("kind") not in KINDS:
        fails.append("%s: bad kind %r" % (iid, d.get("kind")))


def _stale(d, ref, fails):
    """ref(quote, label) checks one quote and returns its normalised path or None."""
    iid, st = d["id"], d.get("stale")
    if d.get("kind") != "stale":
        if st:
            fails.append("%s: non-stale item has a stale block" % iid)
        return []
    if not st:
        fails.append("%s: stale item without stale block" % iid)
        return []
    used = []
    for part in ("superseded", "current"):
        if part not in st:
            fails.append("%s: stale block missing %s" % (iid, part))
            continue
        used.append((st[part], ref(st[part], "%s stale.%s" % (iid, part))))
        if not st[part].get("fact"):
            fails.append("%s: stale.%s has no fact" % (iid, part))
    if "superseded" in st and "current" in st and \
            (st["superseded"].get("path"), st["superseded"].get("line")) == (st["current"].get("path"), st["current"].get("line")):
        fails.append("%s: superseded and current cite the same line" % iid)
    if not st.get("markers"):
        fails.append("%s: no stale markers" % iid)
    return used


def _load_jsonl(path, fails):
    items = []
    with open(path, encoding="utf-8") as f:
        for i, l in enumerate(f.read().split("\n"), 1):
            if l.strip():
                try:
                    items.append(json.loads(l))
                except ValueError as e:
                    fails.append("%s line %d: invalid JSON: %s" % (os.path.basename(path), i, e))
    return items


def _published(root, rel):
    """Header lines (URL, Published, Fetched) of a saved source; rel must already be normalised and checked."""
    with open(os.path.join(root, rel), encoding="utf-8") as f:
        head = f.read(2000).split("\n\n", 1)[0].split("\n")
    return {l.split(":", 1)[0]: l.split(":", 1)[1].strip() for l in head if ":" in l}


_BLOBS = {}


def _grep(term, roots):
    """Path of the first text file under any root that contains term (case-insensitive), else None. Inside a corpus
    root, its cerebrollm/eval folder is skipped (relative to that root): once the corpus is regenerated it holds
    these very questions."""
    t = term.lower()
    for r in roots:
        if r not in _BLOBS:
            blobs = []
            for dp, _, fs in os.walk(r):
                parts = os.path.relpath(dp, r).split(os.sep)
                if ".git" in parts or parts[:2] == ["cerebrollm", "eval"]:
                    continue
                for fn in fs:
                    try:
                        with open(os.path.join(dp, fn), encoding="utf-8", errors="ignore") as f:
                            blobs.append((os.path.join(dp, fn), f.read().lower()))
                    except OSError:
                        pass
            _BLOBS[r] = blobs
        for fp, text in _BLOBS[r]:
            if t in text:
                return fp
    return None


def check_public(path=PUBLIC, sources=SOURCES, corpus=None):
    """Group 3 absent terms are always checked against `sources`, and against `corpus` when it is given."""
    fails, cache, seen, counts = [], {}, set(), {}
    items = _load_jsonl(path, fails)
    ref = lambda q, label: _ref(sources, q, label, cache, fails)  # noqa: E731
    for d in items:
        _common(d, fails, seen)
        iid, g, kind = d.get("id", "?"), d.get("group"), d.get("kind")
        counts[(g, kind)] = counts.get((g, kind), 0) + 1
        if g == 2:
            qs = d.get("quotes") or []
            if not qs:
                fails.append("%s: no quotes" % iid)
            elif d.get("source") != posixpath.normpath(str(qs[0].get("path"))).split("/")[0]:
                fails.append("%s: source %r does not match first quote path" % (iid, d.get("source")))
            if not d.get("key_facts"):
                fails.append("%s: no key facts" % iid)
            checked = [(q, ref(q, "%s quote %d" % (iid, j + 1))) for j, q in enumerate(qs)]
            checked += _stale(d, ref, fails)
            dates = []
            for q, n in checked:
                if n is None:
                    continue
                try:
                    h = _published(sources, n)
                except OSError:
                    continue
                if not (h.get("URL", "").startswith("https://") and h.get("Fetched") and h.get("Published")):
                    fails.append("%s: %s lacks URL, Published or Fetched header" % (iid, n))
                elif h["Published"] < CUTOFF:
                    fails.append("%s: %s published %s, before %s" % (iid, n, h["Published"], CUTOFF))
                dates.append(h.get("Published", ""))
            if d.get("released") != max(dates or [""]):
                fails.append("%s: released %r does not match the newest source date" % (iid, d.get("released")))
        elif g == 3:
            if kind != "unanswerable":
                fails.append("%s: group 3 item is not unanswerable" % iid)
            if d.get("quotes") or d.get("key_facts"):
                fails.append("%s: unanswerable item must have no quotes and no key facts" % iid)
            if d.get("expected") != "not in the sources":
                fails.append("%s: expected must be 'not in the sources'" % iid)
            terms = d.get("absent_terms") or []
            if not terms:
                fails.append("%s: no absent_terms" % iid)
            roots = [sources] + ([corpus] if corpus and os.path.isdir(corpus) else [])
            for t in terms:
                hit = _grep(t, roots)
                if hit:
                    fails.append("%s: absent term %r occurs in %s" % (iid, t, hit))
        else:
            fails.append("%s: group %r is not 2 or 3" % (iid, g))
    if corpus is not None and not os.path.isdir(corpus):
        fails.append("corpus root not found: %s" % corpus)
    for k, want in WANT_PUBLIC.items():
        if counts.get(k, 0) != want:
            fails.append("expected %d group %s %s items, found %d" % (want, k[0], k[1], counts.get(k, 0)))
    if len(items) != sum(WANT_PUBLIC.values()):
        fails.append("expected %d public items, found %d" % (sum(WANT_PUBLIC.values()), len(items)))
    return fails, items


def check_private(path, notes_root, public_ids=(), never=(), skip=()):
    """Group 1 items. Counts are not fixed: the owner drops items at the gate. No path is opened before
    safe_rel accepts it, including the note records that no quote cites."""
    fails, cache, seen = [], {}, set(public_ids)
    with open(path, encoding="utf-8") as f:
        items = json.load(f)
    ref = lambda q, label: _ref(notes_root, q, label, cache, fails, never, skip)  # noqa: E731
    for d in items:
        _common(d, fails, seen)
        iid = d.get("id", "?")
        if d.get("group") != 1 or not iid.startswith("G1-"):
            fails.append("%s: private items must be group 1 with an id starting G1-" % iid)
        if d.get("kind") not in ("exact", "paraphrase", "stale"):
            fails.append("%s: group 1 kind must be exact, paraphrase or stale" % iid)
        qs = d.get("quotes") or []
        if not qs:
            fails.append("%s: no quotes" % iid)
        elif d.get("source") != posixpath.normpath(str(qs[0].get("path"))).split("/")[0]:
            fails.append("%s: source %r does not match first quote path" % (iid, d.get("source")))
        if not d.get("key_facts"):
            fails.append("%s: no key facts" % iid)
        checked = [(q, ref(q, "%s quote %d" % (iid, j + 1))) for j, q in enumerate(qs)]
        checked += _stale(d, ref, fails)
        pick = d.get("pick") or {}
        notes = pick.get("notes") or []
        if not notes or not pick.get("why"):
            fails.append("%s: pick record needs notes and why" % iid)
        recorded = {}
        for n in notes:
            rn, err = safe_rel(notes_root, n.get("path"), never, skip)
            if err:
                fails.append("%s: note record %s: %s" % (iid, n.get("path"), err))
            else:
                recorded[rn] = n
        for r, rn in checked:
            if rn is None:
                continue
            n = recorded.get(rn)
            if n is None:
                fails.append("%s: %s has no note record" % (iid, rn))
            elif not isinstance(r.get("line"), int) or not (n["line_start"] <= r["line"] <= n["line_end"]):
                fails.append("%s: %s line %r is outside the recorded range" % (iid, rn, r.get("line")))
        for rn, n in recorded.items():
            full = os.path.join(notes_root, rn)
            if os.path.isfile(full):
                with open(full, "rb") as f:
                    if hashlib.sha256(f.read()).hexdigest() != n.get("sha256"):
                        fails.append("%s: %s changed since it was picked (sha256 differs)" % (iid, rn))
    return fails, items


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", help="corpus root (default: [corpus] path of research/model-study/study.toml)")
    ap.add_argument("--private")
    ap.add_argument("--sources", help="SOURCES.txt (default: beside the private items file)")
    ap.add_argument("--notes-root", help="overrides projects_folder from SOURCES.txt")
    a = ap.parse_args(argv)
    try:
        corpus = a.corpus or corpus_from_study()
    except (OSError, ValueError) as e:
        print("FAIL no corpus root: %s" % e)
        return 1
    fails, items = check_public(corpus=corpus)
    msg = "OK %d" % len(items)
    if a.private:
        src = read_sources(a.sources or os.path.join(os.path.dirname(os.path.abspath(a.private)), "SOURCES.txt"))
        root = a.notes_root or src["projects_folder"]
        if not root or not os.path.isdir(root):
            print("FAIL projects folder not found: %r" % root)
            return 1
        f2, p_items = check_private(a.private, root, {d.get("id") for d in items}, src["never_open"], src["skip"])
        fails += f2
        msg += " private %d" % len(p_items)
    if fails:
        print("\n".join(fails))
        print("FAIL %d problem(s)" % len(fails))
        return 1
    print(msg)
    return 0


if __name__ == "__main__":
    sys.exit(main())
