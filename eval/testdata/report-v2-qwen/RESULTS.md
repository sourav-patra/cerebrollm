# Results v2: 35 public items across models and arms (development step N6a)

Source of the tables except time and keyword grade: `./summary.json` (made by `python3 eval/run_v2.py --out <OUT> report --judge qwen3.5:9b` from the records under `./<model>/<arm>/` and the grades in `./judge/`). Grader: `qwen3.5:9b` thinking off (rubric `eval/judge.py` for the 20 answerable items, `eval/judge_v2.py` `RUBRIC_UN` for the 15 unanswerable items). The time and keyword-grade tables are computed from the records themselves. Classes are defined in `eval/GRADING-v2.md`. 'Majority' means more than half of the runs of an item.

## Per model and arm

| Model | Arm | Runs | Correct (of 20, majority) | Correct (run level) | Abstained correctly (of 15, majority) | Right outcome (of 35, majority) | Confidently wrong items (majority) | Confidently wrong (runs) | Abstained wrong (runs) | Empty (runs) | Aim 90% / under 2% |
|---|---|---|---|---|---|---|---|---|---|---|---|
| gpt-oss-20b | A4 | 105 | 14 (70.0%) | 42/60 (70.0%) | 12 (80.0%) | 26 (74.3%) | 7 | 21/105 (20.0%) | 6 | 0 | not met |
| gemma4-12b | A0 | 105 | 16 (80.0%) | 48/60 (80.0%) | 12 (80.0%) | 28 (80.0%) | 7 | 21/105 (20.0%) | 0 | 0 | not met |
| gemma4-12b | A4 | 105 | 15 (75.0%) | 45/60 (75.0%) | 12 (80.0%) | 27 (77.1%) | 6 | 18/105 (17.1%) | 6 | 0 | not met |

Aim: right outcome at least 90 percent of the 35 items (majority) and confidently wrong under 2 percent of runs. Confidently wrong: a wrong answer to an answerable item, or any answer to an unanswerable item.

## Items with any confidently-wrong run (rule of three)

- gpt-oss-20b A4: 7 of 35 items with a confidently-wrong run (G2-EX-01, G2-EX-04, G2-PA-05, G2-ST-03, G3-UN-01, G3-UN-06, G3-UN-11)
- gemma4-12b A0: 7 of 35 items with a confidently-wrong run (G2-EX-01, G2-PA-01, G2-PA-05, G2-ST-03, G3-UN-01, G3-UN-06, G3-UN-11)
- gemma4-12b A4: 6 of 35 items with a confidently-wrong run (G2-EX-01, G2-PA-05, G2-ST-03, G3-UN-01, G3-UN-06, G3-UN-11)

## Majority correct by kind

| Model | Arm | exact (of 10) | paraphrase (of 7) | stale (of 3) | unanswerable (of 15) |
|---|---|---|---|---|---|
| gpt-oss-20b | A4 | 8 | 4 | 2 | 12 |
| gemma4-12b | A0 | 9 | 5 | 2 | 12 |
| gemma4-12b | A4 | 9 | 4 | 2 | 12 |

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

## Grader cross-check (gpt-oss:20b answers graded by qwen3.5:9b and by gemma4:12b thinking off)

Same verdict on 72 of 105 answers (68.6%); Cohen's kappa on Y/N -0.027.
- arm A0, answerable items: 15 of 20 the same
- arm A0, unanswerable items: 10 of 15 the same
- arm A4, answerable items: 27 of 40 the same
- arm A4, unanswerable items: 20 of 30 the same

Disagreements: 33 (listed in `./summary.json` under `judge_disagreements`).

## Keyword grade against the model grade (answerable items, GRADING.md section 1)

| Model | Arm | Answers | Both Y | Keyword Y, model N | Keyword N, model Y |
|---|---|---|---|---|---|
| gpt-oss-20b | A4 | 60 | 42 | 9 | 0 |
| gemma4-12b | A0 | 60 | 48 | 12 | 0 |
| gemma4-12b | A4 | 60 | 45 | 9 | 0 |

Grader replies that did not parse (recorded as error): 0.
