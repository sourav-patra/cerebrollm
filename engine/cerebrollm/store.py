"""Shared constructors: vector store, embedding model, direct SQL, state file."""
import json
import os
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


# What the index rows hold. 1 (0.2.0 and earlier, no key in state.json): the file sha256 per chunk.
# 2: also passage_sha256, the sha256 of each chunk's own text, which verify uses after an unrelated edit.
# The number is stored inside last_index, the summary each index run replaces whole, so a run by an older
# cerebrollm (which writes a summary without it) leaves no stale marker behind. Beside it, index_table names
# the database and table the run wrote, so a marker written for another table never vouches for this one.
INDEX_FORMAT = 2


def index_table(cfg):
    """The database and data table an index run writes, as stored in last_index["index_table"]."""
    return "%s.%s" % (cfg.pg["database"], cfg.data_table)


def index_format(state, table):
    """The format of the rows the last recorded index run wrote into table (index_table): 1 when the summary
    has no index_format (0.2.0 and earlier); None when no run is recorded, the value is not a whole number,
    or the summary names another table or none."""
    last = state.get("last_index")
    if not isinstance(last, dict) or not last:
        return None
    if "index_format" not in last:
        return 1
    value = last["index_format"]
    if not isinstance(value, int) or isinstance(value, bool) or last.get("index_table") != table:
        return None
    return value


def older_format(state, table):
    """True when state.json records an index run whose rows in table are not known to be of INDEX_FORMAT.
    No recorded run (nothing indexed yet) is not older."""
    return bool(state.get("last_index")) and index_format(state, table) != INDEX_FORMAT


def format_warning(cfg):
    """The one warning line for an index of another format or an unreadable state.json, else None. Reads
    state.json only."""
    try:
        state = read_state(cfg)
    except (OSError, ValueError) as exc:
        return ("WARNING: %s cannot be read (%s); run `cerebrollm index` to rewrite it."
                % (cfg.state_path, type(exc).__name__))
    table = index_table(cfg)
    if not older_format(state, table):
        return None
    return ("WARNING: the index in %s has format %s and this cerebrollm needs %d; run `cerebrollm index` once "
            "(`index --changed` also rebuilds it in full). Until then verify answers CHANGED after any edit "
            "to a file." % (table, index_format(state, table) or "unknown", INDEX_FORMAT))


def read_state(cfg):
    """state.json as a dict; {} when it is absent. ValueError when it is not JSON or not a JSON object; OSError
    when it exists and cannot be read."""
    try:
        state = json.loads(cfg.state_path.read_text())
    except FileNotFoundError:
        return {}
    if not isinstance(state, dict):
        raise ValueError("%s does not hold a JSON object" % cfg.state_path)
    return state


def write_state(cfg, **fields):
    """Merge fields into state.json. A state.json that cannot be read or parsed is replaced, so an index run
    repairs it; the new file is written beside it and renamed over it, which needs only the folder to be
    writable."""
    cfg.state_dir.mkdir(parents=True, exist_ok=True)
    try:
        state = read_state(cfg)
    except (OSError, ValueError):
        state = {}
    state.update(fields)
    state["updated"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    tmp = cfg.state_path.with_name(cfg.state_path.name + ".tmp")
    tmp.write_text(json.dumps(state, indent=2, sort_keys=True))
    os.replace(tmp, cfg.state_path)
