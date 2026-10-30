#!/usr/bin/env python3
"""Check eval/items.jsonl against the corpus. Stdlib only.

Usage: python3 eval/check_items.py [CORPUS_ROOT]
Prints OK 70 when all 70 items pass, otherwise one line per failure and exits 1.
"""
import json
import os
import sys

DEFAULT_ROOT = os.path.expanduser("~/cerebrollm-corpus")
ITEMS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "items.jsonl")
EXTERNAL = {"llama_index", "ollama", "pgvector", "promptfoo"}
KINDS = {"exact", "paraphrase", "stale"}
WANT = {("scored", "exact"): 20, ("scored", "paraphrase"): 20, ("scored", "stale"): 20,
        ("practice", "exact"): 4, ("practice", "paraphrase"): 3, ("practice", "stale"): 3}


def read_lines(root, rel, cache):
    if rel not in cache:
        full = os.path.join(root, rel)
        if os.path.commonpath([os.path.realpath(full), os.path.realpath(root)]) != os.path.realpath(root):
            cache[rel] = None
        elif not os.path.isfile(full):
            cache[rel] = None
        else:
            with open(full, encoding="utf-8", newline="") as f:
                cache[rel] = [l.rstrip("\r") for l in f.read().split("\n")]
    return cache[rel]


def check_quote(root, q, label, cache, fails):
    for k in ("path", "line", "text"):
        if k not in q:
            fails.append("%s: quote missing %s" % (label, k))
            return
    L = read_lines(root, q["path"], cache)
    if L is None:
        fails.append("%s: source path does not exist: %s" % (label, q["path"]))
        return
    n = q["line"]
    if not isinstance(n, int) or n < 1 or n > len(L):
        fails.append("%s: %s line %r out of range (file has %d lines)" % (label, q["path"], n, len(L)))
        return
    if not q["text"].strip() or q["text"] not in L[n - 1]:
        fails.append("%s: %s:%d does not contain %r (line is %r)" % (label, q["path"], n, q["text"][:60], L[n - 1][:80]))


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_ROOT
    fails, cache, seen, counts, n_cere = [], {}, set(), {}, 0
    if not os.path.isdir(root):
        print("FAIL corpus root not found: %s" % root)
        return 1
    with open(ITEMS, encoding="utf-8") as f:
        raw = [l for l in f.read().split("\n") if l.strip()]
    items = []
    for i, l in enumerate(raw, 1):
        try:
            items.append(json.loads(l))
        except ValueError as e:
            fails.append("line %d: invalid JSON: %s" % (i, e))
    for d in items:
        iid = d.get("id", "?")
        for k in ("id", "set", "kind", "source", "question", "key_facts", "quotes"):
            if k not in d:
                fails.append("%s: missing field %s" % (iid, k))
        if iid in seen:
            fails.append("%s: duplicate id" % iid)
        seen.add(iid)
        key = (d.get("set"), d.get("kind"))
        counts[key] = counts.get(key, 0) + 1
        if d.get("kind") not in KINDS:
            fails.append("%s: bad kind %r" % (iid, d.get("kind")))
        if not d.get("key_facts"):
            fails.append("%s: no key facts" % iid)
        qs = d.get("quotes") or []
        if not qs:
            fails.append("%s: no quotes" % iid)
        elif d.get("source") != qs[0]["path"].split("/")[0]:
            fails.append("%s: source %r does not match first quote path" % (iid, d.get("source")))
        if d.get("source") == "cerebrollm":
            n_cere += 1
        for j, q in enumerate(qs):
            check_quote(root, q, "%s quote %d" % (iid, j + 1), cache, fails)
        st = d.get("stale")
        if d.get("kind") == "stale":
            if not st:
                fails.append("%s: stale item without stale block" % iid)
            else:
                for part in ("superseded", "current"):
                    if part not in st:
                        fails.append("%s: stale block missing %s" % (iid, part))
                    else:
                        check_quote(root, st[part], "%s stale.%s" % (iid, part), cache, fails)
                        if not st[part].get("fact"):
                            fails.append("%s: stale.%s has no fact" % (iid, part))
                if "superseded" in st and "current" in st and \
                        (st["superseded"].get("path"), st["superseded"].get("line")) == (st["current"].get("path"), st["current"].get("line")):
                    fails.append("%s: superseded and current cite the same line" % iid)
                if not st.get("markers"):
                    fails.append("%s: no stale markers" % iid)
        elif st:
            fails.append("%s: non-stale item has a stale block" % iid)
    if len(items) != 70:
        fails.append("expected 70 items, found %d" % len(items))
    for k, want in WANT.items():
        if counts.get(k, 0) != want:
            fails.append("expected %d %s %s items, found %d" % (want, k[0], k[1], counts.get(k, 0)))
    if n_cere > 10:
        fails.append("cerebrollm source used for %d items (max 10)" % n_cere)
    for d in items:
        if d.get("source") not in EXTERNAL | {"cerebrollm"}:
            fails.append("%s: unknown source %r" % (d.get("id"), d.get("source")))
    if fails:
        print("\n".join(fails))
        print("FAIL %d problem(s)" % len(fails))
        return 1
    print("OK %d" % len(items))
    return 0


if __name__ == "__main__":
    sys.exit(main())
