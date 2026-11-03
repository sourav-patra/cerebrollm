# Changelog

Versions follow `pyproject.toml`. Each entry says whether a full `cerebrollm index` is needed after the upgrade.

## Unreleased

Documentation only; no re-index needed.

- README: a walk-through image, two figures (`docs/site/context.svg`, `docs/site/parts.svg`), a requirements table, an MCP setup section with host examples and a short results table with a documentation table pointing to the details. The full results and limits moved to `docs/RESULTS.md`, troubleshooting to `docs/TROUBLESHOOTING.md`, and the repository map and provenance to `docs/REPOSITORY.md`. The product page shows the same figures. The README follows the Entry pages rule: a problem section with one line of evidence, key features, and paragraphs of at most 60 words. `DOC-PHILOSOPHY.md` is updated from the shared copy, which adds that rule.
- Documentation rules now live where contributors look: a "Writing docs" section in `CONTRIBUTING.md`, one line in a new `AGENTS.md`, the README lint as `scripts/readme_lint.py` (version 7) and a `docs-lint` workflow that runs it on every pull request. `DOC-PHILOSOPHY.md` and its checksum file are removed. README headings are now Why, Features, Quick start and Docs.

## 0.1.0 (unreleased; the date is set when the owner tags it)

First public release. No earlier release exists, so no migration applies.

Added

- The `cerebrollm` command: `index` (table-swap rebuild or `--changed`), `search` (lexical, vector or hybrid with reciprocal-rank fusion, tier and recency boosts), `verify`, `status`, `ask` and `mcp`.
- `ask`: search top 20, cross-encoder rerank to 8, a local generator, verification of every citation, and an output gate that prints `Not in the sources.` unless a citation verifies `OK`.
- A read-only MCP server with the tools `search` (with a `rerank` option) and `verify`.
- Authority tiers (T1 to T4), status rules, supersession and duplicate collapse, a secret scan and never-index rules, all set in `cerebrollm.toml`.
- A model allow-list (`models.toml`) that admits only Apache-2.0 and MIT models and refuses names ending `-cloud`.
- Packaging: distribution `cerebrollm`, console script `cerebrollm`, optional extra `rerank` (sentence-transformers and torch), packaged default configuration.
- Evaluation scripts, public question sets (`eval/items.jsonl`, 70 items; `eval/items-v2.jsonl`, 35 public items), grading rules, raw run records and results (`eval/RESULTS.md`), and the model study results (`research/model-study/RESULTS.md`).
- Ubuntu setup scripts (`engine/setup/`), CI for the tests that need no PostgreSQL, Ollama or GPU, and a static product page (`docs/site/`).

Measured results are listed in `README.md` with their source files, including the v2 evaluation (`eval/RESULTS-v2.md`) and the Qwen3.6 rows (8,000-token prompt; the context ladder is not measured).

Status: early research. `ask` checks that a quote exists in the source, not that it answers the question; a relevance check is the first item proposed for 0.2. The aim of at least 90% right outcomes with under 2% confidently wrong runs is met by Claude Sonnet 5.5 with plain search and by no local model.

Skipped or not checked: the release date; the Qwen3.6 and GLM-4.7-Flash context ladder.
