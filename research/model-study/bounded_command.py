"""Run one study command, preserving complete output and its immediate exit."""
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

OUT = Path(__file__).resolve().parent
label, *args = sys.argv[1:]
assert args and '/' not in label
path = OUT/'attempt-2-commands'
path.mkdir(exist_ok=True)
assert not (path/(label+'.json')).exists(), 'Use a new attempt label'
command = [sys.executable, '-B', *args]
start = time.time()
with (path/(label+'.log')).open('w') as log:
    proc = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT, start_new_session=True,
                            env={**os.environ, 'PYTHONDONTWRITEBYTECODE':'1'})
    try:
        code = proc.wait(timeout=850)
        timed_out = False
    except subprocess.TimeoutExpired:
        os.killpg(proc.pid, signal.SIGKILL)
        code = proc.wait()
        timed_out = True
receipt = {'command':command,'exit':code,'timeout':timed_out,'seconds':time.time()-start,
           'log':str(path/(label+'.log'))}
(path/(label+'.json')).write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt),flush=True)
output = (path/(label+'.log')).read_text()
lines = output.splitlines()
print('Complete output:',path/(label+'.log'),'lines omitted from chat:',max(0,len(lines)-8),flush=True)
print('\n'.join(lines[-8:]),flush=True)
sys.exit(code if code >= 0 else 1)
