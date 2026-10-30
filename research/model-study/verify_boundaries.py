"""Hash the complete live table read-only and compare cerebrollm source files."""
import argparse
import hashlib
import json
import signal
import sys
from pathlib import Path

import psycopg2
from study import OUT, REPO, load, save
sys.path.insert(0,str(REPO))
from cerebrollm.config import load as config_load

signal.signal(signal.SIGALRM,lambda *_: (_ for _ in ()).throw(TimeoutError('840-second command limit')))
signal.alarm(840)
p=argparse.ArgumentParser()
p.add_argument('phase',choices=['before','after'])
a=p.parse_args()
cfg=config_load()
conn=psycopg2.connect(host=cfg.pg['socket_dir'],port=cfg.pg['port'],dbname=cfg.pg['database'],user=cfg.pg['user'],connect_timeout=5)
conn.set_session(readonly=True)
with conn,conn.cursor() as cur:
    cur.execute("SELECT count(*),md5(string_agg(md5(concat_ws('|',node_id,text,metadata_::text,embedding::text,text_search_tsv::text)),'' ORDER BY node_id)) FROM data_chunks")
    count,digest=cur.fetchone()
conn.close()
before=load('preflight.json')
actual={name:hashlib.sha256((REPO/name).read_bytes()).hexdigest() for name in before['source_hashes']}
result={'live_table':'data_chunks','rows':count,'full_live_digest':digest,
        'source_hashes_match_preflight':actual==before['source_hashes'],'source_hashes':actual}
if a.phase=='after':
    baseline=load('boundaries-before.json')
    result['live_table_matches_before']=digest==baseline['full_live_digest'] and count==baseline['rows']
save('boundaries-'+a.phase+'.json',result)
if a.phase=='after':
    assert result['live_table_matches_before'],'Live table differs from baseline; failed match saved'
assert result['source_hashes_match_preflight'],'Cerebrollm source differs from baseline'
print('PASS:',a.phase,'live rows',count,'full digest',digest,'source hashes unchanged')
