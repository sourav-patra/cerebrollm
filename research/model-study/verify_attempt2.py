"""Check attempt-2 measurements, preserved baseline, boundaries and handoff."""
import argparse
import ast
import hashlib
import json
import os
from pathlib import Path

from study import OUT, load, save, tag, api
from report_attempt2 import VARIANTS, EMBED, AGENT, FAST

p=argparse.ArgumentParser()
p.add_argument('--partial',action='store_true')
args=p.parse_args()
receipt=load('run-receipt.json')
assert receipt['attempt']==2
assert receipt['chosen']=={'R1':None,'R2a':None,'R2b':None}
inputs=load('verified-inputs.json')
for name,digest in inputs['hashes'].items():
    assert hashlib.sha256((OUT/name).read_bytes()).hexdigest()==digest,name
baseline=load('verified-baseline.json')
for name,digest in baseline['raw_result_hashes'].items():
    assert hashlib.sha256((OUT/'code/phi4-default'/name).read_bytes()).hexdigest()==digest,name
assert not list((OUT/'speed').glob('**/*.json')), 'Attempt 2 must defer speed'
boundary=load('boundaries-after.json')
assert boundary['source_hashes_match_preflight'] and boundary['live_table_matches_before']
assert boundary['rows']==30533
counts=[]
recorded={(r['model'],r['mode']):r for r in receipt['progress']}
for model,mode in VARIANTS:
    folder=OUT/'code'/tag(model,mode)
    results=[json.loads(p.read_text()) for p in folder.glob('result_*.json')]
    errors=[json.loads(p.read_text()) for p in folder.glob('error_*.json')]
    tools=[json.loads(p.read_text()) for p in (OUT/'tools'/tag(model,mode)).glob('*.json')]
    ids=[r['index'] for r in results+errors]
    assert len(ids)==len(set(ids))
    if not args.partial: assert len(results)+len(errors)==40 and len(tools)==12,(model,mode)
    for r in results:
        cmd=r['test']['command']
        assert cmd[cmd.index('--network')+1]=='none'
        assert cmd[cmd.index('-v')+1].endswith(':/w:ro')
        assert r['passed']==(r['test']['exit']==0)
        assert r['request']['options']['temperature']==0
        if model!='phi4': assert len(r['load_average_before'])==3
    for r in tools:
        if model!='phi4': assert len(r['load_average_before'])==3
        if 'response' in r:
            calls=r['response']['message'].get('tool_calls',[])
            passed=len(calls)==1 and calls[0].get('function',{}).get('name')==r['expected']['name'] and calls[0]['function'].get('arguments')==r['expected']['arguments']
            assert r['passed']==passed
        else: assert not r['passed']
    report=recorded[(model,mode)]
    assert report['code_passed']==sum(r['passed'] for r in results)
    assert report['tools_passed']==sum(r['passed'] for r in tools)
    assert report['code_completed']==len(results) and report['code_errors']==len(errors)
    assert report['tools_completed']==len(tools)
    if len(results)+len(errors)==40:
        assert report['code_pass_percent']==sum(r['passed'] for r in results)*2.5
    if len(results)+len(errors)==40 and len(tools)==12:
        combined=50*sum(r['passed'] for r in results)/40+50*sum(r['passed'] for r in tools)/12
        assert abs(report['combined']-combined)<1e-10
    counts.append({'model':model,'mode':mode,'code':len(results),'errors':len(errors),'tools':len(tools)})
selection=load('selection-set.json')['items']
recorded_r1={r['model']:r for r in receipt['retrieval']}
for model,table in EMBED:
    summary=OUT/f'index/{table}/summary.json'
    if not args.partial: assert summary.exists(),model
    if summary.exists(): assert json.loads(summary.read_text())['chunks']==5091
    for mode in ['vector','hybrid']:
        for k in [5,10]:
            paths=list((OUT/f'retrieval/{table}/{mode}-{k}').glob('*.json'))
            if not args.partial: assert len(paths)==150,(model,mode,k)
            for path in paths:
                r=json.loads(path.read_text())
                i=int(path.stem)
                assert r['expected_ids']==[selection[i]['node_id']]
                assert r['query']==selection[i]['question']
                assert len(r['load_average_before'])==3
                positions=[j+1 for j,nid in enumerate(r['retrieved_ids']) if nid==selection[i]['node_id']]
                hit=float(bool(positions))
                mrr=1/min(positions) if positions else 0
                assert r['metric_dict']['hit_rate']['score']==hit
                assert abs(r['metric_dict']['mrr']['score']-mrr)<1e-10
            if len(paths)==150:
                values=[json.loads(path.read_text()) for path in paths]
                field='hit_at_5' if k==5 else 'hit_at_10'
                assert abs(recorded_r1[model]['modes'][mode][field]-sum(r['metric_dict']['hit_rate']['score'] for r in values)/150)<1e-10
                if k==10:
                    assert abs(recorded_r1[model]['modes'][mode]['mrr_at_10']-sum(r['metric_dict']['mrr']['score'] for r in values)/150)<1e-10
for path in OUT.glob('*.py'):
    ast.parse(path.read_text(),filename=str(path))
for name in ['RESULTS.md','speed-notes.md']:
    data=(OUT/name).read_text()
    assert data.rstrip().splitlines()[-1].startswith('Skipped or not checked:')
    assert len(data.encode())<24000
assert '```text\n'+load('protocol.json')['qwen_query_prefix']+'\n```' in (OUT/'RESULTS.md').read_text()
commands=[json.loads(p.read_text()) for p in (OUT/'attempt-2-commands').glob('*.json')]
assert all(r['seconds']<900 for r in commands)
assert receipt['free_bytes']>=8000000000
assert os.statvfs(OUT).f_bavail*os.statvfs(OUT).f_frsize>=8000000000
if not args.partial:
    assert receipt['quality_complete'] and receipt['r1_complete']
    assert receipt['provisional_R1']
    assert len(receipt['finalists']['R2a'])==2
    eligible=[r for r in receipt['retrieval'] if r['index']['within_60_minutes']]
    winner=max(eligible,key=lambda r:(r['modes']['hybrid']['hit_at_5'],r['modes']['hybrid']['mrr_at_10'],r['index']['chunks_per_minute']))
    assert receipt['provisional_R1']==winner['model']
    agent=sorted([recorded[k] for k in AGENT],key=lambda r:(r['combined'],r['code_pass_percent']),reverse=True)[:2]
    assert [(r['model'],r['mode']) for r in receipt['finalists']['R2a']]==[(r['model'],r['mode']) for r in agent]
    best=max(r['code_pass_percent'] for r in receipt['progress'])
    assert receipt['best_code_pass_percent']==best
    fast={k for k in FAST if recorded[k]['code_pass_percent']>=best-10}
    assert {(r['model'],r['mode']) for r in receipt['finalists']['R2b']}==fast
    names={m['name'] for m in receipt['models_on_disk']['models']}
    assert 'bge-m3:latest' in names and 'gpt-oss:120b-cloud' in names
    assert not names.intersection({'phi4:latest','qwen3:14b','qwen3:8b','gpt-oss:20b','devstral:24b'})
    actual=api('tags')['models']
    assert {m['name']:m['digest'] for m in actual}=={m['name']:m['digest'] for m in receipt['models_on_disk']['models']}
result={'status':'PASS','scope':'partial progress' if args.partial else 'all correctness and speed handoff; speed remains deferred',
        'counts':counts,'failed_commands':[r for r in commands if r['exit']!=0],
        'checks':['fixed inputs and phi4 raw hashes unchanged','new case loads recorded','code sandbox and tool scores checked',
                  'cerebrollm sources and full live table unchanged','Python syntax and document checks','commands under 15 minutes'],
        'hashes':{n:hashlib.sha256((OUT/n).read_bytes()).hexdigest() for n in ['RESULTS.md','speed-notes.md','run-receipt.json']}}
save('attempt-2-verification.json',result)
print(json.dumps({'status':result['status'],'scope':result['scope'],'counts':counts}))
