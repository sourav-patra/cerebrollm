"""Read-only host checks and pinned inputs for development step D."""
import gzip
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import random
import subprocess
import sys
import time

import httpx
import psycopg2

OUT = Path(__file__).resolve().parent
from studyconfig import ENGINE_DIR as REPO
sys.path.insert(0, str(REPO))
from cerebrollm.config import load


def save(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2, default=str) + '\n')


def main():
    cfg = load()
    client = httpx.Client(timeout=60, follow_redirects=True)
    evidence = {'time': time.time(), 'python': sys.executable,
                'versions': {p: importlib.metadata.version(p) for p in
                             ['llama-index-core', 'llama-index-embeddings-ollama',
                              'llama-index-vector-stores-postgres']},
                'free_bytes': os.statvfs(OUT).f_bavail * os.statvfs(OUT).f_frsize}
    for endpoint in ['version', 'tags', 'ps']:
        r = client.get('http://127.0.0.1:11434/api/' + endpoint)
        r.raise_for_status()
        evidence[endpoint] = r.json()
    evidence['cerebrollm_revision'] = subprocess.run(
        ['git', '-C', str(REPO), 'rev-parse', 'HEAD'], capture_output=True, text=True).stdout.strip()
    evidence['source_hashes'] = {str(p.relative_to(REPO)): hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in [REPO / 'cerebrollm.toml', *sorted((REPO / 'cerebrollm').glob('*.py'))]}
    conn = psycopg2.connect(host=cfg.pg['socket_dir'], port=cfg.pg['port'],
                            dbname=cfg.pg['database'], user=cfg.pg['user'], connect_timeout=5)
    conn.set_session(readonly=True)
    with conn, conn.cursor() as cur:
        cur.execute("SELECT column_name,data_type FROM information_schema.columns WHERE table_name=%s ORDER BY ordinal_position", (cfg.data_table,))
        evidence['live_schema'] = cur.fetchall()
        cur.execute('SELECT node_id, text, metadata_ FROM data_chunks ORDER BY node_id')
        all_rows = cur.fetchall()
    conn.close()
    evidence['live_rows'] = len(all_rows)
    evidence['live_fingerprint'] = hashlib.sha256(json.dumps(all_rows, default=str, sort_keys=True).encode()).hexdigest()
    rows = [dict(node_id=n, text=t, metadata=m) for n,t,m in all_rows
            if m.get('status') in ['locked','current'] and m.get('domain') == cfg.domain]
    assert len(rows) >= 150
    save('corpus-snapshot.json', rows)
    sample = random.Random(27).sample(rows, 150)
    save('selection-chunks.json', sample)
    evidence['default_chunks'] = len(rows)
    evidence['selection_seed'] = 27
    save('preflight.json', evidence)
    # Download only public inputs, with source bodies and hashes kept on disk.
    sources = OUT / 'sources'
    sources.mkdir(exist_ok=True)
    urls = {
        'humaneval-commit.json': 'https://api.github.com/repos/openai/human-eval/commits/master',
        'qwen-embedding-0.6b.md': 'https://huggingface.co/Qwen/Qwen3-Embedding-0.6B/raw/main/README.md',
        'qwen-embedding-4b.md': 'https://huggingface.co/Qwen/Qwen3-Embedding-4B/raw/main/README.md',
        'phi4.md': 'https://huggingface.co/microsoft/phi-4/raw/main/README.md',
        'gpt-oss-20b.md': 'https://huggingface.co/openai/gpt-oss-20b/raw/main/README.md',
        'qwen3-14b.md': 'https://huggingface.co/Qwen/Qwen3-14B/raw/main/README.md',
        'qwen3-8b.md': 'https://huggingface.co/Qwen/Qwen3-8B/raw/main/README.md',
        'llama-embedding-qa.py': 'https://raw.githubusercontent.com/run-llama/llama_index/v0.10.68/llama-index-core/llama_index/core/evaluation/retrieval/embedding_qa_dataset.py',
    }
    receipts = []
    for name, url in urls.items():
        r = client.get(url)
        receipts.append({'name': name, 'url': url, 'status': r.status_code,
                         'sha256': hashlib.sha256(r.content).hexdigest()})
        (sources/name).write_bytes(r.content)
        save('sources/manifest.json', receipts)
    commit = json.loads((sources/'humaneval-commit.json').read_text())['sha']
    for name in ['data/HumanEval.jsonl.gz', 'LICENSE']:
        url = f'https://raw.githubusercontent.com/openai/human-eval/{commit}/{name}'
        r = client.get(url)
        r.raise_for_status()
        path = sources / Path(name).name
        path.write_bytes(r.content)
        receipts.append({'name': path.name, 'url': url, 'commit': commit,
                         'sha256': hashlib.sha256(r.content).hexdigest(), 'status':r.status_code})
    problems = [json.loads(line) for line in gzip.decompress((sources/'HumanEval.jsonl.gz').read_bytes()).splitlines()]
    problems.sort(key=lambda p: int(p['task_id'].split('/')[1]))
    sample = random.Random(27).sample(problems, 40)
    save('humaneval-40.json', sample)
    save('sources/manifest.json', receipts)
    print(json.dumps({'default_chunks':len(rows),'sample':150,'HumanEval':len(sample),'free_bytes':evidence['free_bytes'], 'source_status':[(r['name'],r['status']) for r in receipts]}))


if __name__ == '__main__':
    main()
