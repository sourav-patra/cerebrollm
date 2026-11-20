"""N6a report: tables from the saved records and grades. Run in Ubuntu (it calls `cerebrollm verify`):
python3 eval/run_v2.py report. Writes eval/runs/v2/summary.json and eval/RESULTS-v2.md; with --out DIR,
DIR/summary.json and DIR/RESULTS.md. With --set NAME, the item set's own files and counts (eval/itemset.py)
and, in place of v2, its name in the paths. Stdlib only.
"""
import collections
import json
import os
import shlex
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import analyze as A  # noqa: E402
import grade_lib as G  # noqa: E402
import n2_lib as L  # noqa: E402
import run_v2 as R  # noqa: E402

# `report --judge` (or CEREBROLLM_V2_JUDGE) picks the grader whose grades the tables use, else the item set's grader;
# gemma4:12b stays the cross-check
IS = R.ITEMSET   # the item set of this run: counts, grader, results file
PRIMARY, SECOND = os.environ.get("CEREBROLLM_V2_JUDGE") or IS.judge, "gemma4:12b"
PRIMARY_THINK = "thinking %s" % (R.JV.JUDGES[PRIMARY] or "off")   # "thinking medium" for gpt-oss:20b
ARMS = ["A0", "A3", "A4"]
HANDCHECK_MIN = 30   # graded answers a person reads before the target is claimed
GRADER_FIELD = {"gpt-oss:20b": "gpt-oss", "gemma4:12b": "gemma4"}   # keys of summary.json judge_disagreements; other graders use their own name
CACHE = os.path.join(R.V2, "verify-cache.json")
CLI = os.path.join(L.HERE, "..", "engine", "bin", "cerebrollm")
# With --out the report stays inside the run folder and names it; the committed RESULTS-v2.md is never touched.
SETARG = "" if IS.name == "v2" else "--set %s " % IS.name
DEFAULT = os.path.abspath(os.path.join(L.RUNS, IS.runs_dir))
if os.path.abspath(R.V2) == DEFAULT:
    SRC, RESULTS = "eval/runs/" + IS.runs_dir, IS.results
    CMD = "python3 eval/run_v2.py %sreport" % SETARG
else:   # paths in the report are relative to the report, which sits in the run folder
    SRC, RESULTS = ".", os.path.join(R.V2, "RESULTS.md")
    CMD = "python3 eval/run_v2.py %s--out %s report" % (SETARG, shlex.quote(os.path.abspath(R.V2)))
if PRIMARY != IS.judge:
    CMD += " --judge " + PRIMARY


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


def target_blocker():
    """Why the grader's verdicts cannot yet support the item set's target, or None. Two records of the run folder are
    needed: the grader's canary check, passed (`run_v2.py grade` writes it), and a hand check of a random sample of
    graded answers with no disagreement (`run_v2.py sample` draws the sample; the person writes handcheck.json). Each
    record counts only for the grades it names: the item set, the grader, the grader's model digest and the sha256 of
    its grades file (R.batch_evidence); the canary record must also hold every configured canary with the expected
    verdict, whatever its `passed` says."""
    if IS.target_pct is None:
        return None
    want = R.batch_evidence(PRIMARY)
    if want["judge_digest"] is None:
        return "the grades of %s do not record one model digest" % PRIMARY
    try:
        with open(R.canary_path(PRIMARY), encoding="utf-8") as f:
            canary = json.load(f)
    except OSError:
        return "the grader canary check of %s has not run" % PRIMARY
    stale = [k for k, v in want.items() if canary.get(k) != v]
    if stale:
        return "the canary record of %s is for other grades (%s differ)" % (PRIMARY, ", ".join(stale))
    results = canary.get("results")
    if (not isinstance(results, list) or not all(isinstance(r, dict) for r in results)
            or sorted(repr((r.get("id"), r.get("answer"), r.get("want"))) for r in results) != sorted(map(repr, IS.canaries))):
        return "the canary record of %s does not hold the configured canaries of %s" % (PRIMARY, IS.name)
    bad = [r["answer"] for r in results if r["want"] != r.get("got")]
    if bad:
        return "the grader canary check of %s failed on %s" % (PRIMARY, "; ".join(repr(a) for a in bad))
    try:
        with open(os.path.join(R.V2, "handcheck.json"), encoding="utf-8") as f:
            hand = json.load(f)
    except OSError:
        return "no hand check of a random sample of graded answers (handcheck.json)"
    stale = [k for k, v in want.items() if hand.get(k) != v]
    if stale:
        return "handcheck.json is for other grades (%s differ)" % ", ".join(stale)
    if not isinstance(hand.get("sampled"), int) or hand["sampled"] < HANDCHECK_MIN:
        return "the hand check sampled fewer than %d graded answers" % HANDCHECK_MIN
    if hand.get("disagreements") != 0:
        return "the hand check found %s disagreements with the grader" % hand.get("disagreements")
    return None


def majority(classes, name):
    return sum(c == name for c in classes) * 2 > len(classes)


def rule_of_three(arm, per, runs=3, target_pct=None, blocker=None):
    """Items with any confidently-wrong run, and the 95% upper bound 3 / unique items on the share of such items
    when there are none. per: item id -> [class per run]. Fails when an item has fewer than `runs` graded runs;
    a run whose grade did not parse ("error") does not count as graded. With target_pct (the item set's target),
    the line ends by saying whether the printed bound is under it; an item with a confidently-wrong run means
    no bound is printed and the target is not reached. A `blocker` (why the grader's verdicts cannot yet support the
    target) turns "reached" into "not claimed" with that reason."""
    short = sorted(i for i, v in per.items() if sum(c != "error" for c in v) < runs)
    if short:
        raise SystemExit("report refused: arm %s has fewer than %d graded runs for %s" % (arm, runs, ", ".join(short)))
    bad = sorted(i for i, v in per.items() if "confidently-wrong" in v)
    line = f"{arm}: {len(bad)} of {len(per)} items with a confidently-wrong run" + (f" ({', '.join(bad)})" if bad else "")
    if not bad:
        line += (f"; 95% upper bound on the share of items with a confidently-wrong run {pct(3, len(per))} "
                 f"(3 / {len(per)} unique items), conditional on independent draws from the item population "
                 "(repeated runs of the same item are not independent trials); it does not bound the run-level rate")
    if target_pct is not None:
        reached = not bad and float(pct(3, len(per))[:-1]) < target_pct
        state = ("not claimed (%s)" % blocker) if reached and blocker else ("reached" if reached else "not reached")
        line += f". Target under {target_pct:g}%: {state}"
    return len(bad), line


def kappa(pairs):
    n = len(pairs)
    po = sum(a == b for a, b in pairs) / n
    ca, cb = collections.Counter(a for a, _ in pairs), collections.Counter(b for _, b in pairs)
    pe = sum(ca[v] * cb[v] for v in set(ca) | set(cb)) / (n * n)
    return None if pe == 1 else round((po - pe) / (1 - pe), 3)


def pct(a, b):
    return f"{100 * a / b:.1f}%" if b else "n/a"


def retrieval_only():
    """Print how many answerable items the saved searches (arm A3) hold, and which they miss or lack; no grades are
    needed and nothing is written or claimed."""
    R.bind_folder(create=False)
    answerable = [i for i in R.load_items() if i["kind"] != "unanswerable"]
    hits = {i["id"]: retrieval_hit(i) for i in answerable}
    missing = [k for k, v in hits.items() if v is None]
    print(f"Top-8 default search holds every quoted line for {sum(bool(v) for v in hits.values())} of {len(hits)} answerable items; "
          f"{len(hits) - len(missing)} checked, missing retrieval records: {', '.join(missing) or 'none'}; "
          f"not-hit items: {', '.join(k for k, v in hits.items() if v is False) or 'none'}.")


def main():
    R.bind_folder(create=False)
    items = {i["id"]: i for i in R.load_items()}
    answerable = [i for i in items.values() if i["kind"] != "unanswerable"]
    unans = [i for i in items.values() if i["kind"] == "unanswerable"]
    judged = {(r["model"], r["arm"], r["id"], r["run"]): r for r in R.read_grades(R.judge_path(PRIMARY))}
    second = {(r["model"], r["arm"], r["id"], r["run"]): r for r in R.read_grades(R.judge_path(SECOND))}
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
    if not rows:
        raise SystemExit("report refused: no graded runs by %s in %s; run `grade` first (the saved-search check alone is "
                         "`report --retrieval-only`)" % (PRIMARY, R.V2))
    S = {"models": {}}
    lines = []
    n_all, n_ans, n_un = IS.total, IS.n_answerable, IS.n_unanswerable
    lines.append(f"# Results {IS.name}: {n_all} public items across models and arms (development step N6a)\n")
    lines.append(f"Source of the tables except time and keyword grade: `{SRC}/summary.json` (made by `{CMD}` from the records "
                 f"under `{SRC}/<model>/<arm>/` and the grades in `{SRC}/judge/`). Grader: `{PRIMARY}` {PRIMARY_THINK} "
                 f"(rubric `eval/judge.py` for the {n_ans} answerable items, `eval/judge_v2.py` `RUBRIC_UN` for the {n_un} unanswerable items). "
                 "The time and keyword-grade tables are computed from the records themselves. "
                 "Classes are defined in `eval/GRADING-v2.md`. 'Majority' means more than half of the runs of an item.\n")
    hdr = (f"| Model | Arm | Runs | Correct (of {n_ans}, majority) | Correct (run level) | Abstained correctly (of {n_un}, majority) | "
           f"Right outcome (of {n_all}, majority) | Confidently wrong items (majority) | Confidently wrong (runs) | Abstained wrong (runs) | Empty (runs) | Aim 90% / under 2% |")
    lines += ["## Per model and arm\n", hdr, "|" + "---|" * 12]
    bounds = []
    blocker = target_blocker()
    for (m, a), per in sorted(rows.items(), key=lambda x: (list(R.MODELS).index(x[0][0]), x[0][1])):
        cl = {i: per.get(i, []) for i in items}
        cw_any, bound_line = rule_of_three(f"{m} {a}", cl, target_pct=IS.target_pct, blocker=blocker)
        bounds.append(bound_line)
        n_runs = sum(len(v) for v in per.values())
        run_cls = collections.Counter(c for v in per.values() for c in v)
        corr = sum(majority(cl[i["id"]], "correct") for i in answerable)
        abst = sum(majority(cl[i["id"]], "abstained-correctly") for i in unans)
        cw_items = sum(majority(v, "confidently-wrong") for v in cl.values())
        corr_runs = run_cls["correct"]
        n_ans_runs = sum(len(cl[i["id"]]) for i in answerable)
        cw = run_cls["confidently-wrong"]
        right = (corr + abst) / n_all
        aim = "met" if right >= 0.9 and cw / n_runs < 0.02 else "not met"
        S["models"].setdefault(m, {})[a] = {
            "records_graded": n_runs, f"correct_majority_of_{n_ans}": corr, "correct_runs": corr_runs, "answerable_runs": n_ans_runs,
            f"abstained_correctly_majority_of_{n_un}": abst, f"right_outcome_majority_of_{n_all}": corr + abst,
            "confidently_wrong_items_majority": cw_items, "confidently_wrong_runs": cw, "abstained_wrong_runs": run_cls["abstained-wrong"],
            "empty_runs": run_cls["empty"], "error_runs": run_cls["error"], "aim": aim, "items_any_confidently_wrong": cw_any,
            "by_kind_majority_ok": {k: sum(majority(cl[i["id"]], "abstained-correctly" if k == "unanswerable" else "correct")
                                           for i in items.values() if i["kind"] == k) for k in ("exact", "paraphrase", "stale", "unanswerable")}}
        lines.append(f"| {m} | {a} | {n_runs} | {corr} ({pct(corr, n_ans)}) | {corr_runs}/{n_ans_runs} ({pct(corr_runs, n_ans_runs)}) | "
                     f"{abst} ({pct(abst, n_un)}) | {corr + abst} ({pct(corr + abst, n_all)}) | {cw_items} | {cw}/{n_runs} ({pct(cw, n_runs)}) | "
                     f"{run_cls['abstained-wrong']} | {run_cls['empty']} | {aim} |")
    lines.append(f"\nAim: right outcome at least 90 percent of the {n_all} items (majority) and confidently wrong under 2 percent of runs. "
                 "Confidently wrong: a wrong answer to an answerable item, or any answer to an unanswerable item.\n")
    lines += ["## Items with any confidently-wrong run (rule of three)\n"] + ["- " + b for b in bounds] + [""]
    lines += ["## Majority correct by kind\n", f"| Model | Arm | exact (of {IS.kind_count('exact')}) | paraphrase (of {IS.kind_count('paraphrase')}) | stale (of {IS.kind_count('stale')}) | unanswerable (of {n_un}) |", "|---|---|---|---|---|---|"]
    for m, d in S["models"].items():
        for a, v in d.items():
            k = v["by_kind_majority_ok"]
            lines.append(f"| {m} | {a} | {k['exact']} | {k['paraphrase']} | {k['stale']} | {k['unanswerable']} |")
    # retrieval, citations, timing
    hits = {i["id"]: retrieval_hit(i) for i in answerable}
    nh = sum(bool(v) for v in hits.values())
    missing = [k for k, v in hits.items() if v is None]
    partial = (f" {len(hits) - len(missing)} of {len(hits)} were checked; missing retrieval records: {', '.join(missing)}."
               if 0 < len(missing) < len(hits) else "")
    lines += ["\n## Retrieval and citations (arm A3)\n",
              f"Top-8 default search holds every quoted line for {nh} of {len(answerable)} answerable items "
              f"(`{SRC}/retrieval/A3/`). Not-hit items: {', '.join(k for k, v in hits.items() if v is False) or 'none'}.{partial}\n",
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
    authors = IS.judge if IS.name == "v2" else (", ".join(sorted({k[0] for k in second if k in judged})) or "the")   # v2 keeps its heading
    lines.append(f"\n## Grader cross-check ({authors} answers graded by {PRIMARY} and by {SECOND} thinking off)\n")
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
        lines.append(f"\nDisagreements: {len(dis)} (listed in `{SRC}/summary.json` under `judge_disagreements`).")
        # v2 keeps its field names whatever grader is named; other sets name the grader
        p_name, s_name = ("gpt-oss", "gemma4") if IS.name == "v2" else (GRADER_FIELD.get(PRIMARY, PRIMARY), GRADER_FIELD.get(SECOND, SECOND))
        S["judge_disagreements"] = [{"key": list(k), p_name: judged[k]["verdict"], s_name: second[k]["verdict"],
                                     "reason_" + p_name: judged[k]["reason"], "reason_" + s_name: second[k]["reason"]} for k in dis]
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
    open(RESULTS, "w", encoding="utf-8", newline="\n").write("\n".join(lines) + "\n")
    print("\n".join(lines))
