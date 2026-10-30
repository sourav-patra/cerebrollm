# R1 on the WSL machine (2026-10-29)

Authority: development step L, issue #10, ruling R-2. Record: the development step L record (not published). Raw results and their hashes: `r1-wsl/` and `selection/`.

Machine: Windows 11, RTX 4070 SUPER 12 GB, Ollama 0.40.12 on Windows, engine and PostgreSQL in Ubuntu-24.04 (WSL2). Corpus: the public corpus of ruling R-1 (1,416 Markdown files at pinned commits, `research/corpus/manifest.json`). Snapshot: the 13,431 chunks of the live table after a full `index` with bge-m3 (13,382 `current`, 49 `superseded`; 13,346 distinct texts), sha256 `5900cdc7...ba7c19` (`r1-wsl/snapshot-info.json`; `selection/snapshot-manifest.json` lists every node id in sampling order with status and text sha256 so the sample can be replayed: `python -m unittest test_selection_replay`). Every model indexes exactly this snapshot into its own table at `num_ctx` 8,192 (documents carry no prefix; Qwen queries carry the prefix of issue #10).

Selection set (rebuilt, see `selection/protocol.json`): 150 chunks, seed 27, phi4 (temperature 0, `num_ctx` 16,384) writing one question per chunk with the LlamaIndex `generate_qa_embedding_pairs` helper and the original prompt. Sources: promptfoo 96, llama_index 42, ollama 10, cerebrollm 2. Two further chunks drawn from the same seeded permutation produced no valid question in five attempts (each question named a path or file) and were skipped; the next chunks were used. None of the 150 sampled chunks has identical text under another node id, so node-id scoring and text-identity scoring give the same numbers for every cell below.

## Table (150 questions; hit@k = share of questions whose chunk is in the top k, MRR@10 = mean reciprocal rank in the top 10)

Scored by node id (the fixed rule) and, identically, by text identity.

| Model | Chunks | Index min | Chunks/min | Vector hit@5 / hit@10 / MRR@10 | Hybrid hit@5 / hit@10 / MRR@10 | `ollama ps` at `num_ctx` 8,192 |
|---|---:|---:|---:|---|---|---|
| `bge-m3` | 13,431 | 8.77 | 1,532 | 0.853 / 0.907 / 0.741 | 0.893 / 0.913 / 0.812 | 689 MB, 100% GPU |
| `qwen3-embedding:0.6b` | 13,431 | 8.96 | 1,499 | 0.900 / 0.920 / 0.795 | 0.927 / 0.953 / 0.846 | 1.7 GB, 100% GPU |
| `qwen3-embedding:4b` | 13,431 | 8.78 | 1,530 | 0.853 / 0.880 / 0.759 | 0.907 / 0.933 / 0.811 | 4.1 GB, 100% GPU |

Embedding length: bge-m3 1,024 and `qwen3-embedding:0.6b` 1,024 natively; `qwen3-embedding:4b` returns 2,560 natively and 1,024 when the request carries `dimensions: 1024` (the original method of `retrieval.py`), so the schema stays 1,024. `r1-wsl/embedding-dims.json`.

Index time and chunks/min are capped, not measured at full speed: `embed_pace.py` limits every embed call to 25 texts per second (1,500 chunks/min) because Windows ran out of ephemeral ports at full speed (HTTP 400 "Only one usage of each socket address"; the two failed unpaced runs are in `r1-wsl/logs/l-index-bge.attempt1.log` and `l-index-bge.attempt2.log`). The figures that explain it, about 3.4 TCP connections per embedded text and 11,438 sockets in TIME_WAIT of 16,384 dynamic ports, were read from console output and are unverified: no log was kept; the command that measures them is `r1-wsl/logs/socket-probe.sh` (needs a loaded embedding model) with `netstat -ano | find /c "TIME_WAIT"` before and after. All three models finished at the cap, so chunks/min does not separate them. Backoff seconds excluded from index time: 0 for all three (`r1-wsl/r1-table.json`, `r1-wsl/index/<table>/summary.json`).

## Rule and choice

Rule (fixed in development step D before any result): highest hybrid hit@5 on node-id scoring, then hybrid MRR@10, then chunks/min; indexing under 60 minutes. All three index in under 9 minutes.

Choice: `qwen3-embedding:0.6b`. Deciding number: hybrid hit@5 0.927 against 0.907 (`qwen3-embedding:4b`) and 0.893 (`bge-m3`); the later tie-breakers were not reached. Its hybrid MRR@10 (0.846) and both vector figures are also the highest. The margin over the 4B model is 3 of 150 questions at hit@5; this is a small sample, so the ordering of the 0.6B and 4B models is not firmly established, but the rule is applied as written.

Live index: `engine/cerebrollm.toml` now sets `model = "qwen3-embedding:0.6b"` and an `[ollama] query_prefix`; `store.embed_model` passes the prefix as the query instruction (documents get none). The live table was rebuilt with a full `index`: 13,431 chunks, 583.2 s (9.7 min) of embedding, 1,412 documents, same paced wrapper (`r1-wsl/logs/l-index-qwen.log`: summary, `status` and the live row count before the swap; a first attempt that hit a Postgres deadlock in the swap is `l-index-qwen.attempt1.log` with `postgres-deadlock-excerpt.log`). It held 13,431 chunks (bge-m3) before the swap (same log). The first live index with bge-m3 is `r1-wsl/logs/l-index-bge.log` (709.3 s including one 130 s backoff). `bge-m3` stays installed.

# R2 on the WSL machine (2026-10-29)

Authority: development step M, issue #11, rulings R-3 to R-5. Record: the development step M record (not published). Raw per-case files, their hashes and the tables: `r2-wsl/` (`r2-table.md`, `r2-table.json`). Scripts: `r2_wsl.py` (measurements), `r2_report.py` (tables and rules).

Machine: RTX 4070 SUPER 12 GB, Ollama 0.40.12 on Windows, runner in Ubuntu-24.04, generated code in `docker.exe run --rm --network none --read-only`, read-only mount, 20-second timeout (sandbox proven first: `r2-wsl/sandbox-check.json`). Method as in development step D: 40 HumanEval tasks (seed 27), temperature 0, one attempt, `num_ctx` 16,384, `num_predict` 4,096 for code and 2,048 for tools. phi4 was re-run on this machine (R-3); its Mac numbers stay below as reference.

Tool scenarios: the 2026-10-27 scenario file was never committed, so these 12 are new, written and committed (commit 2d64db3, blob sha256 `0299a9aa...2a4`) before any model ran. Four tools (`read_file`, `write_file`, `run_tests`, `search_code`), three scenarios each, scored by exact tool name and exact argument equality on the first reply.

## Correctness and speed (all rows measured; speed = mean of 3 valid runs after a warm-up)

| Model / mode | Code pass@1 | Tool pass | Combined /100 | Gen tok/s, 8,000-token prompt / 200-token prompt | Prompt tok/s (8,000) | TTFT s (8,000) | GPU share at 16,384 (`ollama ps`) |
|---|---:|---:|---:|---|---:|---:|---|
| `phi4` / default | 35/40 (87.5%) | 0/12 (no tool support, HTTP 400) | 43.75 | 14.5 / 22.2 | 1,711 | 4.48 | 81% (19% CPU), 12 GB |
| `devstral:24b` / default | 33/40 (82.5%) | 11/12 | 87.08 | 4.3 / 6.7 | 834 | 7.67 | 58% (42% CPU), 17 GB |
| `gpt-oss:20b` / medium (R2a) | 39/40 (97.5%) | 12/12 | 98.75 | 46.2 / 60.2 | 3,302 | 4.69 | 71% (29% CPU), 14 GB |
| `gpt-oss:20b` / low (R2b) | 38/40 (95.0%) | 12/12 | 97.50 | 58.2 / 60.3 | 3,300 | 2.42 | 71% (29% CPU), 14 GB |
| `qwen3:14b` / thinking on (R2a) | 37/40 (92.5%) | 12/12 | 96.25 | 15.7 / 25.0 | 1,831 | 4.41 | 84% (16% CPU), 12 GB |
| `qwen3:14b` / thinking off (R2b) | 36/40 (90.0%) | 12/12 | 95.00 | 15.1 / 25.0 | 1,830 | 4.14 | 84% (16% CPU), 12 GB |
| `qwen3:8b` / thinking off (R2b) | 33/40 (82.5%) | 12/12 | 91.25 | 67.5 / 81.5 | 4,142 | 1.88 | 100%, 7.5 GB |

For the record, ruling R-4 (not in the rules; both exceed 12 GB VRAM):

| Model / mode | Code pass@1 | Tool pass | Combined /100 | Gen tok/s 8,000 / 200 | Prompt tok/s (8,000) | TTFT s (8,000) | GPU share |
|---|---:|---:|---:|---|---:|---:|---|
| `qwen3-coder:30b` / default | 38/40 (95.0%) | 9/12 | 85.00 | 42.0 / 41.7 | 1,576 | 4.73 | 51% (49% CPU), 20 GB |
| `qwen3:30b` / thinking off | 2/40 (5.0%) | 12/12 | 52.50 | 43.6 / 43.4 | 1,594 | 5.08 | 51% (49% CPU), 20 GB |

Notes on the numbers:
- `qwen3:14b` thinking on: 3 of the 3 failures stopped at the 4,096-token limit with the answer still inside the reasoning (empty content). `qwen3:30b` with `think: false` still writes its reasoning into the content ("Okay, let's see..."), so 37 of 40 code cases fail with a SyntaxError from the prose; 5 stopped at the token limit and 1 request returned HTTP 500. The tool column for `qwen3:30b` is not affected.
- `devstral:24b` carries a chat-template system prompt of about 1,200 tokens, so its "200-token" prompt measured 1,262 tokens (calibration in `speed/devstral-24b-default/200-calibration.json`). Its 200-token prompt rate (75 tok/s) counts only uncached tokens and is not comparable.
- phi4 passes 35/40 here and passed 33/40 on the Mac; the difference is not investigated (same prompt, temperature 0, same seed; different hardware and Ollama version).
- Load: Ubuntu one-minute load stayed at or below 1.13 during correctness (per-case values in each record). Speed runs passed the quiet-machine gate defined in the run record before each measurement (Ubuntu load at most 0.19, Windows CPU at most 19.8%, GPU at most 14%, only the model under test loaded); all 42 core speed runs were valid.

## Rules applied (issue #11, as written)

- Best R2 code pass@1 across modes: 97.5% (`gpt-oss:20b` medium). Best combined: 98.75 (same).
- R2a (highest combined with generation at least 15 tokens/s at 16,384 context and 100% GPU): no candidate qualifies. The R2a candidates (`devstral:24b`, `gpt-oss:20b` medium, `qwen3:14b` thinking on, `phi4`) run at 58%, 71%, 84% and 81% GPU. `gpt-oss:20b` medium and `qwen3:14b` thinking on fail only the GPU gate; `devstral:24b` (4.3 tok/s) and `phi4` (14.5 tok/s) also fail the 15 tok/s minimum. Closest by combined score: `gpt-oss:20b` medium (98.75, 46.2 tok/s, 71% GPU), then `qwen3:14b` thinking on (96.25, 15.7 tok/s, 84% GPU). R2a is left unfilled; the 100% GPU requirement is the owner's to relax.
- R2b (highest generation tok/s among models within 10 points of the best code pass@1, that is 87.5% or more): `gpt-oss:20b` low, 58.2 tok/s at the 8,000-token prompt (60.3 at 200) against `phi4` 14.5 and `qwen3:14b` off 15.1. `qwen3:8b` is faster (67.5) but 15 points below the best code score, so it is excluded.
- Sharing (one model fills two roles if within 5 points of the best in each): `gpt-oss:20b` medium and low are within 5 points of the best combined score and code pass@1, but the shared model must also pass the R2a gate, which it does not (71% GPU). Not applied.
- Ruling R-4: the 30B models cannot meet 100% GPU, so they are listed for the record and excluded from the rules.

## Chosen set (at most four models including the embedding model)

1. `qwen3-embedding:0.6b` (R1, from the section above).
2. `gpt-oss:20b`: R2a at reasoning effort medium (ruling R-10) and R2b at reasoning effort low.

Ruling R-10 (2026-10-29, decision delegated by the owner) replaces the 100% GPU part of the R2a gate with the 15 tok/s speed gate it stood for. Under it `gpt-oss:20b` medium qualifies (46.2 tok/s at 71% GPU) and has the best combined score (98.75); the sharing rule then holds, since it is within 5 points of the best in both roles. The 30B models also pass the speed gate (42.0 and 43.6 tok/s) but score lower combined (85.00 and 52.50), so the choice is unchanged. Under the rule as written R2a stays empty. Reasons: `STUDY-DONE.md`.

## Models on disk after ruling R-5

| Model | Bytes | Digest | Why kept |
|---|---:|---|---|
| `gpt-oss:20b` | 13,793,441,566 | `f38aa0c53da5f8c49d08c43a99df24ff53167fe68e24664a7777288e7656fdfe` | chosen (R2b) |
| `qwen3-embedding:0.6b` | 639,150,858 | `ac6da0dfba84a81fdbfbaf330198c33cd77c4cdfc53e8bc50eb581914a15621d` | chosen (R1) |
| `bge-m3:latest` | 1,157,672,605 | `7907646426070047a77226ac3e684fbbe8410524f7b4a74d02837e43f2146bab` | protected |
| `qwen3.5:9b` | 6,550,825,550 | `56671c2ab9385f9cfcb404638e32cd62d88e3501d44822208363c010179a3c90` | pre-existing |
| `kimi-k3:cloud` | 308 | `630e737485bd19f7244fa91f135be116780a25e942ceed0d2aceabaccbd5bf99` | pre-existing, never called |
| `phi4:latest` | 9,053,116,391 | `ac896e5b8b34a1f4efa7b14d7520725140d5512484457fab45d2a4ea14c69dba` | not chosen; kept because lane N2 needs it, remove after N2 |

Removed (ruling R-5, `ollama rm`, pinned digests stay in `engine/models.toml` for a verified re-pull): `qwen3-embedding:4b`, `devstral:24b`, `qwen3:14b`, `qwen3:8b`, `qwen3-coder:30b`, `qwen3:30b`. Free disk on C: 374,769,573,888 bytes after removal (306,323,005,440 before).

Not measured: the Windows CPU load for each correctness case (only at the start and end of each model unit, `r2-wsl/units.jsonl`); the R2a candidates at a context where they fit the GPU (for example `qwen3:14b` at `num_ctx` 8,192), because the context is fixed at 16,384 and system settings are not changed; significance of differences of one or two of 40 tasks.

## New candidates, 2026-10-29

Authority: development step M2, issue #11, ruling R-10. Record: the development step M2 record (not published). Same scripts (`r2_wsl.py`, `r2_report.py`), same machine and settings as the section above; tables in `r2-wsl/r2-table-M2.md` and `.json` (the R2 tables stay as committed). The owner asked that neither download be kept; `gemma4:12b` was removed after measuring (`r2-wsl/inventory-after-M2.txt`).

- `gemma4:12b` (digest `6114515d63c17436a7c0417d82820ac65ad643e2806c5a3c89cb62846436ed0b`, Apache-2.0 licence layer, 8.0 GB download, capabilities completion, vision, audio, tools, thinking with levels false/true). Modes tested as for `qwen3:14b`: thinking on (R2a) and thinking off (R2b).
- `nemotron-3.5-lightning` (tag `30b` = `latest`, 23.7 GiB): not pulled. Its registry licence layer is the NVIDIA Open Model License Agreement, not Apache-2.0 or MIT, so `model_guard.py pull` refuses it (exit 2, reason recorded in `engine/models.toml` with `allowed = false`). Widening the licence rule is not this lane's decision. Not measured.

| Model / mode | Code pass@1 | Tool pass | Combined /100 | Gen tok/s, 8,000-token prompt / 200-token prompt | Prompt tok/s (8,000) | TTFT s (8,000) | GPU share at 16,384 (`ollama ps`) |
|---|---:|---:|---:|---|---:|---:|---|
| `gemma4:12b` / thinking on | 24/40 (60.0%) | 12/12 | 80.00 | 103.9 / 119.1 | 2,557 | 3.14 | 100% |
| `gemma4:12b` / thinking off | 39/40 (97.5%) | 12/12 | 98.75 | 100.5 / 106.2 | 2,535 | 3.12 | 100% |

Notes:
- Thinking on: all 16 code failures stopped at the 4,096-token limit with an empty or partial answer (the reasoning used the budget), the same failure as `qwen3:14b` thinking on. Thinking off: 1 failure (task index 11, ended normally, test failed).
- GPU share: Ollama reports 100% GPU, but its size field shows 1.5 GB for a model whose download is 8.0 GB, so the ratio is not evidence by itself. `nvidia-smi` read 10.9 to 11.4 GB used with only this model loaded against 1.5 GB with nothing loaded, which fits a fully resident model at 16,384 context. Not checked against the Ollama server log.
- Generation speed is about 100 tok/s. A dense 11.9B Q4_K_M model reading 7.4 GB of weights per token on this card's 504 GB/s memory would stop near 68 tok/s, and the model carries a 465 MB `draft` layer (parameter `draft_num_predict 3`), which suggests speculative decoding. That is not verified (server log not read), and the speed prompt asks for a long explanation, which may favour drafting; a prompt with less predictable output could give a lower rate.
- Speed gate: 12 of 12 runs valid; before each run Ubuntu load at most 0.54, Windows CPU at most 22.4%, GPU at most 18%; 13 deferrals at 30 s (GPU utilisation up to 90% right after the warm-up), recorded in `r2-wsl/speed-deferred.jsonl`. Ubuntu load during correctness at most 1.40.

Rules with the new rows. As written (100% GPU) R2a would go to `gemma4:12b` thinking on (103.9 tok/s, 100% GPU, combined 80.00), the only qualifier, because it is the only R2a candidate at 100% GPU. Under ruling R-10 (speed gate only, the rule now in force):
- R2a: `gpt-oss:20b` medium keeps it (combined 98.75; `gemma4:12b` thinking on scores 80.00 because of the token-limit failures).
- R2b: `gemma4:12b` thinking off (100.5 tok/s, code 97.5%, within 10 points of the best 97.5%) beats `gpt-oss:20b` low (58.2 tok/s, 95.0%).
- Sharing: the rule lets one model fill both roles if it is within 5 points of the best in each. `gemma4:12b` thinking off ties the best combined score (98.75) and the best code score (97.5%) and is faster than `gpt-oss:20b` medium (100.5 against 46.2 tok/s) at 100% GPU instead of 71%, but the study scripts list only thinking-on modes as R2a candidates, so the rule as coded does not offer it for R2a.

Would either replace `gpt-oss:20b`? `gemma4:12b` thinking off would replace `gpt-oss:20b` low in R2b on the measured numbers, and ties `gpt-oss:20b` medium on combined score. Whether it takes both roles depends on allowing thinking off as an R2a mode, which the brief does not. The owner decides; it is not on disk, so it must be pulled again (`model_guard.py pull gemma4:12b`, about 6 minutes). `nemotron-3.5-lightning` has no result.

Not measured: `nemotron-3.5-lightning` (licence refusal, above); whether speculative decoding is active in `gemma4:12b`; speed on a prompt with less predictable output; significance of one task out of 40.

# Mac results (reference, 2026-10-27, Apple M4 Pro, private corpus of 5,091 chunks)

Status: correctness_in_progress. R2 role winners await speed qualification.

Updated: 2026-10-27T10:02:04.284977+00:00. Authority: development step D, attempt-2 instructions.

## Verified inputs

- Reused all 150 questions, the 5,091-chunk snapshot, fixed HumanEval subset and 12 scenarios. `verified-inputs.json` records their hashes. No eval-set item was opened.
- Phi4 generated the questions with the LlamaIndex 0.10.68 helper exported as `generate_question_context_pairs`, an alias of `generate_qa_embedding_pairs`. The installed core 0.14.25 removed it. The isolated historical helper and verified wheel hashes remain in `sources/`; the runner uses installed core types.
- Reused phi4: 33/40 code passes, 0/12 tool calls, combined 41.25/100. `verified-baseline.json` records the raw hashes. Phi4 correctness was not rerun.
- HumanEval uses revision `b9453e8f1865df0a0057a1383767caa400acfbcf`, numeric task-ID sorting and seed 27. Temperature 0, one attempt, context 16,384. Each generated test runs only in a no-network Docker container with a read-only mount and 20-second timeout.
- New correctness records include before/after load averages. The old phi4 records have no per-case load readings; none were reconstructed. `attempt-2-commands/` retains full logs, exits and command durations.

## Retrieval embedding

| Model | Chunks | Chunks/min | Index minutes | Vector hit@5 / hit@10 / MRR@10 | Hybrid hit@5 / hit@10 / MRR@10 | Index residency |
|---|---:|---:|---:|---|---|---|
| `bge-m3` | 5091 | 945.39 | 5.385 | 0.506667 / 0.553333 / 0.385146 | 0.680000 / 0.746667 / 0.538220 | `bge-m3:latest    790764642607    1.3 GB    100% GPU     262144     14 minutes from now` |
| `qwen3-embedding:0.6b` | 5091 | 688.64 | 7.393 | 0.580000 / 0.673333 / 0.483140 | 0.693333 / 0.746667 / 0.586812 | `qwen3-embedding:0.6b    ac6da0dfba84    5.7 GB    100% GPU     262144     14 minutes from now` |
| `qwen3-embedding:4b` | 2688/5091 | pending | 33.038 so far | pending / pending / pending | pending / pending / pending | `pending` |

Provisional R1 choice: pending complete indexing and evaluation.
The fixed primary comparison uses hybrid hit@5, then MRR@10, then chunks/min; indexing must finish in under 60 minutes. Vector results remain visible. Index time sums embedding-and-insert batch times and excludes operator pauses. Raw evaluator results and batch load readings live in `retrieval/` and `index/`.
The snapshot has 4,249 distinct texts across 5,091 node IDs. Of the 150 sampled chunks, 51 have identical text under another ID. Cerebrollm deduplicates returned text, while the evaluator requires the sampled ID. An identical-text result under another ID receives no credit. The fixed scoring rule is unchanged; `retrieval-identity-check.json` records this limitation.
Qwen queries use this exact prefix:

```text
Instruct: Given a web search query, retrieve relevant passages that answer the query
Query:
```

 Documents have no prefix. Copied TOML files change only table and model. Each vector has 1,024 dimensions. R1 indexing residency snapshots are in each index summary; R2 memory qualification is deferred.

## Agentic coding

| Model / mode | Code pass / attempted | Code pass@1 | Tool pass / completed | Combined /100 | One-minute load range |
|---|---:|---:|---:|---:|---|
| `phi4` / default | 33/40 | 82.5% | 0/12 | 41.250 | not recorded in attempt 1 |
| `devstral:24b` / default | 0/0 | pending | 0/0 | pending | not recorded in attempt 1 |
| `gpt-oss:20b` / medium | 0/0 | pending | 0/0 | pending | not recorded in attempt 1 |
| `qwen3:14b` / thinking-on | 0/0 | pending | 0/0 | pending | not recorded in attempt 1 |

Combined = 0.5 x code percentage + 0.5 x tool percentage. Native tool failures score zero; text is never converted into a tool call. Errors consume an attempt and remain in raw evidence. R2a requires at least 15 generation tokens/s at context 16,384 with 100% GPU residency. No candidate is speed-qualified.
R2a finalists: pending all correctness results.

## Fast output

| Model / mode | Code pass / attempted | Code pass@1 | Tool pass / completed | Combined /100 | One-minute load range |
|---|---:|---:|---:|---:|---|
| `phi4` / default | 33/40 | 82.5% | 0/12 | 41.250 | not recorded in attempt 1 |
| `gpt-oss:20b` / low | 0/0 | pending | 0/0 | pending | not recorded in attempt 1 |
| `qwen3:14b` / thinking-off | 0/0 | pending | 0/0 | pending | not recorded in attempt 1 |
| `qwen3:8b` / thinking-off | 0/0 | pending | 0/0 | pending | not recorded in attempt 1 |

R2b chooses the highest generation tokens/s among original R2b candidates within 10 percentage points of the best measured R2 code score across modes. GPT-OSS uses low reasoning for R2b and medium for R2a. Qwen uses thinking off for R2b and on for R2a.
Best code pass@1: None%. R2b finalists: pending all correctness results.

## Speed measurements

All R2 prompt/generation rates, time to first token, memory size and CPU/GPU qualification remain pending for tonight after the owner restart. Attempt 2 runs no speed test and never gates correctness on load. The speed notes (not published) contain exact pull and measurement commands. The attempt-1 phi4 gate at load 93.078 remains raw evidence, not a valid measurement.

## Published scores

| Candidate | Published result, reported, not checked here | Source |
|---|---|---|
| `devstral:24b` | SWE-bench Verified: 46.8% | [vendor source](https://mistral.ai/news/devstral/) |
| `gpt-oss:20b` | SWE-bench Verified: {"low": 37.4, "medium": 53.2, "high": 60.7}% | [vendor source](https://cdn.openai.com/pdf/419b6906-9da6-406c-a19d-1bb078ac7637/oai_gpt-oss_model_card.pdf) |
| `qwen3:14b` | BFCL v3 (tool use, not repository patch solving): {"thinking-on": 70.4, "thinking-off": 61.5}% | [vendor source](https://arxiv.org/html/2505.09388v1) |
| `qwen3:8b` | BFCL v3 (tool use, not repository patch solving): {"thinking-on": 68.1, "thinking-off": 60.2}% | [vendor source](https://arxiv.org/html/2505.09388v1) |
| `phi4` | HumanEval (single-function coding, not agentic coding): 82.6% | [vendor source](https://huggingface.co/microsoft/phi-4) |

Published HumanEval and BFCL results measure function coding and tool use respectively; they do not establish repository-agent performance. Published scaffolds and precision differ from this run. Source bodies and receipts from attempt 1 remain in `sources/`.

## Choice and disk

Final chosen set: pending speed tests. The provisional embedding choice is recorded above. Sharing a model across roles requires being within 5 points of the best in each; the final set may contain at most four models. The protected live `bge-m3` model stays installed.

| Installed model | Bytes | Decimal GB |
|---|---:|---:|
| `qwen3-embedding:4b` | 2496704041 | 2.496704 |
| `qwen3-embedding:0.6b` | 639150858 | 0.639151 |
| `phi4:latest` | 9053116391 | 9.053116 |
| `bge-m3:latest` | 1157672605 | 1.157673 |
| `gpt-oss:120b-cloud` | 307 | 0.000000 |

Free disk: 18,016,751,616 bytes (18.017 GB). Floor: 8 GB. `model-actions.jsonl` records before/after inventory, disk and each permitted removal. The cloud entry was never invoked.

## Boundaries and continuation

`boundaries-after.json` verifies all 30,533 live rows including embeddings against `boundaries-before.json`, plus cerebrollm source hashes. Cerebrollm revision: `5e059f3f45d6cb664dd7e06d6c56cc0ae6495071`. Study tables are separate from `data_chunks`.
The local Codex fallback and local run record continue because no external reporting tool was used (its default log paths lie outside the authorized folder). The attempt-2 instructions cite a routing pick; this controller claims no new pick/outcome. External reporting remains pending because only this folder is writable.
Resume incomplete correctness units from their per-case records. After every R2 variant is complete, remove each study-pulled R2 model and phi4; tonight repull the finalists using the speed notes (not published). The earlier resume brief is superseded by the 27 Oct attempt-2 instructions.

Skipped or not checked: all R2 speed qualification; final role winners; optional practice set; full SWE-bench and production agent behavior; external reporting; `qwen3-coder:30b` and `qwen3:30b` (18.56 GB each, excluded by the brief for disk and default GPU-memory limits).
