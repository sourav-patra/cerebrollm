# Model study done (2026-10-29, WSL machine)

Sources: `RESULTS.md` (R1 and R2 sections), the records of development steps L and M (not published).

## One line per role

- R1 embedding: `qwen3-embedding:0.6b`. Hybrid hit@5 0.927 against 0.907 (`qwen3-embedding:4b`) and 0.893 (`bge-m3`) on 150 questions; hybrid MRR@10 0.846; indexes the 13,431-chunk corpus in 9.7 minutes (capped by the embed pacer).
- R2a agentic coding: `gpt-oss:20b` at reasoning effort medium, under ruling R-10 (owner delegated the decision, 2026-10-29). Combined 98.75 (code 39/40, tools 12/12), 46.2 tok/s at an 8,000-token prompt with 71% of the model on the GPU. Under the rule as written R2a is empty: no candidate runs at 100% GPU with a 16,384 context on 12 GB VRAM (`gpt-oss:20b` medium 71%, `qwen3:14b` thinking on 84%, `phi4` 81%, `devstral:24b` 58%); `devstral:24b` (4.3 tok/s) and `phi4` (14.5 tok/s) also miss the 15 tok/s minimum. Closest: `gpt-oss:20b` medium, combined 98.75 (code 39/40, tools 12/12), 46.2 tok/s at an 8,000-token prompt.
- R2b fast output: `gpt-oss:20b` at reasoning effort low. Code 38/40 (95.0%, best is 97.5%), tools 12/12, 58.2 tok/s at an 8,000-token prompt and 60.3 at 200. `qwen3:8b` is faster (67.5 tok/s) but 15 points below the best code score.

## Models left on disk

| Model | Bytes | Digest |
|---|---:|---|
| `gpt-oss:20b` (chosen, R2a and R2b) | 13,793,441,566 | `f38aa0c53da5f8c49d08c43a99df24ff53167fe68e24664a7777288e7656fdfe` |
| `qwen3-embedding:0.6b` (chosen, R1) | 639,150,858 | `ac6da0dfba84a81fdbfbaf330198c33cd77c4cdfc53e8bc50eb581914a15621d` |
| `bge-m3:latest` (protected) | 1,157,672,605 | `7907646426070047a77226ac3e684fbbe8410524f7b4a74d02837e43f2146bab` |
| `qwen3.5:9b` (pre-existing) | 6,550,825,550 | `56671c2ab9385f9cfcb404638e32cd62d88e3501d44822208363c010179a3c90` |
| `kimi-k3:cloud` (pre-existing, never called) | 308 | `630e737485bd19f7244fa91f135be116780a25e942ceed0d2aceabaccbd5bf99` |

Removed under ruling R-5: `qwen3-embedding:4b`, `devstral:24b`, `qwen3:14b`, `qwen3:8b`, `qwen3-coder:30b`, `qwen3:30b`. `phi4` was removed after lane N2 (2026-10-29); `gemma4:12b` was removed after development step M2 by the owner's instruction. They can be pulled again through `model_guard.py pull NAME`; the digests are pinned in `engine/models.toml`.

Free disk on C: 374,769,573,888 bytes (about 375 GB) at 2026-10-29, after the removals.

## For the owner

- Ruling R-10 (decided 2026-10-29 at the owner's request): on this machine the 100% GPU gate is replaced by the measured speed gate it stood for, generation at or above 15 tok/s at an 8,000-token prompt and 16,384 context. The 100% rule came from the Mac, where unified memory makes every model 100% GPU; on a 12 GB card a mixture-of-experts model (`gpt-oss:20b`, about 3.6B active parameters) keeps 46.2 tok/s at 71% GPU, while the dense `devstral:24b` at 58% drops to 4.3. Result: `gpt-oss:20b` fills R2a (medium) and R2b (low), one model for both roles; the chosen set is `qwen3-embedding:0.6b` and `gpt-oss:20b`.
- Not adopted: a dense 27B model such as Qwen3.8-27B would need about 15 GB at 4-bit, so most of it would run on the CPU on 12 GB VRAM, at or below `devstral:24b`'s 4.3 tok/s. Hosted models (Ollama cloud, OpenCode free models, Antigravity) send prompts off the machine, which the plan forbids for the engine's corpus.
- development step M2 (`RESULTS.md`, "New candidates, 2026-10-29"): `gemma4:12b` thinking off scored code 39/40, tools 12/12, combined 98.75, 100.5 tok/s at 100% GPU, so under R-10 it would take R2b from `gpt-oss:20b` low and tie `gpt-oss:20b` medium for R2a. Whether to switch both roles to it is the owner's decision; until then the chosen set above stands. `nemotron-3.5-lightning` was not tested: its NVIDIA Open Model License is outside the allowed list.
- The 12 tool scenarios were rewritten (the Mac file was lost), so tool scores are not comparable with the Mac run.
