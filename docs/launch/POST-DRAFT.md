# Launch post drafts

Drafts for the owner to edit and post. Every number below is in `docs/RESULTS.md`. Post after the fresh-machine quick-start log is committed.

## Show HN

Title:

    Show HN: cerebrollm – local RAG that re-reads the file before it answers

Body:

I built a local retrieval tool for my own Markdown notes. It searches them, asks a local model to quote the one line it relies on, then opens the cited file and checks the quote is there. If the check fails it prints exactly "Not in the sources."

I am posting it early because of how it is documented, more than because of how well it works. Every number in the README names a committed file, and the failed runs are in the repository too.

What I measured, on one machine with a 12 GB GPU and public documentation as the corpus:

- Retrieval took `phi4` from 1 of 60 questions right to 47 of 60.
- On 35 questions about recent releases, `gpt-oss:20b` was confidently wrong in 122 of 175 runs with no retrieval, 17 of 175 with plain search, and 7 of 104 with the quote check.
- The check costs answers. With it, `gpt-oss:20b` gets 28 of 35 items right against 32 of 35 with plain search. It refuses some questions the notes do answer, usually because the model's quote was not word for word.
- My aim is 90% right outcomes with under 2% confidently wrong runs. No local model meets it. A 35-item set cannot show a rate under 2% anyway, and the results page says so.

What it does not do: it reads only Markdown, it is tested only on Ubuntu and WSL2, the largest index I measured is 13,627 chunks, and the gate checks that the quote exists, not that it answers the question. That last gap is the first item for the next release.

It runs on PostgreSQL with pgvector, Ollama and a local reranker. There is a read-only MCP server with `search` and `verify`, so an agent can use it as a tool. MIT licence.

Repository: https://github.com/sourav-patra/cerebrollm
Results and limits: https://github.com/sourav-patra/cerebrollm/blob/main/docs/RESULTS.md

I would like to hear where the evaluation method is weak, and what a larger public item set should contain.

## r/LocalLLaMA

Title:

    I measured how often a local model answers wrongly with RAG, then added a check that re-reads the cited file. Numbers and failed runs inside.

Body:

Setup: RTX 4070 SUPER 12 GB, Ollama, PostgreSQL with pgvector, `qwen3-embedding:0.6b`, `bge-reranker-v2-m3`. 35 questions on release notes dated after 2026-06, 15 of them unanswerable on purpose.

| Model | Plain search: right of 35 | Confidently wrong runs | With quote check: right of 35 | Confidently wrong runs |
|---|---|---|---|---|
| `gemma4:12b` | 33 | 4 of 175 | 22 | 0 of 105 |
| `gpt-oss:20b` | 32 | 17 of 175 | 28 | 7 of 104 |
| `phi4` | 31 | 10 of 175 | 21 | 0 of 105 |

The check makes the model quote one line, then opens the file and looks for the quote. No match means "Not in the sources." It removes most confidently wrong runs and it refuses more often, including on questions the notes answer.

Other things I measured: `qwen3-embedding:0.6b` beat `qwen3-embedding:4b` and `bge-m3` on hybrid hit@5 (0.927, 0.907, 0.893 on 150 questions), and `gpt-oss:20b` ran at 46.2 tokens/s with an 8,000-token prompt and 71% of the model on the GPU.

Limits: Markdown only, Linux and WSL2 only, one machine, 35 items, and a model did the grading (checked against a person on 40 answers).

Code, raw run records and the grading rubric: https://github.com/sourav-patra/cerebrollm

Which model should I run next on a 12 GB card?

## Short post

    cerebrollm 0.1.3: local RAG that re-reads the cited file before it answers, or says "Not in the sources." Every number in the README names a committed file, including the runs where it fails. MIT. https://github.com/sourav-patra/cerebrollm

## Before posting

- The fresh-machine quick-start log is committed.
- The product page is merged and its evidence links open signed out.
- Stay online for the first hours to answer questions. Answer a criticism with a file, or with "not measured".

Skipped or not checked: the title lengths against each site's limit, each site's current rules on self-promotion, and the best posting time.
