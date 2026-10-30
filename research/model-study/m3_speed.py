"""Lane M3: generation speed at 8k, 32k and 64k context with Windows memory readings. Run with the Ubuntu venv, under the GPU lock:

    flock ~/.cerebrollm/gpu.lock python -B m3_speed.py MODEL MODE [--ctx 8192,32768,65536]

Each step loads the model with num_ctx = the step, sends one prompt of about (num_ctx - 600) tokens and records the final
event, `ollama ps`, and a once-per-second sample of Windows free RAM and `\\Memory\\Pages/sec` taken while the request runs.
A step is attempted only if the previous step kept free RAM above 2 GB and showed no sustained paging.
Files: r2-wsl/ctx-speed/LABEL/CTX-RUN.json and LABEL/ladder.json. Method details (prompt, options, seed) are those of r2_wsl.py.
"""
import json
import subprocess
import sys
import threading
import time

import httpx

import r2_wsl
import study
from r2_wsl import CLIENT, OUT, OLLAMA, OLLAMA_URL, extra_options, mode_args, prompt_for, save, tag, wait_quiet

FREE_MIN_MB = 2048     # free RAM must stay above 2 GB
PAGING_PPS = 1000      # a sample above this many pages/s counts as paging ...
PAGING_RUN = 5         # ... and five in a row (about five seconds) as sustained
RUNS = 2
SAMPLER = ("while ($true) { $p = (Get-Counter '\\Memory\\Pages/sec' -SampleInterval 1).CounterSamples[0].CookedValue; "
           "$a = (Get-Counter '\\Memory\\Available MBytes').CounterSamples[0].CookedValue; "
           "$f = (Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory; "
           "Write-Output ('{0},{1},{2}' -f [math]::Round($p, 1), [math]::Round($f / 1024), $a) }")


class Sampler:
    """powershell.exe loop; each line is `pages_per_sec,free_mb,available_mb` with the time it arrived."""

    def __init__(self):
        self.rows = []
        self.proc = subprocess.Popen(['powershell.exe', '-NoProfile', '-Command', SAMPLER], stdout=subprocess.PIPE, text=True)
        self.thread = threading.Thread(target=self._read, daemon=True)
        self.thread.start()

    def _read(self):
        for line in self.proc.stdout:
            try:
                p, f, a = line.strip().split(',')
                self.rows.append({'t': time.time(), 'pages_per_sec': float(p), 'free_mb': float(f), 'available_mb': float(a)})
            except ValueError:
                pass

    def mark(self):
        return len(self.rows)

    def stop(self):
        self.proc.kill()
        self.thread.join(timeout=10)
        return self.rows


def summarise(rows):
    if not rows:
        return {'samples': 0}
    run = longest = 0
    for r in rows:
        run = run + 1 if r['pages_per_sec'] > PAGING_PPS else 0
        longest = max(longest, run)
    pps = sorted(r['pages_per_sec'] for r in rows)
    return {'samples': len(rows), 'min_free_mb': min(r['free_mb'] for r in rows), 'min_available_mb': min(r['available_mb'] for r in rows),
            'max_pages_per_sec': pps[-1], 'median_pages_per_sec': pps[len(pps) // 2], 'longest_paging_run_samples': longest,
            'sustained_paging': longest >= PAGING_RUN, 'free_ok': min(r['free_mb'] for r in rows) > FREE_MIN_MB}


def one_request(model, mode, ctx, content, num_predict):
    payload = {'model': model, 'messages': [{'role': 'user', 'content': content}], 'stream': True, 'keep_alive': '15m',
               'options': {'temperature': 0, 'seed': 27, 'num_ctx': ctx, 'num_predict': num_predict, **extra_options(model, mode)},
               **mode_args(model, mode)}
    first = None
    final = {}
    started = time.monotonic()
    with CLIENT.stream('POST', OLLAMA_URL + '/api/chat', json=payload) as response:
        response.raise_for_status()
        for line in response.iter_lines():
            if line:
                event = json.loads(line)
                if first is None and (event.get('message', {}).get('content') or event.get('message', {}).get('thinking')):
                    first = time.monotonic() - started
                final = event
    return payload, final, first, time.monotonic() - started


def step(model, mode, label, ctx, sampler):
    # warm-up at this context: loads the model and measures tokens per filler word for the prompt size
    _, probe, _, _ = one_request(model, mode, ctx, prompt_for(1000, 0), 1)
    per_rep = probe['prompt_eval_count'] / 1000
    target = ctx - 600
    reps = max(1, int(target / per_rep))
    runs = []
    for run in range(1, RUNS + 1):
        before = wait_quiet(model, label)
        ps_before = subprocess.run([OLLAMA, 'ps'], capture_output=True, text=True, timeout=30).stdout
        start = sampler.mark()
        payload, final, ttft, wall = one_request(model, mode, ctx, prompt_for(reps, 10 + run), 256)
        during = summarise(sampler.rows[start:])
        api_ps = CLIENT.get(OLLAMA_URL + '/api/ps').json()['models']
        cli_ps = subprocess.run([OLLAMA, 'ps'], capture_output=True, text=True, timeout=30).stdout
        entry = next((m for m in api_ps if m.get('model') in (model, model + ':latest')), None)
        pe, cached = final.get('prompt_eval_count'), final.get('prompt_eval_cached_count', 0)
        ok = bool(pe and final.get('prompt_eval_duration') and final.get('eval_duration') and final.get('done'))
        problems = []
        if not ok:
            problems.append('final event incomplete')
        elif abs(pe - target) > target * 0.05:
            problems.append(f'prompt_eval_count {pe} differs from the target {target} by more than 5% (truncated?)')
        if final.get('load_duration', 0) > 2e9:
            problems.append('model was loaded during the measurement')
        rec = {'model': model, 'mode': mode, 'num_ctx': ctx, 'run': run, 'target_prompt_tokens': target, 'valid': not problems, 'problems': problems,
               'before': before, 'ollama_ps_before': ps_before, 'ollama_ps_after': cli_ps, 'ps_api': api_ps,
               'gpu_pct': round(100 * entry['size_vram'] / entry['size'], 1) if entry else None,
               'memory_during_request': during, 'ttft_seconds': ttft, 'wall_seconds': wall, 'final': final,
               'prompt_tps': (pe - cached) / (final['prompt_eval_duration'] / 1e9) if ok else None,
               'generation_tps': final['eval_count'] / (final['eval_duration'] / 1e9) if ok else None,
               'request_options': payload['options']}
        save(f'ctx-speed/{label}/{ctx}-{run}.json', rec)
        print(label, ctx, run, 'valid', not problems, problems, 'gen_tps', rec['generation_tps'], 'prompt_tps', rec['prompt_tps'],
              'gpu%', rec['gpu_pct'], 'memory', during, flush=True)
        runs.append(rec)
        if not during.get('free_ok', False) or during.get('sustained_paging', True):
            break  # do not repeat a run that exhausted RAM
    return runs


def ladder(model, mode, steps):
    study.MODELS.add(model)
    for other in [n for n in r2_wsl.ps_models() if n not in (model, model + ':latest')]:  # e.g. another lane's embedding model, kept 5 min after its last call
        r = subprocess.run([OLLAMA, 'stop', other], capture_output=True, text=True, timeout=60)
        print(f'unloaded {other} before the ladder (ollama stop exit {r.returncode}); ollama ps now: {r2_wsl.ps_models()}', flush=True)
        time.sleep(3)
    assert all(n in (model, model + ':latest') for n in r2_wsl.ps_models()), 'another model is loaded: ' + str(r2_wsl.ps_models())
    label = tag(model, mode)
    sampler = Sampler()
    time.sleep(4)
    result = {'model': model, 'mode': mode, 'ollama_version': CLIENT.get(OLLAMA_URL + '/api/version').json().get('version'), 'steps': {}, 'rule': f'free RAM > {FREE_MIN_MB} MB and no {PAGING_RUN} consecutive Pages/sec samples above {PAGING_PPS}'}
    try:
        for ctx in steps:
            runs = step(model, mode, label, ctx, sampler)
            mem = runs[-1]['memory_during_request']
            go = mem.get('free_ok', False) and not mem.get('sustained_paging', True)
            result['steps'][ctx] = {'runs': len(runs), 'valid_runs': sum(r['valid'] for r in runs), 'memory': mem, 'next_step_allowed': go}
            save(f'ctx-speed/{label}/ladder.json', result)
            if not go:
                print(f'STOP after {ctx}: free RAM or paging rule failed; higher steps not attempted', flush=True)
                break
    finally:
        sampler.stop()
        r2_wsl.guard('unload', model)
        r2_wsl.guard('check-empty')


if __name__ == '__main__':
    steps = [8192, 32768, 65536]
    if '--ctx' in sys.argv:
        steps = [int(x) for x in sys.argv[sys.argv.index('--ctx') + 1].split(',')]
    ladder(sys.argv[1], sys.argv[2], steps)
