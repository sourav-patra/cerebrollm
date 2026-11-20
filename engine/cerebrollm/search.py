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

from . import corpus, rules, store

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


DATE_TIME = re.compile(r"[0-9]{4}-?[0-9]{2}-?[0-9]{2}T")   # the only date-time separator accepted is T


def _bare_date(text):
    try:
        return datetime.date.fromisoformat(text)
    except ValueError:
        return None


def parse_instant(text, upper=False):
    """(instant, exclusive) for an ISO 8601 date or date-time. A bare date is midnight UTC; with
    upper=True it is the end of that day, given as the next midnight UTC with exclusive=True (the last
    representable day is given as its final microsecond, not exclusive). A date-time needs the separator
    T; without an offset it is UTC. Raises ValueError("Invalid date ...") on any other input."""
    text = (text or "").strip()
    day = _bare_date(text)
    try:
        if day is not None:
            start = datetime.datetime(day.year, day.month, day.day, tzinfo=datetime.timezone.utc)
            if not upper:
                return start, False
            try:
                return start + datetime.timedelta(days=1), True
            except OverflowError:   # 9999-12-31: no next midnight exists
                return datetime.datetime.max.replace(tzinfo=datetime.timezone.utc), False
        if not DATE_TIME.match(text):
            raise ValueError(text)
        when = datetime.datetime.fromisoformat(text)
    except (ValueError, OverflowError):
        raise ValueError("Invalid date %r: use an ISO 8601 date or date-time, e.g. 2026-01-31 or "
                         "2026-01-31T09:30:00+05:30." % text) from None
    if when.tzinfo is None:
        when = when.replace(tzinfo=datetime.timezone.utc)
    return when, False


def parse_scope(since=None, until=None):
    """(since, until, until_exclusive): the parsed bounds, each None when not given (None is the only
    value that means not given; an empty string is an invalid date). Raises ValueError("Invalid
    date ...") for a bad date or a since that falls after the whole until range."""
    lower = parse_instant(since)[0] if since is not None else None
    upper, exclusive = parse_instant(until, upper=True) if until is not None else (None, False)
    if lower is not None and upper is not None and (lower >= upper if exclusive else lower > upper):
        raise ValueError("Invalid date range: since %r is after until %r." % (since, until))
    return lower, upper, exclusive


def _like_escape(text):
    return text.replace("\\", "\\\\").replace("%", r"\%").replace("_", r"\_")


def _prefix(path_prefix):
    """The path prefix without one trailing "/"."""
    prefix = path_prefix or ""
    return prefix[:-1] if prefix.endswith("/") else prefix


def in_scope(path, mtime, prefix, lower, upper, exclusive):
    """True when a document with this root-relative path and stored mtime (ISO 8601 text) lies under
    the prefix and inside the date range; the one definition both the lookup and the hit check use.
    A missing or unreadable mtime never satisfies a date bound."""
    if prefix and not (path == prefix or path.startswith(prefix + "/")):
        return False
    if lower is None and upper is None:
        return True
    try:
        when = datetime.datetime.fromisoformat(mtime)
    except (TypeError, ValueError):
        return False
    if when.tzinfo is None:
        when = when.replace(tzinfo=datetime.timezone.utc)
    if lower is not None and when < lower:
        return False
    if upper is not None and (when >= upper if exclusive else when > upper):
        return False
    return True


def scope_doc_ids(cfg, all_status, project, path_prefix=None, since=None, until=None):
    """The document ids (the ref_doc_id stored with every chunk: domain, project, ref and path, unique
    per document) of the indexed documents under the path prefix and inside the date range that the
    other filters (domain, status, project) allow, sorted. One direct query on the live data table
    fetches the candidates, narrowed by the prefix at a path-segment boundary; the dates are then
    compared in Python as instants, so offsets that name the same instant compare equal and a stored
    mtime that cannot be read excludes only its own document."""
    lower, upper, exclusive = parse_scope(since, until)
    prefix = _prefix(path_prefix)
    where, args = ["metadata_->>'domain' = %s"], [cfg.domain]
    if not all_status:
        where.append("metadata_->>'status' = any(%s)")
        args.append(ACTIVE_STATUS)
    if project:
        where.append("metadata_->>'project' = %s")
        args.append(project)
    if prefix:
        where.append(r"(metadata_->>'path' = %s or metadata_->>'path' like %s escape '\')")
        args += [prefix, _like_escape(prefix) + "/%"]
    sql = ("select distinct metadata_->>'ref_doc_id', metadata_->>'path', metadata_->>'mtime' from %s where %s"
           % (cfg.data_table, " and ".join(where)))
    with store.sql(cfg) as cur:
        cur.execute(sql, args)
        rows = cur.fetchall()
    return sorted({doc_id for doc_id, path, mtime in rows
                   if doc_id and path and in_scope(path, mtime, prefix, lower, upper, exclusive)})


def _in_value(text):
    """A value as the text of a PGVectorStore IN filter, which pastes it between single quotes into a
    sqlalchemy text() clause: a quote is doubled and a colon is escaped so it is not read as a bind
    parameter."""
    return text.replace("'", "''").replace(":", r"\:")


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


def _allowed(cfg, key):
    """True for an also_at key ("root:path") of a configured root whose path the index may hold."""
    name, _, path = key.partition(":")
    return (name in cfg.roots and not rules.never_reason(path, cfg.never)
            and rules.classify(name, path, cfg.rules) is not None)


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


def run_search(cfg, query, k=None, mode=None, all_status=False, project=None, synonyms=None,
               path_prefix=None, since=None, until=None):
    """Return a list of hit dicts, best first, with distinct chunk text. path_prefix, since and until
    (strings, see parse_instant and scope_doc_ids) restrict both retrieval arms before the candidate
    limit; no document in scope gives no hits."""
    scope_range = parse_scope(since, until)   # a bad date fails before anything else runs
    scope_prefix = _prefix(path_prefix)
    query = sanitize(query)   # PGVectorStore ORs the words into to_tsquery
    if not query:
        return []
    k = k or cfg.search["default_k"]
    mode = mode or cfg.search["default_mode"]
    fetch = max(k * cfg.search["fetch_factor"], 40)
    index = VectorStoreIndex.from_vector_store(store.vector_store(cfg), embed_model=store.embed_model(cfg))
    filters = _filters(cfg, all_status, project)
    scoped = bool(path_prefix) or since is not None or until is not None
    if scoped:
        doc_ids = scope_doc_ids(cfg, all_status, project, path_prefix, since, until)
        if not doc_ids:
            return []
        filters.filters.append(MetadataFilter(key="ref_doc_id", value=[_in_value(d) for d in doc_ids],
                                              operator=FilterOperator.IN))
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
        # the lookup and the retrieval are separate queries: a full index swap between them could bring
        # in a row of the new table whose date or path differs from the one admitted, so each hit is
        # checked again (at worst a search during a swap returns fewer hits, never an out-of-scope one)
        if scoped and not in_scope(meta.get("path") or "", meta.get("mtime"), scope_prefix, *scope_range):
            continue
        # shortcut: a stale row whose root, tier rule or never-index rule no longer allows its path is dropped with
        # its copies; promoting a copy needs its own supersession status and ref, which the row does not hold.
        # A re-index restores an allowed copy.
        if not _allowed(cfg, copy_key(meta)):
            continue
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
            "sha256": meta.get("sha256"), "mtime": meta.get("mtime"),
            "also_at": [k for k in entry["also_at"] if _allowed(cfg, k)],
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
