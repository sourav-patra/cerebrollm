Grades in this file: model grade (gpt-oss:20b, GRADING.md section 3).

### haiku: scored items (60), per-question majority over the runs; run pass rate = share of all runs correct

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

### phi4: scored items (60), per-question majority over the runs; run pass rate = share of all runs correct

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

### Retrieval: scored items where a top-8 hit covers a line in `quotes` (exact / paraphrase / stale / all)

| Arm | exact | paraphrase | stale | all |
|---|---|---|---|---|
| A1 | 15/20 | 14/20 | 6/20 | 35/60 |
| A2 | 18/20 | 17/20 | 10/20 | 45/60 |
| A3 | 18/20 | 17/20 | 10/20 | 45/60 |

Stale items only: a top-8 hit on the superseding line (`stale.current`): A1 5/20, A2 9/20, A3 9/20.

