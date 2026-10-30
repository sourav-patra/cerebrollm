"""Lane M3 smoke test: does `draft_num_predict` in the request options change what the Ollama runner does?
Runs the same 200-token request for draft_num_predict 4, 0 and 4 again (warm), saves the final events and the server-log
lines that mention speculative decoding to r2-wsl/smoke/qwen36-draft.json. Run under the GPU lock.
"""
import json
import os
import re
import subprocess
import sys
import time

import r2_wsl
import study
from m3_speed import one_request
from r2_wsl import save

def _server_log():
    local = subprocess.run(['powershell.exe', '-NoProfile', '-Command', '$env:LOCALAPPDATA'], capture_output=True, text=True, timeout=30).stdout.strip()
    return subprocess.run(['wslpath', '-u', local], capture_output=True, text=True, timeout=30).stdout.strip() + '/Ollama/server.log'


LOG = _server_log()
SEP = re.escape(chr(92)) + '/'  # backslash and slash
HOME_PATH = re.compile(f'[A-Za-z]:[{SEP}]+Users[{SEP}]+[^{SEP}\\s"]+')  # a user folder in a log line, replaced before saving
model = sys.argv[1]
study.MODELS.add(model)
text = 'Explain binary search with a Python example and its complexity, in about 300 words.'
size_before = os.path.getsize(LOG) if os.path.exists(LOG) else 0
out = []
for mode in ('mtp4-think-off', 'mtp0-think-off', 'mtp4-think-off'):
    payload, final, ttft, wall = one_request(model, mode, 16384, text, 200)
    out.append({'mode': mode, 'options': payload['options'], 'eval_count': final.get('eval_count'), 'eval_duration': final.get('eval_duration'),
                'gen_tps': final['eval_count'] / (final['eval_duration'] / 1e9), 'load_duration': final.get('load_duration'),
                'final': final, 'wall_seconds': wall})
    print(mode, 'gen tok/s', round(out[-1]['gen_tps'], 1), 'load_s', round(final.get('load_duration', 0) / 1e9, 1), flush=True)
time.sleep(1)
log_lines = []
if os.path.exists(LOG):
    with open(LOG, 'rb') as f:
        f.seek(size_before)
        log_lines = [HOME_PATH.sub('<home>', x) for x in f.read().decode(errors='replace').splitlines()
                     if any(k in x.lower() for k in ('spec', 'draft', 'mtp', 'offload', 'layers', 'kv', 'flash'))]
save('smoke/qwen36-draft.json', {'runs': out, 'server_log_lines_during_smoke': log_lines[-80:]})
print('\n'.join(log_lines[-40:]))
r2_wsl.guard('unload', model)
r2_wsl.guard('check-empty')
