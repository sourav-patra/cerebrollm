"""Shared constructors: vector store, embedding model, direct SQL, state file."""
import json
import time
from contextlib import contextmanager

import psycopg2

from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.vector_stores.postgres import PGVectorStore


def vector_store(cfg, table=None):
    return PGVectorStore.from_params(
        connection_string=cfg.sync_url, async_connection_string=cfg.async_url,
        table_name=table or cfg.table, embed_dim=cfg.pg["embed_dim"], hybrid_search=True,
        text_search_config=cfg.pg["text_search_config"])


def embed_model(cfg):
    # ollama_additional_kwargs is sent as "options" on every embed call; num_ctx caps the context
    # Ollama loads the model with (unset, Ollama uses the model's own maximum).
    # query_prefix (optional) goes before each search query only; documents are embedded as they are.
    return OllamaEmbedding(model_name=cfg.ollama["model"], base_url=cfg.ollama["base_url"],
                           embed_batch_size=16, ollama_additional_kwargs=cfg.ollama_options,
                           query_instruction=cfg.ollama.get("query_prefix") or None)


@contextmanager
def sql(cfg):
    conn = psycopg2.connect(host=cfg.pg["socket_dir"], port=cfg.pg["port"],
                            dbname=cfg.pg["database"], user=cfg.pg["user"])
    try:
        with conn, conn.cursor() as cur:
            yield cur
    finally:
        conn.close()


def _regclass(cur, name):
    cur.execute("select to_regclass(%s)", (name,))
    return cur.fetchone()[0] is not None


def table_exists(cfg):
    with sql(cfg) as cur:
        return _regclass(cur, cfg.data_table)


def row_count(cfg, data_table):
    with sql(cfg) as cur:
        if not _regclass(cur, data_table):
            return 0
        cur.execute("select count(*) from %s" % data_table)
        return cur.fetchone()[0]


def drop_table(cfg, data_table):
    with sql(cfg) as cur:
        cur.execute("drop table if exists %s" % data_table)


def relations(cur, data_table):
    """(kind, name) of the indexes and the id sequence that PGVectorStore creates for a data table."""
    cur.execute("select indexname from pg_indexes where schemaname = current_schema() and tablename = %s",
                (data_table,))
    rels = [("INDEX", r[0]) for r in cur.fetchall()]
    cur.execute("select pg_get_serial_sequence(%s, 'id')", (data_table,))
    seq = cur.fetchone()[0]
    if seq:
        rels.append(("SEQUENCE", seq.split(".")[-1]))
    return rels


def _moved(name, src, dst):
    """The name a relation takes when its table moves from table name src to dst. PGVectorStore names
    the indexes after the table (chunks_idx) and the primary key and sequence after the data table
    (data_chunks_pkey, data_chunks_id_seq)."""
    for prefix in ("data_" + src, src):
        if name.startswith(prefix):
            return ("data_" + dst if prefix.startswith("data_") else dst) + name[len(prefix):]
    raise RuntimeError("relation %s does not carry the table name %s" % (name, src))


def swap_in(cfg):
    """Make the new data table the live one in one transaction. The live table and its relations take
    the _old names and are dropped; the new table and its relations take the live names. The live table
    is unchanged until the commit."""
    live, new = cfg.table, cfg.next_table
    old_data = "data_%s_old" % live
    with sql(cfg) as cur:
        cur.execute("drop table if exists %s" % old_data)
        live_exists = _regclass(cur, cfg.data_table)
        live_rels = relations(cur, cfg.data_table) if live_exists else []
        new_rels = relations(cur, cfg.next_data_table)
        for kind, name in live_rels:
            cur.execute("alter %s %s rename to %s" % (kind, name, _moved(name, live, live + "_old")))
        if live_exists:
            cur.execute("alter table %s rename to %s" % (cfg.data_table, old_data))
        for kind, name in new_rels:
            cur.execute("alter %s %s rename to %s" % (kind, name, _moved(name, new, live)))
        cur.execute("alter table %s rename to %s" % (cfg.next_data_table, cfg.data_table))
        cur.execute("drop table if exists %s" % old_data)


def model_digest(cfg):
    import ollama
    name = cfg.ollama["model"]
    for m in ollama.Client(host=cfg.ollama["base_url"]).list().models:
        if m.model == name or m.model == name + ":latest":   # a name with a tag (qwen3-embedding:0.6b) must match its own tag
            return m.digest
    return None


def read_state(cfg):
    try:
        return json.loads(cfg.state_path.read_text())
    except FileNotFoundError:
        return {}


def write_state(cfg, **fields):
    cfg.state_dir.mkdir(parents=True, exist_ok=True)
    state = read_state(cfg)
    state.update(fields)
    state["updated"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    cfg.state_path.write_text(json.dumps(state, indent=2, sort_keys=True))
