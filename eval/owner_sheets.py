"""Blind owner-grading sheets: 20 scored answers per model, drawn with a fixed seed, arm hidden.

Run after analyze.py: python3 eval/owner_sheets.py
Writes eval/owner-grading/sheet-<A|B>.md (what the owner sees; the letter hides the model) and key-<A|B>.json (arm, item, run, code grade).
The sheet shows the question, the answer, and the reference (key facts, source quote); never the arm or the code grade.
"""
import json
import os
import re
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import n2_lib as L  # noqa: E402

SEED = 27
LABELS = {"haiku": "A", "phi4": "B"}  # the sheets carry only the letter; the key holds the model
OUT = os.path.join(L.HERE, "owner-grading")


def main():
    items = {i["id"]: i for i in L.load_items()}
    graded = [json.loads(l) for l in open(os.path.join(L.RUNS, "graded.jsonl"), encoding="utf-8")]
    os.makedirs(OUT, exist_ok=True)
    for model in sorted({g["model"] for g in graded}):
        pool = sorted((g for g in graded if g["model"] == model and g["set"] == "scored"),
                      key=lambda g: (g["arm"], g["id"], g["run"]))
        pick = random.Random(SEED).sample(pool, 20)
        label = LABELS[model]
        key, sheet = [], [f"# Owner grading sheet {label}\n",
                          "Grade each answer correct (Y) or incorrect (N) against the reference. The arm is hidden. "
                          "Fill the Grade line of each entry. Known limit: an answer with citations in square brackets came from the retrieval arm.\n"]
        for n, g in enumerate(pick, 1):
            it = items[g["id"]]
            rec = json.load(open(os.path.join(L.RUNS, model, g["arm"], g["id"], f"run-{g['run']}.json"), encoding="utf-8"))
            ans = rec["answer"].strip()
            fence = "`" * max(3, max((len(r) for r in re.findall(r"`+", ans)), default=0) + 1)  # longer than any fence inside
            ref = "; ".join(q["text"] for q in it["quotes"])
            if it["kind"] == "stale":
                ref += f" | current: {it['stale']['current']['fact']} | out of date: {it['stale']['superseded']['fact']}"
            sheet += [f"## S{n:02d}\n", f"Question: {it['question']}\n", "Answer:\n", fence + "text", ans, fence + "\n",
                      f"Reference ({it['quotes'][0]['path']}): {ref}\n", f"Key facts: {json.dumps(it['key_facts'], ensure_ascii=False)}\n",
                      "Grade (Y/N): \n"]
            key.append({"sample": f"S{n:02d}", "id": g["id"], "arm": g["arm"], "run": g["run"], "kind": g["kind"],
                        "code_correct": g["correct"]})
        with open(os.path.join(OUT, f"sheet-{label}.md"), "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(sheet))
        with open(os.path.join(OUT, f"key-{label}.json"), "w", encoding="utf-8", newline="\n") as f:
            json.dump({"seed": SEED, "sheet": label, "model": model, "pool_size": len(pool), "samples": key}, f, indent=1)
        print(model, len(pick))


if __name__ == "__main__":
    main()
