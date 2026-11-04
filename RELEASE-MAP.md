# Release map

0.1.1 is the current release: 0.1.0 with the `verify` and `search` fixes below, early research and built and measured as far as `README.md` states. Everything under 0.2 and later is proposed and not measured; an item moves into a release only when its acceptance check runs.

## 0.1.1 (contents)

| Area | What changed | Evidence |
|---|---|---|
| `verify` | an excluded or secret-bearing file answers as an absent quote; an empty quote answers `MISSING`; a git `ref` that git could read as an option, or that names no commit, is refused | `engine/tests/test_verify.py` |
| `search` | a hit or copy whose root is gone or whose path is excluded is dropped | `engine/tests/test_search.py` |
| Engine tests | 134 passed, 6 skipped without PostgreSQL and Ollama | `engine/tests` |

## 0.1.0 (contents)

| Area | What ships | Evidence |
|---|---|---|
| Engine | `index`, `search`, `verify`, `status`, `ask`, `mcp`; tiers, status, supersession, secret scan | `engine/tests` (113 passed, 6 skipped without PostgreSQL and Ollama) |
| Answer gate | prints an answer only with an `OK` citation, else `Not in the sources.` | `engine/tests/test_answer.py`, `docs/site/ask-flow.svg` |
| Retrieval | hybrid search; optional reranker | `eval/runs/retrieval/R-summary.md` |
| Models | allow-list of Apache-2.0 and MIT models; default `qwen3-embedding:0.6b` and `gpt-oss:20b` | `research/model-study/RESULTS.md` |
| Evaluation | public item sets, grading rules, raw records | `eval/RESULTS.md` |
| Answer quality | v2 evaluation: 35 public items, plain search and `ask` per model; aim met by one hosted model only | `eval/RESULTS-v2.md` |
| Packaging | wheel and sdist, console script, `rerank` extra | `pyproject.toml` |

## 0.2 (proposed, not measured)

Each item has one acceptance check; none has run.

1. A relevance check: `ask` accepts a verified quote only when the quote answers the question, so a real quote from an unrelated passage no longer passes the gate.
2. `ask` prints only the verified quotes, counts a citation only when its path is among the 8 retrieved hits, and shows the generator's own text only on request.
3. The engine refuses a non-loopback Ollama address unless the user allows it.
4. The reranker weights are hashed when they load.
5. The MCP `search` tool caps `k` and `page`.
6. A second public item set large enough to bound a 2% confidently-wrong rate, and a report that prints the bound.
7. A network capture check for `index`, `search` and `ask`.
8. `status` reports the mode of the PostgreSQL socket folder.

## Later (proposed, not measured)

- Accept `path (lines a-b)` as a citation suffix.
- Test the search input sanitiser and the parameterised SQL path.
- Platform checks on macOS and native Windows (untested today).

## How a proposed item becomes measured

Run its acceptance check, save the output under `eval/runs/` or `engine/tests/`, and move the row into the release table with the file name.

Skipped or not checked: the acceptance checks of every proposed item; sizes and dates are not estimated here.
