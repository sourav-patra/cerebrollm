"""Full index of the corpus into the live table with the paced embedding model (see embed_pace.py).

Same code path as `cerebrollm index` (indexer.run_index builds <table>_next and swaps), with the embed model
wrapped so the Windows port limit is not hit. Prints the run_index summary and the backoff seconds.
"""
import json
import sys
import time

import embed_pace
from study import REPO
sys.path.insert(0, str(REPO))
from cerebrollm import config, indexer, store
import psycopg2.errors
from llama_index.embeddings.ollama import OllamaEmbedding


class Paced(OllamaEmbedding):
    def get_general_text_embeddings(self, texts):
        return embed_pace.paced(lambda: OllamaEmbedding.get_general_text_embeddings(self, texts), len(texts))

    def get_general_text_embedding(self, text):
        return embed_pace.paced(lambda: OllamaEmbedding.get_general_text_embedding(self, text), 1)


def paced_model(cfg):
    return Paced(model_name=cfg.ollama['model'], base_url=cfg.ollama['base_url'], embed_batch_size=16,
                 ollama_additional_kwargs=cfg.ollama_options)


def swap_in_with_retry(cfg):
    """swap_in is one transaction. On 2026-10-29 it deadlocked with autovacuum ANALYZE on the new table
    (Postgres rolled it back, live table unchanged); a retry after the analyze finishes succeeds."""
    for attempt in range(5):
        try:
            return original_swap_in(cfg)
        except psycopg2.errors.DeadlockDetected:
            print('swap deadlock (autovacuum), retry', attempt + 1, flush=True)
            time.sleep(10)
    raise RuntimeError('swap_in deadlocked 5 times')


original_swap_in = store.swap_in

if __name__ == '__main__':
    store.swap_in = swap_in_with_retry
    store.embed_model = paced_model
    indexer.store.embed_model = paced_model
    cfg = config.load()
    t = time.time()
    summary = indexer.run_index(cfg)
    summary['backoff_seconds'] = embed_pace.backoff_total
    summary['pace_max_texts_per_second'] = embed_pace.MAX_TEXTS_PER_SECOND
    summary['wall_seconds'] = round(time.time() - t, 1)
    print(json.dumps(summary, indent=2))
