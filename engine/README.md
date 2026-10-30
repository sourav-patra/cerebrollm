# cerebrollm

A local retrieval tool for your own authoritative documents. It indexes Markdown by authority tier, searches it
(lexical, vector or both), and re-reads the source to confirm a quote before anyone states it. A plumb line checks
what is true.

Status: 0.1.0, early research. The measured results are in the repository root `README.md`.

Almost no new code. The pieces are LlamaIndex components configured in `cerebrollm.toml`:

| Job | Component |
|---|---|
| Split Markdown at headings | `MarkdownNodeParser`, then `TableRows` (one node per table data row) and `SentenceSplitter` for prose (800 tokens, 60 overlap) |
| Incremental index, deletes | `IngestionPipeline` with a persistent `SimpleDocumentStore`, strategy `UPSERTS_AND_DELETE` |
| Store, lexical and vector | `PGVectorStore` (Postgres 16 + pgvector 0.7.0), hybrid search on, English text search |
| Embeddings | `OllamaEmbedding`, model `qwen3-embedding:0.6b` (1024 dimensions) with the query prefix `[ollama] query_prefix`; `http://127.0.0.1:11434` |
| Retrieval, fusion | `VectorIndexRetriever` in `default` and `sparse` mode; reciprocal rank fusion in `cerebrollm/search.py` (the LlamaIndex formula, k = 60), so the lexical arm can take its own query |
| Filters | `MetadataFilters` on domain, status, project |

The glue is `cerebrollm/glue.py`: a `Document` whose hash ignores mtime, a step that merges a bare heading
into the section after it, a step that gives each Markdown table one node per data row, and a step that
records each chunk's title, heading path and character span. Everything else in `cerebrollm/` is the rules,
the corpus reader, the search and the four commands.

## Licences

| Dependency | Licence |
|---|---|
| PostgreSQL 16 (Postgres.app) and pgvector 0.7.0 | PostgreSQL licence (permissive) |
| llama-index-core, llama-index-vector-stores-postgres, llama-index-embeddings-ollama | MIT |
| ollama (Python client), Ollama | MIT |
| qwen3-embedding:0.6b model (Alibaba Qwen), the live embedding model | Apache-2.0 (`engine/models.toml`) |
| bge-m3 model (BAAI), the earlier embedding model, compared in the model study | MIT |
| SQLAlchemy, pgvector (Python), mcp, tiktoken | MIT |
| asyncpg, nltk | Apache-2.0 |
| psycopg2-binary | LGPL-3.0 with exceptions (used as a library, unmodified) |

Read from package metadata on 26 Oct 2026 for the Python packages (`importlib.metadata`); the PostgreSQL,
pgvector, Ollama and bge-m3 licences are as recorded in the plan.
`requirements.txt` pins every installed package.

psycopg2-binary is a separate dependency that pip installs unmodified; the cerebrollm wheel does not bundle it.
The PostgreSQL licence is permissive (BSD-style). Model licences apply to the models you pull; `models.toml` lists
only Apache-2.0 or MIT models as allowed.

## Setup

Follow the install section of the repository root `README.md`. On Ubuntu 24.04, `setup/root-ubuntu.sh` (needs sudo, run once by a person) installs the packages and `setup/user.sh` (no root, safe to re-run) creates the environment and the PostgreSQL cluster. Defaults: virtual environment `$HOME/.cerebrollm/venv`, PostgreSQL cluster `$HOME/.cerebrollm/pg16` with database `rag_local`, user `cerebrollm`, Unix socket `$HOME/.cerebrollm/pg16/sock`, port 54329, no TCP; Ollama with `qwen3-embedding:0.6b`; state in `$HOME/.cerebrollm`. Paths in `cerebrollm.toml` accept `~` and `$VARS`, and an unset variable stops the load with the key that uses it.

The configuration file is found in this order: `--config PATH`, the environment variable `CEREBROLLM_CONFIG`, then the copy that ships with the package (`python -c "from cerebrollm.config import DEFAULT_CONFIG; print(DEFAULT_CONFIG)"` prints its path; copy it, edit the `[[root]]` and `[[rule]]` entries and pass the copy with `--config`).

## Commands

`bin/cerebrollm` runs the venv's Python from a source checkout. After `pip install`, the `cerebrollm` command does the same; `python -m cerebrollm` works from `engine/`.

```
cerebrollm index [--changed]          # no flag: build <table>_next, then swap it in; --changed: re-embed only changed files
cerebrollm status                     # counts per tier and status, skips, last index, model and digest
cerebrollm search "QUESTION" [--k 8] [--mode lexical|vector|hybrid] [--all-status] [--project P] [--json]
cerebrollm verify PATH "QUOTE" [--ref REF]
cerebrollm ask "QUESTION" [--model gpt-oss:20b] [--think low|medium|high|off] [--no-rerank] [--json]
```

A full `cerebrollm index` builds the `<table>_next` table while search reads the live table, then swaps it in; a new table with no rows or under half the live rows is refused and kept, and the printed command drops it. `[ollama] query_prefix` (optional; set for Qwen3-Embedding) is put before each search query and never before documents. `[ollama] num_ctx = 8192` is sent to Ollama with each embed call; `cerebrollm status` prints it.

`search` defaults: mode hybrid, domain `org`, status `locked` or `current`, then the tier boost
(T1 x1.30, T2 x1.15, T3 x1.00, T4 x0.85, in `cerebrollm.toml`) applied to the fused score, then the
recency boost (`[search.recency]`, default weight 0.005: a document dated now gets at most 0.5 % more,
and the extra halves every 30 days of age; the date is the commit date or file date stored at index
time). `--all-status` removes the status filter and both boosts. Output is capped near 2,000 tokens
(4 characters per token). Hits with identical chunk text are shown once, the best-ranked; the other
paths are added to its `also_at`, and the list is filled to `k` with the next distinct hits. The lexical
arm gets the query with synonym alternatives appended (see Chunking, embedded text and synonyms). Each hit
shows rank, score, tier, status, path, line span, ref, project, heading path, sha256 prefix,
`also_at=[...]` when copies exist elsewhere, and text.
`SOURCE-CHANGED` is printed when the file on disk no longer matches the indexed sha256, in which
case the line span may be wrong.

`verify` re-reads the source (file, or `git show REF:PATH`), compares the quote with whitespace
normalised, and compares the sha256 with the indexed one: `OK`, `CHANGED` (quote present, file changed
since indexing), `MISSING` (quote absent), `GONE` (file absent). Exit 0 only for `OK`. One addition to
the four outcomes: `UNINDEXED` (quote present but the path is not in the index; exit 1). `PATH` may be
absolute or the relative path that `search` prints.

## ask

`cerebrollm ask` runs default search for the top 20, reranks them with the cross-encoder
`BAAI/bge-reranker-v2-m3` (Apache-2.0; folder and pinned revision in the `[reranker]` section of
`models.toml`; CUDA when visible, else CPU) to the top 8, and prompts the generator (`--model`, default
`gpt-oss:20b`; it must be an allowed chat model in `models.toml`, never a `-cloud` name) to quote one line
and cite its path as `"quote" [path]`. Every citation goes through `verify`. The answer is printed only when
at least one citation has code `OK` (a quote shorter than 8 characters is not a citation); otherwise the
output is exactly `Not in the sources.` An answer that is itself that phrase abstains even if it carries a
citation. A failure in search, rerank or generation prints an error on stderr and exits 2; it never prints an answer.
`--json` prints question, model, answer, abstained, citations (path, quote, verify code, detail), the reranked hits
(`search_rank`, `rerank_score`) and timings. The reranker is released before generation so the generator keeps the GPU memory.
Code: `cerebrollm/answer.py` (the gate is `decide`) and `cerebrollm/rerank.py`; tests in `tests/test_answer.py`.
Citation format limit: only `"quote" [path]` (or `[path:12]`, `[path#L12-30]`) counts; a `>` quote block does not.

## MCP server

`cerebrollm mcp` serves two tools over MCP on stdio: `search` and `verify`. It is read-only and exposes
no index, status or write tool. `search` takes `query`, `k`, `mode`, `all_status`, `project`, `page` and `rerank`
and returns one page of hits (`k` per page, default from `cerebrollm.toml`) capped at `token_budget`.
The result starts with a line stating that the text is retrieved data, each hit sits between
`<<<BEGIN RETRIEVED DATA>>>` and `<<<END RETRIEVED DATA>>>`, and the last line says whether another
page exists. `verify` takes `path`, `quote` and `ref` and returns the code and its detail line. When
Postgres or Ollama is down, a tool returns one line with the cause and the start command; the server
keeps running.

Register the server with an MCP host as a stdio server whose command is `cerebrollm mcp` (the host configuration is outside this repository).

## What is indexed

Only Markdown files that match a tier rule. A rule match is first-wins, in the order of
`cerebrollm.toml`.

| Tier | Status | Where (the rules shipped in `cerebrollm.toml`; edit them for your own folders) |
|---|---|---|
| T1 | locked | specification folders of a git repository (`docs/specs/**` at a fixed ref), a notes folder `locked/`, and `ADR-*` and `POLICY-*` files |
| T2 | current | top-level notes, `JOURNAL*` and `STATUS*` records, each project's `INDEX.md` |
| T3 | current | repository `README.md`, `AGENTS.md`, `docs/**/*.md`, and the public documentation folders the evaluation uses (`llama_index`, `ollama`, `pgvector`, `promptfoo`, `cerebrollm`) |
| T4 | draft | `drafts/**` |

A file that no rule matches is not indexed; there is no catch-all rule on purpose.

Never indexed: any path under `evidence/`, `runs/`, `run/`, `logs/`, `archive/`,
`.obsidian/`, or a directory starting `scratch`, `stage` or `sim`; any path under
`research/` (the evaluation's own plan and items; the
prefix is `path_prefixes` in `cerebrollm.toml` and is checked before any file is read); files ending
`.log`, `.json`, `.jsonl`, `.patch`, `.map`, `.lock`, `.sha256`; files named `GOLDEN-*` (the held-out
question set); symlinks; and any file the secret scan flags
(counted in `status`; the pattern list is `SECRET_PATTERNS` in `cerebrollm/rules.py`).

Supersession: files in the same root and directory whose names differ only by a revision token
(`rev16`, `r7`, `-r2`) or a date (`2026-10-24`, `18-oct`, `17-oct-2026`) form a family. Only the
member with the highest (revision, date) keeps its status; the others become `superseded`. Members
tied at the top all stay. Files whose name starts with `JOURNAL` are append-only daily records, not
revisions, so they never form a family. A file is also `superseded` when one of its first 30 lines
is a `Status:` line (any case) whose value starts with "superseded", or a line starting
`Superseded by`. A phrase inside another status value does not count:
`Status: current; individual details may be superseded by a later note` leaves the file `current`.
The rules are `rules.family`, `rules.apply_supersession` and `rules.status_line_superseded`;
`tests/test_rules.py` holds the tables.

Duplicates: files with the same sha256 are indexed once, under one path. The kept copy has the
highest authority (locked or current before draft before superseded, then the lower tier number),
then the folder that sorts last, so the newest lock folder wins among equal copies. The other paths
are listed in its metadata as `also_at`, written as `root:path`. Because authority comes before
folder order, a current T2 file with a copy under `drafts/` keeps its T2 entry rather than becoming a
draft. `rules.collapse_duplicates` holds the rule; `status` reports the number of copies collapsed.
Copies with different bytes but identical chunk text (two versions that share a section) are not collapsed
at index time; `search` shows that text once and lists the other path in `also_at`.

Recency: within a tier, newer documents get a small extra score: `1 + weight * 0.5 ** (age / half_life)`
with `weight` and `half_life_days` in `[search.recency]` of `cerebrollm.toml`. The weight is below the
step between adjacent hybrid ranks near the top of the list (about 0.5 to 0.8 %), so the boost
reorders near-ties and does not reverse a clearly better text match.

## Chunking, embedded text and synonyms

Table rows: a Markdown table (a line starting `|`, then a dashes separator line, then the lines starting
`|`) becomes one node per data row. The node text is `Document: <title>`, `Section: <heading path>` (when
the section has one), the table's header row and separator, then the row. The row's character span in the
document is the row alone. Prose between tables is split as before. Tables inside fenced code are prose.
`TableRows` in `cerebrollm/glue.py`, placed before the sentence splitter in `indexer.chunk_steps`.

Embedded text: each node is embedded with its `path`, `title` (first level-1 heading, else the file name)
and `heading_path` as metadata lines. Every other metadata key is excluded from the embedded text. The
displayed text is the node text only and never includes metadata; for a table row the title and
section are already in the node text, as above.

Synonyms: the `[synonyms]` table in `cerebrollm.toml` (PR = pull request, CI = continuous integration,
RC = release candidate, LLD = low level design, TRD = technical requirements, PRD = product requirements).
The lexical arm (`--mode lexical`, and the lexical half of `hybrid`) appends the
other side's words as OR alternatives: an abbreviation in the query adds its phrase, and a phrase adds its
abbreviation. Matching ignores case and a plural `s`. The vector arm embeds the query as written.
`expand_query` in `cerebrollm/search.py`.

## Tests

`python -m pytest -q` from `engine/`: rules, supersession and duplicate tables, the drafts
never-index rule checked through `corpus.enumerate_corpus` on a temp folder (the drafts folder is never
read), table rows, embedded text and span checks, synonyms, search-time collapse and fusion, recency and
output formatting, verify outcomes on a temp file, and one end-to-end run on a
fixture folder against the real Postgres (own table, dropped afterwards) and Ollama. Test scratch files
go under `$HOME/.cerebrollm/test-scratch`. The end-to-end test is skipped with a message if either is down.

## Known limits and not measured

- Retrieval quality is measured on 60 scored questions over public documentation (top 8 covers a quoted line for 45 of 60 with the default search, 46 of 60 with the reranker; `eval/runs/retrieval/R-summary.md`). It is not measured on other corpora.
- Not measured: the effect of the tier boost values, the chunk size choice, whether the merge of short sections helps, lexical-only recall on paraphrased questions, the effect of the recency weight.
- Not measured: behaviour above about 15,000 chunks (the query is an exact scan, no approximate index). The study corpus has 13,431 chunks and indexed in 9.7 minutes (`research/model-study/RESULTS.md`, R1).
- Family rule limits: only files in the same directory are compared. A second file that differs by a
  word (`-reviewed`, `-evening`) is a different family and does not supersede. Copies with identical
  bytes are collapsed by sha256 instead (see Duplicates); a copy that differs by one byte is indexed
  separately.
- Search collapses identical chunk text, so a section that two spec versions share is shown once. Two
  chunks that differ by a word are both shown.
- The date-without-year token (`18-oct`) is read as 2026.
- Lexical mode still embeds the query (the stock retriever does), so it needs Ollama.
- The lexical arm uses LlamaIndex's PGVectorStore sparse query, which ORs the query words with
  `ts_rank` ordering.
- `cerebrollm index` without `--changed` clears the table before rebuilding.
- The shipped `cerebrollm.toml` carries tier rules for the author's folder layout. Without edits it indexes only the public documentation folders listed above.
