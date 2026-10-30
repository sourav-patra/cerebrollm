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

