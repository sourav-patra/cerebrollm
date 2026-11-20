"""N6a runner: the public items of one item set (default v2, 35 items) across models and arms. Stdlib only.
Rules: eval/GRADING-v2.md. --set NAME picks the item set (eval/itemset-NAME.toml, see eval/itemset.py).

  prepare                        (Ubuntu, GPU lock: embeds one query per item) search once per item, save hits and the A0/A3 prompts
  gen MODEL [--arms A0,A3] [--runs N] [--jobs J]      send the saved prompts; one record per call, resumable, run k outer
  grade --judge gpt-oss:20b|gemma4:12b|qwen3.5:9b [--models a,b]  (Ubuntu or Windows, GPU lock) one grader call per answer, resumable
  report                         (Ubuntu) tables, agreement, summary.json, RESULTS-v2.md

Records: eval/runs/<set>/<model>/<arm>/<id>/run-<k>.json. Grades: eval/runs/<set>/judge/<judge>.jsonl.
"""
import argparse
import glob
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import grade_lib as G  # noqa: E402
import itemset as IS  # noqa: E402
import judge_v2 as JV  # noqa: E402
import n2_lib as L  # noqa: E402

# --set (or CEREBROLLM_ITEMSET) picks the item set; --out (or CEREBROLLM_V2_OUT) writes a run to a fresh folder;
# one() and cmd_grade() skip records that exist
ITEMSET, ENV_ERROR = IS.load_early()   # --set wins over a bad name in the environment
if ENV_ERROR and __name__ != "__main__":
    raise ENV_ERROR
V2 = os.path.abspath(os.environ.get("CEREBROLLM_V2_OUT") or os.path.join(L.RUNS, ITEMSET.runs_dir))
ITEMS = ITEMSET.items
OPTS = {"num_ctx": 16384, "temperature": 0.7, "num_predict": 4096}  # one setting for every local model and arm
CODEX_MODEL = "gpt-6.1-sol"
CLAUDE_MODEL = "claude-sonnet-5-5"
# model key -> config; `think` is sent to Ollama only when present
MODELS = {
    "gpt-oss-20b": {"kind": "ollama", "name": "gpt-oss:20b", "think": "medium", "runs": 5},
    "gemma4-12b": {"kind": "ollama", "name": "gemma4:12b", "think": False, "runs": 5},
    "phi4": {"kind": "ollama", "name": "phi4", "runs": 5},
    "qwen3.5-9b": {"kind": "ollama", "name": "qwen3.5:9b", "think": False, "runs": 5},
    "sonnet-5-5": {"kind": "claude", "runs": 3},
    # "gpt-6.1" (codex) dropped by orchestrator ruling 2026-10-29: codex quota reserved; its 210 calls made before the ruling are not graded or reported
}
CODEX_ALLOWED = {"agent_message", "reasoning", "error"}  # any other item type is a tool use: the call is void


def load_items():
    return [json.loads(l) for l in open(ITEMS, encoding="utf-8") if l.strip()]


MARKER = "itemset.json"


def bind_folder(create=True):
    """Bind the run folder to this item set before anything is prepared, generated or graded, so that a folder never
    mixes sets. A folder with files and no marker was made before item sets were settings and holds v2 only; the
    report (create=False) does not write a marker."""
    marker = os.path.join(V2, MARKER)
    if os.path.exists(marker):
        with open(marker, encoding="utf-8") as f:
            got = json.load(f)["set"]
        if got != ITEMSET.name:
            raise SystemExit("%s is bound to item set %s but this run is %s: use a fresh --out folder" % (V2, got, ITEMSET.name))
    elif os.path.isdir(V2) and os.listdir(V2):
        if ITEMSET.name != "v2":
            raise SystemExit("%s holds files with no item set recorded (v2, made before item sets were settings) but this run "
                             "is %s: use a fresh --out folder" % (V2, ITEMSET.name))
    elif create:
        write_json(marker, {"set": ITEMSET.name})


def prompt_file(arm, iid):
    return os.path.join(V2, "prompts", arm, iid + ".txt")


def rec_path(model, arm, iid, k):
    return os.path.join(V2, model, arm, iid, f"run-{k}.json")


def write_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
    os.replace(tmp, path)


# ---------------------------------------------------------------- prepare
def cmd_prepare(arms):
    bind_folder()
    for it in load_items():
        hits = []
        if "A3" in arms:
            import prepare as P
            rp = os.path.join(V2, "retrieval", "A3", it["id"] + ".json")
            if os.path.exists(rp):
                hits = json.load(open(rp, encoding="utf-8"))
            else:
                hits = P.search(it["question"], [])
                write_json(rp, hits)
                time.sleep(0.5)
        for arm in arms:
            os.makedirs(os.path.dirname(prompt_file(arm, it["id"])), exist_ok=True)
            with open(prompt_file(arm, it["id"]), "w", encoding="utf-8", newline="\n") as f:
                f.write(L.build_prompt(arm, it["question"], hits if arm == "A3" else []))
        print(it["id"], flush=True)


# ---------------------------------------------------------------- generation
def call_ollama(cfg, prompt):
    body = {"model": cfg["name"], "prompt": prompt, "stream": False, "keep_alive": "10m", "options": OPTS}
    if "think" in cfg:
        body["think"] = cfg["think"]
    req = urllib.request.Request(L.OLLAMA + "/api/generate", json.dumps(body).encode(),
                                 {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=1800) as r:
        d = json.load(r)
    d.pop("context", None)
    return {"answer": d.get("response", ""), "thinking_chars": len(d.get("thinking") or ""),
            "tokens": {"input": d.get("prompt_eval_count"), "output": d.get("eval_count")},
            "meta": {"done_reason": d.get("done_reason"), "model": d.get("model"), "options": OPTS,
                     "think": cfg.get("think"), "total_duration_ns": d.get("total_duration")},
            "raw": d}


def parse_codex(stdout):
    """Return (answer, item types seen, usage) from `codex exec --json` output."""
    msgs, kinds, usage = [], [], None
    for line in stdout.splitlines():
        try:
            e = json.loads(line)
        except ValueError:
            continue
        if e.get("type") == "item.completed":
            it = e.get("item", {})
            kinds.append(it.get("type"))
            if it.get("type") == "agent_message":
                msgs.append(it.get("text", ""))
        elif e.get("type") == "turn.completed":
            usage = e.get("usage")
    return (msgs[-1] if msgs else ""), kinds, usage


def codex_cmd():
    cmd = [shutil.which("codex") or "codex", "exec", "--ignore-user-config", "--ignore-rules", "--ephemeral",
           "--skip-git-repo-check", "-s", "read-only", "-m", CODEX_MODEL, "-c", "model_reasoning_effort=medium",
           "-c", "web_search=disabled"]
    for f in ("shell_tool unified_exec apps plugins browser_use browser_use_external computer_use in_app_browser "
              "image_generation view_image multi_agent hooks skill_search tool_suggest sleep_tool code_mode_host").split():
        cmd += ["--disable", f]
    return cmd + ["--json", "-"]


def call_codex(prompt):
    last = None
    for wait in (0, 20, 60):
        time.sleep(wait)
        with tempfile.TemporaryDirectory(prefix="n6a-codex-") as cwd:  # empty directory: nothing to discover
            p = subprocess.run(codex_cmd(), input=prompt, capture_output=True, text=True, encoding="utf-8",
                               errors="replace", cwd=cwd, timeout=900)
        answer, kinds, usage = parse_codex(p.stdout)
        tools = [k for k in kinds if k not in CODEX_ALLOWED]
        if tools:  # a tool ran: void, logged, retried
            with open(os.path.join(V2, "void-codex.jsonl"), "a", encoding="utf-8") as f:
                f.write(json.dumps({"kinds": kinds, "answer": answer[:200]}) + "\n")
            last = f"tool item {tools}"
            continue
        if p.returncode != 0 or not answer.strip() or usage is None:
            last = f"exit {p.returncode}: {p.stdout[-300:]!r} {p.stderr[-300:]!r}"
            continue
        return {"answer": answer,
                "tokens": {"input": usage.get("input_tokens"), "output": usage.get("output_tokens"),
                           "cached": usage.get("cached_input_tokens"), "thinking": usage.get("reasoning_output_tokens")},
                "meta": {"model": CODEX_MODEL, "effort": "medium", "item_types": kinds,
                         "router_errors": p.stderr.count("codex_core::tools::router")},
                "raw": {"stdout": p.stdout}}
    raise RuntimeError("codex call failed 3 times: " + str(last))


def call(model, prompt):
    cfg = MODELS[model]
    if cfg["kind"] == "ollama":
        return call_ollama(cfg, prompt)
    if cfg["kind"] == "claude":
        L.HOSTED_ALIAS = CLAUDE_MODEL
        return L.call_hosted(prompt)
    return call_codex(prompt)


def call_ask(model, question):
    """Arm A4 (Ubuntu): `cerebrollm ask --json`, the lane N7 pipeline. Its temperature is 0, so repeated runs are near-identical."""
    cfg = MODELS[model]
    cmd = [os.path.join(L.HERE, "..", "engine", "bin", "cerebrollm"), "ask", question, "--model", cfg["name"], "--json"]
    if "think" in cfg:
        cmd += ["--think", "off" if cfg["think"] is False else cfg["think"]]
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if p.returncode != 0:
        raise RuntimeError(f"ask exit {p.returncode}: {p.stderr[-300:]}")
    d = json.loads(p.stdout)
    return {"answer": d["answer"], "tokens": {}, "citations": d["citations"],
            "meta": {"abstained": d["abstained"], "timings": d["timings"], "hits": d["hits"], "model": cfg["name"],
                     "engine_commit": engine_commit()}}


def engine_commit():
    """The engine commit an A4 run used: CEREBROLLM_ENGINE_COMMIT (set it where git cannot read the worktree,
    such as WSL on a Windows checkout), else git rev-parse HEAD."""
    env = os.environ.get("CEREBROLLM_ENGINE_COMMIT")
    if env:
        return env
    return subprocess.run(["git", "-C", os.path.join(L.HERE, ".."), "rev-parse", "HEAD"], capture_output=True,
                          text=True, check=True).stdout.strip()


def one(model, arm, it, k):
    path = rec_path(model, arm, it["id"], k)
    if os.path.exists(path):
        return
    if arm == "A4":
        prompt = "ask:" + it["question"]
    else:
        with open(prompt_file(arm, it["id"]), encoding="utf-8", newline="") as f:
            prompt = f.read()
    t0, started = time.time(), L.utc()
    try:
        r = call_ask(model, it["question"]) if arm == "A4" else call(model, prompt)
    except Exception as e:  # recorded; the run stays missing and is retried on the next start
        with open(os.path.join(V2, "failures.jsonl"), "a", encoding="utf-8") as f:
            f.write(json.dumps({"model": model, "arm": arm, "id": it["id"], "run": k, "error": str(e)[:500]}) + "\n")
        print("FAIL", model, arm, it["id"], k, str(e)[:120], flush=True)
        return
    write_json(path, {"model": model, "arm": arm, "id": it["id"], "run": k, "set": ITEMSET.name, "started_utc": started,
                      "seconds": round(time.time() - t0, 2), "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
                      **r})


def unload(cfg):
    body = json.dumps({"model": cfg["name"], "keep_alive": 0}).encode()
    urllib.request.urlopen(urllib.request.Request(L.OLLAMA + "/api/generate", body,
                                                  {"Content-Type": "application/json"}), timeout=120).read()


def cmd_gen(model, arms, runs, jobs):
    cfg, items = MODELS[model], load_items()
    runs = runs or cfg["runs"]
    bind_folder()
    list(all_records())   # refuses a folder that holds records of another item set before anything is generated
    todo = [(arm, it, k) for k in range(1, runs + 1) for arm in arms for it in items
            if not os.path.exists(rec_path(model, arm, it["id"], k))]
    print(f"{model}: {len(todo)} calls to do", flush=True)
    t0, n, lock = time.time(), [0], threading.Lock()

    def work(t):
        one(model, t[0], t[1], t[2])
        with lock:
            n[0] += 1
            if n[0] % 20 == 0:
                print(f"{n[0]}/{len(todo)} elapsed {time.time() - t0:.0f}s", flush=True)

    with ThreadPoolExecutor(jobs) as ex:
        list(ex.map(work, todo))
    if cfg["kind"] == "ollama":
        unload(cfg)
    print(f"done {model} {len(todo)} calls in {time.time() - t0:.0f}s", flush=True)


# ---------------------------------------------------------------- grading
def check_set(obj, where):
    """Refuse a record or grade of another item set: a run folder holds one set. Files made before item sets were
    settings carry no `set` and belong to v2."""
    got = obj.get("set", "v2")
    if got != ITEMSET.name:
        raise SystemExit("%s is of item set %s but this run is %s: use a fresh --out folder" % (where, got, ITEMSET.name))


def all_records(models=None):
    for p in sorted(glob.glob(os.path.join(V2, "*", "A*", "*", "run-*.json"))):
        parts = os.path.relpath(p, V2).replace("\\", "/").split("/")
        if parts[0] in (models or MODELS) and parts[0] in MODELS:
            with open(p, encoding="utf-8") as f:
                check_set(json.load(f), p)
            yield parts[0], parts[1], parts[2], int(re.search(r"run-(\d+)", parts[3]).group(1)), p


def tags_digest(model):
    with urllib.request.urlopen(L.OLLAMA + "/api/tags", timeout=30) as r:
        return {m["name"]: m["digest"] for m in json.load(r)["models"]}[model]


def judge_path(judge):
    return os.path.join(V2, "judge", judge.replace(":", "-") + ".jsonl")


def read_jsonl(path):
    return [json.loads(l) for l in open(path, encoding="utf-8")] if os.path.exists(path) else []


def read_grades(path):
    """The rows of a grader file, each checked to be of this run's item set."""
    rows = read_jsonl(path)
    for r in rows:
        check_set(r, path)
    return rows


def canary_path(judge):
    return os.path.join(V2, "canary-" + judge.replace(":", "-") + ".json")


def canary(judge, call=None):
    """Grade the item set's canary answers (eval/itemset-NAME.toml) with `judge` and record whether every verdict is the
    expected one. The report claims the target only when this record says passed."""
    items = {i["id"]: i for i in load_items()}
    results = []
    for iid, answer, want in ITEMSET.canaries:
        results.append({"id": iid, "answer": answer, "want": want,
                        "got": JV.judge(items[iid], answer, judge, call=call)["verdict"]})
    rec = {"judge": judge, "set": ITEMSET.name, "passed": all(r["want"] == r["got"] for r in results), "results": results}
    write_json(canary_path(judge), rec)
    return rec


def cmd_sample(judge, n, seed):
    """Draw a random sample of graded answers for the hand check, with a fixed seed, into handcheck-sample.jsonl."""
    import random
    bind_folder(create=False)
    rows = sorted(read_grades(judge_path(judge)), key=lambda r: (r["model"], r["arm"], r["id"], r["run"]))
    if not rows:
        raise SystemExit("no grades by %s in %s" % (judge, V2))
    items = {i["id"]: i for i in load_items()}
    out = os.path.join(V2, "handcheck-sample.jsonl")
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        for r in random.Random(seed).sample(rows, min(n, len(rows))):
            with open(rec_path(r["model"], r["arm"], r["id"], r["run"]), encoding="utf-8") as g:
                answer = json.load(g)["answer"]
            f.write(json.dumps({"model": r["model"], "arm": r["arm"], "id": r["id"], "run": r["run"],
                                "question": items[r["id"]]["question"], "answer": answer, "grader_verdict": r["verdict"],
                                "grader_reason": r["reason"], "your_verdict": None}, ensure_ascii=False) + "\n")
    print("wrote %s: read each answer, set your_verdict to Y or N, then write handcheck.json "
          '{"sampled": N, "disagreements": D, "by": "<who>"} in the run folder' % out)


def cmd_grade(judge, models):
    bind_folder()
    items = {i["id"]: i for i in load_items()}
    out = judge_path(judge)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    done = {(r["model"], r["arm"], r["id"], r["run"]) for r in read_grades(out)}
    digest = tags_digest(judge)
    if ITEMSET.canaries:
        rec = canary(judge)
        print("canary check of %s on %s: %s" % (judge, ITEMSET.name, "passed" if rec["passed"] else "FAILED " + json.dumps(
            [r for r in rec["results"] if r["want"] != r["got"]])), flush=True)
    todo = [r for r in all_records(models) if r[:4] not in done]
    print(f"{judge}: {len(done)} done, {len(todo)} to do", flush=True)
    t0 = time.time()
    with open(out, "a", encoding="utf-8", newline="\n") as f:
        for n, (m, a, i, k, p) in enumerate(todo, 1):
            answer = json.load(open(p, encoding="utf-8"))["answer"]
            if not G.strip_think(answer or "").strip():
                r = {"verdict": "empty", "reason": "no text after removing the think block", "attempts": 0,
                     "seconds": 0, "prompt_sha256": None, "info": None}
            else:
                r = JV.judge(items[i], answer, judge)
            row = {"model": m, "arm": a, "id": i, "run": k, "set": ITEMSET.name, "kind": items[i]["kind"], "judge": judge,
                   "judge_digest": digest, "rubric_un_sha256": JV.RUBRIC_UN_SHA256, "rubric_sha256": JV.J.RUBRIC_SHA256,
                   **{x: r[x] for x in ("verdict", "reason", "attempts", "seconds", "prompt_sha256", "info")}}
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            f.flush()
            if n % 25 == 0 or r["verdict"] == "error":
                print(f"{n}/{len(todo)} {m}/{a}/{i}/{k} {r['verdict']} elapsed {time.time() - t0:.0f}s", flush=True)
    try:
        urllib.request.urlopen(urllib.request.Request(
            L.OLLAMA + "/api/generate", json.dumps({"model": judge, "keep_alive": 0}).encode(),
            {"Content-Type": "application/json"}), timeout=120).read()
    except Exception as e:  # unload failure is reported, not fatal
        print("unload failed:", e)


def classify(item, answer, verdict, abstained=None):
    """Class of one answer (see GRADING-v2.md): correct, abstained-correctly, abstained-wrong, empty, confidently-wrong."""
    if verdict == "empty":
        return "empty"
    if verdict == "error":
        return "error"
    if item["kind"] == "unanswerable":
        return "abstained-correctly" if verdict == "Y" else "confidently-wrong"
    if verdict == "Y":
        return "correct"
    ab = abstained if abstained is not None else G.has_disclaimer(G.tokens(G.strip_think(answer or "")))
    return "abstained-wrong" if ab else "confidently-wrong"


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", dest="itemset", help="item set (default v2): eval/itemset-NAME.toml")
    ap.add_argument("--out", help="run folder (default eval/runs/<set>); records, grades and the report go there")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("prepare").add_argument("--arms", default="A0,A3")
    g = sub.add_parser("gen")
    g.add_argument("model", choices=sorted(MODELS))
    g.add_argument("--arms", default="A0,A3")
    g.add_argument("--runs", type=int)
    g.add_argument("--jobs", type=int, default=1)
    j = sub.add_parser("grade")
    j.add_argument("--judge", required=True, choices=sorted(JV.JUDGES))
    j.add_argument("--models", default=",".join(MODELS))
    r = sub.add_parser("report")
    r.add_argument("--judge", choices=sorted(JV.JUDGES), help="grader whose grades the tables use (default: the item set's grader)")
    r.add_argument("--retrieval-only", action="store_true",
                   help="print only how many answerable items the saved searches (arm A3) hold; writes nothing, claims nothing")
    s = sub.add_parser("sample", help="draw a random sample of graded answers for the hand check")
    s.add_argument("--judge", choices=sorted(JV.JUDGES), help="default: the item set's grader")
    s.add_argument("--n", type=int, default=30)
    s.add_argument("--seed", type=int, default=1)
    a = ap.parse_args()
    if ENV_ERROR and not a.itemset:
        raise ENV_ERROR
    if a.itemset:
        os.environ[IS.ENV] = a.itemset   # also read by report_v2's own import
        ITEMSET = IS.load()
        ITEMS = ITEMSET.items
        if not os.environ.get("CEREBROLLM_V2_OUT"):
            V2 = os.path.abspath(os.path.join(L.RUNS, ITEMSET.runs_dir))
    if a.out:
        os.environ["CEREBROLLM_V2_OUT"] = V2 = os.path.abspath(a.out)   # also read by report_v2's own import
    if a.cmd == "report" and a.judge:
        os.environ["CEREBROLLM_V2_JUDGE"] = a.judge   # read by report_v2's own import
    if a.cmd == "prepare":
        cmd_prepare(a.arms.split(","))
    elif a.cmd == "gen":
        cmd_gen(a.model, a.arms.split(","), a.runs, a.jobs)
    elif a.cmd == "grade":
        cmd_grade(a.judge, a.models.split(","))
    elif a.cmd == "sample":
        cmd_sample(a.judge or ITEMSET.judge, a.n, a.seed)
    else:
        import report_v2
        report_v2.retrieval_only() if a.retrieval_only else report_v2.main()
