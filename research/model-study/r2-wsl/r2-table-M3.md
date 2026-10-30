| Model / mode | Code pass@1 | Tool pass | Combined | Gen tok/s 8,000 / 200 | Prompt tok/s 8,000 | TTFT s 8,000 | GPU % | `ollama ps` (8,000-token run) |
|---|---:|---:|---:|---|---:|---:|---:|---|
| `phi4` / default | 35/40 (87.5%) | 0/12 | 43.75 | 14.5 / 22.2 | 1711 | 4.48 | 80.9 | phi4:latest    ac896e5b8b34    12 GB    19%/81% CPU/GPU    16384      llamacpp    14 minutes from now |
| `devstral:24b` / default | 33/40 (82.5%) | 11/12 | 87.08 | 4.3 / 6.7 | 834 | 7.67 | 58.2 | devstral:24b    9bd74193e939    17 GB    42%/58% CPU/GPU    16384      llamacpp    14 minutes from now |
| `gpt-oss:20b` / medium | 39/40 (97.5%) | 12/12 | 98.75 | 46.2 / 60.2 | 3302 | 4.69 | 71.4 | gpt-oss:20b    f38aa0c53da5    14 GB    29%/71% CPU/GPU    16384      llamacpp    14 minutes from now |
| `gpt-oss:20b` / low | 38/40 (95.0%) | 12/12 | 97.50 | 58.2 / 60.3 | 3300 | 2.42 | 71.4 | gpt-oss:20b    f38aa0c53da5    14 GB    29%/71% CPU/GPU    16384      llamacpp    14 minutes from now |
| `qwen3:14b` / thinking-on | 37/40 (92.5%) | 12/12 | 96.25 | 15.7 / 25.0 | 1831 | 4.41 | 84.3 | qwen3:14b    bdbd181c33f2    12 GB    16%/84% CPU/GPU    16384      llamacpp    14 minutes from now |
| `qwen3:14b` / thinking-off | 36/40 (90.0%) | 12/12 | 95.00 | 15.1 / 25.0 | 1830 | 4.14 | 84.3 | qwen3:14b    bdbd181c33f2    12 GB    16%/84% CPU/GPU    16384      llamacpp    14 minutes from now |
| `qwen3:8b` / thinking-off | 33/40 (82.5%) | 12/12 | 91.25 | 67.5 / 81.5 | 4142 | 1.88 | 100.0 | qwen3:8b    500a1f067a9f    7.5 GB    100% GPU     16384      llamacpp    14 minutes from now |
| `gemma4:12b` / thinking-on | 24/40 (60.0%) | 12/12 | 80.00 | 103.9 / 119.1 | 2557 | 3.14 | 100.0 | gemma4:12b    6114515d63c1    1.5 GB    100% GPU     16384      llamacpp    14 minutes from now |
| `gemma4:12b` / thinking-off | 39/40 (97.5%) | 12/12 | 98.75 | 100.5 / 106.2 | 2535 | 3.12 | 100.0 | gemma4:12b    6114515d63c1    1.5 GB    100% GPU     16384      llamacpp    14 minutes from now |
| `qwen3.6:35b-a3b-coding-mtp-q4_K_M` / mtp4-think-off | 37/40 (92.5%) | 12/12 | 96.25 | 52.9 / 53.9 | 1146 | 6.60 | 41.3 | qwen3.6:35b-a3b-coding-mtp-q4_K_M    6f7983cafbe2    22 GB    59%/41% CPU/GPU    16384      llamacpp    14 minutes from now |
| `qwen3.6:35b-a3b-coding-mtp-q4_K_M` / mtp0-think-off | 36/40 (90.0%) | 12/12 | 95.00 | 51.3 / 51.9 | 1225 | 6.17 | 43.9 | qwen3.6:35b-a3b-coding-mtp-q4_K_M    6f7983cafbe2    22 GB    56%/44% CPU/GPU    16384      llamacpp    14 minutes from now |
| `glm-4.7-flash:q4_K_M` / think-off | 0/0 (incomplete) | 0/0 | not measured | not measured / not measured | not measured | not measured | not measured | not measured |

Speed by context (lane M3 ladder):

| Model / mode | num_ctx | Prompt tokens | Gen tok/s (runs) | Prompt tok/s | GPU % | Min free RAM MB | Max Pages/sec | Sustained paging | `ollama ps` after |
|---|---:|---:|---|---:|---:|---:|---:|---|---|
| `qwen3.6:35b-a3b-coding-mtp-q4_K_M` / mtp4-think-off | 8192 | not measured | | | | | | | |
| `qwen3.6:35b-a3b-coding-mtp-q4_K_M` / mtp4-think-off | 32768 | not measured | | | | | | | |
| `qwen3.6:35b-a3b-coding-mtp-q4_K_M` / mtp4-think-off | 65536 | not measured | | | | | | | |
| `qwen3.6:35b-a3b-coding-mtp-q4_K_M` / mtp0-think-off | 8192 | not measured | | | | | | | |
| `qwen3.6:35b-a3b-coding-mtp-q4_K_M` / mtp0-think-off | 32768 | not measured | | | | | | | |
| `qwen3.6:35b-a3b-coding-mtp-q4_K_M` / mtp0-think-off | 65536 | not measured | | | | | | | |
| `glm-4.7-flash:q4_K_M` / think-off | 8192 | not measured | | | | | | | |
| `glm-4.7-flash:q4_K_M` / think-off | 32768 | not measured | | | | | | | |
| `glm-4.7-flash:q4_K_M` / think-off | 65536 | not measured | | | | | | | |
