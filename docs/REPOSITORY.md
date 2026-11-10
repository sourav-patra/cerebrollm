# What is in the repository

| Path | Holds |
|---|---|
| `engine/` | the package (`cerebrollm`), its tests, the default configuration and model allow-list, the Ubuntu setup scripts |
| `eval/` | public question sets (`items.jsonl`, `items-v2.jsonl`), grading rules, run scripts, raw run records under `eval/runs/` with `SHA256SUMS`, and `RESULTS.md` |
| `research/model-study/` | the embedding and generator study: scripts, configurations, raw results (`r1-wsl/`, `r2-wsl/`) and `RESULTS.md` |
| `research/corpus/` | the pinned list of public documentation files the evaluation corpus is built from |
| `docs/site/` | the product page (static HTML and CSS), the three figures (SVG) and the walk-through image derived from them |
| `docs/design/`, `docs/*.md` | the four locked design documents, the lock table, and the data, release and governance statements; `docs/PROJECT-PLAN.md` holds the proposed order of work after 0.1.3 |

Provenance: this repository starts from a clean history. The files were copied from the private working repository, and a mechanical pass replaced machine paths and account names with `~`, `%USERPROFILE%` or `<repo>`. `docs/scrub-manifest.json` lists every file that pass changed, with its sha256 before and after, and the `SHA256SUMS` files were regenerated for those files. Text in `research/` and `eval/` refers to work orders, receipts, rulings and issue numbers of that private repository; they are not published. 100 raw evaluation records whose retrieved passages quote private plan documents are withheld (50 of the first question set: 19 prompt and 31 retrieval records; 50 of the v2 evaluation); the published scores are unchanged and `eval/runs/WITHHELD.sha256` lists the 100 hashes (see `eval/RESULTS.md` and `eval/RESULTS-v2.md`). The manifest `research/corpus/manifest.json` has no entry for those plan documents. Its remaining `cerebrollm/` entries come from this project's public documents at a commit of the private history, so `research/corpus/fetch_corpus.py` skips that source in a clone of this repository and builds the four upstream sources only.

Skipped or not checked: the withheld records themselves; only their hashes are published.
