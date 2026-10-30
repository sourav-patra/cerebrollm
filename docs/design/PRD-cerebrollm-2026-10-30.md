---
id: PRD-cerebrollm
kind: contract
governs: 0.1.0 (first public release); section 6 lists what 0.2 proposes
status: LOCKED 2026-10-30 by the owner (content of draft v6)
sources: README.md (Aim, agreed 2026-10-29), engine/ code and tests, eval/RESULTS.md, eval/GRADING-v2.md, eval/RESULTS-v2.md, eval/runs/v2/summary.json, research/model-study/STUDY-DONE.md, eval/runs/retrieval/R-summary.md
checked-at: engine code at source revision 02a00dd (unchanged at 233ef75: `git diff --stat 02a00dd 233ef75 -- engine` prints nothing); results at 233ef75, 2026-10-30 (the public repository starts a new history; the hashes are for the review record)
---

Read section 4 to see what 0.1.0 must do, section 7 for the questions the owner answers before this file is locked, and section 2 for what is measured today.

# cerebrollm PRD: grounded answers from your own documents, or an honest "not in the sources"

## 1. What it is and who it is for

cerebrollm is a local retrieval layer over a person's own authoritative Markdown documents. It indexes them with a tier and a status, searches them (keyword, vector or both), reranks, and re-reads the source file to confirm a quote before anyone states it. Two programs front it: `cerebrollm ask`, which answers with a local model, and `cerebrollm mcp`, a read-only server that lets other models search and verify. The index and the engine stay on the user's machine.

Users:

- U1, a person who uses a cloud model with thinking on and wants it to answer from their documents. The model reaches cerebrollm through the MCP server, calls `search`, and calls `verify` before stating a quote.
- U2, a person who runs local models for private or offline work. The model runs on the same machine; `cerebrollm ask` runs search, rerank, generation and verification and prints either a verified answer or the exact line `Not in the sources.`

Both users keep the index, the source files and the check on their own machine. Document text leaves the machine through a model host the user connects (U1) or through an address the user sets for the local model server; downloads and installs are listed in POLICY section 4. Figure 1 in `TRD-cerebrollm-2026-10-30.md` (file `figures/trd-components.svg`) shows the boundary and both paths.

## 2. Where it stands (observed 2026-10-30)

Marks: E observed in code or by a check run in this pass; R reported by a committed result file or log;  P proposed; N not measured, with the command that would measure it.

- E: the engine has 15 Python modules under `engine/cerebrollm/` and 119 test functions in `engine/tests/` (`grep -c "def test_" engine/tests/test_*.py`).
- R: the suite passed on 2026-10-29 as `119 passed, 61 subtests passed` (`eval/runs/retrieval/n7-evidence/engine-suite.log`). It was not re-run in this pass.
- R: retrieval puts the line an item asks for in the top 8 for 45 of 60 scored items with default search, 46 with search top 20 then rerank to 8, and 48 anywhere in the top 20 (`eval/runs/retrieval/R-summary.md`). The rerank gain is one item in sixty; no significance test was run.
- R: with retrieval the local model phi4 answers 47 of 60 scored questions correctly (model grade, majority of 5 runs) against 1 without retrieval; the hosted small model of that comparison answers 48 with and 47 without (`eval/runs/judge/tables.md`, `eval/RESULTS.md` name it). The grader agreed with the owner on 39 of 40 answers in its first validation run. These arms use a citation prompt, not the `ask` gate.
- R: the embedding model `qwen3-embedding:0.6b` scored hybrid hit@5 0.927 on 150 generated questions against 0.907 and 0.893 for two alternatives (`research/model-study/RESULTS.md`).
- R: the `ask` pipeline is graded on the 35 public v2 items (arm A4): the aim is not met for any model. Section 2.1 gives the numbers.
- N: the engine in a clean environment from the installed package (packaging is a separate work item, requirement RQ-13; command in the RQ-13 row).
- N: behaviour above about 15,000 chunks; the vector query is an exact scan (`engine/README.md`, Known limits). Pending benchmark: index a corpus of 30,000 or more chunks and time `cerebrollm search` and `cerebrollm ask`; no script exists yet (P).

### 2.1 Graded result of the aim (R, 35 public v2 items)

Source: `eval/RESULTS-v2.md` and `eval/runs/v2/summary.json` at 233ef75, table "Per model and arm". Grader: `gpt-oss:20b`, the same model as the default generator; a second grader (`gemma4:12b`) agreed on 432 of 454 answers of the `gpt-oss:20b` records (95.2%, Cohen's kappa 0.899); it did not grade the other models' answers. Classes follow `eval/GRADING-v2.md`; majority means more than half of an item's runs. A4 is the `ask` pipeline with 3 runs per item; A3 is search top 8 plus a citation prompt with no gate, 5 runs per item for the local models; A0 is no retrieval.

| Model and arm | Right outcome of 35 | Correct of 20 | Abstained correctly of 15 | Confidently wrong runs | Aim |
|---|---|---|---|---|---|
| `gpt-oss:20b`, A4 (gates the release) | 28 (80.0%) | 15 | 13 | 7 of 104 (6.7%) | not met |
| `gpt-oss:20b`, A3 | 32 (91.4%) | 19 | 13 | 17 of 175 (9.7%) | not met |
| `gpt-oss:20b`, A0 | 6 (17.1%) | 3 | 3 | 122 of 175 (69.7%) | not met |
| `gemma4:12b`, A4 | 22 (62.9%) | 7 | 15 | 0 of 105 | not met |
| `phi4`, A4 | 21 (60.0%) | 6 | 15 | 0 of 105 | not met |

What the table shows:
- RQ-01 and RQ-02 are not met for the default model: 28 of 35 items (80.0%) against 90%, and 7 of 104 runs (6.7%) against 2%. The hosted model of the study (arm A3 only, no gate; named in `eval/RESULTS-v2.md`) reached 34 of 35 items and 0 of 105 confidently wrong runs.
- The `gpt-oss:20b` A4 run is missing one record: item G2-EX-04, run 3, failed twice: first with a CUDA error, then on retry with an HTTP 500 from the model server (the last two lines for that run in `eval/runs/v2/failures.jsonl`). The check under RQ-01 prints it as missing, so RQ-01 is not satisfied for that model until the run is regenerated.
- Which class fails (derived from the summary rows, not from reading records): the 59 answerable `gpt-oss:20b` A4 runs split into 43 correct and 16 abstained wrongly, so none of the 7 confidently wrong runs is on an answerable item; they are answers to unanswerable questions that passed the gate. The cause of the 16 wrong abstentions and of the 7 passes is not diagnosed in this pass (N; command: read `citations[].verify` in `eval/runs/v2/gpt-oss-20b/A4/*/run-*.json`). TRD limits K-1 and K-3 describe how such a pass is possible.
- Pipeline comparison, not a gate-only effect: A3 and A4 differ in more than the gate. A3 runs at temperature 0.7 with default search top 8 (`OPTS` in `eval/run_v2.py`); A4 runs at temperature 0 with search top 20 reranked to 8 and the gate (`engine/cerebrollm/answer.py`). Confidently wrong runs fall from 9.7% (A3) to 6.7% (A4) and right outcome falls from 91.4% to 80.0%. The run counts differ (175 and 104), so the comparison is indicative.
- With no retrieval, no model answered more than 3 of the 20 answerable items correctly. The v2 items cite documents published after 2026-06 (`eval/GRADING-v2.md`).
- For arm A3, default search top 8 holds every quoted line for 20 of 20 answerable items (`eval/RESULTS-v2.md`, "Retrieval and citations"). Coverage for the A4 pipeline (top 20 reranked to 8) is not inspected (N; command: compare `hits` in the A4 records with the item quotes), so retrieval and reranking are not excluded as causes of the A4 failures.

## 3. Goals

1. At least 90% of answers are the right outcome: a correct answer backed by a citation that `verify` confirms, or a correct "not in the sources" for a question the documents do not answer.
2. Fewer than 2% of runs are confidently wrong: a specific wrong answer, or any specific answer to a question the documents do not answer.
3. Correct abstention is reported as its own number beside the correct answers, so abstaining cannot hide a retrieval failure.
4. Any model can use the layer: cloud models through the MCP server, local models through `ask`.
5. A person can rebuild the index, rerun the evaluation and see the same tables.

Goals 1 and 2 are the aim agreed on 2026-10-29. Neither is met for `ask` today (section 2.1).

## 4. Requirements

Priority: must for 0.1.0, should for 0.1.0 if it can be checked, P for a proposal that 0.2 may take.

| ID | Requirement | Check | Evidence and state |
|---|---|---|---|
| RQ-01 | At least 90% of the 35 public v2 items reach the right outcome (per-item majority of 3 runs, arm A4) | generate with `python3 eval/run_v2.py gen MODEL --arms A4 --runs 3`, grade with `python3 eval/run_v2.py grade --judge JUDGE`, then `python3 eval/run_v2.py report`; accept the report only when the key check below prints no missing key, no extra key, no duplicate and no error for MODEL, in generation and in grades (the report skips missing grades) | R: not met, 28 of 35 (80.0%) for `gpt-oss:20b` (section 2.1); the key check prints G2-EX-04 run 3 missing for that model. must |
| RQ-02 | Confidently wrong runs are under 2% of arm A4 runs; the result file states the observed count and the rule-of-three upper bound computed on unique items | same commands as RQ-01; `grep -L '"abstained": \(true\|false\)' eval/runs/v2/*/A4/*/run-*.json` prints no file, because the classifier falls back to phrase matching when that flag is missing (`eval/run_v2.py`, `classify`); the bound line is added by hand (3 divided by the number of unique items) until the report prints it | R: not met, 7 of 104 runs (6.7%) for `gpt-oss:20b` (section 2.1). `ask` runs at temperature 0, so the 3 runs of one item are near-identical and the independent trials are the 35 items (`call_ask` in `eval/run_v2.py`). With zero observed, the 95% upper bound by the rule of three is 3 of 35, 8.6%, far above 2%; the 105 runs do not change that. The bound holds only if the items are independent draws from the questions a user could ask. They are written by the maintainer from named public release notes, not drawn at random, so the bound is conditional on that assumption and describes this item set. For the bound an item fails when any of its runs is confidently wrong; the run-level rate stays the headline. This set can show a rate but cannot prove the target. must |
| RQ-03 | The report lists `correct`, `abstained-correctly`, `abstained-wrong`, `empty` and `confidently-wrong` as separate rows | `eval/report_v2.py` classes; `python3 eval/test_run_v2.py` | E: classes defined in `eval/GRADING-v2.md` and `eval/run_v2.py`. R: the 4 tests passed on 2026-10-29. must |
| RQ-04 | In text mode `ask` prints an answer only when at least one citation has verify code OK; otherwise stdout is exactly `Not in the sources.`. With `--json` the `answer` field carries the same text and `abstained` is true | `engine/tests/test_answer.py` gate and CLI tests | R: in the 119 tests that passed on 2026-10-29. must |
| RQ-05 | A failure in search, rerank or generation prints one line on stderr, exits 2 and prints no answer | `engine/tests/test_answer.py` CLI tests | R: in the 119 tests that passed on 2026-10-29. must |
| RQ-06 | `verify` returns OK, CHANGED, MISSING, GONE or UNINDEXED and exits 0 only for OK | `engine/tests/test_verify.py` | R: 7 tests, passed on 2026-10-29. must |
| RQ-07 | The MCP server offers `search` and `verify` only, read-only, with retrieved text marked as data | `engine/tests/test_mcp_server.py` | R: 19 tests, passed on 2026-10-29. must |
| RQ-08 | In the default configuration `index`, `search`, `ask` and `verify` call no hosted model or embedding service (a non-loopback Ollama address is not refused until LLD I-04); `ask` refuses model names ending `-cloud` or `:cloud` | tests for the refusal; a network capture during `ask` | R: refusal tested on 2026-10-29. N: no capture has been run; command: run `ask` under `strace -f -e trace=connect` and list the addresses. must |
| RQ-09 | Only Markdown that matches a tier rule is indexed; never-index paths, symlinks and files flagged by the secret scan are skipped and counted | `engine/tests/test_rules.py`, `test_corpus.py` | R: passed on 2026-10-29. must |
| RQ-10 | Default search returns `locked` and `current` documents, boosted by tier and recency; `superseded` and `draft` appear only with `--all-status` | `engine/tests/test_search.py`, `test_rules.py` | R: passed on 2026-10-29. must |
| RQ-11 | A full rebuild fills a new table and swaps it in; a new table that is empty or under half the live rows is refused | `engine/tests/test_swap.py` | R: 9 tests, passed on 2026-10-29. must |
| RQ-12 | The evaluation compares arms with and without retrieval on public items and publishes the item files, the grading rules and the per-answer records | `eval/` contents; `python3 eval/check_items_v2.py` | E: v1 comparison in `eval/RESULTS.md`; R: v2 graded in `eval/RESULTS-v2.md`. must |
| RQ-13 | A person can install 0.1.0 into a fresh environment and run `cerebrollm --help` and `cerebrollm ask --help` | wheel installed in a fresh venv; both commands exit 0 | N: packaging is in progress in a separate work item; command: in a new venv `pip install dist/*.whl && cerebrollm --help && cerebrollm ask --help`. must |
| RQ-14 | Only models under Apache-2.0 or MIT are pulled, from an allow-list with pinned digests | `research/model-study/test_model_guard.py`; `engine/models.toml` | E: allow-list present; the 67 guard tests were not re-run in this pass. must |
| RQ-15 | `ask` reranks the top 20 hits to 8 with a local cross-encoder, and a flag turns that off | `engine/tests/test_answer.py` rerank tests | R: tests passed on 2026-10-29. The measured effect is one item in sixty. should |
| RQ-16 | The public tree holds no private note, machine path, account name or personal email | leak scan over the tree, output saved | N: owned by the release work item. must |
| RQ-17 | The README states the measured results with their source files and marks every unmeasured claim | reviewer reads README against `eval/` result files | N: README is rewritten in the release work item. must |
| RQ-18 | P: `ask` marks or drops generator text that no verified citation covers | new test in `engine/tests/test_answer.py` | P: today the whole answer prints once one citation verifies (`decide` in `engine/cerebrollm/answer.py`; TRD known limit K-1). should |
| RQ-19 | P: `verify` gives the same answer for a quote in an excluded file as for a quote that is absent | new test in `engine/tests/test_verify.py` | P: today the codes differ (`run_verify` in `engine/cerebrollm/verify.py`; TRD known limit K-2). should |
| RQ-20 | P: a second public item set of at least 200 unique items, so that zero confidently wrong items bound the rate at 1.5% (3 of 200) | new item file and the same report | P: needed because RQ-02 cannot be shown on 35 items. should |

RQ-01 key check, run from the repository root with MODEL set to the directory name of the model (for example `gpt-oss-20b`). It needs the generation records and the primary grades each to hold exactly the 35 item ids of `eval/items-v2.jsonl` with runs 1 to 3, once each, with no error grade:

```
python3 - MODEL <<'E'
import json, sys, glob, collections
m = sys.argv[1]
ids = [json.loads(l)['id'] for l in open('eval/items-v2.jsonl', encoding='utf-8')]
want = {(i, k) for i in ids for k in (1, 2, 3)}
gen = collections.Counter()
for p in glob.glob('eval/runs/v2/%s/A4/*/run-*.json' % m):
    d = json.load(open(p, encoding='utf-8'))
    gen[(d['id'], d['run'])] += 1
rows = [json.loads(l) for l in open('eval/runs/v2/judge/gpt-oss-20b.jsonl', encoding='utf-8')]
rows = [r for r in rows if r['model'] == m and r['arm'] == 'A4']
gr = collections.Counter((r['id'], r['run']) for r in rows)
for name, c in (('generation', gen), ('grade', gr)):
    print(name, 'missing', sorted(want - set(c)), 'extra', sorted(set(c) - want),
          'duplicate', [k for k, v in c.items() if v > 1])
print('error', [(r['id'], r['run']) for r in rows if r['verdict'] == 'error'])
E
```

Run on 2026-10-30: `gpt-oss-20b` prints `missing [('G2-EX-04', 3)]` for both generation and grade; `gemma4-12b` and `phi4` print empty lists everywhere.

## 5. Out of scope

- Answering from a model's own memory when the documents are silent. The layer abstains instead.
- A hosted retrieval, embedding or reranking service, and any `-cloud` model in the engine.
- Writing to, editing or deleting the user's documents. The engine reads them.
- File types other than Markdown, and any multi-user server, login or access control.
- Approximate vector indexes and scale beyond about 15,000 chunks until measured.
- Training or fine-tuning a model.
- Proving that a model's cited line answers the question. `verify` proves the quote exists in an indexed file; a grader or a person judges relevance.

## 6. Order of work

1. Release work item (separate): packaging, README, CI, leak scan, the four documents locked (RQ-13, RQ-16, RQ-17).
2. Regenerate the missing `gpt-oss:20b` A4 record (G2-EX-04, run 3) and re-run the key check (RQ-01 to RQ-03); section 2.1 is filled.
3. The aim is not met: diagnose the 16 wrong abstentions and the 7 confidently wrong passes of `gpt-oss:20b` A4 by stage (search, rerank, generate, gate) before adding features (section 2.1).
4. 0.2 candidates in order: RQ-18, RQ-19, RQ-20. Each lands as one pull request with its test.

## 7. Owner questions

The owner answered every question below on 2026-10-30 by accepting the recommendation. The recommendation to question 6 is to decide after the graded results; they now exist (section 2.1) and that decision stays open.

A. The aim
1. Right outcome counts a correct answer and a correct abstention together against 90% of items, and confidently wrong is counted over runs against 2%. Confirm this reading of the 2026-10-29 aim. Recommended: yes, because `eval/report_v2.py` already computes it this way.
2. The aim is measured per model. Which pairing is the gate: `gpt-oss:20b` (the default generator) only, or every model in the report? Recommended: `gpt-oss:20b` gates the release; other models are reported, not gated.
3. RQ-02 cannot be proven on 35 items: the bound is 8.6% (the evidence column of RQ-02 gives the arithmetic). Accept a reported rate with its upper bound for 0.1.0, and make RQ-20 the proof for a later version? Recommended: yes.

B. Release
4. May 0.1.0 be published before the aim is met if the README states the measured numbers and the status "early research"? Recommended: yes, with the README stating the gap.
5. Supported platforms: Ubuntu 24.04 under WSL2 is the only tested setup. State Linux as tested and macOS and native Windows as untested? Recommended: yes.

C. Behaviour
6. Today `ask` prints the generator's whole text once one citation verifies. Change to print only verified quotes in 0.2 (RQ-18)? Recommended: wait for the v2 A4 records, then decide from how often unverified text accompanies a verified quote.
7. `verify` reveals whether a quote exists in a file the index excludes (RQ-19). Fix in 0.2? Recommended: yes; a private file's content is the thing the exclusion protects.
8. Switch the default generator from `gpt-oss:20b` to `gemma4:12b`, which scored the same code and tool results at higher speed in the model study (`research/model-study/STUDY-DONE.md`)? Recommended: no change until the A4 records compare them.

## 8. Not measured and limits of the evidence

- Why `gpt-oss:20b` abstains wrongly on 16 answerable runs and passes 7 unanswerable runs (section 2.1).
- The aim on a user's own corpus. The public items test public documentation; the owner's private items are not in this repository.
- The effect of the tier boost, recency weight and chunk size (`engine/README.md`, Known limits). Pending benchmark: the retrieval measure `eval/runs/retrieval/measure_rerank.py` run with the boosts set to 1.0 in a copy of the configuration; no ablation script exists yet (P).
- Whether a hosted model knows the public documents from training: the hosted arm without retrieval scored 47 of 60. The v2 arm without retrieval measures baseline accuracy on documents published after 2026-06 (no model answered more than 3 of 20 correctly, section 2.1); training exposure stays unknown.
- The model grader is itself a model. Its 40-answer validation does not bound its error on other answers (`eval/RESULTS.md`).

Skipped or not checked: figures (the TRD carries them; this document has none); the 119-test suite and the 67 model-guard tests were not re-run in this pass; no network capture of `ask` was made; the individual A4 records were not read, so the causes in section 2.1 are not diagnosed; the grader is the default generator, with a second grader checked on its own answers only.
