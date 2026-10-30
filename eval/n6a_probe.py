"""N6a GPU probe: load gemma4:12b with the runner's num_ctx, print Ollama's version and per-model size_vram, exit 1 when no model is on the GPU."""
import json
import sys
import urllib.request

O = "http://127.0.0.1:11434"


def call(path, body=None):
    req = urllib.request.Request(O + path, json.dumps(body).encode() if body else None, {"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=600))


print("ollama", call("/api/version")["version"])
call("/api/generate", {"model": "gemma4:12b", "prompt": "hi", "stream": False, "think": False, "keep_alive": "1m",
                       "options": {"num_ctx": 16384, "num_predict": 8}})
ms = call("/api/ps")["models"]
for m in ms:
    print(m["name"], "size", m["size"], "size_vram", m["size_vram"], "context", m.get("context_length"))
call("/api/generate", {"model": "gemma4:12b", "keep_alive": 0})
sys.exit(0 if ms and all(m["size_vram"] > 0 for m in ms) else 1)
