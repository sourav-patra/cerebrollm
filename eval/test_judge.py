"""Tests for eval/judge.py: prompt building and reply parsing. No Ollama call. Run: python3 eval/test_judge.py"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import judge as J  # noqa: E402
import n2_lib as L  # noqa: E402

items = {i["id"]: i for i in L.load_items()}
n = 0


def check(cond, msg):
    global n
    assert cond, msg
    n += 1


# prompt building
ex = items["ST-01"]
p = J.build_prompt(ex, "<think>hidden</think>Use /api/embed with input.")
check(p.startswith(J.RUBRIC), "rubric first")
check(ex["question"] in p and ex["quotes"][0]["text"] in p, "question and reference line")
check("Current statement: " + ex["stale"]["current"]["fact"] in p, "stale current")
check("Out-of-date statement: " + ex["stale"]["superseded"]["fact"] in p, "stale superseded")
check("hidden" not in p and "Use /api/embed with input." in p, "think block stripped, answer kept")
check(p.rstrip().endswith("<<<END ANSWER>>>"), "answer delimited")
plain = next(i for i in items.values() if i["kind"] == "exact")
check("Out-of-date" not in J.build_prompt(plain, "x"), "no stale block on a non-stale item")
alt = next(i for i in items.values() if any(isinstance(k, list) for k in i["key_facts"]))
check("[" in J.build_prompt(alt, "x").split("Key facts:")[1].split("\n")[0], "alternatives shown in brackets")
check(len(J.RUBRIC_SHA256) == 64, "rubric hash")

# reply parsing
check(J.parse_reply('{"verdict": "Y", "reason": "ok"}') == ("Y", "ok"), "valid")
for bad in ("not json", '{"reason": "x"}', '{"verdict": "Y"}', '{"verdict": "maybe", "reason": "x"}', "[1]"):
    try:
        J.parse_reply(bad)
        check(False, "should fail: " + bad)
    except ValueError:
        check(True, "")


# retry once, then error
def seq(*replies):
    it = iter(replies)
    calls = []

    def call(prompt):
        calls.append(prompt)
        return next(it), {}
    return call, calls


good = json.dumps({"verdict": "N", "reason": "r"})
call, calls = seq("garbage", good)
r = J.judge(plain, "a", call)
check(r["verdict"] == "N" and r["attempts"] == 2 and len(calls) == 2, "retry then ok")
call, calls = seq("garbage", '{"verdict": "Y"}')
r = J.judge(plain, "a", call)
check(r["verdict"] == "error" and len(calls) == 2 and "raw=" in r["reason"], "two bad replies give error, not Y or N")
call, calls = seq(good)
check(J.judge(plain, "a", call)["attempts"] == 1 and len(calls) == 1, "no retry on a good reply")

# owner grades parse: 20 per sheet
s = list(J.owner_samples())
check(len(s) == 40 and all(x[6] in "YN" for x in s), "40 owner grades")
print("OK", n)
