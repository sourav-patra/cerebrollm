"""cerebrollm index: LlamaIndex IngestionPipeline over the enumerated corpus."""
import os
import sys
import time
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


def run_index(cfg, changed=False, log=print):
    """Index the corpus. changed=True re-embeds only changed files in the live table. A full run builds
    cfg.next_table and swaps it in after the pipeline finishes, so search reads the live table until the
    swap: a failed run drops the new table, and a new table with no rows or under half the live rows is
    refused (SystemExit) and kept for inspection. Returns a summary dict."""
    started = time.time()
    entries, scan = corpus.enumerate_corpus(cfg)
    if not entries:
        raise SystemExit("refusing to index: the corpus scan found no files (would delete everything)")
    docs = make_documents(entries)
    cfg.state_dir.mkdir(parents=True, exist_ok=True)
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
