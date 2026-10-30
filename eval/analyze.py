"""Grade every saved record, verify A3 citations, compute the tables. Run in Ubuntu: python3 eval/analyze.py [--grades judge|code]

Reads eval/runs/<model>/<arm>/<id>/run-<k>.json. --grades code (keyword grade, GRADING.md section 1) writes
eval/runs/graded.jsonl (only if absent), eval/runs/verify-cache.json, eval/runs/summary.json and eval/runs/tables.md.
--grades judge (default; model grade from eval/runs/judge/graded.jsonl, GRADING.md section 3) writes
eval/runs/judge/summary.json and eval/runs/judge/tables.md and leaves the code-grade files alone.
Stdlib only. Rules: eval/GRADING.md (frozen).
"""
import argparse
import glob
import json
import math
import os
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import grade_lib as G  # noqa: E402
import n2_lib as L  # noqa: E402

CLI = os.path.join(L.HERE, "..", "engine", "bin", "cerebrollm")
CACHE = os.path.join(L.RUNS, "verify-cache.json")
KINDS = ["exact", "paraphrase", "stale"]
ARM_ORDER = ["A0", "A1", "A2", "A3"]
MODELS = ("haiku", "phi4")  # other lanes keep their runs in other folders under eval/runs/
PATH_RE = re.compile(r"[A-Za-z0-9_.\-]+(?:/[A-Za-z0-9_.\-]+)+\.[A-Za-z0-9]{1,5}")
QUOTE_RES = [re.compile(r'"([^"\n]{8,})"'), re.compile("“([^”\n]{8,})”"),
             re.compile(r"^>\s*(.{8,})$", re.M)]


def citations(answer):
    """Pairs (path, quote): each quoted string with the nearest cited path in the answer."""
    text = G.strip_think(answer)
    paths = [(m.start(), m.end(), m.group(0).rstrip(".")) for m in PATH_RE.finditer(text)]
    pairs = []
    if not paths:
        return pairs
    seen = set()
    for rx in QUOTE_RES:
        for m in rx.finditer(text):
            q = m.group(1).strip()
            if PATH_RE.fullmatch(q) or q in seen:  # a quoted path is a path, not a quote
                continue
            seen.add(q)
            d = lambda p: min(abs(p[0] - m.end()), abs(m.start() - p[1]))  # noqa: E731
            pairs.append((min(paths, key=d)[2], q))
    return pairs


def verify_all(pairs):
    cache = json.load(open(CACHE, encoding="utf-8")) if os.path.exists(CACHE) else {}
    todo = [p for p in sorted(set(pairs)) if json.dumps(p) not in cache]
    if not todo:  # verify-cache.json is hashed in SHA256SUMS: do not rewrite it when nothing changed
        return cache

    def one(p):
        r = subprocess.run([CLI, "verify", p[0], p[1]], capture_output=True, text=True)
        return json.dumps(p), {"exit": r.returncode, "stdout": r.stdout.strip()[:300],
                               "ok": r.returncode == 0 and r.stdout.startswith("OK")}

    with ThreadPoolExecutor(6) as ex:
        for k, v in ex.map(one, todo):
            cache[k] = v
    with open(CACHE, "w", encoding="utf-8", newline="\n") as f:
        json.dump(cache, f, ensure_ascii=False, indent=0, sort_keys=True)
    return cache


def sign_test(b, c):
    n = b + c
    if n == 0:
        return 1.0
    tail = sum(math.comb(n, i) for i in range(min(b, c) + 1)) / 2 ** n
    return min(1.0, 2 * tail)


def main(grades="judge"):
    out_dir = L.RUNS if grades == "code" else os.path.join(L.RUNS, "judge")
    items = {i["id"]: i for i in L.load_items()}
    recs = []
    for p in sorted(p for m in MODELS for p in glob.glob(os.path.join(L.RUNS, m, "A?", "*", "run-?.json"))):
        with open(p, encoding="utf-8") as f:
            recs.append(json.load(f))
    allpairs = []
    for r in recs:
        r["_pairs"] = citations(r["answer"]) if r["arm"] == "A3" else []
        allpairs += r["_pairs"]
    cache = verify_all(allpairs)

    graded = []
    for r in recs:
        it = items[r["id"]]
        ok, detail = G.grade(it, r["answer"])
        row = {"model": r["model"], "arm": r["arm"], "id": r["id"], "run": r["run"], "set": it["set"],
               "kind": it["kind"], "correct": ok, "detail": detail, "tokens": r["tokens"], "seconds": r["seconds"],
               "answer_chars": len(r["answer"]), "meta": r["meta"]}
        if r["arm"] == "A3":
            vs = [bool(cache[json.dumps(p)]["ok"]) for p in r["_pairs"]]
            row["citations"] = [{"path": p[0], "quote": p[1], "verify_ok": v} for p, v in zip(r["_pairs"], vs)]
            row["has_verified_citation"] = any(vs)
        graded.append(row)
    code_path = os.path.join(L.RUNS, "graded.jsonl")
    if grades == "code" and not os.path.exists(code_path):  # graded.jsonl is hashed in SHA256SUMS: never rewrite it
        with open(code_path, "w", encoding="utf-8", newline="\n") as f:
            for g in graded:
                f.write(json.dumps(g, ensure_ascii=False) + "\n")
    if grades == "judge":
        jv = {}
        for l in open(os.path.join(L.RUNS, "judge", "graded.jsonl"), encoding="utf-8"):
            j = json.loads(l)
            jv[(j["model"], j["arm"], j["id"], j["run"])] = j["verdict"]
        for g in graded:
            v = jv[(g["model"], g["arm"], g["id"], g["run"])]  # KeyError: a record without a judge line
            g["code_correct"], g["judge_verdict"], g["correct"] = g["correct"], v, v == "Y"  # error counts as not correct

    models = sorted({g["model"] for g in graded})
    summary = {"calls": {}, "cells": {}, "sign": {}, "tokens": {}, "citations": {}, "practice": {}}
    if grades == "judge":  # code mode must write exactly the pre-N4 summary.json (it is hashed in SHA256SUMS)
        summary.update(grades=grades, judge_errors=sum(g["judge_verdict"] == "error" for g in graded),
                       changed_majority={})
    out = []
    for m in models:
        arms = [a for a in ARM_ORDER if any(g["model"] == m and g["arm"] == a for g in graded)]
        maj, runs_n = {}, {}
        for a in arms:
            by_q = {}
            for g in graded:
                if g["model"] == m and g["arm"] == a and g["set"] == "scored":
                    by_q.setdefault(g["id"], []).append(g["correct"])
            runs_n[a] = sorted({len(v) for v in by_q.values()})
            maj[a] = {q: sum(v) * 2 > len(v) for q, v in by_q.items()}
            if grades == "judge":
                cq = {}
                for g in graded:
                    if g["model"] == m and g["arm"] == a and g["set"] == "scored":
                        cq.setdefault(g["id"], []).append(g["code_correct"])
                ch = {q: maj[a][q] for q, v in cq.items() if (sum(v) * 2 > len(v)) != maj[a][q]}
                summary["changed_majority"][f"{m}/{a}"] = {
                    "changed": len(ch), "code_to_judge_correct": sorted(q for q, j in ch.items() if j),
                    "code_to_judge_incorrect": sorted(q for q, j in ch.items() if not j)}
            full = {q: all(v) and len(v) == 5 for q, v in by_q.items()}
            summary["calls"][f"{m}/{a}"] = sum(1 for g in graded if g["model"] == m and g["arm"] == a)
            cell = {"runs_per_question": runs_n[a], "questions": len(by_q)}
            for k in KINDS + ["all"]:
                qs = [q for q in by_q if k == "all" or items[q]["kind"] == k]
                runs = [x for q in qs for x in by_q[q]]
                cell[k] = {"n": len(qs), "majority_correct": sum(maj[a][q] for q in qs),
                           "run_pass_rate": round(sum(runs) / len(runs), 4) if runs else None,
                           "pass5": sum(full[q] for q in qs) if all(len(by_q[q]) == 5 for q in qs) else None}
            summary["cells"][f"{m}/{a}"] = cell
            tk = [g["tokens"] for g in graded if g["model"] == m and g["arm"] == a]
            summary["tokens"][f"{m}/{a}"] = {
                "calls": len(tk), "input_total": sum(t["input"] or 0 for t in tk),
                "output_total": sum(t["output"] or 0 for t in tk),
                "input_mean": round(sum(t["input"] or 0 for t in tk) / len(tk), 1),
                "output_mean": round(sum(t["output"] or 0 for t in tk) / len(tk), 1),
                "thinking_total": sum(t.get("thinking") or 0 for t in tk) if m != "phi4" else None}
            pr = [g["correct"] for g in graded if g["model"] == m and g["arm"] == a and g["set"] == "practice"]
            summary["practice"][f"{m}/{a}"] = {"records": len(pr), "correct": sum(pr)}
        if "A3" in maj:
            for b in arms:
                if b == "A3":
                    continue
                for k in KINDS + ["all"]:
                    qs = [q for q in maj["A3"] if q in maj[b] and (k == "all" or items[q]["kind"] == k)]
                    only3 = sum(maj["A3"][q] and not maj[b][q] for q in qs)
                    onlyb = sum(maj[b][q] and not maj["A3"][q] for q in qs)
                    p = sign_test(only3, onlyb)
                    summary["sign"][f"{m}/A3-vs-{b}/{k}"] = {"A3_only": only3, "other_only": onlyb,
                                                              "ties_dropped": len(qs) - only3 - onlyb,
                                                              "p": round(p, 6), "significant_5pct": p < 0.05}
            a3 = [g for g in graded if g["model"] == m and g["arm"] == "A3"]
            pairs = [c for g in a3 for c in g["citations"]]
            summary["citations"][m] = {
                "a3_answers": len(a3), "with_any_citation": sum(1 for g in a3 if g["citations"]),
                "with_verified_citation": sum(g["has_verified_citation"] for g in a3),
                "pairs": len(pairs), "pairs_verify_ok": sum(c["verify_ok"] for c in pairs),
                "scored_answers": sum(1 for g in a3 if g["set"] == "scored"),
                "scored_with_verified_citation": sum(g["has_verified_citation"] for g in a3 if g["set"] == "scored")}

    # retrieval hit: a top-8 hit whose path and line span contain a quoted source line of the item (scored items)
    summary["retrieval_hit"] = {}
    for arm in ("A1", "A2", "A3"):
        res = {k: [0, 0] for k in KINDS + ["all"]}
        for it in items.values():
            if it["set"] != "scored":
                continue
            hits = json.load(open(os.path.join(L.RUNS, "retrieval", arm, it["id"] + ".json"), encoding="utf-8"))
            ok = any(h["path"] == q["path"] and h["line_start"] <= q["line"] <= h["line_end"]
                     for h in hits for q in it["quotes"])
            for k in (it["kind"], "all"):
                res[k][0] += ok
                res[k][1] += 1
        summary["retrieval_hit"][arm] = {k: f"{a}/{b}" for k, (a, b) in res.items()}
        # stale items: a top-8 hit on the superseding (current) line, which is stale.current, not quotes[]
        cur = [(it["stale"]["current"]["path"], it["stale"]["current"]["line"], it["id"]) for it in items.values()
               if it["set"] == "scored" and it["kind"] == "stale"]
        n = 0
        for path, line, iid in cur:
            hits = json.load(open(os.path.join(L.RUNS, "retrieval", arm, iid + ".json"), encoding="utf-8"))
            n += any(h["path"] == path and h["line_start"] <= line <= h["line_end"] for h in hits)
        summary["retrieval_hit"][arm]["stale_current_line"] = f"{n}/{len(cur)}"
    with open(os.path.join(out_dir, "summary.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(summary, f, indent=1, sort_keys=True)

    # markdown tables
    if grades == "judge":
        out.append("Grades in this file: model grade (gpt-oss:20b, GRADING.md section 3).\n")
    for m in models:
        out.append(f"### {m}: scored items (60), per-question majority over the runs; run pass rate = share of all runs correct\n")
        out.append("| Arm | Runs/q | exact (20) | paraphrase (20) | stale (20) | all (60) | run pass rate e/p/s/all | pass^5 e/p/s/all |")
        out.append("|---|---|---|---|---|---|---|---|")
        for a in ARM_ORDER:
            c = summary["cells"].get(f"{m}/{a}")
            if not c:
                if m != "phi4" and a in ("A1", "A2"):
                    out.append(f"| {a} | not run, ruling R-7 | | | | | | |")
                continue
            rp = " / ".join(("-" if c[k]['run_pass_rate'] is None else f"{c[k]['run_pass_rate']:.2f}") for k in KINDS + ["all"])
            p5 = " / ".join("-" if c[k]["pass5"] is None else str(c[k]["pass5"]) for k in KINDS + ["all"])
            out.append(f"| {a} | {','.join(map(str, c['runs_per_question']))} | " +
                       " | ".join(str(c[k]["majority_correct"]) for k in KINDS + ["all"]) + f" | {rp} | {p5} |")
        out.append("")
        for a in ARM_ORDER:
            c = summary.get("changed_majority", {}).get(f"{m}/{a}")
            if c:
                out.append(f"Majority grades changed from keyword to model grade, {m}/{a}: {c['changed']} of 60 "
                           f"(now correct: {', '.join(c['code_to_judge_correct']) or 'none'}; now incorrect: "
                           f"{', '.join(c['code_to_judge_incorrect']) or 'none'}).\n")
        out.append(f"Sign test, {m}: A3 against each arm on per-question majority (A3 only / other only / ties dropped, two-sided exact p)\n")
        out.append("| Comparison | exact | paraphrase | stale | all |")
        out.append("|---|---|---|---|---|")
        for b in ARM_ORDER[:3]:
            row = []
            for k in KINDS + ["all"]:
                s = summary["sign"].get(f"{m}/A3-vs-{b}/{k}")
                row.append("-" if not s else f"{s['A3_only']}/{s['other_only']}/{s['ties_dropped']}, p={s['p']:.4f}" +
                           (" *" if s["significant_5pct"] else ""))
            if all(r == "-" for r in row):
                row = ["not run, ruling R-7"] + [""] * 3 if m != "phi4" else row
            out.append(f"| A3 vs {b} | " + " | ".join(row) + " |")
        out.append("")
        out.append(f"Tokens and calls, {m} (all calls including practice items)\n")
        out.append("| Arm | Calls | input total | output total | input mean | output mean |")
        out.append("|---|---|---|---|---|---|")
        for a in ARM_ORDER:
            t = summary["tokens"].get(f"{m}/{a}")
            if t:
                out.append(f"| {a} | {t['calls']} | {t['input_total']} | {t['output_total']} | {t['input_mean']} | {t['output_mean']} |")
        ci = summary["citations"].get(m)
        if ci:
            out.append(f"\nA3 citations, {m}: {ci['with_any_citation']}/{ci['a3_answers']} answers have a quote and path; "
                       f"{ci['with_verified_citation']}/{ci['a3_answers']} have at least one citation that `verify` prints OK for; "
                       f"{ci['pairs_verify_ok']}/{ci['pairs']} extracted citations verify OK.\n")
    out.append("### Retrieval: scored items where a top-8 hit covers a line in `quotes` (exact / paraphrase / stale / all)\n")
    out.append("| Arm | exact | paraphrase | stale | all |")
    out.append("|---|---|---|---|---|")
    for arm, v in summary["retrieval_hit"].items():
        out.append(f"| {arm} | " + " | ".join(v[k] for k in KINDS + ["all"]) + " |")
    out.append("\nStale items only: a top-8 hit on the superseding line (`stale.current`): " +
               ", ".join(f"{a} {v['stale_current_line']}" for a, v in summary["retrieval_hit"].items()) + ".\n")
    with open(os.path.join(out_dir, "tables.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--grades", choices=["judge", "code"], default="judge")
    main(ap.parse_args().grades)
