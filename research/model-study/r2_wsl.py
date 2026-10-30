"""R2 on the WSL machine (development step M, issue #11). Run with the Ubuntu venv: python -B r2_wsl.py ACTION [MODEL].

Every case is a file under r2-wsl/, so an interrupted unit resumes where it stopped.
  sandbox            prove the container (network denied, write denied, 20 s timeout) before generated code runs
  correctness MODEL  40 HumanEval cases and 12 tool scenarios for every mode of MODEL, then unload through the guard
  speed MODEL        8,000- and 200-token prompts, 3 runs each after a warm-up, quiet-machine gate
  quiet              print the quiet-machine reading and exit 0 (quiet) or 1
Method, prompts, options and scoring are those of study.py (development step D); only the output folder, the
shared HTTP client, the Docker path conversion and the Windows load readings differ.
"""
import json
import os
import subprocess
import sys
import time

import httpx

import study
from study import OUT as STUDY, extract_code, extra_options, mode_args, tag
from studyconfig import DOCKER, OLLAMA, OLLAMA_URL, hostpath

OUT = STUDY / 'r2-wsl'
GUARD = STUDY / 'model_guard.py'
MODES = {'phi4': ['default'], 'devstral:24b': ['default'], 'gpt-oss:20b': ['medium', 'low'],
         'qwen3:14b': ['thinking-on', 'thinking-off'], 'qwen3:8b': ['thinking-off'],
         'qwen3-coder:30b': ['default'], 'qwen3:30b': ['thinking-off'],
         'gemma4:12b': ['thinking-on', 'thinking-off'],
         'qwen3.6:35b-a3b-coding-mtp-q4_K_M': ['mtp4-think-off', 'mtp0-think-off'], 'glm-4.7-flash:q4_K_M': ['think-off']}  # development steps M2 and M3 (lane M3: Qwen3.6 MTP tag with draft_num_predict 4 and 0, GLM-4.7-Flash); M2: nemotron-3.5-lightning refused by the guard (licence)
study.MODELS.update(['qwen3-coder:30b', 'qwen3:30b', 'gemma4:12b', 'qwen3.6:35b-a3b-coding-mtp-q4_K_M', 'glm-4.7-flash:q4_K_M'])
# Quiet machine: Ubuntu 1-minute load <= 4, Windows CPU (5 s mean) <= 25 %, GPU utilisation <= 20 %, and
# `ollama ps` lists nothing but the model under test. Idle readings on 2026-10-29: CPU 8-16 %, GPU 6-12 %.
QUIET = {'load1': 4.0, 'win_cpu_pct': 25.0, 'gpu_util_pct': 20.0}
CLIENT = httpx.Client(timeout=1800, trust_env=False)  # one client: Windows runs out of ports with many short connections


def save(path, value):
    path = OUT / path
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(value, indent=2, default=str) + '\n')
    tmp.replace(path)


def load(path):
    return json.loads((OUT / path).read_text())


def append(path, value):
    with (OUT / path).open('a') as f:
        f.write(json.dumps(value, default=str) + '\n')


def post(endpoint, payload):
    r = CLIENT.post(OLLAMA_URL + '/api/' + endpoint, json=payload)
    r.raise_for_status()
    return r.json()


def ps_models():
    return [m['model'] for m in CLIENT.get(OLLAMA_URL + '/api/ps').json().get('models', [])]


def windows_cpu():
    cmd = ['powershell.exe', '-NoProfile', '-Command',
           "(Get-Counter '\\Processor(_Total)\\% Processor Time' -SampleInterval 1 -MaxSamples 5 | "
           "% { $_.CounterSamples[0].CookedValue } | Measure-Object -Average).Average"]
    return round(float(subprocess.run(cmd, capture_output=True, text=True, timeout=60).stdout.strip()), 1)


def gpu_reading():
    out = subprocess.run(['nvidia-smi.exe', '--query-gpu=utilization.gpu,memory.used', '--format=csv,noheader,nounits'],
                         capture_output=True, text=True, timeout=30).stdout.strip().split(',')
    return int(out[0]), int(out[1])


def snapshot():
    util, mem = gpu_reading()
    return {'time': time.time(), 'loadavg': os.getloadavg(), 'win_cpu_pct': windows_cpu(),
            'gpu_util_pct': util, 'gpu_mem_mib': mem, 'ollama_ps': ps_models()}


def is_quiet(snap, model):
    return (snap['loadavg'][0] <= QUIET['load1'] and snap['win_cpu_pct'] <= QUIET['win_cpu_pct']
            and snap['gpu_util_pct'] <= QUIET['gpu_util_pct'] and all(n in (model, model + ':latest') for n in snap['ollama_ps']))


def chat(model, mode, messages, num_predict, tools=None):
    payload = {'model': model, 'messages': messages, 'stream': False, 'keep_alive': '15m',
               'options': {'temperature': 0, 'seed': 27, 'num_ctx': 16384, 'num_predict': num_predict, **extra_options(model, mode)},
               **mode_args(model, mode)}
    if tools is not None:
        payload['tools'] = tools
    load_before = os.getloadavg()
    started = time.monotonic()
    response = post('chat', payload)
    return {'request': payload, 'response': response, 'wall_seconds': time.monotonic() - started,
            'load_average_before': load_before, 'load_average_after': os.getloadavg()}


def sandbox_run(folder, script, name):
    cmd = [DOCKER, 'run', '--rm', '--name', name, '--network', 'none', '--read-only', '--cap-drop', 'ALL',
           '--security-opt', 'no-new-privileges', '--memory', '256m', '--cpus', '1', '--pids-limit', '64',
           '--user', '65534:65534', '--tmpfs', '/tmp:rw,noexec,nosuid,size=16m',
           '-v', hostpath(folder) + ':/w:ro', 'python:3.13-slim', 'python', '/w/' + script]
    started = time.monotonic()
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
        result = {'exit': r.returncode, 'stdout': r.stdout, 'stderr': r.stderr, 'timeout': False}
    except subprocess.TimeoutExpired as e:
        result = {'exit': None, 'stdout': str(e.stdout or ''), 'stderr': str(e.stderr or ''), 'timeout': True}
    finally:
        cleanup = subprocess.run([DOCKER, 'rm', '-f', name], capture_output=True, text=True, timeout=30)
    result.update(command=cmd, wall_seconds=time.monotonic() - started,
                  cleanup={'exit': cleanup.returncode, 'stdout': cleanup.stdout, 'stderr': cleanup.stderr})
    return result


def sandbox_check():
    folder = OUT / 'sandbox-check'
    folder.mkdir(parents=True, exist_ok=True)
    p = study.load('humaneval-40.json')[0]
    # Each probe exits 0 only when the sandbox did its job.
    probes = {
        'positive': (p['prompt'] + p['canonical_solution'] + '\n' + p['test'] + '\ncheck(' + p['entry_point'] + ')\n', 0, False),
        'negative': ('raise RuntimeError("deliberate negative control")\n', 1, False),
        'network': ('import socket\ntry:\n    socket.create_connection(("1.1.1.1", 53), timeout=5)\nexcept OSError as e:\n'
                    '    print("network denied:", e)\nelse:\n    raise SystemExit("NETWORK REACHABLE")\n', 0, False),
        'write': ('try:\n    open("/w/x.txt", "w")\nexcept OSError as e:\n    print("mount write denied:", e)\nelse:\n'
                  '    raise SystemExit("MOUNT WRITABLE")\ntry:\n    open("/etc/x.txt", "w")\nexcept OSError as e:\n'
                  '    print("root fs write denied:", e)\nelse:\n    raise SystemExit("ROOT FS WRITABLE")\n', 0, False),
        'timeout': ('while True:\n    pass\n', None, True)}
    results = []
    for name, (body, want_exit, want_timeout) in probes.items():
        (folder / (name + '.py')).write_text(body)
        r = sandbox_run(folder, name + '.py', 'r2-sandbox-' + name)
        listed = subprocess.run([DOCKER, 'ps', '-a', '--filter', 'name=r2-sandbox-' + name, '--format', '{{.Names}}'],
                                capture_output=True, text=True, timeout=30).stdout.strip()
        ok = (r['timeout'] == want_timeout and (want_timeout or (r['exit'] == 0 if want_exit == 0 else r['exit'] not in (0, None)))
              and listed == '')
        if want_timeout:
            ok = ok and 19 <= r['wall_seconds'] <= 30
        results.append({'name': name, 'ok': ok, 'container_left_behind': listed, **r})
        print(name, 'ok' if ok else 'FAILED', 'exit', r['exit'], 'timeout', r['timeout'], round(r['wall_seconds'], 1), 's', flush=True)
    save('sandbox-check.json', results)
    assert all(x['ok'] for x in results), 'sandbox check failed; no generated code may run'
    print('PASS: positive passes, negative fails, network denied, writes denied, 20 s timeout enforced, no container left')


def code_unit(model, mode):
    problems = study.load('humaneval-40.json')
    label = tag(model, mode)
    folder = OUT / 'code' / label
    folder.mkdir(parents=True, exist_ok=True)
    errors = 0
    for i, p in enumerate(problems):
        if (folder / f'result_{i}.json').exists() or (folder / f'error_{i}.json').exists():
            continue
        prompt = ('Implement the Python function below. Return the complete executable function '
                  'with any needed imports, in one Python code block, without explanations.\n\n' + p['prompt'])
        try:
            r = chat(model, mode, [{'role': 'user', 'content': prompt}], 4096)
            generated = extract_code(r['response']['message'].get('content', ''), p['entry_point'])
            (folder / f'test_{i}.py').write_text(generated + '\n' + p['test'] + '\ncheck(' + p['entry_point'] + ')\n')
            test = sandbox_run(folder, f'test_{i}.py', f'r2-{label}-{i}'.replace(':', '-'))
            save(f'code/{label}/result_{i}.json', {'task_id': p['task_id'], 'index': i, **r, 'test': test,
                                                   'passed': test['exit'] == 0})
            print(label, 'code', i + 1, 'passed', test['exit'] == 0, flush=True)
            errors = 0
        except (httpx.HTTPError, subprocess.SubprocessError) as e:
            save(f'code/{label}/error_{i}.json', {'error': repr(e), 'index': i, 'task_id': p['task_id'],
                                                  'load_average': os.getloadavg(), 'passed': False})
            print(label, 'code', i + 1, 'ERROR', repr(e), flush=True)
            errors += 1
            if errors >= 3:
                raise SystemExit('three consecutive errors; stop and look')


def tools_unit(model, mode):
    suite = study.load('tool-scenarios.json')
    label = tag(model, mode)
    for i, case in enumerate(suite['scenarios']):
        name = f'tools/{label}/{i:02d}.json'
        if (OUT / name).exists():
            continue
        try:
            r = chat(model, mode, [{'role': 'system', 'content': 'Choose exactly one next tool call. Do not execute tools or return explanations.'},
                                   {'role': 'user', 'content': case['prompt']}], 2048, suite['tools'])
            calls = r['response']['message'].get('tool_calls', [])
            passed = (len(calls) == 1 and calls[0].get('function', {}).get('name') == case['expected']['name']
                      and calls[0]['function'].get('arguments') == case['expected']['arguments'])
            save(name, {'id': case['id'], **r, 'expected': case['expected'], 'passed': passed})
        except httpx.HTTPStatusError as e:
            # Unsupported native tools is a measured zero; text is never converted into a tool call.
            save(name, {'id': case['id'], 'error': e.response.text, 'status': e.response.status_code, 'passed': False,
                        'load_average': os.getloadavg()})
        print(label, 'tools', i + 1, load(name)['passed'], flush=True)


def guard(*args):
    r = subprocess.run([sys.executable, '-B', str(GUARD), *args], capture_output=True, text=True, timeout=7200)
    print('guard', *args, 'exit', r.returncode, r.stdout.strip(), r.stderr.strip(), flush=True)
    if r.returncode != 0:  # 2 refused, 1 failed: the unit stops before any inference
        raise SystemExit(f'guard {" ".join(args)} exited {r.returncode}; unit stopped')
    return r.returncode


def correctness(model):
    guard('pull', model)  # a no-op when installed; records the digest otherwise
    for mode in MODES[model]:
        label = tag(model, mode)
        start = snapshot()
        append('units.jsonl', {'unit': 'correctness-start', 'label': label, **start})
        code_unit(model, mode)
        tools_unit(model, mode)
        append('units.jsonl', {'unit': 'correctness-end', 'label': label, **snapshot()})
    guard('unload', model)
    guard('check-empty')


WORDS = ('river stone window garden copper lantern harbor meadow candle engine ribbon valley market pencil forest '
         'bridge anchor saddle thread mirror orchard puzzle quartz rocket season ticket velvet wagon yellow zephyr '
         'basket cobalt dagger ember falcon glacier hammer island jungle kettle ladder marble nectar oyster pepper').split()


def filler(n):
    # Varied words, not one repeated token: Ollama 0.40.12 aborts a reply that repeats ("token repeat limit reached").
    return ' '.join(WORDS[(i * 7 + i // len(WORDS)) % len(WORDS)] for i in range(n))


def prompt_for(reps, run):
    # The leading marker (a single digit, 1 to 6 by mode and run) keeps runs from sharing a cached prefix; Ollama keeps
    # several cache slots, so a second mode of the same model would otherwise hit the first mode's identical prompt.
    return (f'Performance measurement run {run}. Read the following data.\n' + filler(reps) +
            '\nWrite a detailed explanation of binary search, including Python examples and complexity. Continue for at least 500 words.')


def calibrate(model, mode, length):
    """Filler size that makes the whole prompt `length` tokens. A model whose chat template already carries a long
    system prompt (devstral, about 1,200 tokens) cannot reach 200: the smallest prompt is used and its size recorded."""
    overhead = chat(model, mode, [{'role': 'user', 'content': 'hi'}], 1)['response'].get('prompt_eval_count')
    reps = max(1, int(length * 0.7))
    for _ in range(10):
        got = chat(model, mode, [{'role': 'user', 'content': prompt_for(reps, 0)}], 1)['response'].get('prompt_eval_count')
        if abs(got - length) <= max(2, length * 0.005) or (reps == 1 and got > length):
            return {'repetitions': reps, 'length': length, 'prompt_tokens': got, 'template_overhead_tokens': overhead}
        reps = max(1, round(reps * length / got)) if got > length or reps > 1 else reps
    raise SystemExit(f'calibration failed for {model} at {length}')


def wait_quiet(model, label):
    for attempt in range(20):
        snap = snapshot()
        if is_quiet(snap, model):
            return snap
        append('speed-deferred.jsonl', {'label': label, 'attempt': attempt, **snap})
        time.sleep(30)
    raise SystemExit('machine not quiet for 10 minutes; speed deferred for ' + label)


def speed_unit(model, mode):
    label = tag(model, mode)
    for length in (8000, 200):
        cal = f'speed/{label}/{length}-calibration.json'
        if not (OUT / cal).exists():
            save(cal, calibrate(model, mode, length))
        calib = load(cal)
        reps, target = calib['repetitions'], calib['prompt_tokens']
        for run in (1, 2, 3):
            name = f'speed/{label}/{length}-{run}.json'
            if (OUT / name).exists() and load(name)['valid']:
                continue
            chat(model, mode, [{'role': 'user', 'content': 'Warm up. Count from one to twenty.'}], 32)
            before = wait_quiet(model, label)
            payload = {'model': model, 'messages': [{'role': 'user', 'content': prompt_for(reps, MODES[model].index(mode) * 3 + run)}], 'stream': True,
                       'keep_alive': '15m', 'options': {'temperature': 0, 'seed': 27, 'num_ctx': 16384, 'num_predict': 256, **extra_options(model, mode)},
                       **mode_args(model, mode)}
            first = first_content = None
            events = 0
            started = time.monotonic()
            with CLIENT.stream('POST', OLLAMA_URL + '/api/chat', json=payload) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if not line:
                        continue
                    event = json.loads(line)
                    events += 1
                    elapsed = time.monotonic() - started
                    msg = event.get('message', {})
                    if first is None and (msg.get('content') or msg.get('thinking')):
                        first = elapsed
                    if first_content is None and msg.get('content'):
                        first_content = elapsed
                    final = event
            wall = time.monotonic() - started
            api_ps = CLIENT.get(OLLAMA_URL + '/api/ps').json()['models']
            cli_ps = subprocess.run([OLLAMA, 'ps'], capture_output=True, text=True, timeout=30).stdout
            after_load = os.getloadavg()
            entry = next((m for m in api_ps if m.get('model') in (model, model + ':latest')), None)
            gpu_pct = round(100 * entry['size_vram'] / entry['size'], 1) if entry else None
            problems = []
            pe, cached = final.get('prompt_eval_count'), final.get('prompt_eval_cached_count', 0)
            if not final.get('done'):
                problems.append('stream did not complete')
            if pe is None or not final.get('prompt_eval_duration') or not final.get('eval_duration'):
                problems.append('final event lacks timing fields')
            else:
                if abs(pe - target) > max(2, target * 0.005):
                    problems.append(f'prompt_eval_count {pe} differs from the calibrated {target}')
                if cached > calib['template_overhead_tokens'] + 2:
                    problems.append(f"{cached} prompt tokens came from the cache; the chat template alone is {calib['template_overhead_tokens']}")
            if final.get('load_duration', 0) > 2e9:
                problems.append('model was loaded during the measurement')
            if after_load[0] > QUIET['load1']:
                problems.append('Ubuntu load after the run above threshold')
            ok = pe is not None and final.get('prompt_eval_duration') and final.get('eval_duration')
            rec = {'model': model, 'mode': mode, 'length': length, 'run': run, 'calibration': calib, 'valid': not problems, 'problems': problems,
                   'before': before, 'load_average_after': after_load, 'ttft_seconds': first,
                   'first_visible_content_seconds': first_content, 'wall_seconds': wall, 'events': events, 'final': final,
                   'prompt_tps': (pe - cached) / (final['prompt_eval_duration'] / 1e9) if ok else None,
                   'generation_tps': final['eval_count'] / (final['eval_duration'] / 1e9) if ok else None,
                   'ps_api': api_ps, 'ps_cli': cli_ps, 'gpu_pct': gpu_pct, 'request': payload}
            if (OUT / name).exists():  # keep the invalid record, then rerun under a new file
                save(f'speed/{label}/{length}-{run}-invalid-{int(time.time())}.json', load(name))
            save(name, rec)
            print(label, length, run, 'valid', not problems, problems, 'gen_tps', rec['generation_tps'],
                  'prompt_tps', rec['prompt_tps'], 'gpu%', gpu_pct, flush=True)


def speed(model):
    guard('pull', model)
    assert all(n in (model, model + ':latest') for n in ps_models()), 'another model is loaded: ' + str(ps_models())
    for mode in MODES[model]:
        speed_unit(mode=mode, model=model)
    guard('unload', model)
    guard('check-empty')


if __name__ == '__main__':
    action = sys.argv[1]
    if action == 'sandbox':
        sandbox_check()
    elif action == 'quiet':
        snap = snapshot()
        print(json.dumps(snap), 'QUIET' if is_quiet(snap, sys.argv[2] if len(sys.argv) > 2 else 'none') else 'NOT QUIET')
        sys.exit(0 if is_quiet(snap, sys.argv[2] if len(sys.argv) > 2 else 'none') else 1)
    elif action == 'correctness':
        correctness(sys.argv[2])
    elif action == 'speed':
        speed(sys.argv[2])
    else:
        sys.exit(__doc__)
