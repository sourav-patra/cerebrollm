"""Self-check of grade_lib against GRADING.md: gold answers pass, superseded-only answers fail, worked cases.
Run: python eval/test_grade.py   (stdlib only; prints OK <n> or the failures)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import grade_lib as G  # noqa: E402
import n2_lib as L  # noqa: E402

items = {i["id"]: i for i in L.load_items()}
fails = []
n = 0


def check(name, cond):
    global n
    n += 1
    if not cond:
        fails.append(name)


for it in items.values():
    gold = " ".join(q["text"] for q in it["quotes"])
    if it["kind"] == "stale":
        gold += " " + it["stale"]["current"]["text"]
    check(f"gold {it['id']}", G.grade(it, gold)[0])
    check(f"empty {it['id']}", not G.grade(it, "")[0])
    if it["kind"] == "stale":
        # the superseded fact alone must fail (it has no current key fact or states a marker)
        check(f"superseded-only {it['id']}", not G.grade(it, it["stale"]["superseded"]["fact"])[0])

# worked cases from GRADING.md
fake = {"kind": "stale", "key_facts": ["external"], "quotes": [{"text": "x"}],
        "stale": {"markers": ["extended"], "current": {"text": "y"}}}
check("w1", not G.grade(fake, "use external, or use extended if no compression is needed")[0])
fake2 = {"kind": "stale", "key_facts": ["options transform"], "quotes": [{"text": "x"}],
         "stale": {"markers": ["options postprocess"], "current": {"text": "y"}}}
check("w2", G.grade(fake2, "use options.transform; options.postprocess is a deprecated alias")[0])
check("w3", not G.grade(fake2, "use options.transform and options.postprocess")[0])
fake3 = {"kind": "stale", "key_facts": ["top p"], "quotes": [{"text": "x"}],
         "stale": {"markers": ["typical_p"], "current": {"text": "y"}}}
check("w4", not G.grade(fake3, "choose typical_p instead of top_p or min_p")[0])
check("w5", G.grade(fake3, "use top_p, not typical_p")[0])
check("w6", G.grade(fake3, "typical_p (deprecated) so use top_p")[0])
check("t1", G.tokens("4 * dimensions + 8") == "4 times dimensions plus 8".split())
check("t2", G.tokens("4 * dimensions - 8") == "4 times dimensions minus 8".split())
check("t3", G.tokens("--filter-sample-seed") == "filter sample seed".split())
check("t4", G.tokens("4GB") != G.tokens("4 GB"))
check("think", G.grade(fake, "<think>extended external</think> nothing")[0] is False)

# GRADING.md line 15: a disclaimer switches the 80 percent fallback off (only a contiguous key-fact match passes)
ex19, ex17 = items["EX-19"], items["EX-17"]
import json as _json
for iid, it in (("EX-19", ex19), ("EX-17", ex17)):
    for k in range(1, 6):
        rec = _json.load(open(os.path.join(L.RUNS, "haiku", "A0", iid, f"run-{k}.json"), encoding="utf-8"))
        if G.has_disclaimer(G.tokens(rec["answer"])):
            check(f"disclaimer {iid} run {k}", not G.grade(it, rec["answer"])[0])
check("d1", not G.grade(ex19, "I don't know the option that makes filter sample use the same seed.")[0])
check("d2", G.grade(ex19, "I'm not sure, but it is --filter-sample-seed.")[0])  # exact key fact still passes
check("d4", G.has_disclaimer(G.tokens("The docs doesn’t say.")) and G.has_disclaimer(G.tokens("Not Mentioned")))
check("d5", not G.has_disclaimer(G.tokens("The default is 5m.")))
print(("OK %d" % n) if not fails else "FAIL " + "; ".join(fails))
sys.exit(1 if fails else 0)
