"""Only allowlisted local Ollama pulls/removals, with disk receipts."""
import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import time

import httpx
from study import OUT, BASE, MODELS, api, save, append

ESTIMATES = {'phi4':9053116391,'qwen3-embedding:0.6b':640000000,'qwen3-embedding:4b':2500000000,
             'devstral:24b':14330000000,'gpt-oss:20b':13790000000,
             'qwen3:14b':9280000000,'qwen3:8b':5230000000}


def free():
    v = os.statvfs(OUT)
    return v.f_bavail*v.f_frsize


def disk():
    r = subprocess.run(['df','-h',str(OUT)],text=True,capture_output=True,timeout=10)
    return {'command':r.args,'exit':r.returncode,'stdout':r.stdout,'free_bytes':free()}


def main():
    p = argparse.ArgumentParser()
    p.add_argument('action',choices=['pull','remove','unload','inventory'])
    p.add_argument('--model',choices=sorted(MODELS))
    a = p.parse_args()
    signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError('840-second command limit')))
    signal.alarm(840)
    state_path = OUT/'models-managed.json'
    managed = json.loads(state_path.read_text()) if state_path.exists() else []
    receipt = {'action':a.action,'model':a.model,'time':time.time(),'disk_before':disk(),'tags_before':api('tags')}
    try:
        if a.action=='pull':
            assert a.model in ESTIMATES
            existing = {x['name'] for x in receipt['tags_before']['models']}
            if a.model in existing or a.model+':latest' in existing:
                receipt['status']='already installed; not claimed as pulled'
            else:
                assert free()-ESTIMATES[a.model] >= 8000000000, 'Disk hold: pull would leave less than 8 GB'
                events = []
                with httpx.Client(timeout=780,trust_env=False) as client:
                    with client.stream('POST',BASE+'/api/pull',json={'model':a.model,'stream':True}) as response:
                        response.raise_for_status()
                        for line in response.iter_lines():
                            if not line: continue
                            e = json.loads(line)
                            if 'error' in e: raise RuntimeError(e['error'])
                            assert free()>=8000000000, 'Disk floor reached during pull'
                            events.append(e)
                            if len(events)==1 or e.get('status')!=events[-2].get('status'):
                                print(e,flush=True)
                            append('model-pull-progress.jsonl',{'model':a.model,'time':time.time(),**e})
                assert events[-1]['status']=='success'
                managed = json.loads(state_path.read_text()) if state_path.exists() else []
                managed.append(a.model)
                save('models-managed.json',sorted(set(managed)))
                receipt['status']='pulled'
        elif a.action=='remove':
            assert a.model=='phi4' or a.model in managed, 'Removal outside authorization'
            assert a.model!='bge-m3'
            with httpx.Client(timeout=60,trust_env=False) as client:
                r = client.request('DELETE',BASE+'/api/delete',json={'model':a.model})
                r.raise_for_status()
            receipt['status']='removed'
        elif a.action=='unload':
            receipt['response']=api('generate',{'model':a.model,'keep_alive':0})
            receipt['status']='unloaded'
        else:
            receipt['status']='inventory'
        receipt['disk_after']=disk()
        receipt['tags_after']=api('tags')
        assert receipt['disk_after']['free_bytes']>=8000000000
    except Exception as e:
        receipt['error']=repr(e)
        receipt['disk_after']=disk()
        append('model-actions.jsonl',receipt)
        print(json.dumps(receipt,indent=2),flush=True)
        raise
    append('model-actions.jsonl',receipt)
    print(json.dumps(receipt,indent=2),flush=True)


if __name__=='__main__': main()
