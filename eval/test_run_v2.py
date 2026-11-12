"""Checks for N6a: python eval/test_run_v2.py"""
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import judge_v2 as JV  # noqa: E402
import report_v2 as RV  # noqa: E402
import run_v2 as R  # noqa: E402

UN = {"kind": "unanswerable", "question": "What is the default of FOO?", "key_facts": [], "quotes": []}
EX = {"kind": "exact", "question": "q", "key_facts": ["ten"], "quotes": [{"path": "a.md", "line": 1, "text": "ten"}]}


class T(unittest.TestCase):
    def test_classify(self):
        c = R.classify
        self.assertEqual(c(UN, "It is 5.", "N"), "confidently-wrong")
        self.assertEqual(c(UN, "Not in the sources.", "Y"), "abstained-correctly")
        self.assertEqual(c(EX, "ten", "Y"), "correct")
        self.assertEqual(c(EX, "nine", "N"), "confidently-wrong")
        self.assertEqual(c(EX, "I don't know.", "N"), "abstained-wrong")
        self.assertEqual(c(EX, "Not in the sources.", "N", abstained=True), "abstained-wrong")
        self.assertEqual(c(EX, "", "empty"), "empty")
        self.assertEqual(c(EX, "<think>x</think>", "empty"), "empty")

    def test_report_with_out_stays_in_the_run_folder(self):
        import subprocess
        import tempfile
        self.assertEqual(RV.RESULTS, os.path.join(R.L.HERE, "RESULTS-v2.md"))   # default: the committed file
        with tempfile.TemporaryDirectory() as d:
            out = os.path.join(d, "run x")   # a space: the printed command must quote the folder
            code = "import report_v2 as P; print(P.RESULTS); print(P.SRC); print(P.CMD)"
            p = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=True,
                               cwd=os.path.dirname(os.path.abspath(__file__)),
                               env=dict(os.environ, CEREBROLLM_V2_OUT=out))
            self.assertEqual(p.stdout.split("\n")[:3], [os.path.join(out, "RESULTS.md"), ".",
                                                        "python3 eval/run_v2.py --out '%s' report" % out])

    def test_engine_commit_from_the_environment(self):
        os.environ["CEREBROLLM_ENGINE_COMMIT"] = "abc123"
        try:
            self.assertEqual(R.engine_commit(), "abc123")
        finally:
            del os.environ["CEREBROLLM_ENGINE_COMMIT"]

    def test_prompts(self):
        self.assertIn("Y only when the answer says the information is not in the sources", JV.build_prompt(UN, "I do not know."))
        self.assertNotIn("Reference lines", JV.build_prompt(UN, "x"))
        self.assertIn("Reference lines", JV.build_prompt(EX, "x"))

    def test_judge_retry(self):
        replies = iter(["not json", '{"verdict":"Y","reason":"ok"}'])
        r = JV.judge(UN, "x", "gpt-oss:20b", call=lambda p: (next(replies), {}))
        self.assertEqual((r["verdict"], r["attempts"]), ("Y", 2))
        r = JV.judge(UN, "x", "gpt-oss:20b", call=lambda p: ("bad", {}))
        self.assertEqual(r["verdict"], "error")

    def test_rule_of_three(self):
        per = {"I-%02d" % n: ["correct"] * 3 for n in range(35)}
        cw, line = RV.rule_of_three("m A4", per)
        self.assertEqual(cw, 0)
        self.assertIn("8.6% (3 / 35 unique items)", line)
        self.assertIn("conditional on independent draws from the item population", line)
        per["I-07"] = ["correct", "confidently-wrong", "correct"]
        cw, line = RV.rule_of_three("m A4", per)
        self.assertEqual(cw, 1)
        self.assertNotIn("upper bound", line)
        self.assertIn("(I-07)", line)
        per["I-09"] = ["correct", "correct"]
        with self.assertRaisesRegex(SystemExit, "fewer than 3 graded runs for I-09"):
            RV.rule_of_three("m A4", per)
        per["I-09"] = ["correct", "correct", "error"]
        with self.assertRaisesRegex(SystemExit, "for I-09"):
            RV.rule_of_three("m A4", per)
        per["I-09"], per["I-10"] = ["correct"] * 3, []
        with self.assertRaisesRegex(SystemExit, "for I-10"):
            RV.rule_of_three("m A4", per)

    def test_codex_parse(self):
        ev = [{"type": "item.completed", "item": {"type": "error", "message": "m"}},
              {"type": "item.completed", "item": {"type": "agent_message", "text": "first"}},
              {"type": "item.completed", "item": {"type": "agent_message", "text": "final"}},
              {"type": "turn.completed", "usage": {"input_tokens": 3}}]
        a, kinds, u = R.parse_codex("\n".join(json.dumps(e) for e in ev) + "\nnot json")
        self.assertEqual((a, u["input_tokens"]), ("final", 3))
        self.assertFalse([k for k in kinds if k not in R.CODEX_ALLOWED])
        a, kinds, u = R.parse_codex(json.dumps({"type": "item.completed", "item": {"type": "command_execution"}}))
        self.assertEqual([k for k in kinds if k not in R.CODEX_ALLOWED], ["command_execution"])


if __name__ == "__main__":
    unittest.main()
