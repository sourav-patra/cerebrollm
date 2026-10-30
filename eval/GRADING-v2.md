# Grading rules for the v2 item set (development step N5)

`eval/GRADING.md`, `eval/items.jsonl` and `eval/check_items.py` stay frozen. This file adds only what the new items need. Nothing here changes how the 70 frozen items are graded.

## Items

`eval/items-v2.jsonl` holds 35 public items. Group 1 (own project docs, about 27 picks) is private: it lives in `~/.cerebrollm/private-eval/items.json` outside this repository and is loaded only with `--private`. The owner marks each pick keep or drop in `PICKS.md` before any model sees it.

| Group | What | Kinds | Where the sources are |
|---|---|---|---|
| 1 | The owner's own project docs (private; kept items only) | exact, paraphrase, stale | `<projects folder>/<project>/...`, never copied into this repository |
| 2 | Public documentation released after 2026-06 | exact 10, paraphrase 7, stale 3 | `eval/v2-sources/` (GitHub release notes; each file records URL, publication date and fetch date) |
| 3 | Questions on the corpus topics whose answer is in no indexed document | unanswerable 15 | none; `absent_terms` must occur in neither the corpus nor `eval/v2-sources/` |

Fields are those of `items.jsonl` plus `group`, and: `released` (group 2: newest publication date among the cited sources), `tags` (`public-fork` marks a fork of a public project), `pick` (group 1 only: note path, sha256 at pick time, line range, reason), and for group 3 `expected`, `absent_terms`, `note`.

## Grading

- Groups 1 and 2, kinds exact, paraphrase and stale: the code grading of `GRADING.md` section 1 and the model grading of section 3, unchanged. `eval/grade_lib.py` reads these items as it reads the old ones.
- Group 3, kind unanswerable: the correct answer is that the information is not in the sources. An answer that gives a specific value, name or procedure for the asked fact is confidently wrong, whether or not it hedges. An answer that says it does not know and gives nothing else is correct. The model-grader rubric for this kind must be written and frozen in the order that runs the arms, before the first run; `grade_lib.grade` does not handle this kind and the keyword grade is not used for it.
- Report abstentions as their own number: for groups 1 and 2 an abstention is incorrect; for group 3 it is correct.

## Checking

`python3 eval/check_items_v2.py [--private ~/.cerebrollm/private-eval/items.json]` (it reads `SOURCES.txt` beside that file for the projects folder and the never-open list; `--sources` and `--notes-root` override) verifies every path, line and quote, the publication date of each group 2 source (on or after 2026-07-01), the group counts, that no `absent_terms` entry occurs in the corpus, and for group 1 the sha256 and line range recorded at pick time. A note that changed since it was picked fails the check: re-pick it. Tests: `python3 -m unittest eval/test_check_items_v2.py`.

## Model-grader rubric for unanswerable items (development step N6a, frozen before the first graded call)

Items of kind `unanswerable` (group 3) use this rubric instead of the one in `GRADING.md` section 3. Everything else about the model grader is as in section 3: one call per answer, JSON `{"verdict": "Y"|"N", "reason": "<one sentence>"}`, temperature 0, an unparsable reply retried once and then recorded as `error`. The wording in `eval/judge_v2.py` `RUBRIC_UN` is the text of record.

1. Y only when the answer says the information is not in the sources (or that it does not know) and states no invented answer for the asked fact.
2. N when the answer gives a specific value, name, version, flag, command or procedure for the asked fact, whether or not it hedges and whether or not it cites a source.
3. N when the answer says it does not know and then offers a guess or a general-knowledge value for the asked fact.
4. Describing what the sources do cover does not change the verdict while no answer to the asked fact is given. An answer that only asserts that the thing does not exist, without saying the sources lack it or that it does not know, is N.
5. Citations and style do not change the verdict.

The grader sees the question and the answer only. An empty answer is not sent to the grader: it is recorded as `empty`, neither correct nor confidently wrong.

## Classes reported by lane N6a

For every answer: `correct` (answerable item, grader Y), `abstained-correctly` (unanswerable item, grader Y), `abstained-wrong` (answerable item, grader N, and the answer contains a phrase of `grade_lib.DISCLAIMERS` or, for arm A4, the pipeline printed `Not in the sources.`), `empty` (no text after removing a think block), `confidently wrong` (every other grader N: a wrong answer to an answerable item, or any answer to an unanswerable item). Per item the class of the majority of runs is used (more than half of the runs); the run-level rate is reported beside it. Aim: at least 90 percent correct, under 2 percent confidently wrong.

