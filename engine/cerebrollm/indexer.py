"""cerebrollm index: LlamaIndex IngestionPipeline over the enumerated corpus."""
import errno
import fcntl
import os
import stat
import sys
import time
from contextlib import contextmanager
from pathlib import Path

from llama_index.core.ingestion import DocstoreStrategy, IngestionPipeline
from llama_index.core.node_parser import MarkdownNodeParser, SentenceSplitter
from llama_index.core.storage.docstore import SimpleDocumentStore

from . import corpus, store
from .glue import LocateChunks, MergeSmall, SourceDoc, TableRows

REPO = Path(__file__).resolve().parent.parent
META_KEYS = ["domain", "project", "tier", "status", "path", "root", "ref", "sha256", "mtime", "also_at"]


def make_documents(entries):
    docs = []
    for e in entries:
        meta = {k: e[k] for k in META_KEYS}
        docs.append(SourceDoc(
            text=e["text"], doc_id=corpus.doc_id(e), metadata=meta,
            excluded_embed_metadata_keys=[k for k in META_KEYS if k != "path"],
            excluded_llm_metadata_keys=META_KEYS))
    return docs


def chunk_steps(cfg, texts):
    """The transformations before embedding: parse at headings, merge short sections, one node per
    table row, sentence split (prose), then locate each chunk in its document."""
    ch = cfg.chunking
    return [
        MarkdownNodeParser(),
        MergeSmall(texts=texts, min_chars=ch["min_chunk_chars"]),
        TableRows(texts=texts),
        SentenceSplitter(chunk_size=ch["chunk_size"], chunk_overlap=ch["chunk_overlap"]),
        LocateChunks(texts=texts),
    ]


def build_pipeline(cfg, docs, vector_store, docstore):
    texts = {d.doc_id: d.text for d in docs}
    # disable_cache: the default in-memory transformation cache returned node lists from before
    # LocateChunks ran (chunks without char_start, title or heading_path). Each run is a full run
    # over the corpus and nothing is persisted, so the cache saved no work.
    return IngestionPipeline(
        transformations=chunk_steps(cfg, texts) + [store.embed_model(cfg)],
        docstore=docstore, vector_store=vector_store,
        docstore_strategy=DocstoreStrategy.UPSERTS_AND_DELETE, disable_cache=True)


def drop_command(cfg):
    """The command that drops the new table of a refused run."""
    return ("PYTHONPATH=%s %s -c \"from cerebrollm import config, store; "
            "store.drop_table(config.load('%s'), '%s')\"" % (REPO, sys.executable, cfg.path, cfg.next_data_table))


FLOCK_TRIES = 5   # a failed flock whose holder the kernel no longer lists was released meanwhile: retry
PG_NAME_LIMIT = 63   # NAMEDATALEN - 1: PostgreSQL cuts every identifier at this many bytes


def _open_lock_file(path):
    """Open <state_dir>/index.lock for flock without ever writing to it. An absent file is created empty
    (O_EXCL); an existing one is opened read-only, so a file that is not ours keeps its bytes. A symbolic
    link and anything but a regular file are refused (O_NONBLOCK: opening a FIFO does not hang)."""
    flags = os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | flags, 0o600)
    except FileExistsError:
        try:
            fd = os.open(path, os.O_RDONLY | flags)
        except OSError as exc:
            if exc.errno == errno.ELOOP:
                raise SystemExit("refusing to index: lock file %s is a symbolic link; move it away and run "
                                 "again" % path) from None
            raise
    if not stat.S_ISREG(os.fstat(fd).st_mode):
        os.close(fd)
        raise SystemExit("refusing to index: lock file %s is not a regular file; move it away and run again"
                         % path)
    return fd


def _flock_holder(fd):
    """The process id the kernel lists in /proc/locks for the flock on this file, or None (lock released
    in the meantime, or no /proc/locks). Linux only, like the supported platforms."""
    st = os.fstat(fd)
    dev = "%02x:%02x:%d" % (os.major(st.st_dev), os.minor(st.st_dev), st.st_ino)
    try:
        with open("/proc/locks") as f:
            for line in f:
                parts = line.split()
                if len(parts) >= 6 and parts[1] == "FLOCK" and parts[5] == dev:
                    return int(parts[4])
    except (OSError, ValueError):
        pass
    return None


def _take_flock(fd, path):
    """Take the flock, or exit naming the holder's process id. A holder the kernel no longer lists has
    released the lock between the two calls, so the flock is tried again (FLOCK_TRIES times)."""
    for _ in range(FLOCK_TRIES):
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return
        except BlockingIOError:
            holder = _flock_holder(fd)
            if holder:
                raise SystemExit("index already running: %s is held by process %d" % (path, holder)) from None
            time.sleep(0.05)
    # shortcut: reached only where /proc/locks lists no flock holder (no /proc, or a holder in another
    # PID namespace); replace if such a platform becomes supported.
    raise SystemExit("index already running: %s is held by another process; this system's lock table "
                     "(/proc/locks) does not name it" % path)


def _table_lock_names(cfg):
    """Every data table a run can create, rename or drop: the live table, the table a full run builds
    (_next) and the name the live table takes during the swap (_old)."""
    return [cfg.data_table, cfg.next_data_table, "data_%s_old" % cfg.table]


def _refuse_overlong_table_names(cfg):
    """PostgreSQL cuts an identifier at NAMEDATALEN - 1 = 63 bytes. A derived table name past that is
    stored under its first 63 bytes, which can be another config's table (data_<p>_next of one config
    and the live table of the config named <p>_nex), while the lock keys, hashed from the full names,
    differ. The relations named after the build table (index <t>_next_idx_1, key data_<t>_next_pkey,
    sequence data_<t>_next_id_seq) are cut too. store.swap_in reads each relation's stored name from the
    catalog and store._moved derives the new name from it by the table-name prefix, raising RuntimeError
    for a name that does not start with it, so the swap relies on every derived name keeping the pattern
    that PostgreSQL gives it when nothing is cut. The longest of all these is the sequence, so one check on
    it covers every derived name. Refuse such a table name before any lock, file or table is touched."""
    longest = "data_%s_next_id_seq" % cfg.table
    size = len(longest.encode())
    if size > PG_NAME_LIMIT:
        table_size = len(cfg.table.encode())
        raise SystemExit("refusing to index: the name %r derived from postgres.table is %d bytes and "
                         "PostgreSQL cuts names at %d, so another config's table could be the same table. "
                         "Use a postgres.table of at most %d bytes (this one is %d)"
                         % (longest, size, PG_NAME_LIMIT, PG_NAME_LIMIT - (size - table_size), table_size))


@contextmanager
def writer_lock(cfg):
    """Hold the index writer locks, or exit at once (SystemExit, status 1) when another run holds one:
    an exclusive flock on <state_dir>/index.lock (the docstore and state files), then one PostgreSQL
    session advisory lock per data table name the run can change (_table_lock_names), so two configs
    whose tables overlap never write at once. The key is the 64-bit hashtextextended of the name as
    PostgreSQL folds it, with no schema: runs whose search paths differ still agree on it, and the same
    name in two schemas, or a hash collision, only makes the runs refuse each other. A contender names
    the flock holder from the kernel's lock table. The operating system releases the flock and the
    server the advisory locks when the process dies. The lock session sets idle_session_timeout to 0: it
    stays idle for the whole run, and a server that ends idle sessions would release the advisory locks.
    A table name whose derived names PostgreSQL would cut is refused first (_refuse_overlong_table_names)."""
    _refuse_overlong_table_names(cfg)
    cfg.state_dir.mkdir(parents=True, exist_ok=True)
    path = cfg.state_dir / "index.lock"
    fd = _open_lock_file(path)
    try:
        _take_flock(fd, path)
        conn = store.connect(cfg)
        try:
            conn.autocommit = True   # the locks belong to the session; no transaction stays open
            with conn.cursor() as cur:
                cur.execute("SET idle_session_timeout = 0")
                for name in _table_lock_names(cfg):
                    cur.execute("select pg_try_advisory_lock(hashtextextended(lower(%s), 0))", (name,))
                    if not cur.fetchone()[0]:
                        raise SystemExit("index already running: table %s is locked by another index run"
                                         % name)
            yield
        finally:
            conn.close()   # ends the session, which releases the advisory locks
    finally:
        os.close(fd)   # releases the flock; the file is kept


def run_index(cfg, changed=False, log=print):
    """Index the corpus under writer_lock: while another index run holds it, exit at once. changed=True
    re-embeds only changed files in the live table. A full run builds cfg.next_table and swaps it in
    after the pipeline finishes, so search reads the live table until the swap: a failed run drops the
    new table, and a new table with no rows or under half the live rows is refused (SystemExit) and kept
    for inspection. Returns a summary dict."""
    with writer_lock(cfg):
        return _run_index(cfg, changed)


def _run_index(cfg, changed):
    started = time.time()
    entries, scan = corpus.enumerate_corpus(cfg)
    if not entries:
        raise SystemExit("refusing to index: the corpus scan found no files (would delete everything)")
    docs = make_documents(entries)
    if changed:
        vs = store.vector_store(cfg)
        if cfg.docstore_path.exists():
            docstore = SimpleDocumentStore.from_persist_path(str(cfg.docstore_path))
        else:
            docstore = SimpleDocumentStore()
        out_path = cfg.docstore_path
    else:
        store.drop_table(cfg, cfg.next_data_table)   # left by a refused run
        vs = store.vector_store(cfg, table=cfg.next_table)
        docstore = SimpleDocumentStore()
        out_path = cfg.next_docstore_path
    try:
        pipeline = build_pipeline(cfg, docs, vs, docstore)
        nodes = pipeline.run(documents=docs, show_progress=False)
        docstore.persist(str(out_path))
    except BaseException:
        if not changed:
            store.drop_table(cfg, cfg.next_data_table)
            out_path.unlink(missing_ok=True)
        raise
    if not changed:
        new_rows = store.row_count(cfg, cfg.next_data_table)
        live_rows = store.row_count(cfg, cfg.data_table)
        if new_rows == 0 or 2 * new_rows < live_rows:
            raise SystemExit(
                "refusing to swap: %s has %d rows, live %s has %d (the new table needs rows and at least half "
                "the live rows). The live table and docstore.json are unchanged; %s and docstore.next.json are "
                "kept for inspection. To drop the new table: %s"
                % (cfg.next_data_table, new_rows, cfg.data_table, live_rows, cfg.next_data_table,
                   drop_command(cfg)))
        store.swap_in(cfg)
        os.replace(out_path, cfg.docstore_path)
    duration = time.time() - started
    located = sum(1 for n in nodes if n.metadata.get("char_start", -1) >= 0)
    summary = {
        "mode": "changed" if changed else "full", "duration_s": round(duration, 1),
        "documents": len(docs), "chunks_embedded": len(nodes), "chunks_located": located,
        "chunks_per_min": round(len(nodes) / duration * 60) if nodes else 0,
        "skipped_rule": scan["skipped_rule"], "skipped_secret": scan["skipped_secret"],
        "no_rule": scan["counts"].get("no_rule", 0), "files_seen": scan["counts"]["seen"],
        "duplicates_collapsed": scan["counts"].get("duplicates_collapsed", 0),
    }
    store.write_state(cfg, last_index=summary, last_index_time=time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                      embedding_model=cfg.ollama["model"], embedding_digest=store.model_digest(cfg))
    return summary
