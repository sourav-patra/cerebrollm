"""Build the prompts for arms A0..A3 for all 70 items: run the engine's search, save its output and the prompt.

Run in Ubuntu: python3 eval/prepare.py [--reuse]   (needs PostgreSQL and the embedding model in Ollama)
Writes eval/runs/retrieval/<arm>/<id>.json (the search's JSON hits) and eval/runs/prompts/<arm>/<id>.txt.
"""
import json
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import n2_lib as L  # noqa: E402

CLI = os.path.join(L.HERE, "..", "engine", "bin", "cerebrollm")


def search(question, flags):
    for wait in (0, 30, 130):  # 130 s: the Windows port-exhaustion backoff of embed_pace.py
        time.sleep(wait)
        p = subprocess.run([CLI, "search", question, "--k", "8", "--json", *flags], capture_output=True, text=True)
        if p.returncode == 0:
            return json.loads(p.stdout)
    raise RuntimeError(f"search failed: {p.stderr[-500:]}")


def main():
    for it in L.load_items():
        for arm, (flags, _) in L.ARMS.items():
            out = L.prompt_path(arm, it["id"])
            os.makedirs(os.path.dirname(out), exist_ok=True)
            hits = []
            if flags is not None:
                rp = os.path.join(L.RUNS, "retrieval", arm, it["id"] + ".json")
                os.makedirs(os.path.dirname(rp), exist_ok=True)
                if "--reuse" in sys.argv and os.path.exists(rp):  # rebuild prompts from the saved search output
                    hits = json.load(open(rp, encoding="utf-8"))
                else:
                    hits = search(it["question"], flags)
                with open(rp, "w", encoding="utf-8", newline="\n") as f:
                    json.dump(hits, f, ensure_ascii=False, indent=1)
                if "--reuse" not in sys.argv:
                    time.sleep(0.5)  # one embed request per search; stay far below the port limit
            with open(out, "w", encoding="utf-8", newline="\n") as f:
                f.write(L.build_prompt(arm, it["question"], hits))
        print(it["id"], flush=True)


if __name__ == "__main__":
    main()
