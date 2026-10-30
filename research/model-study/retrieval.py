"""Isolated R1 tables, using cerebrollm ranking and LlamaIndex evaluation.

WSL rerun (development step L): protocol and selection set come from selection/, raw results go to r1-wsl/,
the corpus snapshot is read from SNAPSHOT (exported by r1_prepare.py), every embed call carries
num_ctx 8192, and each retrieval is scored by node id and by text identity.
"""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import time

import embed_pace
from study import OUT, REPO, api, append, load, save, ps
from studyconfig import engine_config_text
sys.path.insert(0,str(REPO))
from cerebrollm import config, search, store
from llama_index.core import VectorStoreIndex
from llama_index.core.evaluation import RetrieverEvaluator
from llama_index.core.retrievers import BaseRetriever
from llama_index.core.schema import TextNode, NodeWithScore, MetadataMode
from llama_index.core.vector_stores.types import VectorStoreQueryMode
from llama_index.core.vector_stores.utils import metadata_dict_to_node
from llama_index.embeddings.ollama import OllamaEmbedding

TABLES = {'bge-m3':'study_d_bge_m3','qwen3-embedding:0.6b':'study_d_qwen_06b',
          'qwen3-embedding:4b':'study_d_qwen_4b'}
R1 = 'r1-wsl'
SNAPSHOT = Path(os.environ.get('R1_SNAPSHOT', os.path.expanduser('~/cerebrollm-scratch/corpus-snapshot.json')))
PROTOCOL = load('selection/protocol.json')
PREFIX = PROTOCOL['qwen_query_prefix']
NUM_CTX = PROTOCOL['num_ctx']


def snapshot():
    return json.loads(SNAPSHOT.read_text())


def sha(text):
    return hashlib.sha256(text.encode()).hexdigest()


class StudyEmbedding(OllamaEmbedding):
    def get_general_text_embeddings(self,texts):
        payload = {'model':self.model_name,'input':texts,'keep_alive':'15m','options':{'num_ctx':NUM_CTX}}
        if self.model_name.startswith('qwen3-embedding'):
            payload['dimensions']=1024
        result = embed_pace.paced(lambda: api('embed',payload),len(texts))
        assert all(len(e)==1024 for e in result['embeddings']), 'Server failed to honor 1024-dimensional vectors'
        return result['embeddings']

    def get_general_text_embedding(self,text):
        return self.get_general_text_embeddings([text])[0]

    async def aget_general_text_embeddings(self,texts):
        return self.get_general_text_embeddings(texts)

    async def aget_general_text_embedding(self,text):
        return self.get_general_text_embedding(text)


def study_config_text(engine_text,model,table):
    """The engine configuration of one study table: table and model set explicitly, whatever model the live
    engine/cerebrollm.toml selects, and no query_prefix (StudyEmbedding applies the Qwen prefix from
    selection/protocol.json). Everything else is the engine file as it is."""
    text = re.sub(r'^table = "[^"]*"[^\r\n]*',f'table = "{table}"',engine_text,count=1,flags=re.M)
    text = re.sub(r'^model = "[^"]*"[^\r\n]*',f'model = "{model}"',text,count=1,flags=re.M)
    text = re.sub(r'^query_prefix = [^\r\n]*(?:\r?\n)?','',text,count=1,flags=re.M)
    assert f'table = "{table}"' in text and f'model = "{model}"' in text and 'query_prefix' not in text
    return engine_config_text(text)   # study.toml sets data and corpus paths


def cfg_for(model):
    table = TABLES[model]
    path = OUT/R1/f'cerebrollm-{table}.toml'
    copied = study_config_text((REPO/'cerebrollm.toml').read_text(),model,table)
    path.parent.mkdir(parents=True,exist_ok=True)
    if not path.exists(): path.write_text(copied)
    assert path.read_text()==copied
    cfg = config.load(path)
    baseline = config.load()
    changed = [(section,key) for section in baseline.data if isinstance(baseline.data[section],dict)
               for key in baseline.data[section] if cfg.data[section].get(key)!=baseline.data[section][key]]
    assert set(changed)<= {('postgres','table'),('ollama','model'),('ollama','query_prefix'),('postgres','socket_dir')}
    assert cfg.data_table=='data_'+table and cfg.data_table!='data_chunks'
    return cfg


def embedding(model):
    return StudyEmbedding(model_name=model,base_url='http://127.0.0.1:11434',
                          embed_batch_size=16,query_instruction=PREFIX if model.startswith('qwen3-embedding') else None)


def as_node(row):
    node = metadata_dict_to_node(row['metadata'])
    node.set_content(row['text'])
    node.id_=row['node_id']
    node.embedding=None
    return node


def index(model,start,count):
    cfg = cfg_for(model)
    rows = snapshot()
    vs = store.vector_store(cfg)
    embed = embedding(model)
    started = time.monotonic()
    for offset in range(start,min(start+count,len(rows)),16):
        batch = rows[offset:min(offset+16,start+count,len(rows))]
        key = f'{R1}/index/{cfg.table}/{offset:05d}.json'
        if (OUT/key).exists(): continue
        tick = time.monotonic()
        waited = embed_pace.backoff_total
        load_before = os.getloadavg()
        nodes = [as_node(r) for r in batch]
        embeddings = embed.get_text_embedding_batch([n.get_content(metadata_mode=MetadataMode.EMBED) for n in nodes])
        for n,e in zip(nodes,embeddings): n.embedding=e
        # An interrupted add must be inspected before resuming. No table is cleared automatically.
        vs.add(nodes)
        receipt = {'model':model,'table':cfg.data_table,'start':offset,'chunks':len(batch),
                   'duration_seconds':time.monotonic()-tick-(embed_pace.backoff_total-waited),'backoff_seconds':embed_pace.backoff_total-waited,'embedding_dimension':len(embeddings[0]),
                   'load_average_before':load_before,'load_average_after':os.getloadavg()}
        save(key,receipt)
        print(model,'indexed',offset+len(batch),'/',len(rows),flush=True)
    save(f'{R1}/index/{cfg.table}/memory-{start:05d}.json',ps())
    with store.sql(cfg) as cur:
        cur.execute('SELECT count(*),count(distinct node_id) FROM '+cfg.data_table)
        n,unique = cur.fetchone()
    assert n==unique, 'Duplicate node IDs after interrupted insert; inspect before continuing'
    print('Table',cfg.data_table,n,'distinct nodes; command seconds',time.monotonic()-started,flush=True)
    if n==len(rows):
        receipts = [json.loads(p.read_text()) for p in (OUT/R1/'index'/cfg.table).glob('[0-9]*.json')]
        seconds = sum(r['duration_seconds'] for r in receipts)
        assert sum(r['chunks'] for r in receipts)==n
        save(f'{R1}/index/{cfg.table}/summary.json',{'model':model,'chunks':n,'duration_seconds':seconds,
                 'chunks_per_minute':n/seconds*60,'within_60_minutes':seconds<3600,
                 'timing':'sum of sequential embedding-and-insert batches; excludes operator pauses between bounded commands',
                 'memory':ps(),'query_prefix':PREFIX if model.startswith('qwen3-embedding') else ''})


class CerebrollmRetriever(BaseRetriever):
    def __init__(self,model,mode,k):
        self.cfg=cfg_for(model)
        self.mode=mode
        self.k=k
        self.index=VectorStoreIndex.from_vector_store(store.vector_store(self.cfg),embed_model=embedding(model))
        super().__init__()

    def _retrieve(self,query_bundle):
        cfg=self.cfg
        query=search.sanitize(query_bundle.query_str)
        fetch=max(self.k*cfg.search['fetch_factor'],40)
        filters=search._filters(cfg,False,None)
        def arm(mode):
            return self.index.as_retriever(similarity_top_k=fetch,vector_store_query_mode=mode,filters=filters)
        hits=arm(VectorStoreQueryMode.DEFAULT).retrieve(query)
        if self.mode=='hybrid':
            lexical=search.expand_query(query,cfg.synonyms) if cfg.search.get('synonyms_enabled') else query
            hits=search.rrf_fuse([hits,arm(VectorStoreQueryMode.SPARSE).retrieve(lexical)])
        now=datetime.datetime.now(datetime.timezone.utc)
        recency=cfg.search['recency']
        ranked=[]
        for h in hits:
            meta=h.node.metadata
            score=(h.score or 0)*cfg.search['tier_boost'].get(meta.get('tier'),1)
            score*=search.recency_multiplier(meta.get('mtime'),now,recency['weight'],recency['half_life_days'])
            ranked.append({'score':score,'node':h.node,'meta':meta})
        ranked.sort(key=lambda x:-x['score'])
        return [NodeWithScore(node=e['item']['node'],score=e['item']['score']) for e in search.distinct_by_text(ranked,self.k)]


def evaluate(model):
    """One raw file per (table, mode, k). Node-id scoring comes from the LlamaIndex evaluator; text identity
    credits a retrieved chunk whose text equals the sampled chunk's text, whatever its id."""
    cfg=cfg_for(model)
    assert load(f'{R1}/index/{cfg.table}/summary.json')['chunks']==len(snapshot())
    data=load('selection/selection-set.json')['items']
    for mode in ['vector','hybrid']:
        for k in [5,10]:
            evaluator=RetrieverEvaluator.from_metric_names(['hit_rate','mrr'],retriever=CerebrollmRetriever(model,mode,k))
            records=[]
            for d in data:
                result=evaluator.evaluate(d['question'],expected_ids=[d['node_id']])
                hashes=[sha(t) for t in result.retrieved_texts]
                rank=hashes.index(d['text_sha256'])+1 if d['text_sha256'] in hashes else None
                records.append({'index':d['index'],'node_id':d['node_id'],'text_sha256':d['text_sha256'],
                                'retrieved_ids':result.retrieved_ids,'retrieved_text_sha256':hashes,
                                'id_hit':result.metric_vals_dict['hit_rate'],'id_mrr':result.metric_vals_dict['mrr'],
                                'text_hit':1.0 if rank else 0.0,'text_mrr':1/rank if rank else 0.0})
            n=len(records)
            summary={key:sum(r[key] for r in records)/n for key in ['id_hit','id_mrr','text_hit','text_mrr']}
            save(f'{R1}/retrieval/{cfg.table}/{mode}-{k}.json',{'model':model,'table':cfg.data_table,'mode':mode,'k':k,
                 'questions':n,'summary':summary,'load_average_after':os.getloadavg(),'records':records})
            print(model,mode,'k',k,summary,flush=True)


def self_check():
    for m in TABLES:
        cfg=cfg_for(m)
        assert cfg.data_table!='data_chunks'
    rows=snapshot()
    node=as_node(rows[0])
    assert node.node_id==rows[0]['node_id'] and node.text==rows[0]['text']
    assert StudyEmbedding(model_name='qwen3-embedding:0.6b',base_url='http://127.0.0.1:11434',query_instruction=PREFIX)._format_query('hello')==PREFIX+' hello'
    print('PASS: 3 isolated configs change only table/model; original node IDs/text preserved; Qwen query prefix applied')


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('action',choices=['index','evaluate','self-check'])
    p.add_argument('--model',choices=TABLES,default='bge-m3')
    a=p.parse_args()
    if a.action=='index': index(a.model,0,10**9)
    elif a.action=='evaluate': evaluate(a.model)
    else: self_check()
