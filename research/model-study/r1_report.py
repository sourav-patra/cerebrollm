"""Apply the fixed R1 rule to r1-wsl/ results: write r1-wsl/r1-table.json and print the table."""
import json
from retrieval import TABLES, R1, OUT

rows = {}
for model, table in TABLES.items():
    s = json.loads((OUT / R1 / 'index' / table / 'summary.json').read_text())
    r = {'model': model, 'chunks': s['chunks'], 'index_minutes': s['duration_seconds'] / 60,
         'chunks_per_min': s['chunks_per_minute'], 'under_60_min': s['within_60_minutes'],
         'ollama_ps': s['memory']['stdout'].strip().splitlines()[-1]}
    backoff = sum(json.loads(p.read_text()).get('backoff_seconds', 0)
                  for p in (OUT / R1 / 'index' / table).glob('[0-9]*.json'))
    r['backoff_seconds_excluded'] = backoff
    for mode in ['vector', 'hybrid']:
        for k in [5, 10]:
            d = json.loads((OUT / R1 / 'retrieval' / table / f'{mode}-{k}.json').read_text())['summary']
            for scoring, pre in [('id', 'id_'), ('text', 'text_')]:
                r[f'{scoring}_{mode}_hit@{k}'] = d[pre + 'hit']
                r[f'{scoring}_{mode}_mrr@{k}'] = d[pre + 'mrr']
    rows[model] = r
eligible = [r for r in rows.values() if r['under_60_min']]
ranked = sorted(eligible, key=lambda r: (-r['id_hybrid_hit@5'], -r['id_hybrid_mrr@10'], -r['chunks_per_min']))
out = {'rule': 'highest hybrid hit@5 (node-id scoring), then hybrid MRR@10, then chunks/min; index under 60 minutes',
       'choice': ranked[0]['model'] if ranked else None, 'order': [r['model'] for r in ranked], 'rows': rows}
(OUT / R1 / 'r1-table.json').write_text(json.dumps(out, indent=2) + '\n')
for scoring in ['id', 'text']:
    print(f'scoring: {scoring}')
    for r in rows.values():
        print('| %-22s | %d | %.2f | %.0f | v %.3f / %.3f / %.3f | h %.3f / %.3f / %.3f |' % (
            r['model'], r['chunks'], r['index_minutes'], r['chunks_per_min'],
            r[f'{scoring}_vector_hit@5'], r[f'{scoring}_vector_hit@10'], r[f'{scoring}_vector_mrr@10'],
            r[f'{scoring}_hybrid_hit@5'], r[f'{scoring}_hybrid_hit@10'], r[f'{scoring}_hybrid_mrr@10']))
print('choice:', out['choice'], out['order'])
