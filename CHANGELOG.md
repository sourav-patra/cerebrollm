# Changelog

Versions follow `pyproject.toml`. Each entry says whether a full `cerebrollm index` is needed after the upgrade.

## Unreleased

Evaluation only. No re-index needed.

- `engine/models.toml` allows `qwen3.5:9b` and `qwen3.8:27b` as chat models (Apache-2.0). `eval/run_v2.py` uses `qwen3.5-9b` (thinking off) as the v3 generator. `grade --judge` and `report --judge` take `qwen3.8:27b` (the v3 grader), `qwen3.6:35b-a3b-coding-mtp-q4_K_M` and `qwen3.5:9b` besides the earlier two, all with thinking off; `report` without `--judge` uses the item set's grader (`gpt-oss:20b` for v2, so its output is unchanged). Of the three new graders only `qwen3.8:27b` and `qwen3.6:35b-a3b-coding-mtp-q4_K_M` passed the five v3 canary answers on 2026-11-20; `qwen3.5:9b` accepted a wrong answer.
- A second public question set, `eval/items-v3.jsonl`: 163 items over the release notes of three open-source projects (Ruff, uv, pydantic; 68 saved files from 2026-07-06 to 2026-11-19) with 50 exact, 35 paraphrase, 14 stale and 64 unanswerable items. With no confidently wrong item the report prints 1.8% (3 / 163) as the rule-of-three upper bound, under the 2% target; the 35-item v2 set prints 8.6%. The figure assumes independent draws of items, which this hand-drafted set does not meet, so it is not a bound on a population rate (`eval/ITEMS-v3.md`). Every quote is checked present by `eval/check_items_v2.py --set v3`; `eval/ITEMS-v3.md` describes the set, its limits and the commands that run it.
- The counts that were fixed at 35, 20 and 15 in `eval/check_items_v2.py` and `eval/report_v2.py` are settings of each item set (`eval/itemset-v2.toml`, `eval/itemset-v3.toml`, read by `eval/itemset.py`). `run_v2.py`, `check_items_v2.py` and `verify_v2_sources.py` take `--set NAME`; the v2 report is byte-identical to before, checked against a saved report of a synthetic run. The checker also fails on a duplicate question. New run records and grade rows carry the set name, and a run folder that holds records of another set is refused (records made before this carry none and count as v2). `--set` wins over a stale `CEREBROLLM_ITEMSET`.
- `eval/itemset_config.py` writes a config for a set's own corpus folder (`$HOME/cerebrollm-corpus-NAME`), table (`chunks_NAME`) and state folder, with the rules the v3 source folders need, so a benchmark never writes into the corpus the shipped config indexes. It writes only under the repository or `$HOME/.cerebrollm`, through an exclusively created temporary file, and replaces an existing file only with `--force`. `verify_v2_sources.py` sends the optional GitHub token to https://api.github.com only, drops it from every redirect, and fails on a missing or empty sources folder.
- `run_v2.py` binds a run folder to its item set (`itemset.json`) before `prepare`, `gen` or `grade`. `grade` first grades the set's canary answers and records the result; `sample` draws a random sample of graded answers for a hand check; `report --retrieval-only` prints the saved-search coverage on its own, and a plain `report` fails when nothing is graded. For a set with a target, the report prints `not claimed (reason)` unless the canary check passed and a hand check of at least 30 graded answers found no disagreement.
- The canary record and `handcheck.json` count only for the grades they name: the item set, the grader, its model digest and the sha256 of its grades file, all of which `sample` prints. The report also checks that the canary record holds every configured canary with the expected verdict. `run_v2.py` refuses a run folder outside the repository and `$HOME/.cerebrollm` before it writes; the v3 runbook now uses `~/.cerebrollm/runs/v3-qwen`. Sets other than v2 run and grade only on local Ollama models. The `itemset.json` marker is installed in one exclusive step, and a process that loses the race checks the installed one. `itemset_config.py` refuses source folder names it cannot write into a rule, and parses the config before installing it. The v3 staging commands stop at the first failing step. The v3 overlap test compares with the v2 set only.
- The report's target gate accepts `handcheck.json` only with a non-empty `reviewer` and `"reviewer_kind": "person"` (`sample` prints both fields; the declaration is the writer's own), and the report reads the grades file once, so the tables, the digest and the grades hash come from the same batch; `sample` does the same for its rows and the evidence it prints. The report also says "missing retrieval records" when every record is missing, which changes a report of a run with no saved searches (the v2 saved reports in `eval/testdata` were regenerated for it); a report with all records present is unchanged. The guide's count of stale items that share one question shape is corrected to 8 of 14.

## 0.2.0

`ask` prints only what `verify` confirmed. No re-index needed.

- `verify` matches a quote that contains any link or URL syntax (a Markdown link or image, an autolink, an HTML link, `://`, `www.`, `mailto:`) only when it occurs in the file exactly, whitespace aside. Before, such a quote could match with link destinations and markup dropped, so a link the model added or changed could print inside a verified `ask` answer.
- `setup/root-ubuntu.sh` leaves a PostgreSQL service unit that existed before it, running or stopped, exactly as it was; it stops and disables the packaged service only when its own install created it. Before, it stopped and disabled any packaged PostgreSQL service.
- `ask` prints the verified quotes, one `"quote" [path]` line each, in place of the generator's whole text; the generator's own text prints only with the new `--show-text`, after an `Unverified text:` line. `--json` keeps the verified quotes in `answer` and gains `show_text` and `generator_text`, which is null unless `--show-text` is given (LLD issue I-02).
- A citation counts only when its path, with `.` and `..` resolved, is among the 8 passages the generator saw; any other path, or one that leaves the root, gets the code `NOT_RETRIEVED` and `verify` is not run (I-02).
- `python3 eval/run_v2.py` takes `--out DIR` for generation, grading and report, and stores the engine commit in each A4 record as `meta.engine_commit`. With `--out`, the report writes `DIR/summary.json` and `DIR/RESULTS.md` and leaves `eval/RESULTS-v2.md` alone.

Measured on the 35-item v2 set with `gpt-oss:20b` (thinking medium, 3 runs per item, graded by `gpt-oss:20b`, one machine): right outcomes 33 of 35, the same as 0.1.2; correct answerable runs 54 of 60 (was 56); confidently wrong runs 2 of 105 (was 0). The 0.1.2 figures here come from a rerun of 0.1.2 (commit 56f13e0) on the same machine, index and grader as this measurement; the 0.1.2 entry below reports an earlier run, 3 of 105. One confidently wrong run (G2-EX-05 run 1) is an incomplete answer: one of three required types was a verified quote. The other (G2-EX-03 run 3) is wrong: asked for the context window of one model, it printed the verified line "24-48 GiB VRAM: 32k context" from Ollama's general context-length page, where the reference is 262K. A verified quote can still answer a different question; release map 0.3 item 1, a relevance check, targets that. Aggregates, engine commits and the two cases: `docs/evidence/A4-verified-quotes-2026-11-12.md`; run records are not committed.

## 0.1.3

Hardening. No re-index needed. A config whose Ollama address is not `127.0.0.1`, `localhost` or `::1` must add `allow_remote = true` under `[ollama]`.

- The engine refuses an Ollama `base_url` that is not `127.0.0.1`, `localhost` or `::1` unless `[ollama] allow_remote = true` is set (LLD issue I-04).
- The reranker refuses weights whose sha256 differs from `model_sha256` in `models.toml`; the check reads the file once per process, about 2.4 s on the development machine (I-05).
- The MCP `search` tool refuses `k` above 50 and `page` above 100, and caps a `default_k` above 50 at 50 (I-06).
- `status` prints the mode of the PostgreSQL socket folder and warns when other users can reach it; `setup/user.sh` now sets the folder to 700, because the cluster trusts every socket connection (I-10). Re-run `setup/user.sh` or `chmod 700 ~/.cerebrollm/pg16/sock` on an existing install.
- New tests for the search sanitiser and the parameterised SQL path (I-12), and `engine/tests/capture_network.py`, which lists every address the Python code of `index`, `search` and `ask` connects to; C code such as libpq is not seen (I-09).
- `python3 eval/run_v2.py report` refuses an arm with fewer than 3 graded runs for any item, and prints per arm the count and ids of items with any confidently-wrong run and, when there are none, the rule-of-three 95% upper bound `3 / unique items` on that share (I-11). On this tree it refuses the committed v2 A4 arms, whose withheld raw records leave five items without graded runs.

## 0.1.2

`ask` gets more answers right and fewer confidently wrong. No re-index needed.

- Name gate: `ask` answers `Not in the sources.` without calling the model when the question names something that neither a retrieved passage nor any indexed chunk contains, such as an invented flag or type. Names are found by shape (backticks, `--flags`, dotted or snake_case names, camelCase, PascalCase, capitalised words inside a sentence, and a plain word before a kind noun when a passage names a neighbour). Matching ignores `-`, `_`, `.` and plural endings. It is a heuristic; `engine/README.md` lists its known misses. The `--json` output gains the key `absent_terms`.
- `verify`: a quote must start and end on a word boundary, so "port 80" no longer matches "port 8080" and `require_auth` no longer matches `require_auth_extra`. Text is compared in Unicode composed form. Quotes that differ from the source only in Markdown links, list markers, backticks or paired `*` emphasis still verify.
- Citations also accept the `[path (lines a-b)]` form the prompt shows.

Measured on the 35-item v2 set with `gpt-oss:20b` (thinking medium, 3 runs per item, one machine): right outcomes 33 of 35 (94.3%, was 31), confidently wrong runs 3 of 105 (2.9%, was 9), mean time per call 17.0 s (was 21.4 s). The under-2% confidently wrong aim is not met. Engine tests: 152 passed, 6 skipped without PostgreSQL.

## 0.1.1

Security fixes in `verify` and `search`: upgrade if an MCP host, an agent or another person can call them. No re-index needed.

- `verify` (command and MCP tool) answers for an excluded path exactly as for an absent quote: `MISSING` with the same detail. Never-index and tier rules are checked on the canonical path before the file is read; a file with a secret pattern is checked after. A path that leaves its root, also through a link, is `GONE` without a read. Before this, `verify` read any file under a registered root and told whether a quote was in it, including never-index folders (LLD issue I-01).
- For a git root, `verify` refuses a `ref` that git could read as an option or that names no commit, and answers `GONE` without reading (LLD issue I-03). A tree id as `ref` no longer reaches a file under another path.
- `search` drops a hit whose root is no longer configured or whose path no tier rule or a never-index rule matches, and leaves copies whose path is excluded, or whose root is not configured, out of `also_at`, so a stale index row for a newly excluded folder is not returned; a re-index brings back an allowed copy of a dropped hit. A root name may not contain `:`.
- `verify` answers `MISSING` for an empty or whitespace-only quote, and still `GONE` for a file that is not there. Before this, an empty quote matched any readable file, so `verify` reported `OK`, `CHANGED` or `UNINDEXED` and confirmed that the file exists.

- README: a walk-through image, two figures (`docs/site/context.svg`, `docs/site/parts.svg`), a requirements table, an MCP setup section with host examples and a short results table with a documentation table pointing to the details. The full results and limits moved to `docs/RESULTS.md`, troubleshooting to `docs/TROUBLESHOOTING.md`, and the repository map and provenance to `docs/REPOSITORY.md`. The product page shows the same figures. The README follows the Entry pages rule: a problem section with one line of evidence, key features, and paragraphs of at most 60 words. `DOC-PHILOSOPHY.md` is updated from the shared copy, which adds that rule.
- Documentation rules now live where contributors look: a "Writing docs" section in `CONTRIBUTING.md`, one line in a new `AGENTS.md`, the README lint as `scripts/readme_lint.py` (version 7) and a `docs-lint` workflow that runs it on every pull request. `DOC-PHILOSOPHY.md` and its checksum file are removed. README headings are now Why, Features, Quick start and Docs.

## 0.1.0 (2026-10-30)

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
