# Results: with and without retrieval (issue #12, Part N2)

Run date 2026-10-29, regraded after review round 1 (the disclaimer rule below). Items: `eval/items.jsonl` (frozen at 8399adb; sha256 `8f733d40...5741cc5`, unchanged). Grading: `eval/GRADING.md` as frozen, implemented in `eval/grade_lib.py`. The headline section below uses model grades (`eval/runs/judge/summary.json`); the rest of the file uses keyword grades, and every keyword number is in `eval/runs/summary.json` (made by `eval/analyze.py` from the 2,100 record files under `eval/runs/haiku/` and `eval/runs/phi4/`; per-record grades in `eval/runs/graded.jsonl`). The run record with commands, hashes and deviations is `step N2 record` in the private working repository. The promptfoo reports open offline: `eval/runs/promptfoo-hosted.html`, `eval/runs/promptfoo-local.html` (single files, no network resources).

## Withheld raw records

100 raw records under `eval/runs/` are not in this repository. 50 are prompt and retrieval records of 16 items of the first question set (`prompts/A1` 13, `prompts/A2` 3, `prompts/A3` 3, `retrieval/A1` 13, `retrieval/A2` 3, `retrieval/A3` 3, `retrieval/R-default` 3, `retrieval/R-rerank` 9). 50 are v2 records (`v2/gemma4-12b/A4` 15, `v2/gpt-oss-20b/A4` 14, `v2/phi4/A4` 15, `v2/prompts` 3, `v2/retrieval` 3; see `eval/RESULTS-v2.md`). The retrieved passages in them quote documents of the private working repository. The scores in this file and in `eval/runs/summary.json`, `eval/runs/judge/` and `eval/runs/retrieval/R-summary.*` are unchanged: they were computed from the full record set before the records were withheld. Running `eval/analyze.py` on this tree reads only the remaining records, so the retrieval table it prints for the affected items differs from the published one. `eval/runs/WITHHELD.sha256` lists the sha256 of each withheld file. The answer records under `eval/runs/haiku/` and `eval/runs/phi4/` are all present.

## Headline: model grades (development step N4)

The grades in this section come from a model grader, `gpt-oss:20b` on the local Ollama (digest `f38aa0c5...`, reasoning effort medium, temperature 0), one call per answer, rubric in `eval/GRADING.md` section 3, code in `eval/judge.py`. The owner asked for an intelligent grader after the keyword grader agreed with the owner 17/20 per sheet. The keyword results stay further down under their own heading.

Validation, run once with the rubric frozen (commit f9f90e1) on the 40 owner-graded answers: the judge agrees with the owner on 19/20 for sheet A (Haiku) and 20/20 for sheet B (phi4) in run 1, and 20/20 and 20/20 in run 2 (a rerun of the same 40; one verdict flipped between the runs, A S15). Run 1 disagreement: sheet A, S15, item ST-10, owner N, judge Y, reason "The answer correctly recommends using the agent workflow API (FunctionAgent) and acknowledges AgentWorkflow, aligning with the reference that deprecated classes are replaced by AgentWorkflow." Both sheets reach the 18/20 that `GRADING.md` requires. Records: `eval/runs/judge/validation-1.jsonl`, `validation-2.jsonl`. The sample is the 40 answers the owner graded; the judge was not tuned on them.

Full run: all 2,100 answers, 1,348 Y, 752 N, 0 error, no retry needed (`attempts` is 1 on every line), 2 h 04 min (7,462 s by the script clock, 7,434 s summed over the calls), one model digest and one rubric hash on every line (`eval/runs/judge/graded.jsonl`, log `eval/runs/logs/n4-judge.log`). Keyword grade: 1,403 of the 2,100 correct. The two grades differ on 231 records (11 percent): keyword Y and judge N on 143, keyword N and judge Y on 88.

Reading the tables: the headline conclusions did not change. phi4 with retrieval beats phi4 without it (A3 against A0: 46 to 0). A3 against A1 is 8 to 2 (p = 0.11) and against A2 0 to 1, neither significant. Haiku: A3 48 and A0 47 questions correct, 8 to 7 (p = 1.0): no effect shown. The per-kind stale scores for Haiku rise from 14 to 15 questions in both arms. The judge is also a model and the validation sample is 40 answers; its errors on the other 2,060 answers were not measured (command: owner grades a further random sample with `eval/owner_sheets.py` and a new seed, then `python3 eval/judge.py compare`).

Tables from `eval/runs/judge/tables.md` (made by `python3 eval/analyze.py --grades judge`; summary in `eval/runs/judge/summary.json`). Each arm has a line with how many majority grades changed against the keyword grader.

Grades in this file: model grade (gpt-oss:20b, GRADING.md section 3).

#### haiku: scored items (60), per-question majority over the runs; run pass rate = share of all runs correct

| Arm | Runs/q | exact (20) | paraphrase (20) | stale (20) | all (60) | run pass rate e/p/s/all | pass^5 e/p/s/all |
|---|---|---|---|---|---|---|---|
| A0 | 5 | 16 | 16 | 15 | 47 | 0.82 / 0.79 / 0.76 / 0.79 | 16 / 14 / 14 / 44 |
| A1 | not run, ruling R-7 | | | | | | |
| A2 | not run, ruling R-7 | | | | | | |
| A3 | 5 | 15 | 18 | 15 | 48 | 0.74 / 0.91 / 0.78 / 0.81 | 14 / 18 / 14 / 46 |

Majority grades changed from keyword to model grade, haiku/A0: 6 of 60 (now correct: EX-05, ST-01, ST-16; now incorrect: EX-13, PA-14, ST-14).

Majority grades changed from keyword to model grade, haiku/A3: 9 of 60 (now correct: ST-01, ST-02, ST-14, ST-20; now incorrect: EX-13, PA-14, ST-04, ST-05, ST-07).

Sign test, haiku: A3 against each arm on per-question majority (A3 only / other only / ties dropped, two-sided exact p)

| Comparison | exact | paraphrase | stale | all |
|---|---|---|---|---|
| A3 vs A0 | 2/3/15, p=1.0000 | 3/1/16, p=0.6250 | 3/3/14, p=1.0000 | 8/7/45, p=1.0000 |
| A3 vs A1 | not run, ruling R-7 |  |  |  |
| A3 vs A2 | not run, ruling R-7 |  |  |  |

Tokens and calls, haiku (all calls including practice items)

| Arm | Calls | input total | output total | input mean | output mean |
|---|---|---|---|---|---|
| A0 | 350 | 230931 | 181840 | 659.8 | 519.5 |
| A3 | 350 | 1117520 | 192471 | 3192.9 | 549.9 |

A3 citations, haiku: 349/350 answers have a quote and path; 347/350 have at least one citation that `verify` prints OK for; 803/874 extracted citations verify OK.

#### phi4: scored items (60), per-question majority over the runs; run pass rate = share of all runs correct

| Arm | Runs/q | exact (20) | paraphrase (20) | stale (20) | all (60) | run pass rate e/p/s/all | pass^5 e/p/s/all |
|---|---|---|---|---|---|---|---|
| A0 | 5 | 0 | 1 | 0 | 1 | 0.00 / 0.05 / 0.00 / 0.02 | 0 / 0 / 0 / 0 |
| A1 | 5 | 13 | 16 | 12 | 41 | 0.66 / 0.80 / 0.58 / 0.68 | 12 / 16 / 10 / 38 |
| A2 | 5 | 15 | 17 | 16 | 48 | 0.74 / 0.83 / 0.80 / 0.79 | 14 / 16 / 15 / 45 |
| A3 | 5 | 15 | 16 | 16 | 47 | 0.75 / 0.82 / 0.81 / 0.79 | 15 / 15 / 14 / 44 |

Majority grades changed from keyword to model grade, phi4/A0: 3 of 60 (now correct: none; now incorrect: EX-12, PA-10, PA-20).

Majority grades changed from keyword to model grade, phi4/A1: 5 of 60 (now correct: ST-14, ST-19; now incorrect: EX-04, EX-17, PA-10).

Majority grades changed from keyword to model grade, phi4/A2: 6 of 60 (now correct: ST-14, ST-19, ST-20; now incorrect: EX-13, PA-14, ST-04).

Majority grades changed from keyword to model grade, phi4/A3: 8 of 60 (now correct: ST-12, ST-19, ST-20; now incorrect: EX-13, PA-02, PA-11, PA-14, ST-04).

Sign test, phi4: A3 against each arm on per-question majority (A3 only / other only / ties dropped, two-sided exact p)

| Comparison | exact | paraphrase | stale | all |
|---|---|---|---|---|
| A3 vs A0 | 15/0/5, p=0.0001 * | 15/0/5, p=0.0001 * | 16/0/4, p=0.0000 * | 46/0/14, p=0.0000 * |
| A3 vs A1 | 2/0/18, p=0.5000 | 2/2/16, p=1.0000 | 4/0/16, p=0.1250 | 8/2/50, p=0.1094 |
| A3 vs A2 | 0/0/20, p=1.0000 | 0/1/19, p=1.0000 | 0/0/20, p=1.0000 | 0/1/59, p=1.0000 |

Tokens and calls, phi4 (all calls including practice items)

| Arm | Calls | input total | output total | input mean | output mean |
|---|---|---|---|---|---|
| A0 | 350 | 18130 | 42236 | 51.8 | 120.7 |
| A1 | 350 | 632570 | 58126 | 1807.3 | 166.1 |
| A2 | 350 | 563035 | 60990 | 1608.7 | 174.3 |
| A3 | 350 | 577890 | 71642 | 1651.1 | 204.7 |

A3 citations, phi4: 262/350 answers have a quote and path; 184/350 have at least one citation that `verify` prints OK for; 314/579 extracted citations verify OK.

## Setup in one paragraph

Four arms on the corpus `~/cerebrollm-corpus` through the live index (`qwen3-embedding:0.6b`): A0 no retrieval; A1 lexical top 8 (`--all-status`); A2 hybrid top 8 (`--all-status`); A3 default search top 8 plus "Quote the line you rely on and cite its path." (with a one-line format example). Hosted model: Claude Haiku (`claude-haiku-5-5`) through `claude -p --model haiku`, all tools disabled, arms A0 and A3, five runs each over all 70 items = 700 calls (the orchestrator ruled 700 because the frozen set has 70 items; ruling R-7 text said 600; A1 and A2: not run, ruling R-7). Local model: phi4 through Ollama (`num_ctx` 16,384, temperature 0.7, `num_predict` 1,024), arms A0 to A3, five runs each over all 70 items = 1,400 calls. Tables use the 60 scored items; the 10 practice items were run too and are in the call and token counts. Majority = correct in at least 3 of 5 runs.

## Code-grade results (keyword grader, secondary)

Everything below this heading is the keyword grade of `GRADING.md` section 1, as first reported. It is kept as the second column; its tables are `eval/runs/tables.md`.

## Disclaimer rule (implementation of GRADING.md line 15)

`GRADING.md` says an answer that only says it does not know is incorrect. The first grading pass checked only for empty answers, so a disclaimer that restated the question could pass the 80 percent content-word fallback (Haiku A0 EX-19 passed 5 of 5 runs). The grader now treats an answer that contains any of these phrases (case-insensitive, after the normalisation of GRADING.md) as a disclaimer: "I don't know", "I do not know", "not sure", "cannot determine", "can't determine", "unable to determine", "no information", "does not say", "doesn't say", "not mentioned", "not specified". For such an answer the content-word fallback is off and only a contiguous key-fact match (rule 1) can pass it. The rule applies to every model and arm alike. Tests: `eval/test_grade.py` (`OK 186`). `GRADING.md` itself is unchanged.

Grades changed by the rule (records, `eval/runs/regrade-diff.json`; all changes are correct-to-incorrect, none the other way; all on scored items):

| Model / arm | Records | Correct before | Correct after | Changed |
|---|---|---|---|---|
| haiku A0 | 350 | 289 | 280 | 9 |
| haiku A3 | 350 | 292 | 287 | 5 |
| phi4 A0 | 350 | 50 | 27 | 23 |
| phi4 A1 | 350 | 248 | 247 | 1 |
| phi4 A2 | 350 | 280 | 277 | 3 |
| phi4 A3 | 350 | 291 | 285 | 6 |

Total 47 of 2,100 records changed. The rule is a keyword filter: an answer containing such a phrase that also contains the key fact only in a paraphrase now fails, and a correct answer that says "the docs do not say X" about something else while giving the key fact verbatim still passes.

## Findings (keyword grade)

- phi4 (local): retrieval helps. A3 is correct on 49 of 60 questions (majority) against 4 for A0 (45 to 0, p < 0.0001, same direction in each kind). A3 against A1: 9 to 2 overall (p = 0.0654, not significant at 5 percent; per kind 2-1, 2-0, 5-1, none significant). A3 against A2: 2 to 1 (p = 1.0): no difference shown.
- A3 against A2 measures two things together: the engine's default search (status filter, tier boost, recency) and the citation instruction that only A3 carries, as the brief prescribes. It does not isolate the filter and boosts.
- Claude Haiku (hosted): no effect shown. A3 is correct on 49 of 60 questions and A0 on 47; 8 questions go to A3 and 6 to A0 (p = 0.79 overall; per kind 2-2, 3-1, 3-3, none significant). Haiku answers 80 percent of the scored runs correctly without retrieval (A0 majority 47 of 60), so on this set there is little room for retrieval to show a benefit, and a gain of the size seen (2 questions) is within noise. pass^5 is 41 of 60 for A0 and 47 of 60 for A3 (no test was pre-specified for pass^5, so this is a count only). Whether Haiku knows these public documents from training was not measured.
- Where A3 fails on Haiku: 8 scored items fail all five runs. Six (EX-05, EX-06, EX-16, EX-17, ST-10, ST-18) mostly return a disclaimer because retrieval did not return the line. Two stale items (ST-01, ST-02) fail all five runs because the answer names the older value while explaining a conflict between documents, which the stale-marker rule counts as stating it. These are the known limits of the heuristic in `GRADING.md`; the owner sample is the check. No cue rule was retuned.
- Retrieval itself: a top-8 hit covers a line in an item's `quotes` for 35 of 60 scored questions with A1 (lexical), 45 of 60 with A2 and 45 of 60 with A3. For the 20 stale items, a hit on the superseding line (`stale.current`) occurs for 5 of 20 with A1 and 9 of 20 with A2 and A3 (the stale cell of the first table counts `quotes`, which for stale items are the current statements the item asks for, and is 6, 10 and 10). A model with no prior knowledge would be capped near 75 percent (45 of 60) by the 15 retrieval misses; phi4 reaches 49 of 60 with A3, so some correct answers come from other retrieved text or the model's own knowledge (not separated).
- Citations (A3): Haiku 347 of 350 answers carry at least one citation that `engine/bin/cerebrollm verify` prints OK for (803 of 874 extracted quote and path pairs). phi4: 262 of 350 answers have a quote and a path, 184 of 350 have a verified one (314 of 579 pairs). The pairing rule is mine (see receipt); a paraphrase placed in quotes fails verify.
- Cost: Haiku A3 used 1,117,520 input tokens for 350 calls against 230,931 for A0 (4.8 times: retrieved context plus the CLI's fixed context of about 600 tokens per call); phi4 A3 577,890 input tokens against 18,130 for A0.

## Known limits (keyword grade)

- Code grading is a keyword heuristic with false passes and false fails (`GRADING.md`, last section). The owner's blind sample of 40 answers measured 34 agreements (17/20 per sheet).
- The owner sheets hide the arm, but A3 answers carry bracketed path citations and can be recognised by them.
- Haiku and phi4 did not share a temperature (the CLI has no temperature flag; phi4 ran at 0.7).
- The hosted calls carry the CLI's automatic context (about 600 input tokens per call). That it includes the account email rests on probe outputs that were not saved, so it is UNVERIFIED (receipt, D1).

## Owner grading

The owner graded both blind sheets (2026-10-29; `eval/owner-grading/sheet-A.md` is Haiku, `sheet-B.md` is phi4, per `key-A.json` and `key-B.json`) and agreed with the keyword grade on 17/20 per sheet, below the 18/20 that `GRADING.md` requires. The model grader of development step N4 was then validated against the same 40 grades (see the headline section) and the headline numbers are model grades; every number below this point, up to the end of the file, is a keyword grade.

Disagreements (sheet, sample, item, run, owner / code):

| Sheet | Sample | Item | Run | Owner | Code | Cause |
|---|---|---|---|---|---|---|
| A | S04 | ST-01 | 2 | Y | N | Answer names the old value while explaining the change; the stale-marker rule counts it as stated. |
| A | S16 | ST-01 | 3 | Y | N | Same as S04. |
| A | S15 | ST-10 | 1 | N | Y | Answer leads with `FunctionAgent`, names `AgentWorkflow` only for multi-agent use, and ends with an uncertainty disclaimer; the key fact matched. |
| B | S02 | ST-14 | 3 | Y | N | Answer gives "Jailbreak Templates Strategy" without the hyphenated id and names the old `prompt-injection` as deprecated. |
| B | S08 | ST-02 | 1 | Y | N | Answer gives 32k and quotes the old flat 4096 default as overridden; the stale-marker rule counts it as stated. |
| B | S16 | PA-02 | 1 | N | Y | Answer opens "I do not have specific information", then gives 4GB and a made-up citation; the key fact matched the contiguous-run rule, which the disclaimer rule does not block. |

Four of six are code false fails on stale items where the answer mentions the superseded value to reject it, so stale-item scores here are likely low. Two are code false passes on hedged answers.

## Tables, keyword grade (generated by `python3 eval/analyze.py --grades code`, copied from `eval/runs/tables.md`)

### haiku: scored items (60), per-question majority over the runs; run pass rate = share of all runs correct

| Arm | Runs/q | exact (20) | paraphrase (20) | stale (20) | all (60) | run pass rate e/p/s/all | pass^5 e/p/s/all |
|---|---|---|---|---|---|---|---|
| A0 | 5 | 16 | 17 | 14 | 47 | 0.83 / 0.89 / 0.67 / 0.80 | 16 / 16 / 9 / 41 |
| A1 | not run, ruling R-7 | | | | | | |
| A2 | not run, ruling R-7 | | | | | | |
| A3 | 5 | 16 | 19 | 14 | 49 | 0.80 / 0.96 / 0.71 / 0.82 | 16 / 19 / 12 / 47 |

Sign test, haiku: A3 against each arm on per-question majority (A3 only / other only / ties dropped, two-sided exact p)

| Comparison | exact | paraphrase | stale | all |
|---|---|---|---|---|
| A3 vs A0 | 2/2/16, p=1.0000 | 3/1/16, p=0.6250 | 3/3/14, p=1.0000 | 8/6/46, p=0.7905 |
| A3 vs A1 | not run, ruling R-7 |  |  |  |
| A3 vs A2 | not run, ruling R-7 |  |  |  |

Tokens and calls, haiku (all calls including practice items)

| Arm | Calls | input total | output total | input mean | output mean |
|---|---|---|---|---|---|
| A0 | 350 | 230931 | 181840 | 659.8 | 519.5 |
| A3 | 350 | 1117520 | 192471 | 3192.9 | 549.9 |

A3 citations, haiku: 349/350 answers have a quote and path; 347/350 have at least one citation that `verify` prints OK for; 803/874 extracted citations verify OK.

### phi4: scored items (60), per-question majority over the runs; run pass rate = share of all runs correct

| Arm | Runs/q | exact (20) | paraphrase (20) | stale (20) | all (60) | run pass rate e/p/s/all | pass^5 e/p/s/all |
|---|---|---|---|---|---|---|---|
| A0 | 5 | 1 | 3 | 0 | 4 | 0.05 / 0.13 / 0.05 / 0.08 | 0 / 1 / 0 / 1 |
| A1 | 5 | 15 | 17 | 10 | 42 | 0.74 / 0.84 / 0.49 / 0.69 | 14 / 16 / 8 / 38 |
| A2 | 5 | 16 | 18 | 14 | 48 | 0.82 / 0.91 / 0.68 / 0.80 | 16 / 17 / 11 / 44 |
| A3 | 5 | 16 | 19 | 14 | 49 | 0.82 / 0.95 / 0.69 / 0.82 | 16 / 19 / 9 / 44 |

Sign test, phi4: A3 against each arm on per-question majority (A3 only / other only / ties dropped, two-sided exact p)

| Comparison | exact | paraphrase | stale | all |
|---|---|---|---|---|
| A3 vs A0 | 15/0/5, p=0.0001 * | 16/0/4, p=0.0000 * | 14/0/6, p=0.0001 * | 45/0/15, p=0.0000 * |
| A3 vs A1 | 2/1/17, p=1.0000 | 2/0/18, p=0.5000 | 5/1/14, p=0.2188 | 9/2/49, p=0.0654 |
| A3 vs A2 | 0/0/20, p=1.0000 | 1/0/19, p=1.0000 | 1/1/18, p=1.0000 | 2/1/57, p=1.0000 |

Tokens and calls, phi4 (all calls including practice items)

| Arm | Calls | input total | output total | input mean | output mean |
|---|---|---|---|---|---|
| A0 | 350 | 18130 | 42236 | 51.8 | 120.7 |
| A1 | 350 | 632570 | 58126 | 1807.3 | 166.1 |
| A2 | 350 | 563035 | 60990 | 1608.7 | 174.3 |
| A3 | 350 | 577890 | 71642 | 1651.1 | 204.7 |

A3 citations, phi4: 262/350 answers have a quote and path; 184/350 have at least one citation that `verify` prints OK for; 314/579 extracted citations verify OK.

### Retrieval: scored items where a top-8 hit covers a line in `quotes` (exact / paraphrase / stale / all)

| Arm | exact | paraphrase | stale | all |
|---|---|---|---|---|
| A1 | 15/20 | 14/20 | 6/20 | 35/60 |
| A2 | 18/20 | 17/20 | 10/20 | 45/60 |
| A3 | 18/20 | 17/20 | 10/20 | 45/60 |

Stale items only: a top-8 hit on the superseding line (`stale.current`): A1 5/20, A2 9/20, A3 9/20.

Sign-test cells read "A3 only / other arm only / ties dropped, p"; `*` marks p < 0.05 (two-sided exact binomial, ties dropped, per-question majority). Hosted A1 and A2: not run, ruling R-7.

## Not measured

- Hosted arms A1 and A2 (not run, ruling R-7). Command: copy `eval/promptfoo-hosted.yaml` to a config with providers `arms/a1.py` and `arms/a2.py`, then `npx promptfoo@0.125.1 eval -c <config> --repeat 1 --no-cache -j 4`.
- Temperature for the hosted model: the `claude` CLI has no temperature flag; the default was used. phi4 ran at 0.7, so the two models do not share a temperature.
- Whether Haiku's A0 score comes from training data containing these documents. Command: add items on documents newer than its training cutoff, or on private text.
- Differences between retrieval arms for Haiku (A1 and A2 not run).
- Token counts of the retrieved context alone (counts are per call input tokens as reported by Ollama and the CLI; Haiku counts include cache reads and the CLI's fixed context).
- The effect of the CLI's fixed context on Haiku's A0 answers (about 600 input tokens in every call, the same in both arms).
- Failed attempts and retries of the hosted calls (see receipt: failed attempts were not saved).
