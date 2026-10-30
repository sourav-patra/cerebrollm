"""Render honest partial results and a local continuation run record from on-disk evidence."""
import datetime
import hashlib
import json
import os
from pathlib import Path

from study import OUT,load,save,tag,api


def read_many(folder,pattern='*.json'):
    return [json.loads(p.read_text()) for p in sorted((OUT/folder).glob(pattern))]


def main():
    now=datetime.datetime.now(datetime.timezone.utc).isoformat()
    baseline=load('preflight.json')
    inventory=api('tags')
    stat=os.statvfs(OUT)
    free=stat.f_bavail*stat.f_frsize
    progress=[]
    for model,mode in [('phi4','default'),('devstral:24b','default'),('gpt-oss:20b','medium'),
                       ('gpt-oss:20b','low'),('qwen3:14b','thinking-on'),('qwen3:14b','thinking-off'),
                       ('qwen3:8b','thinking-off')]:
        label=tag(model,mode)
        code=read_many('code/'+label,'result_*.json')
        errors=read_many('code/'+label,'error_*.json')
        tools=read_many('tools/'+label)
        speed=[r for r in read_many('speed/'+label) if 'generation_tps' in r]
        valid=[r for r in speed if r['valid_load']]
        ncode=sum(r['passed'] for r in code)
        ntools=sum(r['passed'] for r in tools)
        complete=len(code)==40 and not errors and len(tools)==12
        progress.append({'model':model,'mode':mode,'code_completed':len(code),'code_passed':ncode,'code_errors':len(errors),
                         'tools_completed':len(tools),'tools_passed':ntools,'speed_runs':speed,
                         'valid_speed_runs':len(valid),'quality_complete':complete,
                         'code_pass_percent':ncode/40*100 if len(code)==40 else None,
                         'combined':0.5*ncode/40*100+0.5*ntools/12*100 if complete else None})
    selection=load('selection-set.json') if (OUT/'selection-set.json').exists() else None
    deferred=read_many('speed-deferred/phi4-default')
    blocked=bool(deferred) and not any(r['valid_speed_runs'] for r in progress)
    receipt={'status':'blocked_on_host_load' if blocked else 'pending','time':now,'execution_identity':'Codex primary agent /root; exact runtime model and effort are not exposed',
             'work_order':'development step D','cerebrollm_revision':baseline['cerebrollm_revision'],
             'selection_questions':len(selection['items']) if selection else len(list((OUT/'selection').glob('*.json'))),
             'progress':progress,'models_on_disk':inventory,'free_bytes':free,'load_average':os.getloadavg(),
             'routing':'Local fallback. No external reporting tool was used; its default log and state paths lie outside this folder. No pick or outcome invented.',
             'capture':'Local run record only. No external capture, because only this folder is writable.',
             'chosen':{'R1':None,'R2a':None,'R2b':None},
             'speed_gate':deferred[-1] if deferred else None,
             'source_checks':load('boundaries-after.json') if (OUT/'boundaries-after.json').exists() else load('boundaries-before.json')}
    save('run-receipt.json',receipt)
    lines=[
        'Status: blocked on host load. No role winner is established until the required measurements pass.' if blocked else 'Status: pending. No role winner is established until the required measurements pass.',
        '',f'Updated: {now}. Authority: development step D.',
        '', '## Verified inputs', '',
        f'- The read-only index snapshot contains {baseline["default_chunks"]:,} default-search chunks. Seed 27 selects 150 distinct chunks in `selection-chunks.json`.',
        f'- Phi4 produced {receipt["selection_questions"]} questions with LlamaIndex `generate_question_context_pairs`, the exact alias for `generate_qa_embedding_pairs` in core 0.10.68. The installed core 0.14.25 removed that helper; the historical source is isolated in `sources/`, verified against its wheel hash, and uses the installed core types.',
        '- `verified-inputs.json` records the seed, node-ID/context, filename/path, sentence-copy, tool-schema and HumanEval checks. Manual filename review rejected and rewrote question 0. Rejected drafts remain in `selection-rejected.jsonl` and `selection-raw.jsonl`.',
        '- `humaneval-40.json` contains 40 distinct problems sampled with seed 27 after numeric task-ID sorting from pinned HumanEval revision `b9453e8f1865df0a0057a1383767caa400acfbcf`. `sources/LICENSE` contains the MIT licence. Each model gets temperature 0 and one attempt.',
        '- `sandbox-check.json` records a passing canonical solution and a detected negative control, both in `python:3.13-slim` with `--network none`. Generated code runs only in a container with a read-only model-specific mount and a 20-second deadline.',
        '', '## Retrieval embedding', '',
        '| Model | Indexed chunks | Chunks/min | Index minutes | Vector hit@5 / hit@10 / MRR@10 | Hybrid hit@5 / hit@10 / MRR@10 | Ollama memory | Result |',
        '|---|---:|---:|---:|---|---|---|---|',
    ]
    for model,table in [('bge-m3','study_d_bge_m3'),('qwen3-embedding:0.6b','study_d_qwen_06b'),('qwen3-embedding:4b','study_d_qwen_4b')]:
        path=OUT/'index'/table/'summary.json'
        if not path.exists():
            lines.append(f'| `{model}` | not measured | not measured | not measured | not measured | not measured | not measured | Pending after phi4 R2 baseline |')
        else:
            summary=json.loads(path.read_text())
            values=[]
            for mode in ['vector','hybrid']:
                five=read_many(f'retrieval/{table}/{mode}-5')
                ten=read_many(f'retrieval/{table}/{mode}-10')
                values.append(' / '.join(f'{sum(r["metric_dict"][key]["score"] for r in rows)/150:.4f}' if len(rows)==150 else f'pending ({len(rows)}/150)' for key,rows in [('hit_rate',five),('hit_rate',ten),('mrr',ten)]))
            lines.append(f'| `{model}` | {summary["chunks"]} | {summary["chunks_per_minute"]:.2f} | {summary["duration_seconds"]/60:.2f} | {values[0]} | {values[1]} | see raw `index/{table}/summary.json` | selection pending |')
    lines += ['', 'Rule: highest selection-set hit@5, then MRR, then chunks/min, with indexing under 60 minutes. Both vector and cerebrollm hybrid are reported. The premeasurement protocol uses hybrid, the production default, for the primary choice; a different vector winner must remain visible.',
              '', 'The Qwen query prefix is:', '', '```text',
              'Instruct: Given a web search query, retrieve relevant passages that answer the query', 'Query:', '```', '',
              'Documents receive no prefix. The copied TOML files change only table and model. The adapter requests 1,024 dimensions to match the unchanged cerebrollm configuration and asserts the returned dimension. No live table is cleared or indexed.',
              '', '## Agentic coding', '',
              '| Model / mode | Code passes / completed / 40 | Code pass@1 | Tool calls / completed / 12 | Combined / 100 | Valid speed runs / 6 | 16,384 context, 100% GPU, minimum 15 tok/s |',
              '|---|---|---:|---|---:|---:|---|']
    for r in progress:
        if (r['model'],r['mode']) not in [('phi4','default'),('devstral:24b','default'),('gpt-oss:20b','medium'),('qwen3:14b','thinking-on')]: continue
        lines.append(f'| `{r["model"]}` / {r["mode"]} | {r["code_passed"]} / {r["code_completed"]} / 40 | '+(f'{r["code_pass_percent"]:.1f}%' if r['code_pass_percent'] is not None else 'pending')+f' | {r["tools_passed"]} / {r["tools_completed"]} / 12 | '+(f'{r["combined"]:.2f}' if r['combined'] is not None else 'pending')+f' | {r["valid_speed_runs"]} / 6 | pending |')
    lines += ['', 'Rule: maximize 0.5 x code pass@1 + 0.5 x tool-call percentage, subject to every speed/GPU requirement. Unsupported native tools score zero; tool-call text is never converted to a synthetic call. HTTP failures remain in raw JSON.',
              '', ('Observed during the phi4 baseline: `'+load('phi4-baseline-memory.json')['ps']['stdout'].strip().replace('\n','; ')+'`. This snapshot proves residency at context 16,384; it supplies no valid speed score.') if (OUT/'phi4-baseline-memory.json').exists() else 'Baseline memory observation is pending.',
              '', '## Fast output', '',
              '| Model / mode | Code passes / completed / 40 | Code pass@1 | Valid speed runs / 6 | Generation tok/s | Result |',
              '|---|---|---:|---:|---:|---|']
    for r in progress:
        if r['mode'] not in ['default','low','thinking-off'] or r['model']=='devstral:24b':continue
        lines.append(f'| `{r["model"]}` / {r["mode"]} | {r["code_passed"]} / {r["code_completed"]} / 40 | '+(f'{r["code_pass_percent"]:.1f}%' if r['code_pass_percent'] is not None else 'pending')+f' | {r["valid_speed_runs"]} / 6 | not measured | pending |')
    lines += ['', 'Rule: maximize generation tokens per second among models within 10 percentage points of the best R2 code pass@1. GPT-OSS uses low reasoning for fast output and medium for agentic coding. Qwen uses thinking off for fast output and on for agentic coding.',
              '', '## Speed measurements', '',
              '| Model / mode | Prompt tokens | Run | One-minute load | Prompt tok/s | Generation tok/s | First token seconds | First visible content seconds | Memory / CPU-GPU split | Valid |',
              '|---|---:|---:|---:|---:|---:|---:|---:|---|---|']
    speed_count=0
    for r in progress:
        for s in r['speed_runs']:
            speed_count+=1
            lines.append(f'| `{r["model"]}` / {r["mode"]} | {s["length"]} | {s["repeat"]} | {s["load_average_before"][0]:.3f} | {s["prompt_tps"]:.3f} | {s["generation_tps"]:.3f} | {s["ttft_seconds"]} | {s["first_visible_content_seconds"]} | `{s["ps_after"]["stdout"].strip().replace(chr(10),"; ")}` | {s["valid_load"]} |')
    if not speed_count: lines.append('| None yet | not measured | not measured | not measured | not measured | not measured | not measured | not measured | not measured | pending |')
    if deferred:
        lines += ['', f'The speed gate deferred phi4 before inference at one-minute load {deferred[-1]["load_average"][0]:.3f}, above 4. `speed-deferred.jsonl` preserves gate attempts. `quiet-check-1.json` records load 66.567 after phi4 was unloaded, with no resident Ollama model. No high-load speed measurement is presented as valid.']
    lines += ['', f'The latest host load snapshot is {receipt["load_average"][0]:.3f} / {receipt["load_average"][1]:.3f} / {receipt["load_average"][2]:.3f}. The speed limit is a one-minute load at or below 4. Calibration, warm-up and invalid runs cannot qualify a model. Raw stream events record both thinking-token latency and visible-output latency. Each accepted prompt must measure exactly 8,000 or 200 tokens under that model tokenizer.',
              '', '## Published scores', '', '| Candidate | Published result | Source |', '|---|---|---|']
    for r in load('published-scores.json')['candidates']:
        score='; '.join(f'{k}: {v}%' for k,v in r['score_percent'].items()) if isinstance(r['score_percent'],dict) else str(r['score_percent'])+'%'
        lines.append(f'| `{r["model"]}` | {r["benchmark"]}: {score}; reported, not checked here | [vendor source]({r["url"]}) |')
    lines += ['', 'Phi4 has no vendor agentic-coding score in the inspected Microsoft card. Its 82.6% HumanEval result measures single-function coding. BFCL measures tool use; the Qwen scores do not establish repository patch-solving ability. Different published scaffolds and precision prevent direct comparison with this local run.',
              '', '## Choice and disk', '',
              'Chosen set: pending. Retrieval, agentic coding and fast output have no established winner. One model may fill two roles only within 5 points of the best in each. The final set must contain at most four models, including the embedding model. `bge-m3` remains protected even if another embedder wins.',
              '', '| Installed model | Exact size bytes | Decimal GB | Action |', '|---|---:|---:|---|']
    for m in inventory['models']:
        lines.append(f'| `{m["name"]}` | {m["size"]} | {m["size"]/1e9:.6f} | '+('Protected live embedder' if m['name'].startswith('bge-m3') else 'Protected cloud entry, never invoked' if 'cloud' in m['name'] else 'Retained until required phase permits removal')+' |')
    lines += ['', f'Free disk at this report: {free:,} bytes, {free/1e9:.3f} GB, {free/2**30:.3f} GiB. Required floor: 8,000,000,000 bytes. `model-actions.jsonl` will record each pull/removal with `df -h` and before/after inventories. The successful Docker pull used 718.347 seconds; its digest and complete output are in `docker-pull.json`.',
              '', '## Not tested and not measured', '',
              '- `qwen3-coder:30b` and `qwen3:30b`: excluded by the brief. Each is 18.56 GB; the brief states that the others in place exceed the disk allowance and default GPU memory limit. Neither was pulled or called.',
              '- The optional 10-item practice set and all other eval-set contents were not opened.',
              '- R1 indexing and retrieval scores, candidate pulls/removals, and later R2 tests remain pending while the fixed preceding phase is incomplete.',
              '- A valid speed comparison requires three accepted runs for each of the two prompt lengths after warm-up. High-load results require reruns and supply no winner.',
              '- Full SWE-bench, repository-agent integration and production agent behavior are not tested by this 40-problem/12-call study.',
              '', '## Local run record and continuation', '',
              '`run-receipt.json` names the actual controller, exact source revision, current counts, disk, load and local capture limitation. `boundaries-before.json` hashes all live table contents, including embeddings, before any study table. `boundaries-after.json`, when present, must match it and the cerebrollm source hashes.',
              '', 'No external reporting tool was used: its default state and log paths lie outside the authorized folder. The allowed local fallback is this Codex session; no external record is claimed.',
              '', '`execution-notes.json` preserves startup failures and recoveries, including a failed patch match, the GitHub rate limit, the helper alias lookup and question rewrites. The published PDF table was read as extracted text; visual rendering was unavailable and is not claimed.',
              '', 'Resume from the first incomplete phi4 quality test, then finish valid phi4 speed tests. Only then pull the two Qwen embedders and run R1, remove phi4, and pull/test/remove R2 candidates while preserving leaders and the disk floor. Each script command has an internal 840-second alarm; never wait on a file.',
              '', 'Skipped or not checked: all pending measurements listed above, optional practice questions, production activation, and external reporting.', '']
    (OUT/'RESULTS.md').write_text('\n'.join(lines))
    print('Wrote RESULTS.md and run-receipt.json; study status remains pending; free GB',round(free/1e9,3))


if __name__=='__main__': main()
