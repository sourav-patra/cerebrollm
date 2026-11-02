# Troubleshooting

Each row is a symptom seen while installing or running cerebrollm, its cause and the fix that worked.

| Symptom | Cause | Fix |
|---|---|---|
| `user.sh` stops with `Ollama not reachable on 127.0.0.1:11434` | Ollama is not running, or runs on another address | Start Ollama; under WSL2 with Ollama on Windows, make sure WSL reaches it on loopback |
| `ask` stops with an error that names the reranker folder | the reranker is not downloaded | Download it as in [The reranker](../README.md#the-reranker), or add `--no-rerank` |
| `status` lists no chunks for a folder | no `[[rule]]` in `cerebrollm.toml` matches its files | Add a rule for the folder, then run `index` |
| Indexing on Windows with Ollama on the Windows side fails with `Only one usage of each socket address` | each embedding call opens a new connection and the Windows ephemeral port range runs out | In an administrator shell: `netsh int ipv4 set dynamicport tcp start=10000 num=55535`; the default is `start=49152 num=16384` |
| `cerebrollm` cannot find its configuration after `pip install --user` | the packaged configuration is not on the search path | Pass `--config ~/cerebrollm.toml` or set `CEREBROLLM_CONFIG` |

Skipped or not checked: macOS and native Windows, which are untested.
