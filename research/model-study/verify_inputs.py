"""Verify fixed datasets and the 150-question selection artifact without model calls."""
import hashlib
import json
from pathlib import Path
import random
import re

import jsonschema
from study import OUT,load,save

suite=load('tool-scenarios.json')
assert len(suite['scenarios'])==12
tools={t['function']['name']:t['function']['parameters'] for t in suite['tools']}
assert set(tools)=={'read_file','write_file','run_tests','search_code'}
for s in suite['scenarios']:
    jsonschema.validate(s['expected']['arguments'],tools[s['expected']['name']])
corpus=load('corpus-snapshot.json')
chunks=load('selection-chunks.json')
assert chunks==random.Random(27).sample(corpus,150)
assert len({r['node_id'] for r in chunks})==150
assert all(r['metadata']['status'] in ['locked','current'] for r in corpus)
assert all(not Path(r['metadata']['path']).name.startswith('GOLDEN-') for r in corpus)
data=load('selection-set.json')['items']
assert len(data)==150
for row,chunk in zip(data,chunks):
    q=row['question']
    assert row['valid'] and row['node_id']==chunk['node_id']
    assert not re.search(r'\bREADME\b|[\w-]+\.(?:md|py|json|toml|yaml|yml|txt|js|ts|sh|html|svg|xml)\b|/',q,re.I),row['index']
    assert Path(chunk['metadata']['path']).name.casefold() not in q.casefold()
    sentences=[s.strip().casefold() for s in re.split(r'(?<=[.!?])\s+',chunk['text']) if len(s.split())>=5]
    assert not any(s in q.casefold() for s in sentences),row['index']
    assert list(row['dataset']['queries'].values())==[q]
    assert list(row['dataset']['relevant_docs'].values())==[[row['node_id']]]
    assert row['dataset']['corpus'][row['node_id']]==chunk['text']
problems=load('humaneval-40.json')
assert len(problems)==40 and len({p['task_id'] for p in problems})==40
assert 'MIT License' in (OUT/'sources/LICENSE').read_text()
files=['selection-set.json','selection-chunks.json','humaneval-40.json','tool-scenarios.json','protocol.json']
receipt={'status':'PASS','checks':['seed-27 sample reproduces exactly','150 distinct eligible chunks',
         '150 questions preserve original node IDs and context','no detected filenames, paths or copied sentences',
         '12 expected tool calls validate against their schemas','40 distinct MIT HumanEval problems'],
         'hashes':{f:hashlib.sha256((OUT/f).read_bytes()).hexdigest() for f in files},
         'limits':'Question semantics and all possible filename spellings require manual review; regex checks do not establish answerability.'}
save('verified-inputs.json',receipt)
print('PASS:', '; '.join(receipt['checks']))
