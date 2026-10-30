# Data and telemetry

cerebrollm collects no telemetry. It has no analytics, crash reporting or
update check.

`index` reads the Markdown files in the roots you register, sends their chunks to
the embedding model, and writes rows to a local PostgreSQL database and files to
the folder `~/.cerebrollm`. `search` and `ask` send the query to the embedding
model, read the database and read source files for line spans; `ask` also sends
the retrieved passages to the generator. `verify` reads source files and the
database. `status` reads the database and the state file. `search`, `ask`,
`verify` and `status` write nothing. PostgreSQL is reached over a Unix socket and
Ollama at the address in `cerebrollm.toml`, which defaults to 127.0.0.1:11434
and is not restricted to loopback. `ask` refuses model names ending `-cloud` or
`:cloud`. The package sets `ANONYMIZED_TELEMETRY=False`, `DO_NOT_TRACK=1`,
`HF_HUB_OFFLINE=1` and `TRANSFORMERS_OFFLINE=1` as defaults before it imports any
library; a value you set yourself wins. The index holds the text of your documents
and is not encrypted: protect the folder with your operating system's permissions.

| Action | What leaves the machine | Where to | Retention | Control |
|---|---|---|---|---|
| You set the Ollama address to a host other than your machine | chunk text (`index`), queries (`search`, `ask`), retrieved passages (`ask`) | that host | set by that host | the default is loopback; 0.1.0 does not refuse another address |
| A model host calls the MCP tools `search` or `verify` | the tool results: passages of your documents, paths, line spans | the model provider you chose for that host | set by that provider | you register the server and you choose the host; unregister it to stop |
| `pip install`, `ollama pull`, the one-time download of the reranker | package, model and file names, and the normal network address of your machine | the package index, the model registry and the model host | set by those services | you run these steps yourself |
| `research/model-study/model_guard.py pull` | the model name, to read its manifest | the model registry | set by that service | you run it yourself |
| Evaluation scripts in `eval/` run with a hosted model | public evaluation questions and public retrieved text | the hosted model's provider | set by that provider | the scripts run a hosted model only when you start them with one |
| `research/corpus/fetch_corpus.py`, `research/model-study/fetch_published.py` | requests for public pages | the public hosts named in the scripts | set by those hosts | you run them yourself |

The code in `engine/cerebrollm/` sends nothing else. Dependencies were not audited
for telemetry in 0.1.0, and a network capture of `ask` and `index` has not been run.

Skipped or not checked: dependency telemetry and a network capture of `ask` and `index`.
