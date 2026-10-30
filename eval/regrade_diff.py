"""Compare per-record code grades before and after the disclaimer rule (review round 1).
Usage: python3 eval/regrade_diff.py   (old grades come from commit 095b1c7; writes eval/runs/regrade-diff.json)
"""
import json
import os
import subprocess
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
old = {}
txt = subprocess.run(["git", "show", "095b1c7:eval/runs/graded.jsonl"], capture_output=True, text=True, encoding="utf-8",
                     cwd=HERE, check=True).stdout
for l in txt.splitlines():
    g = json.loads(l)
    old[(g["model"], g["arm"], g["id"], g["run"])] = g
res = defaultdict(lambda: {"records": 0, "changed": 0, "pass_to_fail": 0, "fail_to_pass": 0, "scored_changed": 0,
                           "disclaimer_records": 0, "old_correct": 0, "new_correct": 0})
changed = []
for l in open(os.path.join(HERE, "runs", "graded.jsonl"), encoding="utf-8"):
    g = json.loads(l)
    o = old[(g["model"], g["arm"], g["id"], g["run"])]
    r = res[f"{g['model']}/{g['arm']}"]
    r["records"] += 1
    r["old_correct"] += o["correct"]
    r["new_correct"] += g["correct"]
    r["disclaimer_records"] += bool(g["detail"].get("disclaimer"))
    if o["correct"] != g["correct"]:
        r["changed"] += 1
        r["scored_changed"] += g["set"] == "scored"
        r["pass_to_fail" if o["correct"] else "fail_to_pass"] += 1
        changed.append([g["model"], g["arm"], g["id"], g["run"], g["set"], o["correct"], g["correct"]])
json.dump({"by_model_arm": res, "changed_records": changed}, open(os.path.join(HERE, "runs", "regrade-diff.json"), "w"),
          indent=1, sort_keys=True)
for k, v in sorted(res.items()):
    print(k, v)
