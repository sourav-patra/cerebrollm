# Project plan

This plan says what cerebrollm is for, who it serves, and the order of work after 0.1.3. `RELEASE-MAP.md` stays the record of what each release holds. Every work item here is proposed and not measured until its acceptance check runs; the facts about today name their source.

## Position

cerebrollm is a retrieval tool an AI app or agent calls. It returns passages, checks a quote against the source file, and refuses when the check fails. It is a fixed pipeline. It does not plan or loop.

What sets it apart is the evidence rule: every number names a file in this repository or says that its run records are not committed, failed runs are committed too, and limits sit next to the claims they qualify.

## Who it serves

| Reader | Served today | Blocked by |
|---|---|---|
| A person who runs local models on Linux with Markdown notes | yes | nothing; the fresh-machine install is not re-checked |
| A developer who gives an agent a `search` and `verify` tool over MCP (Model Context Protocol, the tool interface AI apps use) | yes | nothing |
| A small team with PDF and Word documents | no | only Markdown is indexed |
| A team with a corpus far above 15,000 chunks | no | exact scan (every stored vector is compared with the query); larger sizes are not measured |
| A developer on macOS or native Windows | unknown | both are untested |
| A tool that calls web services | no | there is no HTTP API (a web interface other programs can call) |

## What we do not say yet

- "Agentic": the engine is a tool for agents, and the documents say so.
- A corpus size above the measured 13,627 chunks (`docs/RESULTS.md`, from `eval/runs/retrieval/R-summary.json`). A size claim follows the scale ladder below, and names the largest step that ran.
- "Meets the aim": no local model reaches 90% right outcomes with under 2% confidently wrong runs (`eval/RESULTS-v2.md`).

## Phase 0: launch readiness

| Item | Acceptance check | Who |
|---|---|---|
| Product page with evidence links and a not-claimed table | the page deploys and every evidence link opens signed out | owner merges |
| Fresh-machine quick start | every README quick-start step run on a clean Ubuntu 24.04 or WSL2 instance; log committed under `docs/evidence/` | owner's machine |
| Community files | `CODE_OF_CONDUCT.md` and three issue templates render on GitHub | done when merged; owner sets the conduct contact |
| Sidebar | a social preview image is set and Discussions is on | owner, in Settings |
| 0.2 items filed as issues | one issue per item in `RELEASE-MAP.md`, each with its acceptance check | owner or agent |
| Launch post | posted after the fresh-machine log is committed | owner |

## Phase 1: release 0.2, answer quality

These are the three items already in `RELEASE-MAP.md`. They come first because they are the project's main claim.

1. A relevance check, so a real quote from an unrelated passage no longer passes the gate.
2. `ask` prints only verified quotes, counts a citation only when its path is among the 8 retrieved hits, and shows the generator's own text only on request.
3. A second public item set large enough to bound a 2% confidently wrong rate.

## Phase 2: reach more readers

Phases 2 and 3 extend the "Later" list of `RELEASE-MAP.md`; an item moves into `RELEASE-MAP.md` when a release is planned for it.

| Item | Acceptance check |
|---|---|
| One-command setup with Docker Compose for PostgreSQL and pgvector (the PostgreSQL extension that stores the vectors) | the quick start runs on a clean machine with Docker and no `sudo` script; log committed |
| macOS and native Windows | the quick start and `engine/tests` run on each; logs committed |
| More file types, PDF first | a public PDF item set; `verify` confirms quotes against the extracted text and names the page |
| HTTP API for `search`, `verify` and `ask` | the same test cases as the MCP server pass over HTTP; it listens only on this machine (loopback) by default |
| Example n8n workflow (n8n is a workflow automation tool) | the workflow in `docs/` runs against the HTTP API |

## Phase 3: scale, measured in steps

Search scans every vector today. The work is an approximate index in pgvector, batched and resumable indexing, and a ladder of measurements.

| Step | Acceptance check |
|---|---|
| Approximate index (HNSW, a graph index that compares the query with a fraction of the vectors) behind a configuration switch | recall in the top 8 (the share of the exact scan's top 8 it also returns) on the 60 scored questions, same corpus; table committed |
| Scale ladder | at each rising corpus size on public text: indexing time, index size on disk, query latency and top-8 recall; one row per step in `docs/RESULTS.md` |
| Resumable indexing | an `index` run stopped part way finishes on restart without re-embedding finished files |

The README then states the largest step that ran. Corpus sizes for the ladder are not chosen here; hardware offered through a "Propose or fund a measurement" issue decides how far it goes.

## Funding

1. GitHub Sponsors on the owner's account, with `.github/FUNDING.yml` added after approval.
2. "Fund a measurement": a sponsor pays for one acceptance check in this plan. The output is committed whether the result is good or bad. The issue template `measurement.yml` takes these offers.
3. Hardware time from companies whose tools the engine depends on, for the scale ladder.
4. Grants for small local-first projects, applied for after Phase 1.

## Order and its reason

Phase 1 comes before Phases 2 and 3. More file types and more scale multiply the number of answers; the gate's known gaps should close first.

Skipped or not checked: dates and effort for every item, the sizes of the scale ladder, whether GitHub Sponsors is available for the owner's account, and every acceptance check named above.
