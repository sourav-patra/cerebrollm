"""Render the attempt-2 run record and speed handoff from preserved measurements."""
import datetime
import json
import os
from pathlib import Path

from study import OUT, api, load, save, tag
from studyconfig import VENV_PYTHON

VARIANTS = [('phi4','default'),('devstral:24b','default'),('gpt-oss:20b','medium'),
            ('gpt-oss:20b','low'),('qwen3:14b','thinking-on'),('qwen3:14b','thinking-off'),
            ('qwen3:8b','thinking-off')]
AGENT = VARIANTS[:3]+[('qwen3:14b','thinking-on')]
FAST = [('phi4','default'),('gpt-oss:20b','low'),('qwen3:14b','thinking-off'),('qwen3:8b','thinking-off')]
EMBED = [('bge-m3','study_d_bge_m3'),('qwen3-embedding:0.6b','study_d_qwen_06b'),
         ('qwen3-embedding:4b','study_d_qwen_4b')]
PYTHON = VENV_PYTHON


def rows(folder, pattern='*.json'):
    return [json.loads(p.read_text()) for p in sorted((OUT/folder).glob(pattern))]


def main():
    progress=[]
    for model,mode in VARIANTS:
        label=tag(model,mode)
        code=rows('code/'+label,'result_*.json')
        errors=rows('code/'+label,'error_*.json')
        tools=rows('tools/'+label)
        complete=len(code)+len(errors)==40 and len(tools)==12
        n=sum(r['passed'] for r in code)
        t=sum(r['passed'] for r in tools)
        loads=[r['load_average_before'][0] for r in code+errors+tools if 'load_average_before' in r]
        progress.append(dict(model=model,mode=mode,code_completed=len(code),code_errors=len(errors),
            code_passed=n,tools_completed=len(tools),tools_passed=t,quality_complete=complete,
            code_pass_percent=n*2.5 if len(code)+len(errors)==40 else None,
            combined=0.5*n*2.5+0.5*t/12*100 if complete else None,
            one_minute_load_range=[min(loads),max(loads)] if loads else None,valid_speed_runs=0))
    by_key={(r['model'],r['mode']):r for r in progress}
    quality_complete=all(r['quality_complete'] for r in progress)
    retrieval=[]
    for model,table in EMBED:
        summary_path=OUT/f'index/{table}/summary.json'
        summary=json.loads(summary_path.read_text()) if summary_path.exists() else None
        batches=rows(f'index/{table}','[0-9]*.json')
        finished={b['start'] for b in batches}
        index_progress={'chunks':sum(b['chunks'] for b in batches),
                        'duration_seconds':sum(b['duration_seconds'] for b in batches),
                        'next_start':next((i for i in range(0,5091,16) if i not in finished),5091)}
        r=dict(model=model,table=table,index=summary,index_progress=index_progress,modes={})
        for mode in ['vector','hybrid']:
            five=rows(f'retrieval/{table}/{mode}-5')
            ten=rows(f'retrieval/{table}/{mode}-10')
            r['modes'][mode]=dict(completed_5=len(five),completed_10=len(ten),
                hit_at_5=sum(x['metric_dict']['hit_rate']['score'] for x in five)/150 if len(five)==150 else None,
                hit_at_10=sum(x['metric_dict']['hit_rate']['score'] for x in ten)/150 if len(ten)==150 else None,
                mrr_at_10=sum(x['metric_dict']['mrr']['score'] for x in ten)/150 if len(ten)==150 else None)
        retrieval.append(r)
    r1_complete=all(r['index'] and all(v['completed_5']==150 and v['completed_10']==150 for v in r['modes'].values()) for r in retrieval)
    def rank_r1(mode):
        eligible=[r for r in retrieval if r['index'] and r['index']['within_60_minutes'] and r['modes'][mode]['hit_at_5'] is not None]
        return sorted(eligible,key=lambda r:(r['modes'][mode]['hit_at_5'],r['modes'][mode]['mrr_at_10'],r['index']['chunks_per_minute']),reverse=True)
    r1=rank_r1('hybrid')[0]['model'] if r1_complete and rank_r1('hybrid') else None
    finalists_agent=sorted([by_key[k] for k in AGENT],key=lambda r: (r['combined'] or -1,r['code_pass_percent'] or -1),reverse=True)[:2] if quality_complete else []
    best_code=max(r['code_pass_percent'] for r in progress) if quality_complete else None
    finalists_fast=[by_key[k] for k in FAST if by_key[k]['code_pass_percent']>=best_code-10] if quality_complete else []
    inventory=api('tags')
    v=os.statvfs(OUT)
    receipt=dict(status='correctness_complete_speed_deferred' if quality_complete and r1_complete else 'correctness_in_progress',
        time=datetime.datetime.now(datetime.timezone.utc).isoformat(),attempt=2,work_order='development step D',
        authority='27 Oct attempt-2 instructions; a routing pick supplied by the orchestrator, not a pick executed by this session',
        execution_identity='Codex primary agent /root; exact runtime model and effort are not exposed',
        cerebrollm_revision=load('preflight.json')['cerebrollm_revision'],selection_questions=150,
        progress=progress,retrieval=retrieval,r1_complete=r1_complete,quality_complete=quality_complete,
        provisional_R1=r1,chosen={'R1':None,'R2a':None,'R2b':None},
        finalists={'R2a':finalists_agent,'R2b':finalists_fast},best_code_pass_percent=best_code,
        models_on_disk=inventory,free_bytes=v.f_bavail*v.f_frsize,load_average=os.getloadavg(),
        routing=load('protocol.json')['routing'],capture=load('protocol.json')['capture'],
        source_checks=load('boundaries-after.json'),speed_status='Deferred until owner restart and second session tonight; zero speed runs in attempt 2')
    save('run-receipt.json',receipt)
    lines=['Status: '+receipt['status']+'. R2 role winners await speed qualification.','',
        'Updated: '+receipt['time']+'. Authority: development step D, attempt-2 instructions.','',
        '## Verified inputs','',
        '- Reused all 150 questions, the 5,091-chunk snapshot, fixed HumanEval subset and 12 scenarios. `verified-inputs.json` records their hashes. No eval-set item was opened.',
        '- Phi4 generated the questions with the LlamaIndex 0.10.68 helper exported as `generate_question_context_pairs`, an alias of `generate_qa_embedding_pairs`. The installed core 0.14.25 removed it. The isolated historical helper and verified wheel hashes remain in `sources/`; the runner uses installed core types.',
        '- Reused phi4: 33/40 code passes, 0/12 tool calls, combined 41.25/100. `verified-baseline.json` records the raw hashes. Phi4 correctness was not rerun.',
        '- HumanEval uses revision `b9453e8f1865df0a0057a1383767caa400acfbcf`, numeric task-ID sorting and seed 27. Temperature 0, one attempt, context 16,384. Each generated test runs only in a no-network Docker container with a read-only mount and 20-second timeout.',
        '- New correctness records include before/after load averages. The old phi4 records have no per-case load readings; none were reconstructed. `attempt-2-commands/` retains full logs, exits and command durations.','',
        '## Retrieval embedding','',
        '| Model | Chunks | Chunks/min | Index minutes | Vector hit@5 / hit@10 / MRR@10 | Hybrid hit@5 / hit@10 / MRR@10 | Index residency |',
        '|---|---:|---:|---:|---|---|---|']
    for r in retrieval:
        s=r['index']
        vals=[]
        for mode in ['vector','hybrid']:
            m=r['modes'][mode]
            vals.append(' / '.join(f'{m[k]:.6f}' if m[k] is not None else 'pending' for k in ['hit_at_5','hit_at_10','mrr_at_10']))
        residency=next((line.strip() for line in s['memory']['stdout'].splitlines()[1:]
                        if line.split() and line.split()[0] in {r['model'],r['model']+':latest'}),'not resident') if s else 'pending'
        partial=r['index_progress']
        partial_cells=f'{partial["chunks"]}/5091 | pending | {partial["duration_seconds"]/60:.3f} so far'
        lines.append(f'| `{r["model"]}` | '+(f'{s["chunks"]} | {s["chunks_per_minute"]:.2f} | {s["duration_seconds"]/60:.3f}' if s else partial_cells)+f' | {vals[0]} | {vals[1]} | `{residency}` |')
    lines += ['',f'Provisional R1 choice: `{r1}`.' if r1 else 'Provisional R1 choice: pending complete indexing and evaluation.',
        'The fixed primary comparison uses hybrid hit@5, then MRR@10, then chunks/min; indexing must finish in under 60 minutes. Vector results remain visible. Index time sums embedding-and-insert batch times and excludes operator pauses. Raw evaluator results and batch load readings live in `retrieval/` and `index/`.',
        'The snapshot has 4,249 distinct texts across 5,091 node IDs. Of the 150 sampled chunks, 51 have identical text under another ID. Cerebrollm deduplicates returned text, while the evaluator requires the sampled ID. An identical-text result under another ID receives no credit. The fixed scoring rule is unchanged; `retrieval-identity-check.json` records this limitation.',
        'Qwen queries use this exact prefix:', '', '```text', load('protocol.json')['qwen_query_prefix'], '```', '',
        'Documents have no prefix. Copied TOML files change only table and model. Each vector has 1,024 dimensions. R1 indexing residency snapshots are in each index summary; R2 memory qualification is deferred.','',
        '## Agentic coding','',
        '| Model / mode | Code pass / attempted | Code pass@1 | Tool pass / completed | Combined /100 | One-minute load range |',
        '|---|---:|---:|---:|---:|---|']
    def quality_row(r):
        return f'| `{r["model"]}` / {r["mode"]} | {r["code_passed"]}/{r["code_completed"]+r["code_errors"]} | '+(f'{r["code_pass_percent"]:.1f}%' if r['code_pass_percent'] is not None else 'pending')+f' | {r["tools_passed"]}/{r["tools_completed"]} | '+(f'{r["combined"]:.3f}' if r['combined'] is not None else 'pending')+' | '+(f'{r["one_minute_load_range"][0]:.3f} to {r["one_minute_load_range"][1]:.3f}' if r['one_minute_load_range'] else 'not recorded in attempt 1')+' |'
    lines += [quality_row(by_key[k]) for k in AGENT]
    lines += ['', 'Combined = 0.5 x code percentage + 0.5 x tool percentage. Native tool failures score zero; text is never converted into a tool call. Errors consume an attempt and remain in raw evidence. R2a requires at least 15 generation tokens/s at context 16,384 with 100% GPU residency. No candidate is speed-qualified.',
        'R2a finalists: '+(', '.join(f'`{r["model"]}` / {r["mode"]} ({r["combined"]:.3f})' for r in finalists_agent) or 'pending all correctness results')+'.','',
        '## Fast output','',
        '| Model / mode | Code pass / attempted | Code pass@1 | Tool pass / completed | Combined /100 | One-minute load range |',
        '|---|---:|---:|---:|---:|---|']
    lines += [quality_row(by_key[k]) for k in FAST]
    lines += ['', 'R2b chooses the highest generation tokens/s among original R2b candidates within 10 percentage points of the best measured R2 code score across modes. GPT-OSS uses low reasoning for R2b and medium for R2a. Qwen uses thinking off for R2b and on for R2a.',
        f'Best code pass@1: {best_code}%. R2b finalists: '+(', '.join(f'`{r["model"]}` / {r["mode"]}' for r in finalists_fast) or 'pending all correctness results')+'.','',
        '## Speed measurements','',
        'All R2 prompt/generation rates, time to first token, memory size and CPU/GPU qualification remain pending for tonight after the owner restart. Attempt 2 runs no speed test and never gates correctness on load. The speed notes (not published) contain exact pull and measurement commands. The attempt-1 phi4 gate at load 93.078 remains raw evidence, not a valid measurement.','',
        '## Published scores','',
        '| Candidate | Published result, reported, not checked here | Source |','|---|---|---|']
    for r in load('published-scores.json')['candidates']:
        score=json.dumps(r['score_percent'])
        lines.append(f'| `{r["model"]}` | {r["benchmark"]}: {score}% | [vendor source]({r["url"]}) |')
    lines += ['', 'Published HumanEval and BFCL results measure function coding and tool use respectively; they do not establish repository-agent performance. Published scaffolds and precision differ from this run. Source bodies and receipts from attempt 1 remain in `sources/`.','',
        '## Choice and disk','',
        'Final chosen set: pending speed tests. The provisional embedding choice is recorded above. Sharing a model across roles requires being within 5 points of the best in each; the final set may contain at most four models. The protected live `bge-m3` model stays installed.',
        '', '| Installed model | Bytes | Decimal GB |','|---|---:|---:|']
    lines += [f'| `{m["name"]}` | {m["size"]} | {m["size"]/1e9:.6f} |' for m in inventory['models']]
    lines += ['', f'Free disk: {receipt["free_bytes"]:,} bytes ({receipt["free_bytes"]/1e9:.3f} GB). Floor: 8 GB. `model-actions.jsonl` records before/after inventory, disk and each permitted removal. The cloud entry was never invoked.',
        '', '## Boundaries and continuation','',
        '`boundaries-after.json` verifies all 30,533 live rows including embeddings against `boundaries-before.json`, plus cerebrollm source hashes. Cerebrollm revision: `'+receipt['cerebrollm_revision']+'`. Study tables are separate from `data_chunks`.',
        'The local Codex fallback and local run record continue because no external reporting tool was used (its default log paths lie outside the authorized folder). The attempt-2 instructions cite a routing pick; this controller claims no new pick/outcome. External reporting remains pending because only this folder is writable.',
        'Resume incomplete correctness units from their per-case records. After every R2 variant is complete, remove each study-pulled R2 model and phi4; tonight repull the finalists using the speed notes (not published). The earlier resume brief is superseded by the 27 Oct attempt-2 instructions.',
        '', 'Skipped or not checked: all R2 speed qualification; final role winners; optional practice set; full SWE-bench and production agent behavior; external reporting; `qwen3-coder:30b` and `qwen3:30b` (18.56 GB each, excluded by the brief for disk and default GPU-memory limits).','']
    (OUT/'RESULTS.md').write_text('\n'.join(lines))
    plan=['Run the finalist speed commands after the owner restart, with one-minute load at or below 4.','',
        'Status: draft speed handoff, 2026-10-27. Authority: development step D, 27 Oct attempt-2 instructions. Correctness is reused. Every command stays under 15 minutes. No wait loop is permitted.',
        '',f'R1 provisional choice: {r1 or "pending R1 completion"}. The addendum requires no further R1 speed test beyond the recorded full indexing rate.',
        'The current `report_attempt2.py` summarizes correctness only. Tonight, preserve this run record and extend reporting to consume the saved speed JSON before updating role winners; this writer always leaves R2 qualification pending.',
        '', 'Selection: R2a takes the top two original agentic candidates by combined correctness. R2b includes every original fast-output candidate within 10 points of the best R2 code score. Both role modes require separate measurements. If a combined-score tie crosses second place, this provisional list uses higher code pass@1 first; any unresolved tie is reported.',
        '', '1. Check that correctness is complete in `run-receipt.json`; run one model at a time and preserve the 8 GB floor with `model_control.py`. A high-load refusal ends that invocation. Resume only after a new quiet check; use a new repeat number for an invalid measured result.',
        '2. Execute each pull followed by its listed measurements. The existing exact script is `study.py speed`: it calibrates 8,000/200 actual prompt tokens, warms up, then records streamed first token, first visible content, prompt/generation rates, load and `ollama ps`. Every call uses context 16,384, temperature 0 and seed 27. Preserve raw failures.',
        '3. Accept exactly three valid runs at each prompt length for each listed mode. R2a needs every run at least 15 tokens/s and 100% GPU. Aggregate generation by pooled eval_count/eval_duration. Apply the original role/consolidation rules, inventory at most four models and rerun boundary checks before declaring a winner.','']
    wanted=[]
    for r in finalists_agent+finalists_fast:
        key=(r['model'],r['mode'])
        if key not in wanted: wanted.append(key)
    if not quality_complete:
        plan += ['Finalists are pending. Regenerate this file with `report_attempt2.py` after correctness completes.','']
    for model in dict.fromkeys(m for m,_ in wanted):
        plan += [f'## {model}', '', '```sh', f'rtk proxy {PYTHON} -B {OUT}/model_control.py pull --model {model}']
        for m,mode in wanted:
            if m!=model: continue
            for length in [8000,200]:
                for repeat in range(3):
                    plan.append(f'rtk proxy {PYTHON} -B {OUT}/study.py speed --model {m} --mode {mode} --length {length} --repeat {repeat}')
        plan += ['```','', 'Unload after measurement. Retain/delete weights only when the final comparison and disk floor permit it.','']
    plan += ['Skipped or not checked: speed measurements and final selection have not run; no restart or scheduling action was performed.','']
    (OUT/'speed-notes.md').write_text('\n'.join(plan))
    print(json.dumps({'status':receipt['status'],'R1':r1,'finalists':{k:[(r['model'],r['mode']) for r in v] for k,v in receipt['finalists'].items()},'free_GB':receipt['free_bytes']/1e9}))


if __name__=='__main__':
    main()
