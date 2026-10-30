| Model / mode | Code pass@1 | Tool pass | Combined | Gen tok/s 8,000 / 200 | Prompt tok/s 8,000 | TTFT s 8,000 | GPU % | `ollama ps` (8,000-token run) |
|---|---:|---:|---:|---|---:|---:|---:|---|
| `phi4` / default | 35/40 (87.5%) | 0/12 | 43.75 | 14.5 / 22.2 | 1711 | 4.48 | 80.9 | phi4:latest    ac896e5b8b34    12 GB    19%/81% CPU/GPU    16384      llamacpp    14 minutes from now |
| `devstral:24b` / default | 33/40 (82.5%) | 11/12 | 87.08 | 4.3 / 6.7 | 834 | 7.67 | 58.2 | devstral:24b    9bd74193e939    17 GB    42%/58% CPU/GPU    16384      llamacpp    14 minutes from now |
| `gpt-oss:20b` / medium | 39/40 (97.5%) | 12/12 | 98.75 | 46.2 / 60.2 | 3302 | 4.69 | 71.4 | gpt-oss:20b    f38aa0c53da5    14 GB    29%/71% CPU/GPU    16384      llamacpp    14 minutes from now |
| `gpt-oss:20b` / low | 38/40 (95.0%) | 12/12 | 97.50 | 58.2 / 60.3 | 3300 | 2.42 | 71.4 | gpt-oss:20b    f38aa0c53da5    14 GB    29%/71% CPU/GPU    16384      llamacpp    14 minutes from now |
| `qwen3:14b` / thinking-on | 37/40 (92.5%) | 12/12 | 96.25 | 15.7 / 25.0 | 1831 | 4.41 | 84.3 | qwen3:14b    bdbd181c33f2    12 GB    16%/84% CPU/GPU    16384      llamacpp    14 minutes from now |
| `qwen3:14b` / thinking-off | 36/40 (90.0%) | 12/12 | 95.00 | 15.1 / 25.0 | 1830 | 4.14 | 84.3 | qwen3:14b    bdbd181c33f2    12 GB    16%/84% CPU/GPU    16384      llamacpp    14 minutes from now |
| `qwen3:8b` / thinking-off | 33/40 (82.5%) | 12/12 | 91.25 | 67.5 / 81.5 | 4142 | 1.88 | 100.0 | qwen3:8b    500a1f067a9f    7.5 GB    100% GPU     16384      llamacpp    14 minutes from now |

For the record (ruling R-4, not in the rules):

| Model / mode | Code pass@1 | Tool pass | Combined | Gen tok/s 8,000 / 200 | Prompt tok/s 8,000 | TTFT s 8,000 | GPU % | `ollama ps` (8,000-token run) |
|---|---:|---:|---:|---|---:|---:|---:|---|
| `qwen3-coder:30b` / default | 38/40 (95.0%) | 9/12 | 85.00 | 42.0 / 41.7 | 1576 | 4.73 | 51.3 | qwen3-coder:30b    06c1097efce0    20 GB    49%/51% CPU/GPU    16384      llamacpp    14 minutes from now |
| `qwen3:30b` / thinking-off | 2/40 (5.0%) | 12/12 | 52.50 | 43.6 / 43.4 | 1594 | 5.08 | 51.3 | qwen3:30b    ad815644918f    20 GB    49%/51% CPU/GPU    16384      llamacpp    14 minutes from now |

- Best R2 code pass@1 across modes: 97.5%. Best combined: 98.75.
- R2a candidate devstral:24b/default: combined 87.08, gen 4.3 tok/s, GPU 58.2% -> does not qualify
- R2a candidate gpt-oss:20b/medium: combined 98.75, gen 46.2 tok/s, GPU 71.4% -> does not qualify
- R2a candidate qwen3:14b/thinking-on: combined 96.25, gen 15.7 tok/s, GPU 84.3% -> does not qualify
- R2a candidate phi4/default: combined 43.75, gen 14.5 tok/s, GPU 80.9% -> does not qualify
- R2a: none qualifies
- R2b candidate qwen3:14b/thinking-off: code 90.0%, gen 15.1 tok/s -> within 10 points
- R2b candidate gpt-oss:20b/low: code 95.0%, gen 58.2 tok/s -> within 10 points
- R2b candidate phi4/default: code 87.5%, gen 14.5 tok/s -> within 10 points
- R2b candidate qwen3:8b/thinking-off: code 82.5%, gen 67.5 tok/s -> more than 10 points below
- R2b: gpt-oss:20b (low)
- Sharing: the R2a role has no qualifying model, so no model can be shared into it.
- R2a closest by combined score, none passing the gate: gpt-oss:20b (medium) combined 98.75, gen 46.2 tok/s, GPU 71.4% (fails: GPU below 100%); qwen3:14b (thinking-on) combined 96.25, gen 15.7 tok/s, GPU 84.3% (fails: GPU below 100%); devstral:24b (default) combined 87.08, gen 4.3 tok/s, GPU 58.2% (fails: generation below 15 tok/s and GPU below 100%); phi4 (default) combined 43.75, gen 14.5 tok/s, GPU 80.9% (fails: generation below 15 tok/s and GPU below 100%)
