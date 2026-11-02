# Measured results and limits

Every number below comes from a file committed in this repository; each row names it. The README shows a short selection and points here.

## Results

All numbers come from files committed here. "Measured" means a run produced the number; the command or file that holds it is named. Every run used one machine (Windows 11, WSL2 Ubuntu 24.04, RTX 4070 SUPER with 12 GB) and public documentation as the corpus.

| Question | Result | Source | State |
|---|---|---|---|
| Does the top 8 hold a line that answers the question? 60 scored questions on 1,432 documents (13,627 chunks) | default search 45/60, search top 20 then rerank 46/60, any of the top 20 48/60 | `eval/runs/retrieval/R-summary.md` | measured |
| Does retrieval help a small local model? `phi4`, 60 questions, majority of 5 runs, model-graded | without retrieval 1/60, with default search and a citation instruction 47/60 (46 questions gained, 0 lost, p < 0.0001) | `eval/RESULTS.md`, `eval/runs/judge/tables.md` | measured |
| Does retrieval help a strong hosted model? Claude Haiku, same 60 questions | without retrieval 47/60, with 48/60 (8 gained, 7 lost, p = 1.0): no effect shown; Haiku already answers 47 of 60 without retrieval, which leaves little room to show a gain | `eval/RESULTS.md`, `eval/runs/judge/tables.md` | measured |
| How often do citations verify? Answers with at least one `OK` citation | Claude Haiku 347 of 350, `phi4` 184 of 350 | `eval/RESULTS.md` | measured |
| Does the model grader agree with a person? 40 answers graded by a person | 19/20 and 20/20 agreement in run 1, 20/20 and 20/20 in run 2; its error on the other 2,060 answers is not measured | `eval/RESULTS.md` | measured on 40 answers |
| Which embedding model? 150 questions | `qwen3-embedding:0.6b` hybrid hit@5 0.927, against 0.907 (`qwen3-embedding:4b`) and 0.893 (`bge-m3`); 3 questions separate first and second place | `research/model-study/RESULTS.md` | measured |
| Which generator fits a 12 GB card? | `gpt-oss:20b`, reasoning effort medium: code 39/40, tool scenarios 12/12, 46.2 tokens/s at an 8,000-token prompt with 71% of the model on the GPU | `research/model-study/RESULTS.md`, `research/model-study/STUDY-DONE.md` | measured on one machine |
| Do the unit tests pass without PostgreSQL, Ollama or a GPU? | engine 113 passed and 6 skipped; evaluation scripts 186 checks, 29 unit tests with 1 skipped, and 19 judge checks; study scripts 97 tests | `docs/evidence/ci-local.log` | measured |
| Does `ask` meet the aim of at least 90% right outcomes with under 2% confidently wrong runs? | not met by any local model; met only by Claude Sonnet 5.5 with plain search (v2 table below) | `eval/RESULTS-v2.md` | measured |
| Qwen3.6 with multi-token prediction on and off, 8,000-token prompt (`qwen3.6:35b-a3b-coding-mtp-q4_K_M`, thinking off) | on: code 37/40, tools 12/12, 52.9 tokens/s, 41.3% of the model on the GPU; off: code 36/40, tools 12/12, 51.3 tokens/s, 43.9% on the GPU | `research/model-study/r2-wsl/r2-table-M3.md` | measured, one machine; context ladder (8k, 32k, 64k) not measured yet |

## v2 evaluation: 35 public items

The items are 20 answerable questions on public release notes dated after 2026-06 (10 exact, 7 paraphrase, 3 stale) and 15 unanswerable questions. A run is right when it answers an answerable item correctly or says it is not in the sources for an unanswerable one; an item counts when more than half of its runs are right. A run is confidently wrong when it answers an answerable item wrongly or gives any answer to an unanswerable one. Plain search is the top 8 of the default search with the citation instruction (arm A3); `cerebrollm ask` is arm A4. Without retrieval (arm A0) the right outcome is 6 to 15 of 35 and `gpt-oss:20b` is confidently wrong in 122 of 175 runs. Answers were graded by `gpt-oss:20b` (rubric in `eval/GRADING-v2.md`); a second grader, `gemma4:12b`, agreed on 432 of 454 of `gpt-oss:20b`'s answers (kappa 0.899).

| Model | Plain search (A3): right outcome of 35 items, confidently wrong runs | `cerebrollm ask` (A4): right outcome of 35 items, confidently wrong runs |
|---|---|---|
| Claude Sonnet 5.5 (hosted) | 34 (97.1%), 0 of 105 | not run |
| `gemma4:12b` | 33 (94.3%), 4 of 175 (2.3%) | 22 (62.9%), 0 of 105 |
| `gpt-oss:20b` | 32 (91.4%), 17 of 175 (9.7%) | 28 (80.0%), 7 of 104 (6.7%) |
| `phi4` | 31 (88.6%), 10 of 175 (5.7%) | 21 (60.0%), 0 of 105 |

The aim is at least 90% right outcomes and under 2% confidently wrong runs. Claude Sonnet 5.5 with plain search meets it. `gemma4:12b` reaches 94.3% but is confidently wrong in 2.3% of runs; `gpt-oss:20b` and `phi4` miss on both counts. `ask` removes most confidently wrong runs and gives up right outcomes in exchange: it abstains on 16 to 42 runs of answerable questions. With 35 items, even zero confidently wrong items bounds the rate only below 8.6% (rule of three, 3 of 35), so this set cannot show a rate under 2%. Source: `eval/RESULTS-v2.md` and `eval/runs/v2/summary.json`; 50 raw v2 records that quote private documents are withheld and the scores are as committed. Status: early research; the aim is not yet met by local models.

## Limits

- Retrieval misses 14 to 15 of the 60 scored questions in the top 8 on the public corpus (14 with the reranker, 15 without); a missed question usually ends as `Not in the sources.` or a wrong answer from the model's own knowledge. The share of each is not measured.
- The gate does not check that the verified quote answers the question: a real quote from a file that is about something else passes. A relevance check is the first proposed item of 0.2 (`RELEASE-MAP.md`).
- The gate needs one verified citation, not a verified sentence: when the model writes a verified quote plus other text, `ask` prints all of it, and the other text is not checked. A citation is also not required to come from the 8 retrieved passages. Both are proposed changes in `RELEASE-MAP.md`.
- The grader that produced the answer-quality numbers is itself a model checked on 40 answers.
- The 12 tool scenarios and all speeds come from one machine with one GPU. Speeds on other hardware are not measured.
- The default configuration carries tier rules for the author's folder layout; every new corpus folder needs a `[[rule]]`.
- Only Markdown files are indexed.
- Search scans exactly (no approximate index); behaviour above about 15,000 chunks is not measured.
- The index is not encrypted and PostgreSQL uses trust authentication on a Unix socket in `~/.cerebrollm`; protect that folder with file permissions.
- A wheel installed with `pip install --user` or `--target` cannot find the packaged configuration; pass `--config` or set `CEREBROLLM_CONFIG`.
- `engine/models.toml` allows only Apache-2.0 and MIT models. Model licences apply to the models you pull.

Skipped or not checked: the Qwen3.6 context ladder, GLM-4.7-Flash (pulled, not measured), speeds on other hardware, and behaviour above about 15,000 chunks.
