# Results v2: 35 public items across models and arms (development step N6a)

Source of the tables except time and keyword grade: `./summary.json` (made by `python3 eval/run_v2.py --out <OUT> report` from the records under `./<model>/<arm>/` and the grades in `./judge/`). Grader: `gpt-oss:20b` thinking medium (rubric `eval/judge.py` for the 20 answerable items, `eval/judge_v2.py` `RUBRIC_UN` for the 15 unanswerable items). The time and keyword-grade tables are computed from the records themselves. Classes are defined in `eval/GRADING-v2.md`. 'Majority' means more than half of the runs of an item.

## Per model and arm

| Model | Arm | Runs | Correct (of 20, majority) | Correct (run level) | Abstained correctly (of 15, majority) | Right outcome (of 35, majority) | Confidently wrong items (majority) | Confidently wrong (runs) | Abstained wrong (runs) | Empty (runs) | Aim 90% / under 2% |
|---|---|---|---|---|---|---|---|---|---|---|---|
| gpt-oss-20b | A4 | 105 | 17 (85.0%) | 51/60 (85.0%) | 14 (93.3%) | 31 (88.6%) | 2 | 6/105 (5.7%) | 6 | 0 | not met |
| gemma4-12b | A0 | 105 | 20 (100.0%) | 60/60 (100.0%) | 15 (100.0%) | 35 (100.0%) | 0 | 0/105 (0.0%) | 0 | 0 | met |
| gemma4-12b | A4 | 105 | 18 (90.0%) | 54/60 (90.0%) | 15 (100.0%) | 33 (94.3%) | 0 | 0/105 (0.0%) | 6 | 0 | met |

Aim: right outcome at least 90 percent of the 35 items (majority) and confidently wrong under 2 percent of runs. Confidently wrong: a wrong answer to an answerable item, or any answer to an unanswerable item.

## Items with any confidently-wrong run (rule of three)

- gpt-oss-20b A4: 2 of 35 items with a confidently-wrong run (G2-EX-04, G3-UN-01)
- gemma4-12b A0: 0 of 35 items with a confidently-wrong run; 95% upper bound on the share of items with a confidently-wrong run 8.6% (3 / 35 unique items), conditional on independent draws from the item population (repeated runs of the same item are not independent trials); it does not bound the run-level rate
- gemma4-12b A4: 0 of 35 items with a confidently-wrong run; 95% upper bound on the share of items with a confidently-wrong run 8.6% (3 / 35 unique items), conditional on independent draws from the item population (repeated runs of the same item are not independent trials); it does not bound the run-level rate

## Majority correct by kind

| Model | Arm | exact (of 10) | paraphrase (of 7) | stale (of 3) | unanswerable (of 15) |
|---|---|---|---|---|---|
| gpt-oss-20b | A4 | 9 | 5 | 3 | 14 |
| gemma4-12b | A0 | 10 | 7 | 3 | 15 |
| gemma4-12b | A4 | 10 | 5 | 3 | 15 |

## Retrieval and citations (arm A3)

Top-8 default search holds every quoted line for 0 of 20 answerable items (`./retrieval/A3/`). Not-hit items: none.

| Model | A3 answers | With a verified citation | Share |
|---|---|---|---|

## Time (sum of per-call seconds in the records)

| Model | Arm | Calls | Total | Mean per call |
|---|---|---|---|---|
| gpt-oss-20b | A4 | 105 | 50.8 min | 29.0 s |
| gemma4-12b | A0 | 105 | 50.8 min | 29.0 s |
| gemma4-12b | A4 | 105 | 50.8 min | 29.0 s |

## Grader cross-check (gpt-oss:20b answers graded by gpt-oss:20b and by gemma4:12b thinking off)

Same verdict on 84 of 105 answers (80.0%); Cohen's kappa on Y/N -0.089.
- arm A0, answerable items: 17 of 20 the same
- arm A0, unanswerable items: 13 of 15 the same
- arm A4, answerable items: 29 of 40 the same
- arm A4, unanswerable items: 25 of 30 the same

Disagreements: 21 (listed in `./summary.json` under `judge_disagreements`).

## Keyword grade against the model grade (answerable items, GRADING.md section 1)

| Model | Arm | Answers | Both Y | Keyword Y, model N | Keyword N, model Y |
|---|---|---|---|---|---|
| gpt-oss-20b | A4 | 60 | 51 | 0 | 0 |
| gemma4-12b | A0 | 60 | 60 | 0 | 0 |
| gemma4-12b | A4 | 60 | 54 | 0 | 0 |

Grader replies that did not parse (recorded as error): 0.
