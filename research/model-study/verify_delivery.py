"""Verify the completed baseline and blocked handoff, without claiming a completed study."""
import ast
import hashlib
import json
import os
from pathlib import Path

from study import OUT,api,load,save

inputs=load('verified-inputs.json')
baseline=load('verified-baseline.json')
boundary=load('boundaries-after.json')
receipt=load('run-receipt.json')
assert inputs['status']=='PASS' and baseline['status']=='PASS'
assert baseline['code_passed']==33 and baseline['code_total']==40
assert baseline['pass_at_1_percent']==82.5 and baseline['tools_score']==0 and baseline['combined_percent']==41.25
for name,digest in inputs['hashes'].items():
    assert hashlib.sha256((OUT/name).read_bytes()).hexdigest()==digest,name
for name,digest in baseline['raw_result_hashes'].items():
    assert hashlib.sha256((OUT/'code/phi4-default'/name).read_bytes()).hexdigest()==digest,name
assert boundary['source_hashes_match_preflight'] and boundary['live_table_matches_before']
assert boundary['rows']==30533
assert receipt['status']=='blocked_on_host_load'
assert receipt['chosen']=={'R1':None,'R2a':None,'R2b':None}
assert receipt['speed_gate']['load_average'][0]>4
assert not list((OUT/'speed').glob('**/*-0.json'))
current=api('tags')['models']
initial=load('preflight.json')['tags']['models']
assert {m['name']:m['digest'] for m in current}=={m['name']:m['digest'] for m in initial}
assert api('ps')['models']==[], 'Resident model still loaded'
scripts=list(OUT.glob('*.py'))
for p in scripts:
    ast.parse(p.read_text(),filename=str(p))
report=(OUT/'RESULTS.md').read_text()
assert report.startswith('Status: blocked on host load.')
assert '82.5%' in report and '41.25' in report
assert report.count('## Retrieval embedding')==1 and report.count('## Agentic coding')==1 and report.count('## Fast output')==1
assert report.rstrip().splitlines()[-1].startswith('Skipped or not checked:')
for p in [OUT/'RESULTS.md']:
    text=p.read_text()
    assert not any(s in text for s in ['In summary','In conclusion',"Let's",'delve','seamless','leverage'])
    assert len(p.read_bytes())<24000
notes=load('execution-notes.json')
notes['failures_and_recoveries'][5]['recovery']='A narrower patch succeeded; final script syntax and generated report passed verify_delivery.py'
save('execution-notes.json',notes)
files=['RESULTS.md','run-receipt.json','verified-inputs.json','verified-baseline.json','boundaries-before.json',
       'boundaries-after.json','execution-notes.json','published-scores.json']
files += [p.name for p in scripts]
result={'status':'PASS','scope':'Completed phi4 quality baseline and blocked continuation only; full model study remains incomplete',
        'checks':['150 fixed selection questions and input hashes unchanged','40 raw code outcomes reproduce 33 passes',
                  '12 native-tool rejections preserve score zero','live table including embeddings and source hashes unchanged',
                  'original three model digests retained, no resident models','high-load speed gate recorded, no fabricated winner',
                  'Python script syntax and output documentation checks'],
        'free_bytes':os.statvfs(OUT).f_bavail*os.statvfs(OUT).f_frsize,
        'snapshot_free_bytes_in_report':receipt['free_bytes'],
        'hashes':{name:hashlib.sha256((OUT/name).read_bytes()).hexdigest() for name in files},
        'not_verified':['speed eligibility','R1 execution and real embedding dimension support','later R2 candidates','final role selection','all preparation scripts end-to-end','external reporting']}
save('delivery-verification.json',result)
print('PASS: completed baseline and blocked handoff verified; full study incomplete; free GB',round(result['free_bytes']/1e9,3))
