"""Verify the required container with one canonical solution and one deliberate failure."""
import json
from pathlib import Path
import signal
import subprocess
import time
from study import OUT,load,save
from studyconfig import DOCKER, hostpath

signal.signal(signal.SIGALRM,lambda *_: (_ for _ in ()).throw(TimeoutError('120-second command limit')))
signal.alarm(120)
folder=OUT/'sandbox-check'
folder.mkdir(exist_ok=True)
p=load('humaneval-40.json')[0]
cases={'positive':p['prompt']+p['canonical_solution']+'\n'+p['test']+'\ncheck('+p['entry_point']+')\n',
       'negative':'raise RuntimeError("deliberate negative control")\n'}
results=[]
for name,body in cases.items():
    (folder/(name+'.py')).write_text(body)
    cmd=[DOCKER,'run','--rm','--network','none','-v',hostpath(folder)+':/w:ro','python:3.13-slim','python','/w/'+name+'.py']
    started=time.monotonic()
    r=subprocess.run(cmd,text=True,capture_output=True,timeout=20)
    results.append({'name':name,'command':cmd,'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr,
                    'wall_seconds':time.monotonic()-started})
save('sandbox-check.json',results)
assert results[0]['exit']==0 and results[1]['exit']!=0
print('PASS: canonical HumanEval passes, deliberate failure fails; both use python:3.13-slim with --network none')
