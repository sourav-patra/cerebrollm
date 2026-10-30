"""N6a report: tables from the saved records and grades. Run in Ubuntu (it calls `cerebrollm verify`):
python3 eval/run_v2.py report. Writes eval/runs/v2/summary.json and eval/RESULTS-v2.md. Stdlib only.
"""
import collections
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import analyze as A  # noqa: E402
import grade_lib as G  # noqa: E402
import n2_lib as L  # noqa: E402
import run_v2 as R  # noqa: E402

PRIMARY, SECOND = "gpt-oss:20b", "gemma4:12b"
ARMS = ["A0", "A3", "A4"]
CACHE = os.path.join(R.V2, "verify-cache.json")
CLI = os.path.join(L.HERE, "..", "engine", "bin", "cerebrollm")


def verified_cites(records):
    """Per record path: True when at least one (path, quote) pair of the answer prints OK from `cerebrollm verify`."""
    cache = json.load(open(CACHE, encoding="utf-8")) if os.path.exists(CACHE) else {}
    out = {}
    for p, ans in records:
        ok = False
        for pair in A.citations(ans):
            key = json.dumps(pair)
            if key not in cache:
                r = subprocess.run([CLI, "verify", pair[0], pair[1]], capture_output=True, text=True)
                cache[key] = {"exit": r.returncode, "stdout": r.stdout.strip()[:300]}
            ok = ok or (cache[key]["exit"] == 0 and cache[key]["stdout"].startswith("OK"))
        out[p] = ok
    json.dump(cache, open(CACHE, "w", encoding="utf-8", newline="\n"), indent=1)
    return out


def retrieval_hit(item):
    """Top-8 hit on a quoted line (for stale items the current statement is in `quotes`)."""
    p = os.path.join(R.V2, "retrieval", "A3", item["id"] + ".json")
    if not os.path.exists(p) or not item["quotes"]:
        return None
    hits = json.load(open(p, encoding="utf-8"))
    return all(any(h["path"].endswith(q["path"]) and h["line_start"] <= q["line"] <= h["line_end"] for h in hits)
               for q in item["quotes"])


def majority(classes, name):
    return sum(c == name for c in classes) * 2 > len(classes)


def kappa(pairs):
    n = len(pairs)
    po = sum(a == b for a, b in pairs) / n
    ca, cb = collections.Counter(a for a, _ in pairs), collections.Counter(b for _, b in pairs)
    pe = sum(ca[v] * cb[v] for v in set(ca) | set(cb)) / (n * n)
    return None if pe == 1 else round((po - pe) / (1 - pe), 3)


def pct(a, b):
    return f"{100 * a / b:.1f}%" if b else "n/a"


def main():
    items = {i["id"]: i for i in R.load_items()}
    answerable = [i for i in items.values() if i["kind"] != "unanswerable"]
    unans = [i for i in items.values() if i["kind"] == "unanswerable"]
    judged = {(r["model"], r["arm"], r["id"], r["run"]): r for r in R.read_jsonl(R.judge_path(PRIMARY))}
    second = {(r["model"], r["arm"], r["id"], r["run"]): r for r in R.read_jsonl(R.judge_path(SECOND))}
    recs = {}
    for m, a, i, k, p in R.all_records():
        d = json.load(open(p, encoding="utf-8"))
        recs[(m, a, i, k)] = {"path": p, "answer": d["answer"], "seconds": d.get("seconds", 0),
                              "abstained": (d.get("meta") or {}).get("abstained"), "out_tokens": (d.get("tokens") or {}).get("output")}
    a3 = [(r["path"], r["answer"]) for key, r in recs.items() if key[1] == "A3"]
    vc = verified_cites(a3)
    rows = {}  # (model, arm) -> id -> [class per run]
    graded_n = collections.Counter()
    for key, r in recs.items():
        j = judged.get(key)
        if not j:
            continue
        m, a, i, k = key
        rows.setdefault((m, a), {}).setdefault(i, []).append(R.classify(items[i], r["answer"], j["verdict"], r["abstained"]))
        graded_n[(m, a)] += 1
    S = {"models": {}}
    lines = []
    lines.append("# Results v2: 35 public items across models and arms (development step N6a)\n")
    lines.append("Source of every figure: `eval/runs/v2/summary.json` (made by `python3 eval/run_v2.py report` from the records "
                 "under `eval/runs/v2/<model>/<arm>/` and the grades in `eval/runs/v2/judge/`). Grader: `gpt-oss:20b` thinking medium "
                 "(rubric `eval/judge.py` for the 20 answerable items, `eval/judge_v2.py` `RUBRIC_UN` for the 15 unanswerable items). "
                 "Classes are defined in `eval/GRADING-v2.md`. 'Majority' means more than half of the runs of an item.\n")
    hdr = ("| Model | Arm | Runs | Correct (of 20, majority) | Correct (run level) | Abstained correctly (of 15, majority) | "
           "Right outcome (of 35, majority) | Confidently wrong items (majority) | Confidently wrong (runs) | Abstained wrong (runs) | Empty (runs) | Aim 90% / under 2% |")
    lines += ["## Per model and arm\n", hdr, "|" + "---|" * 12]
    for (m, a), per in sorted(rows.items(), key=lambda x: (list(R.MODELS).index(x[0][0]), x[0][1])):
        cl = {i: per.get(i, []) for i in items}
        n_runs = sum(len(v) for v in per.values())
        run_cls = collections.Counter(c for v in per.values() for c in v)
        corr = sum(majority(cl[i["id"]], "correct") for i in answerable)
        abst = sum(majority(cl[i["id"]], "abstained-correctly") for i in unans)
        cw_items = sum(majority(v, "confidently-wrong") for v in cl.values())
        corr_runs = run_cls["correct"]
        n_ans_runs = sum(len(cl[i["id"]]) for i in answerable)
        cw = run_cls["confidently-wrong"]
        right = (corr + abst) / 35
        aim = "met" if right >= 0.9 and cw / n_runs < 0.02 else "not met"
        S["models"].setdefault(m, {})[a] = {
            "records_graded": n_runs, "correct_majority_of_20": corr, "correct_runs": corr_runs, "answerable_runs": n_ans_runs,
            "abstained_correctly_majority_of_15": abst, "right_outcome_majority_of_35": corr + abst,
            "confidently_wrong_items_majority": cw_items, "confidently_wrong_runs": cw, "abstained_wrong_runs": run_cls["abstained-wrong"],
            "empty_runs": run_cls["empty"], "error_runs": run_cls["error"], "aim": aim,
            "by_kind_majority_ok": {k: sum(majority(cl[i["id"]], "abstained-correctly" if k == "unanswerable" else "correct")
                                           for i in items.values() if i["kind"] == k) for k in ("exact", "paraphrase", "stale", "unanswerable")}}
        lines.append(f"| {m} | {a} | {n_runs} | {corr} ({pct(corr, 20)}) | {corr_runs}/{n_ans_runs} ({pct(corr_runs, n_ans_runs)}) | "
                     f"{abst} ({pct(abst, 15)}) | {corr + abst} ({pct(corr + abst, 35)}) | {cw_items} | {cw}/{n_runs} ({pct(cw, n_runs)}) | "
                     f"{run_cls['abstained-wrong']} | {run_cls['empty']} | {aim} |")
    lines.append("\nAim: right outcome at least 90 percent of the 35 items (majority) and confidently wrong under 2 percent of runs. "
                 "Confidently wrong: a wrong answer to an answerable item, or any answer to an unanswerable item.\n")
    lines += ["## Majority correct by kind\n", "| Model | Arm | exact (of 10) | paraphrase (of 7) | stale (of 3) | unanswerable (of 15) |", "|---|---|---|---|---|---|"]
    for m, d in S["models"].items():
        for a, v in d.items():
            k = v["by_kind_majority_ok"]
            lines.append(f"| {m} | {a} | {k['exact']} | {k['paraphrase']} | {k['stale']} | {k['unanswerable']} |")
    # retrieval, citations, timing
    hits = {i["id"]: retrieval_hit(i) for i in answerable}
    nh = sum(bool(v) for v in hits.values())
    lines += ["\n## Retrieval and citations (arm A3)\n",
              f"Top-8 default search holds every quoted line for {nh} of {len(answerable)} answerable items "
              f"(`eval/runs/v2/retrieval/A3/`). Not-hit items: {', '.join(k for k, v in hits.items() if v is False) or 'none'}.\n",
              "| Model | A3 answers | With a verified citation | Share |", "|---|---|---|---|"]
    S["retrieval_hit_items"] = nh
    for m in R.MODELS:
        ks = [k for k in recs if k[0] == m and k[1] == "A3"]
        if ks:
            ok = sum(vc[recs[k]["path"]] for k in ks)
            lines.append(f"| {m} | {len(ks)} | {ok} | {pct(ok, len(ks))} |")
            S["models"].setdefault(m, {}).setdefault("A3", {})["verified_citation_answers"] = ok
    lines += ["\n## Time (sum of per-call seconds in the records)\n", "| Model | Arm | Calls | Total | Mean per call |", "|---|---|---|---|---|"]
    for m in R.MODELS:
        for a in ARMS:
            s = [r["seconds"] for k, r in recs.items() if k[0] == m and k[1] == a]
            if s:
                lines.append(f"| {m} | {a} | {len(s)} | {sum(s) / 60:.1f} min | {sum(s) / len(s):.1f} s |")
    # judge agreement
    both = [(judged[k]["verdict"], second[k]["verdict"], k) for k in second if k in judged]
    lines.append("\n## Grader cross-check (gpt-oss:20b answers graded by gpt-oss:20b and by gemma4:12b thinking off)\n")
    if both:
        agree = sum(a == b for a, b, _ in both)
        yn = [(a, b) for a, b, _ in both if a in "YN" and b in "YN" and a != "empty" and b != "empty"]
        by = collections.defaultdict(lambda: [0, 0])
        for a, b, k in both:
            by[(k[1], items[k[2]]["kind"] == "unanswerable")][1] += 1
            by[(k[1], items[k[2]]["kind"] == "unanswerable")][0] += a == b
        lines.append(f"Same verdict on {agree} of {len(both)} answers ({pct(agree, len(both))}); Cohen's kappa on Y/N {kappa(yn)}.")
        for (arm, un), (x, y) in sorted(by.items()):
            lines.append(f"- arm {arm}, {'unanswerable' if un else 'answerable'} items: {x} of {y} the same")
        S["judge_agreement"] = {"same": agree, "total": len(both), "kappa": kappa(yn)}
        dis = [k for a, b, k in both if a != b]
        lines.append(f"\nDisagreements: {len(dis)} (listed in `eval/runs/v2/summary.json` under `judge_disagreements`).")
        S["judge_disagreements"] = [{"key": list(k), "gpt-oss": judged[k]["verdict"], "gemma4": second[k]["verdict"],
                                     "reason_gpt-oss": judged[k]["reason"], "reason_gemma4": second[k]["reason"]} for k in dis]
    else:
        lines.append("No second-grader records yet.")
    # keyword grade as a second column (answerable items only)
    lines += ["\n## Keyword grade against the model grade (answerable items, GRADING.md section 1)\n",
              "| Model | Arm | Answers | Both Y | Keyword Y, model N | Keyword N, model Y |", "|---|---|---|---|---|---|"]
    for m in R.MODELS:
        for a in ARMS:
            ks = [k for k in recs if k[0] == m and k[1] == a and items[k[2]]["kind"] != "unanswerable" and k in judged]
            if ks:
                kw = {k: G.grade(items[k[2]], recs[k]["answer"])[0] for k in ks}
                both_y = sum(kw[k] and judged[k]["verdict"] == "Y" for k in ks)
                a1 = sum(kw[k] and judged[k]["verdict"] != "Y" for k in ks)
                a2 = sum(not kw[k] and judged[k]["verdict"] == "Y" for k in ks)
                lines.append(f"| {m} | {a} | {len(ks)} | {both_y} | {a1} | {a2} |")
    err = sum(1 for j in list(judged.values()) + list(second.values()) if j["verdict"] == "error")
    lines.append(f"\nGrader replies that did not parse (recorded as error): {err}.")
    S["grader_errors"] = err
    json.dump(S, open(os.path.join(R.V2, "summary.json"), "w", encoding="utf-8", newline="\n"), indent=1, ensure_ascii=False)
    open(os.path.join(L.HERE, "RESULTS-v2.md"), "w", encoding="utf-8", newline="\n").write("\n".join(lines) + "\n")
    print("\n".join(lines))
