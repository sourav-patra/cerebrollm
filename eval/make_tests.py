"""Write promptfoo-tests.json (one test per item: id and question) from items.jsonl."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import n2_lib as L  # noqa: E402

t = [{"vars": {"id": i["id"], "question": i["question"]}, "description": i["id"]} for i in L.load_items()]
with open(os.path.join(L.HERE, "promptfoo-tests.json"), "w", encoding="utf-8", newline="\n") as f:
    json.dump(t, f, indent=1, ensure_ascii=False)
