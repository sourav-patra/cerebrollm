"""cerebrollm search: LlamaIndex retrievers over the Postgres store, reciprocal rank fusion, tier and
recency boosts, synonym alternatives for the lexical arm, and one hit per distinct chunk text."""
import datetime
import hashlib
import json
import re

from llama_index.core import VectorStoreIndex
from llama_index.core.schema import NodeWithScore
from llama_index.core.vector_stores.types import (
    FilterOperator, MetadataFilter, MetadataFilters, VectorStoreQueryMode)

from . import corpus, store

ACTIVE_STATUS = ["locked", "current"]
TSQUERY_OPERATORS = re.compile(r"[&|!():*<>'\"\\]")
WORD = re.compile(r"[a-z0-9]+")
RRF_K = 60.0


def _filters(cfg, all_status, project):
    items = [MetadataFilter(key="domain", value=cfg.domain)]
    if not all_status:
        items.append(MetadataFilter(key="status", value=ACTIVE_STATUS, operator=FilterOperator.IN))
    if project:
        items.append(MetadataFilter(key="project", value=project))
    return MetadataFilters(filters=items)


def _line_span(cfg, meta):
    """(first line, last line, source_matches_index) computed from the character span."""
    start, end = meta.get("char_start", -1), meta.get("char_end", -1)
    if start < 0:
        return None, None, None
    root = next((r for r in cfg.roots.values() if r["ref"] == meta["ref"]), None)
    try:
        data = corpus.read_source(root, meta["path"], meta["ref"])
    except (FileNotFoundError, PermissionError, AttributeError, TypeError):
        return None, None, None
    text = data.decode("utf-8", "replace")
    first = text.count("\n", 0, start) + 1
    last = text.count("\n", 0, max(end - 1, start)) + 1
    return first, last, hashlib.sha256(data).hexdigest() == meta["sha256"]


def sanitize(query):
    """The query with tsquery operators removed and words single-spaced."""
    return " ".join(TSQUERY_OPERATORS.sub(" ", query).split())


def expand_query(query, synonyms):
    """The lexical query with synonym alternatives appended. The lexical arm ORs the query words, so
    an alternative is extra words. An abbreviation in the query adds its phrase; a phrase in the query
    adds its abbreviation. Matching ignores case, and a plural "s" is allowed on the abbreviation or
    the last word of the phrase."""
    low = query.lower()
    words = set(WORD.findall(low))
    extra = []
    for abbr, phrase in synonyms.items():
        a = abbr.lower()
        if a in words or a + "s" in words:
            extra.append(phrase)
        if re.search(r"(?<![a-z0-9])" + re.escape(phrase.lower()) + r"s?(?![a-z0-9])", low):
            extra.append(abbr)
    return query + " " + " ".join(extra) if extra else query


def rrf_fuse(lists, k=RRF_K):
    """Reciprocal rank fusion of ranked hit lists with the formula of LlamaIndex's QueryFusionRetriever:
    each list adds 1 / (rank + k), rank counted from 0. Returns NodeWithScore items, best first."""
    scores, first = {}, {}
    for hits in lists:
        for rank, h in enumerate(sorted(hits, key=lambda x: x.score or 0.0, reverse=True)):
            nid = h.node.node_id
            first.setdefault(nid, h)
            scores[nid] = scores.get(nid, 0.0) + 1.0 / (rank + k)
    return [NodeWithScore(node=first[nid].node, score=s)
            for nid, s in sorted(scores.items(), key=lambda x: -x[1])]


def recency_multiplier(mtime, now, weight, half_life_days):
    """Score multiplier for a document dated `mtime` (ISO 8601: its commit date or file date).

    1 + weight * 0.5 ** (age in days / half_life_days): a document dated now gets at most `weight`
    extra, and the extra halves every half_life_days. A future date counts as age 0. A missing or
    unreadable date gives 1.0, so the document keeps its score.
    """
    if not mtime:
        return 1.0
    try:
        when = datetime.datetime.fromisoformat(mtime)
    except ValueError:
        return 1.0
    if when.tzinfo is None:
        when = when.replace(tzinfo=datetime.timezone.utc)
    age_days = max((now - when).total_seconds() / 86400.0, 0.0)
    return 1.0 + weight * 0.5 ** (age_days / half_life_days)


def copy_key(meta):
    """The "root:path" form used in also_at; the bare path when the root is unknown."""
    root, path = meta.get("root"), meta.get("path")
    return "%s:%s" % (root, path) if root else path


def distinct_by_text(ranked, k):
    """The first k hits whose chunk text is distinct, best first. A later hit with the same text is
    not shown: its own key and any copies it has go into the kept hit's also_at."""
    kept, by_text = [], {}
    for o in ranked:
        text = o["node"].get_content()
        if text in by_text:
            entry = by_text[text]
            kept_key = copy_key(entry["item"]["meta"])
            for p in [copy_key(o["meta"])] + list(o["meta"].get("also_at") or []):
                if p != kept_key and p not in entry["also_at"]:
                    entry["also_at"].append(p)
            continue
        entry = {"item": o, "also_at": list(o["meta"].get("also_at") or [])}
        by_text[text] = entry
        kept.append(entry)
        if len(kept) == k:
            break
    return kept


def run_search(cfg, query, k=None, mode=None, all_status=False, project=None, synonyms=None):
    """Return a list of hit dicts, best first, with distinct chunk text."""
    query = sanitize(query)   # PGVectorStore ORs the words into to_tsquery
    if not query:
        return []
    k = k or cfg.search["default_k"]
    mode = mode or cfg.search["default_mode"]
    fetch = max(k * cfg.search["fetch_factor"], 40)
    index = VectorStoreIndex.from_vector_store(store.vector_store(cfg), embed_model=store.embed_model(cfg))
    filters = _filters(cfg, all_status, project)
    use_synonyms = cfg.search.get("synonyms_enabled", False) if synonyms is None else synonyms
    lexical_query = expand_query(query, cfg.synonyms) if use_synonyms else query

    def retriever(qmode, top_k):
        return index.as_retriever(similarity_top_k=top_k, vector_store_query_mode=qmode, filters=filters)

    if mode == "vector":
        hits = retriever(VectorStoreQueryMode.DEFAULT, fetch).retrieve(query)
    elif mode == "lexical":
        hits = retriever(VectorStoreQueryMode.SPARSE, fetch).retrieve(lexical_query)
    elif mode == "hybrid":
        hits = rrf_fuse([retriever(VectorStoreQueryMode.DEFAULT, fetch).retrieve(query),
                         retriever(VectorStoreQueryMode.SPARSE, fetch).retrieve(lexical_query)])
    else:
        raise ValueError("mode must be lexical, vector or hybrid")

    boost = cfg.search["tier_boost"]
    recency = cfg.search["recency"]
    now = datetime.datetime.now(datetime.timezone.utc)
    out = []
    for h in hits:
        meta = h.node.metadata
        score = h.score or 0.0
        if not all_status:
            score *= boost.get(meta.get("tier"), 1.0)
            score *= recency_multiplier(meta.get("mtime"), now, recency["weight"],
                                        recency["half_life_days"])
        out.append({"score": score, "node": h.node, "meta": meta})
    out.sort(key=lambda x: -x["score"])
    results = []
    for rank, entry in enumerate(distinct_by_text(out, k), 1):
        o = entry["item"]
        meta = o["meta"]
        first, last, fresh = _line_span(cfg, meta)
        results.append({
            "rank": rank, "score": round(o["score"], 5), "tier": meta.get("tier"),
            "status": meta.get("status"), "project": meta.get("project"), "path": meta.get("path"),
            "ref": meta.get("ref"), "title": meta.get("title"), "heading_path": meta.get("heading_path", ""),
            "line_start": first, "line_end": last, "source_unchanged": fresh,
            "sha256": meta.get("sha256"), "mtime": meta.get("mtime"), "also_at": entry["also_at"],
            "text": o["node"].get_content(),
        })
    return results


TRUNCATED = " [...]"


def cap_text(results, budget_tokens, overhead_chars=0):
    """Trim each chunk text so the whole output stays within the token budget (4 chars/token).

    The header of each hit is measured as format_hits prints it (with an empty text), so long paths
    and heading paths are counted. overhead_chars is any other fixed text the caller prints (a wrapper
    line, markers, a page line). What is left is shared equally by the hits; each keeps at least 200
    chars of text, so a page of very long headers can still exceed the budget."""
    if not results:
        return results
    headers = sum(len(format_hits([dict(r, text="")])) for r in results)
    share = (budget_tokens * 4 - overhead_chars - headers) // len(results)
    per = max(200, share)
    for r in results:
        if len(r["text"]) > per:
            r["text"] = r["text"][:per - len(TRUNCATED)].rstrip() + TRUNCATED
            r["truncated"] = True
    return results


def format_hits(results):
    lines = []
    for r in results:
        span = "L%s-%s" % (r["line_start"], r["line_end"]) if r["line_start"] else "L?"
        stale = "" if r["source_unchanged"] in (None, True) else " SOURCE-CHANGED"
        also = " also_at=[%s]" % ", ".join(r["also_at"]) if r.get("also_at") else ""
        lines.append("#%d score=%.4f %s %s %s %s@%s %s %s sha=%s%s%s" % (
            r["rank"], r["score"], r["tier"], r["status"], r["path"], span, r["ref"],
            r["project"], "| " + r["heading_path"] if r["heading_path"] else "",
            (r["sha256"] or "")[:12], also, stale))
        lines.append(r["text"].strip())
        lines.append("")
    return "\n".join(lines)


def to_json(results):
    return json.dumps(results, indent=2, ensure_ascii=False)
