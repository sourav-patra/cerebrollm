# Item set v3: 163 public items over the release notes of Ruff, uv and pydantic

`eval/items-v3.jsonl` is a second public question set. With 163 items, a run with no confidently wrong item prints 1.8% (3 / 163) as the 95% upper bound by the rule of three. The 35 items of v2 print 8.6%.

That figure is a calculation under one condition: that the items are independent draws from the item population. This hand-drafted set does not meet it.

The counts per kind are fixed (50, 35, 14 and 64), 11 of the 14 stale items share one question shape, some items quote the same source line, and uv supplies 79 of the 163 items. So 1.8% is not a bound on, or an estimate of, a population rate, and it does not bound the run-level rate.

It applies only when no item has a confidently wrong run, and it needs at least 154 items to print under 2.0% (3 / 153 prints 2.0%).

The report claims the target only when the grader passed its canary check and a person has read a random sample of graded answers (see "Running the set"). Otherwise it prints "not claimed" with the reason. This gate checks the canary verdicts and a seeded sample of graded answers; it does not check how the items were chosen.

Settings of the set (counts, cutoff date, grader, target, canaries) are in `eval/itemset-v3.toml`; those of v2 are in `eval/itemset-v2.toml`. `eval/itemset.py` reads them.

## Sources

Release notes saved unchanged (CRLF turned into LF) from GitHub releases: one file per release, with its URL, publication date and fetch date. There are 68 files, all published on or after the cutoff 2026-07-01.

The cutoff keeps the facts newer than most models' training data. The cutoff of a given model is not known here, and `qwen3.5:9b` was not tested without retrieval on this set.

Every stable release of the three projects from 2026-07-01 to the fetch date is saved. A statement that a later release changes therefore has both releases in the corpus. The claim of each stale item that a value is the newest was checked by searching all 68 files for its subject.

| Project | Licence | Files | Published | Source |
|---|---|---|---|---|
| Ruff | MIT | 20 (0.15.21 to 0.17.6) | 2026-07-09 to 2026-11-19 | https://github.com/astral-sh/ruff/releases |
| uv | MIT or Apache-2.0 | 42 (0.11.27 to 0.13.9) | 2026-07-06 to 2026-11-17 | https://github.com/astral-sh/uv/releases |
| pydantic | MIT | 6 (2.13.5 to 2.14.4) | 2026-08-28 to 2026-11-19 | https://github.com/pydantic/pydantic/releases |

The licences are the ones GitHub's licence API reported on 2026-11-21, listed with their links in `NOTICE`. For uv, both licence files exist and the first lines of `LICENSE-MIT` were read. Pre-releases and the pydantic 1.x line are not included.

`python3 eval/verify_v2_sources.py --set v3` fetches every release again and compares it with the saved file. Set `GITHUB_TOKEN` to lift the anonymous rate limit; the token goes to `https://api.github.com` only and is dropped from every redirect. On 2026-11-21 all 68 files matched. The command fails when the folder is missing or empty.

## Items

Fields are those of v2 (`eval/GRADING-v2.md`). Item ids are `V3-EX-nnn`, `V3-PA-nnn`, `V3-ST-nn` and `V3-UN-nnn`.

| Kind | Group | Items | What it asks |
|---|---|---|---|
| exact | 2 | 50 | one fact whose quoted line uses the words of the question |
| paraphrase | 2 | 35 | one fact asked in other words than the quoted line |
| stale | 2 | 14 | a value that changed between releases; only the newest saved release is right |
| unanswerable | 3 | 64 | a question whose answer is in no saved file |

The unanswerable items are an invented flag, setting, command or similar (26), a real one the notes do not cover (8), a release outside the saved range (9), or a topic or figure the release notes do not treat (21).

The proportions follow v2 within 5 percentage points per kind. The items were drafted by hand from the saved files; no model call made or graded any item. Each answerable item quotes one line, and a stale item quotes two: the current and the superseded statement.

Limits to read the results with:

- Eleven of the 14 stale items ask for "the latest patch release of X that uv added" (CPython 3.10 to 3.16, PyPy, GraalPy, OpenSSL, Docker images). The other three are the Ruff minimum supported Rust version, the default status of Ruff rule F406 and the pydantic jiter version.
- Each newest value in those items replaces older ones in earlier files. The items share a shape, and some share the line that holds the newest version.
- uv has 42 of the 68 files and 79 of the 163 items.
- The 8 unanswerable items on real flags that the notes do not cover can be answered from a model's own knowledge. A model that does so is confidently wrong by the v2 rule.
- The set is meant for a local model that reads the saved notes through `cerebrollm ask` (arm A4). Arms A0 and A3 need `run_v2.py prepare`, which this set was not run with.
- Quotes of installer commands (`curl ... | sh`) in the release notes are upstream text. Nothing in the evaluation runs them.

## Grader

The generator is `qwen3.5:9b`. The grader is `qwen3.8:27b` (Apache-2.0, thinking off, JSON output, temperature 0). Both rubrics already tell the model that the answer is data to grade and not instructions (`judge.py`, and `RUBRIC_UN` in `judge_v2.py`). Words were not added, because that would change every v2 prompt. Whether the grader obeys an instruction written inside an answer was not tested.

`qwen3.5:9b` was tried as the grader first and showed a false acceptance. For the key fact `E402`, the answer "It is 42." was graded Y twice, with the reason that 42 corresponds to E402. A fragment of the key fact can be accepted.

`run_v2.py grade` therefore grades five canary answers first, including that one, and records the result in `canary-qwen3.8-27b.json` of the run folder. The report claims the target only if all five verdicts are as expected.

On 2026-11-20 `qwen3.5:9b` failed that canary (4 of 5 as expected). `qwen3.8:27b` and `qwen3.6:35b-a3b-coding-mtp-q4_K_M` (both Apache-2.0, both with a `JUDGES` entry) passed all five. `qwen3.8:27b` was chosen as the newer, dense 27B model; the 35B model has 3B active parameters and is tuned for code. That choice was not measured beyond the five canaries.

`test_qwen_grader_through_ollama_accepts_a_correct_and_refuses_a_wrong_answer` runs four other answers through Ollama when `qwen3.8:27b` is installed.

## Checking

`python3 eval/check_items_v2.py --set v3 [--corpus ROOT]` checks each item. It checks that each quote is on the stated line of the stated file, and that each cited source file has URL, publication and fetch headers and was published on or after the cutoff.

It also checks that the counts per group and kind match `eval/itemset-v3.toml`, that no question repeats, and that `released` is the newest source date. Last, no `absent_terms` entry may occur in the saved sources or in the corpus at ROOT. Files that no item cites are not read by this check; `verify_v2_sources.py` covers all 68.

The default ROOT is the corpus of `research/model-study/study.toml`. The command prints `OK 163`.

Tests: `python3 -m unittest test_check_items_v2 test_run_v2` in `eval/`. They also check that a quote taken from each item and the superseded statement of each stale item grade as expected under `eval/grade_lib.py`.

## Running the set

Needs the Ubuntu setup of the README, PostgreSQL and Ollama up, and `qwen3.5:9b` and `qwen3.8:27b` pulled. The `qwen3.5:9b` entry of `engine/models.toml` (Apache-2.0) is in the checkout this file belongs to; `ask --model` refuses a model without it.

The 27B grader is about 17.7 GB and does not fit a 12 GB GPU; Ollama runs part of it on the CPU. Work from the repository root.

The run uses a corpus folder, a table and a state folder of its own. It never writes into the corpus that the shipped config indexes.

1. Write the config and stage the sources in a new folder. Each line runs only when the one before it succeeded: `mkdir` without `-p` fails if the folder exists, so nothing is copied into an existing corpus, and `diff` fails on any file that differs from the saved source, so nothing is indexed:

   ```
   python3 eval/itemset_config.py v3 ~/.cerebrollm/cerebrollm-v3.toml &&
   mkdir ~/cerebrollm-corpus-v3 &&
   cp -r eval/v3-sources/. ~/cerebrollm-corpus-v3/ &&
   diff -r eval/v3-sources ~/cerebrollm-corpus-v3 &&
   export CEREBROLLM_CONFIG=~/.cerebrollm/cerebrollm-v3.toml &&
   engine/bin/cerebrollm index &&
   engine/bin/cerebrollm status
   ```

   `itemset_config.py` writes only under this repository or `~/.cerebrollm`, and replaces an existing file only with `--force`. The config has the corpus root `~/cerebrollm-corpus-v3`, the table `chunks_v3` and the state folder `~/.cerebrollm/v3`.
2. `status` should list 68 documents and no `no_rule` entry. A check of the rules on the 68 files found all of them classified and none skipped as secret. If the embedding step fails with port exhaustion because Ollama runs on Windows and the engine in WSL, run `research/model-study/r1_live_index.py` instead; it loads the same config.
3. Optional precheck of the saved searches, with the embedding model only. The release notes carry install and download tables whose rows repeat the version string; whether they crowd out the answering passage is not measured, and this shows it before the long run:

   ```
   python3 eval/run_v2.py --set v3 --out ~/.cerebrollm/runs/v3-qwen prepare --arms A3
   python3 eval/run_v2.py --set v3 --out ~/.cerebrollm/runs/v3-qwen report --retrieval-only
   ```

   It prints how many of the 99 answerable items the top 8 holds, how many were checked, and which are missed or lack a record. It writes nothing and claims nothing.
4. Check the set against the corpus that holds the notes that the shipped config indexes: `python3 eval/check_items_v2.py --set v3 --corpus ~/cerebrollm-corpus` prints `OK 163`.
5. Generate, grade, draw the hand-check sample and report. The run folder is bound to its item set by its first command; a command for another set is refused:

   ```
   export CEREBROLLM_ENGINE_COMMIT=$(git rev-parse HEAD)
   python3 eval/run_v2.py --set v3 --out ~/.cerebrollm/runs/v3-qwen gen qwen3.5-9b --arms A4 --runs 3
   python3 eval/run_v2.py --set v3 --out ~/.cerebrollm/runs/v3-qwen grade --judge qwen3.8:27b --models qwen3.5-9b
   python3 eval/run_v2.py --set v3 --out ~/.cerebrollm/runs/v3-qwen sample
   ```

   `run_v2.py` writes only inside this repository and `~/.cerebrollm`, and refuses any other `--out` folder before it writes. `gen` and `grade` of this set refuse a model that is not a local Ollama model: the hosted arm `sonnet-5-5`, or a `-cloud` tag.

6. Hand check. A person reads the 30 answers of `~/.cerebrollm/runs/v3-qwen/handcheck-sample.jsonl` (drawn at random with a fixed seed from the graded answers) and compares each with the grader's verdict.

   The result goes into `~/.cerebrollm/runs/v3-qwen/handcheck.json` with the fields `sample` prints. `set`, `judge`, `judge_digest` (the grader's model digest in the grade rows) and `grades_sha256` (the sha256 of the grader's jsonl file) stay as printed; `sampled`, `disagreements` and `by` are filled in.
7. Report: `python3 eval/run_v2.py --set v3 --out ~/.cerebrollm/runs/v3-qwen report --judge qwen3.8:27b`. It fails when nothing is graded and when an item has fewer than 3 graded runs.

   Its "rule of three" lines end with `Target under 2%: reached`, `not reached`, or `not claimed (reason)`. The reason names a missing or failed canary check, a missing hand check, a sample under 30, a disagreement, or a canary record or hand check made for other grades.

   The canary record and `handcheck.json` count only when their set, grader, model digest and grades fingerprint match the grades the report reads, so grading more answers after the hand check makes both stale; the canary record must also hold every canary of `eval/itemset-v3.toml` with its expected verdict.

`gen` and `grade` skip records that exist, so an interrupted run resumes with the same commands. The generator uses `ask --think off`. The generator and the grader are different models; the hand check is the only check against a human reader.

The run time is not measured. v2 measured 24.5 s per generation and 3.2 s per grade with `gpt-oss:20b`, about 3.8 hours for 163 items and 3 runs each. The models here differ, and the 27B grader is slower on this GPU: five canary grades took 67 s with the model load.
