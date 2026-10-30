"""Checks for N6a: python eval/test_run_v2.py"""
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import judge_v2 as JV  # noqa: E402
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
