"""Tables and rule application for R2 on the WSL machine, from the per-case files in r2-wsl/.
Writes r2-wsl/r2-table.json and r2-wsl/r2-table.md. Python standard library only.
"""
import json
from pathlib import Path
import statistics

OUT = Path(__file__).resolve().parent / 'r2-wsl'
CORE = [('phi4', 'default'), ('devstral:24b', 'default'), ('gpt-oss:20b', 'medium'), ('gpt-oss:20b', 'low'),
        ('qwen3:14b', 'thinking-on'), ('qwen3:14b', 'thinking-off'), ('qwen3:8b', 'thinking-off')]
RECORD = [('qwen3-coder:30b', 'default'), ('qwen3:30b', 'thinking-off')]  # ruling R-4: for the record, never in the rules
NEW = [('gemma4:12b', 'thinking-on'), ('gemma4:12b', 'thinking-off')]  # development step M2 (nemotron-3.5-lightning was refused by the guard)
R2A = {('phi4', 'default'), ('devstral:24b', 'default'), ('gpt-oss:20b', 'medium'), ('qwen3:14b', 'thinking-on'), ('gemma4:12b', 'thinking-on')}
R2B = {('phi4', 'default'), ('gpt-oss:20b', 'low'), ('qwen3:14b', 'thinking-off'), ('qwen3:8b', 'thinking-off'), ('gemma4:12b', 'thinking-off')}
M3 = [('qwen3.6:35b-a3b-coding-mtp-q4_K_M', 'mtp4-think-off'), ('qwen3.6:35b-a3b-coding-mtp-q4_K_M', 'mtp0-think-off'),
      ('glm-4.7-flash:q4_K_M', 'think-off')]  # lane M3: no role rules apply, the owner picks
GEN_MIN = 15.0


def label(m, mode):
    return m.replace(':', '-') + '-' + mode


def cases(folder, pattern):
    return [json.loads(p.read_text()) for p in sorted((OUT / folder).glob(pattern))] if (OUT / folder).exists() else []


def row(model, mode):
    lab = label(model, mode)
    code = [c for c in cases(f'code/{lab}', 'result_*.json')] + cases(f'code/{lab}', 'error_*.json')
    tools = cases(f'tools/{lab}', '[0-9]*.json')
    r = {'model': model, 'mode': mode, 'code_done': len(code), 'code_pass': sum(1 for c in code if c['passed']),
         'code_errors': len(cases(f'code/{lab}', 'error_*.json')),
         'tool_done': len(tools), 'tool_pass': sum(1 for t in tools if t['passed']),
         'tool_http_errors': sum(1 for t in tools if 'error' in t)}
    complete = r['code_done'] == 40 and r['tool_done'] == 12
    r['code_pct'] = 100 * r['code_pass'] / 40 if complete else None
    r['tool_pct'] = 100 * r['tool_pass'] / 12 if complete else None
    r['combined'] = 0.5 * r['code_pct'] + 0.5 * r['tool_pct'] if complete else None
    loads = [c['load_average_before'][0] for c in code + tools if 'load_average_before' in c]
    r['load1_range'] = [min(loads), max(loads)] if loads else None
    for length in (8000, 200):
        runs = [json.loads(p.read_text()) for p in sorted((OUT / f'speed/{lab}').glob(f'{length}-[123].json'))] if (OUT / f'speed/{lab}').exists() else []
        runs = [x for x in runs if x['valid']]
        if len(runs) == 3:
            r[f'gen_tps_{length}'] = statistics.mean(x['generation_tps'] for x in runs)
            r[f'prompt_tps_{length}'] = statistics.mean(x['prompt_tps'] for x in runs)
            r[f'ttft_{length}'] = statistics.mean(x['ttft_seconds'] for x in runs)
            r[f'gpu_pct_{length}'] = min(x['gpu_pct'] for x in runs if x['gpu_pct'] is not None)
            r[f'ps_{length}'] = runs[-1]['ps_cli'].strip().splitlines()[-1] if runs[-1]['ps_cli'].strip() else ''
        else:
            r[f'speed_{length}_valid_runs'] = len(runs)
    return r


def apply_rules(rows, r10=False):
    """r10=True: ruling R-10, the 100% GPU part of the R2a gate is replaced by the speed gate alone."""
    by = {(r['model'], r['mode']): r for r in rows}
    log = []
    done = [r for r in rows if r['combined'] is not None]
    best_code = max(r['code_pct'] for r in done)
    best_combined = max(r['combined'] for r in done)
    log.append(f'Best R2 code pass@1 across modes: {best_code:.1f}%. Best combined: {best_combined:.2f}.')
    # R2a: highest combined with generation >= 15 tok/s at 16,384 and 100% GPU (8,000-token prompt, the fuller context).
    pool = []
    for key in R2A:
        r = by.get(key)
        if not r or r['combined'] is None:
            continue
        g, gpu = r.get('gen_tps_8000'), r.get('gpu_pct_8000')
        ok = g is not None and g >= GEN_MIN and (r10 or (gpu is not None and gpu == 100.0))
        log.append(f"R2a candidate {key[0]}/{key[1]}: combined {r['combined']:.2f}, gen {g if g is None else round(g, 1)} tok/s, "
                   f"GPU {gpu}% -> {'qualifies' if ok else 'does not qualify'}")
        if ok:
            pool.append(r)
    r2a = max(pool, key=lambda r: r['combined']) if pool else None
    log.append('R2a: ' + (f"{r2a['model']} ({r2a['mode']})" if r2a else 'none qualifies'))
    # R2b: highest generation tok/s (8,000-token prompt) among R2b candidates within 10 points of the best code pass@1.
    pool = []
    for key in R2B:
        r = by.get(key)
        if not r or r['code_pct'] is None or r.get('gen_tps_8000') is None:
            continue
        within = r['code_pct'] >= best_code - 10
        log.append(f"R2b candidate {key[0]}/{key[1]}: code {r['code_pct']:.1f}%, gen {r['gen_tps_8000']:.1f} tok/s -> "
                   f"{'within 10 points' if within else 'more than 10 points below'}")
        if within:
            pool.append(r)
    r2b = max(pool, key=lambda r: r['gen_tps_8000']) if pool else None
    log.append('R2b: ' + (f"{r2b['model']} ({r2b['mode']})" if r2b else 'none'))
    # Sharing: one model fills both roles if it is within 5 points of the best in each (R2a: combined; R2b: code pass@1).
    # The shared model must still pass the R2a gate, so with no R2a qualifier there is nothing to share.
    sharing = None
    if r2a and r2b and r2a['model'] == r2b['model']:
        sharing = r2a
        log.append(f"Sharing: {r2a['model']} wins both roles.")
    elif r2a and r2b:
        log.append('Sharing: different models won R2a and R2b; one of them fills both only if within 5 points of the best in each.')
    else:
        log.append('Sharing: the R2a role has no qualifying model, so no model can be shared into it.')
    if not r2a:
        near = [r for r in done if (r['model'], r['mode']) in R2A and r.get('gen_tps_8000') is not None]
        near.sort(key=lambda r: -r['combined'])
        def why(r):
            bad = []
            if r['gen_tps_8000'] < GEN_MIN:
                bad.append(f"generation below {GEN_MIN:g} tok/s")
            if not r10 and r['gpu_pct_8000'] != 100.0:
                bad.append('GPU below 100%')
            return ' and '.join(bad)
        log.append('R2a closest by combined score, none passing the gate: ' +
                   '; '.join(f"{r['model']} ({r['mode']}) combined {r['combined']:.2f}, gen {r['gen_tps_8000']:.1f} tok/s, "
                             f"GPU {r['gpu_pct_8000']}% (fails: {why(r)})" for r in near))
    return {'best_code': best_code, 'best_combined': best_combined, 'r2a': r2a and (r2a['model'], r2a['mode']),
            'r2b': r2b and (r2b['model'], r2b['mode']), 'sharing': sharing and (sharing['model'], sharing['mode']), 'log': log}


def fmt(v, spec='.1f'):
    return 'not measured' if v is None else format(v, spec)


def table(rows):
    head = ('| Model / mode | Code pass@1 | Tool pass | Combined | Gen tok/s 8,000 / 200 | Prompt tok/s 8,000 | TTFT s 8,000 | GPU % | `ollama ps` (8,000-token run) |\n'
            '|---|---:|---:|---:|---|---:|---:|---:|---|\n')
    out = ''
    for r in rows:
        code = f"{r['code_pass']}/{r['code_done']} ({fmt(r['code_pct'])}%)" if r['code_pct'] is not None else f"{r['code_pass']}/{r['code_done']} (incomplete)"
        tool = f"{r['tool_pass']}/{r['tool_done']}"
        out += (f"| `{r['model']}` / {r['mode']} | {code} | {tool} | {fmt(r['combined'], '.2f')} | "
                f"{fmt(r.get('gen_tps_8000'))} / {fmt(r.get('gen_tps_200'))} | {fmt(r.get('prompt_tps_8000'), '.0f')} | "
                f"{fmt(r.get('ttft_8000'), '.2f')} | {fmt(r.get('gpu_pct_8000'))} | {r.get('ps_8000', 'not measured')} |\n")
    return head + out


def ctx_table(rows):
    """Lane M3: generation speed by context from ctx-speed/LABEL/CTX-RUN.json, with the Windows memory readings of the same request."""
    out = ('| Model / mode | num_ctx | Prompt tokens | Gen tok/s (runs) | Prompt tok/s | GPU % | Min free RAM MB | Max Pages/sec | Sustained paging | `ollama ps` after |\n'
           '|---|---:|---:|---|---:|---:|---:|---:|---|---|\n')
    for model, mode in rows:
        folder = OUT / 'ctx-speed' / label(model, mode)
        for ctx in (8192, 32768, 65536):
            runs = [json.loads(p.read_text()) for p in sorted(folder.glob(f'{ctx}-[0-9].json'))] if folder.exists() else []
            if not runs:
                out += f'| `{model}` / {mode} | {ctx} | not measured | | | | | | | |\n'
                continue
            ok = [r for r in runs if r['valid']]
            ps = runs[-1]['ollama_ps_after'].strip().splitlines()
            mems = [r['memory_during_request'] for r in runs]
            out += (f"| `{model}` / {mode} | {ctx} | {runs[-1]['final'].get('prompt_eval_count')} | "
                    f"{', '.join(fmt(r['generation_tps']) for r in runs)}{'' if len(ok) == len(runs) else ' (invalid run present)'} | "
                    f"{fmt(runs[-1]['prompt_tps'], '.0f')} | {fmt(runs[-1]['gpu_pct'])} | {fmt(min(m.get('min_free_mb', 0) for m in mems), '.0f')} | "
                    f"{fmt(max(m.get('max_pages_per_sec', 0) for m in mems), '.0f')} | "
                    f"{any(m.get('sustained_paging') for m in mems)} | {ps[-1] if ps else ''} |\n")
    return out


if __name__ == '__main__':
    import sys
    if sys.argv[1:] == ['m3']:  # lane M3: the existing rows for reference, the three new modes, the context ladder
        rows = [row(*k) for k in CORE + NEW + M3]
        md = table(rows) + '\nSpeed by context (lane M3 ladder):\n\n' + ctx_table(M3)
        (OUT / 'r2-table-M3.json').write_text(json.dumps({'rows': rows}, indent=2, default=str) + '\n')
        (OUT / 'r2-table-M3.md').write_text(md)
        print(md)
        sys.exit(0)
    if sys.argv[1:] == ['m2']:  # development step M2: old and new rows, rules as written and under R-10; new files, the R2 files stay as committed
        rows = [row(*k) for k in CORE + NEW]
        plain, r10 = apply_rules(rows), apply_rules(rows, r10=True)
        (OUT / 'r2-table-M2.json').write_text(json.dumps({'rows': rows, 'rules_as_written': plain, 'rules_r10': r10}, indent=2, default=str) + '\n')
        md = (table(rows) + '\nRules as written (100% GPU):\n\n' + '\n'.join('- ' + x for x in plain['log']) +
              '\n\nRules under ruling R-10 (speed gate only):\n\n' + '\n'.join('- ' + x for x in r10['log']) + '\n')
        (OUT / 'r2-table-M2.md').write_text(md)
        print(md)
        sys.exit(0)
    rows = [row(*k) for k in CORE]
    record = [row(*k) for k in RECORD if (OUT / f'code/{label(*k)}').exists() or (OUT / f'speed/{label(*k)}').exists()]
    rules = apply_rules(rows)
    (OUT / 'r2-table.json').write_text(json.dumps({'rows': rows, 'record_only': record, 'rules': rules}, indent=2, default=str) + '\n')
    md = table(rows) + ('\nFor the record (ruling R-4, not in the rules):\n\n' + table(record) if record else '') + '\n' + '\n'.join('- ' + x for x in rules['log']) + '\n'
    (OUT / 'r2-table.md').write_text(md)
    print(md)
