# A4: verified-quotes output against 0.1.2

Arm A4 (`cerebrollm ask`) on the 35 public items of `eval/items-v2.jsonl`, `gpt-oss:20b` thinking medium, 3 runs per item, graded by `gpt-oss:20b` with the rubrics of `eval/GRADING-v2.md`. One machine, one index, one configuration for both runs. Run records are not committed; this file holds the aggregates and the cases.

| Run | Engine commit | Dates (UTC) | Right outcome (of 35, majority) | Correct answerable runs (of 60) | Confidently wrong runs (of 105) | Abstained wrong runs |
|---|---|---|---|---|---|---|
| 0.1.2 rerun | `56f13e0` (0.1.2 engine) | 2026-11-08 | 33 | 56 | 0 | 4 |
| verified quotes | `f1763a9` | 2026-11-08 to 2026-11-11 | 33 | 54 | 2 | 4 |

`f1763a9` is the pre-review commit of the change merged as `eb16826` ([pull request 18](https://github.com/sourav-patra/cerebrollm/pull/18)). Review then added two things the run does not cover: `--json` hides the generator's text without `--show-text`, and a citation path is compared after `.` and `..` are resolved.

The two confidently wrong runs:

- G2-EX-05 run 1, incomplete: the question asks for three types and the printed verified quote names one (`choice`).
- G2-EX-03 run 3, wrong: asked for the context window of one model, `ask` printed the verified line "24-48 GiB VRAM: 32k context" from Ollama's general context-length page; the reference is 262K. A verified quote can answer a different question; release map 0.2 item 1 targets that.

The 0.1.2 release entry in `CHANGELOG.md` reports 3 of 105 confidently wrong runs from an earlier run of the same engine; the rerun above found 0. With 3 runs per item, differences of 1 to 3 runs are within run-to-run variation; no significance test was run.
