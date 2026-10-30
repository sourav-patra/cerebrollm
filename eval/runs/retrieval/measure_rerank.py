"""N7 step 5: top-8 retrieval hit rate of default search against search plus rerank, on the 60 scored v1 items.

Run in Ubuntu from the repository root, under the GPU lock (the embedding model and the reranker load on the GPU):
    flock ~/.cerebrollm/gpu.lock ~/.cerebrollm/venv/bin/python -P eval/runs/retrieval/measure_rerank.py

Writes, next to this file: R-default/<id>.json (search top 8, the A3 setting), R-rerank/<id>.json (search top 20
reranked to top 8, with rerank_score and search_rank), R-summary.json and R-summary.md.
A hit is the analyze.py rule: a top-8 hit whose path and line span contain a quoted source line of the item; for
stale items the superseding line (stale.current) is counted separately."""
import json
import os
import sys
import time
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "engine"))
from cerebrollm import config, rerank, search, status  # noqa: E402

KINDS = ("exact", "paraphrase", "stale")


def covers(hits, path, line):
    return any(h["path"] == path and h["line_start"] is not None and h["line_start"] <= line <= h["line_end"]
               for h in hits)


def first_rank(hits, path, line):
    return next((i + 1 for i, h in enumerate(hits) if h["path"] == path and h["line_start"] is not None
                 and h["line_start"] <= line <= h["line_end"]), None)


def save(arm, item_id, hits):
    d = os.path.join(HERE, arm)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, item_id + ".json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(hits, f, ensure_ascii=False, indent=1)


def main():
    cfg = config.load()
    items = [json.loads(l) for l in open(os.path.join(ROOT, "eval", "items.jsonl"), encoding="utf-8") if l.strip()]
    items = [it for it in items if it["set"] == "scored"]
    assert len(items) == 60, len(items)
    chunks = status.collect(cfg)
    t_rerank = 0.0
    rows = {}
    for it in items:
        default = search.run_search(cfg, it["question"], k=8)
        cands = search.run_search(cfg, it["question"], k=20)
        t = time.time()
        reranked = rerank.rerank(it["question"], cands, top=8)
        t_rerank += time.time() - t
        save("R-default", it["id"], default)
        save("R-rerank", it["id"], reranked)
        q = it["quotes"]
        cur = it["stale"]["current"] if it["kind"] == "stale" else None
        rows[it["id"]] = {
            "kind": it["kind"],
            "default_hit": any(covers(default, x["path"], x["line"]) for x in q),
            "rerank_hit": any(covers(reranked, x["path"], x["line"]) for x in q),
            "in_top20_hit": any(covers(cands, x["path"], x["line"]) for x in q),
            "default_rank": min([r for r in (first_rank(default, x["path"], x["line"]) for x in q) if r] or [None],
                                default=None),
            "rerank_rank": min([r for r in (first_rank(reranked, x["path"], x["line"]) for x in q) if r] or [None],
                               default=None),
            "default_current": covers(default, cur["path"], cur["line"]) if cur else None,
            "rerank_current": covers(reranked, cur["path"], cur["line"]) if cur else None,
        }
        print(it["id"], flush=True)
    rerank.release()

    def rate(key, kind=None):
        sel = [r for r in rows.values() if kind in (None, r["kind"])]
        return "%d/%d" % (sum(bool(r[key]) for r in sel), len(sel))

    summary = {"chunks": chunks["chunks"], "documents": chunks["documents"],
               "embedding_model": chunks["state"].get("embedding_model"),
               "last_index_time": chunks["state"].get("last_index_time"),
               "rerank_seconds_total": round(t_rerank, 1), "items": rows,
               "hit_rate": {k: {kind: rate(k + "_hit", None if kind == "all" else kind) for kind in ("all",) + KINDS}
                            for k in ("default", "rerank", "in_top20")},
               "stale_current_line": {"default": "%d/20" % sum(bool(r["default_current"]) for r in rows.values()),
                                      "rerank": "%d/20" % sum(bool(r["rerank_current"]) for r in rows.values())},
               "moves": dict(Counter("gained" if (not r["default_hit"] and r["rerank_hit"]) else
                                     "lost" if (r["default_hit"] and not r["rerank_hit"]) else "same"
                                     for r in rows.values()))}
    with open(os.path.join(HERE, "R-summary.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(summary, f, indent=1, sort_keys=True)
    lines = ["| arm | all | exact | paraphrase | stale (quotes) | stale (superseding line) |", "|---|---|---|---|---|---|"]
    for name, key in (("default search top 8", "default"), ("search top 20 + rerank top 8", "rerank"),
                      ("(reference) any of search top 20", "in_top20")):
        h = summary["hit_rate"][key]
        cur = summary["stale_current_line"].get(key, "n/a")
        lines.append("| %s | %s | %s | %s | %s | %s |" % (name, h["all"], h["exact"], h["paraphrase"], h["stale"], cur))
    with open(os.path.join(HERE, "R-summary.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n\nmoves (default -> rerank): %s\nrerank seconds total: %s\n" % (
            summary["moves"], summary["rerank_seconds_total"]))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
