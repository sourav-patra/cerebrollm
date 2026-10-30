"""Public dataset and historical LlamaIndex helper, isolated from the venv."""
import gzip
import hashlib
import io
import json
from pathlib import Path
import random
import signal
import subprocess
import zipfile

import httpx

OUT = Path(__file__).resolve().parent
signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError('840-second command limit')))
signal.alarm(840)
S = OUT / 'sources'
client = httpx.Client(timeout=90, follow_redirects=True)
manifest = json.loads((S/'manifest.json').read_text())


def fetch(name, url):
    r = client.get(url)
    r.raise_for_status()
    (S/name).write_bytes(r.content)
    manifest.append({'name':name,'url':url,'sha256':hashlib.sha256(r.content).hexdigest(),'status':r.status_code})
    (S/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return r.content


meta = json.loads(fetch('llama-core-pypi.json', 'https://pypi.org/pypi/llama-index-core/0.10.68/json'))
wheel = next(x for x in meta['urls'] if x['filename'].endswith('.whl'))
data = (S/wheel['filename']).read_bytes() if (S/wheel['filename']).exists() else fetch(wheel['filename'], wheel['url'])
assert hashlib.sha256(data).hexdigest() == wheel['digests']['sha256']
z = zipfile.ZipFile(io.BytesIO(data))
names = [n for n in z.namelist() if n.endswith('.py') and b'def generate_qa_embedding_pairs' in z.read(n)]
print('Helper files:',names)
assert len(names) == 1
(S/'llama-embedding-qa.py').write_bytes(z.read(names[0]))
manifest.append({'name':'llama-embedding-qa.py','wheel_member':names[0],
                 'sha256':hashlib.sha256(z.read(names[0])).hexdigest()})
ref = subprocess.run(['git','ls-remote','https://github.com/openai/human-eval.git','refs/heads/master'],
                     capture_output=True,text=True,timeout=60,check=True)
(S/'humaneval-ls-remote.txt').write_text(ref.stdout)
sha = ref.stdout.split()[0]
data = fetch('HumanEval.jsonl.gz',f'https://raw.githubusercontent.com/openai/human-eval/{sha}/data/HumanEval.jsonl.gz')
fetch('LICENSE',f'https://raw.githubusercontent.com/openai/human-eval/{sha}/LICENSE')
problems = [json.loads(line) for line in gzip.decompress(data).splitlines()]
problems.sort(key=lambda p:int(p['task_id'].split('/')[1]))
sample = random.Random(27).sample(problems,40)
(OUT/'humaneval-40.json').write_text(json.dumps(sample,indent=2)+'\n')
(S/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('HumanEval',sha,len(problems),len(sample))
