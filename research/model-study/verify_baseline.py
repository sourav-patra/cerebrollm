"""Check the completed phi4 baseline and container execution receipts."""
import hashlib
import json
from pathlib import Path
from study import OUT,load,save,extract_code

folder=OUT/'code/phi4-default'
problems=load('humaneval-40.json')
rows=[json.loads((folder/f'result_{i}.json').read_text()) for i in range(40)]
assert not list(folder.glob('error_*.json'))
assert len(rows)==40
for i,(row,p) in enumerate(zip(rows,problems)):
    assert row['task_id']==p['task_id'] and row['index']==i
    request=row['request']
    assert request['model']=='phi4'
    assert request['options']['temperature']==0 and request['options']['num_ctx']==16384
    assert request['messages'][0]['content'].endswith(p['prompt'])
    assert row['response']['done']
    expected=extract_code(row['response']['message'].get('content',''),p['entry_point'])+'\n'+p['test']+'\ncheck('+p['entry_point']+')\n'
    assert (folder/f'test_{i}.py').read_text()==expected
    cmd=row['test']['command']
    assert cmd[cmd.index('--network')+1]=='none'
    assert cmd[cmd.index('-v')+1]==str(folder)+':/w:ro'
    assert 'python:3.13-slim' in cmd
    assert row['test']['exit'] in [0,1] or row['test']['timeout']
    assert row['passed']==(row['test']['exit']==0)
tool_rows=[load(f'tools/phi4-default/{i:02d}.json') for i in range(12)]
assert [r['id'] for r in tool_rows]==list(range(1,13))
assert all(r['status']==400 and 'does not support tools' in r['error'] and not r['passed'] for r in tool_rows)
passes=sum(r['passed'] for r in rows)
result={'status':'PASS','code_passed':passes,'code_total':40,'pass_at_1_percent':passes/40*100,
        'tools_score':0,'tools_total':12,'combined_percent':0.5*passes/40*100,
        'checks':['40 distinct one-attempt model responses','temperature zero, context 16384','saved code matches actual model reply plus held-out tests',
                  '40 no-network/read-only container commands','all container exits captured','12 unsupported native-tool responses preserved'],
        'raw_result_hashes':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(folder.glob('result_*.json'))},
        'limit':'Speed eligibility is pending; this run record establishes baseline code/tool results only.'}
save('verified-baseline.json',result)
print('PASS: phi4 code',passes,'/ 40 =',result['pass_at_1_percent'],'%; tools 0 / 12; combined',result['combined_percent'])
