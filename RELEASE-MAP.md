# Release map

0.1.0 ships as early research and is built and measured as far as `README.md` states. Everything under 0.2 and later is proposed and not measured; an item moves into a release only when its acceptance check runs.

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
2. `verify` returns the same result for an excluded or secret-bearing file as for an absent quote, so it cannot confirm that such a file exists.
3. `ask` prints only the verified quotes, counts a citation only when its path is among the 8 retrieved hits, and shows the generator's own text only on request.
4. `verify` and the MCP tool refuse a git `ref` that git could read as an option.
5. The engine refuses a non-loopback Ollama address unless the user allows it.
6. The reranker weights are hashed when they load.
7. The MCP `search` tool caps `k` and `page`.
8. A second public item set large enough to bound a 2% confidently-wrong rate, and a report that prints the bound.
9. A network capture check for `index`, `search` and `ask`.
10. `status` reports the mode of the PostgreSQL socket folder.

## Later (proposed, not measured)

- Accept `path (lines a-b)` as a citation suffix.
- Test the search input sanitiser and the parameterised SQL path.
- Platform checks on macOS and native Windows (untested today).

## How a proposed item becomes measured

Run its acceptance check, save the output under `eval/runs/` or `engine/tests/`, and move the row into the release table with the file name.

Skipped or not checked: the acceptance checks of every proposed item; sizes and dates are not estimated here.
