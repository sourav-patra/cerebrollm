# README checks

Records of the checks that the "Writing docs" section of `CONTRIBUTING.md` asks for. A check not yet done is listed as pending.

| Check | Revision | Who | Result |
|---|---|---|---|
| `python scripts/readme_lint.py README.md` (version 7) | this pull request | author | 0 fail, 0 warn; 4 figures |
| Every rule in "Writing docs" | 93c3349 | GPT-6.1 Sol, a reviewer from another provider | changes requested: two undefined terms, a target claim without its sample-size limit, a 49-word paragraph, no record of these checks; the terms, the limit and the record fixed in ec68b5b; round 2 found most paragraphs still over 25 words, fixed by splitting paragraphs at sentence ends |
| Figures read against the source at reading size (900 px): `context.svg`, `parts.svg`, `ask-flow.svg` | 93c3349 | GPT-6.1 Sol | labels legible, one style, three distinct views |
| Figures against the code | 3125f76 (pull request 3) | GPT-6.1 Sol, three rounds | approved |
| Figure at reading size: `walkthrough.gif` | none | none | pending |
| Uncoached reader, a model, round 1 | pull request 3 | a model that had not seen the page | three misreadings (an internet claim beside the MCP link, "checks every quote", one-way MCP arrows), all fixed; its other answers were not recorded |
| Uncoached reader, a model, round 2 | this pull request | GPT-6 Luna, given only the README text | right on audience, problem, status, input, output, decision, first action, evidence, limits and the walk-through; misread the opening line as checking the whole answer, so the promise now says only the quote is checked |
| Uncoached reader, a model, round 3 | this pull request | GPT-6 Luna, fresh session | nine of ten answers right; its problem answer says unsupported answers are withheld, which overstates the gate, while its limits answer states correctly that the gate checks that the quote exists, not that it supports the answer; it noted that "No local model meets it yet" and the Claude Sonnet 5.5 result both hold because Sonnet is hosted |
| Uncoached reader, a person | none | none | pending |
| Links open without signing in | none | none | pending |

## Reader answers

The questions: 1 who it is for, 2 the problem, 3 the status, 4 the input, 5 the output, 6 the decision it supports, 7 the first action, 8 the key evidence, 9 the main limits, 10 what the walk-through figure shows, 11 what was unclear or misread. Answers are copied as given.

### Round 2 (GPT-6 Luna, README text only, revision: ec68b5b)

1. It is for people who use local models or let cloud models read their Markdown documents and need answers traceable to files.
2. It searches relevant passages and checks that at least one quoted line still exists in its cited source before showing an answer.
3. Version 0.1.0 is early research; its accuracy and safety goals are not met by any local model yet.
4. The input is a question and Markdown files that match configured indexing rules.
5. The output is an answer with a verified source citation, or exactly `Not in the sources.`
6. It helps you decide whether the indexed notes support an answer you can trace to a file.
7. First, install the system packages and set up Python, Ollama, and PostgreSQL as described in Quick start.
8. The README reports 47 of 60 questions answered correctly by `phi4` with retrieval versus 1 of 60 without; it also reports that the answer gate checks quote presence, not whether the quote supports the answer.
9. It indexes only Markdown, can abstain even when notes contain an answer, and has only been tested on Ubuntu 24.04 under native Linux or WSL2; several setup steps remain unverified.
10. The walk-through figure traces one question through embedding, retrieval of 20 passages, reranking to 8, local answer generation, source re-reading, and the final output gate.
11. I initially read the opening claim as if the whole answer were checked, but the README clarifies that one confirmed quote lets the whole answer through; the rest of its text is unchecked.

### Round 3 (GPT-6 Luna, README text only, revision: the promise change in this pull request)

1. It is for people who use local models, or let cloud models read their Markdown documents, and need answers traceable to files.
2. It retrieves relevant passages and re-reads cited source files so unsupported or unverified answers are withheld.
3. It is version 0.1.0, described as early research; no local model meets its stated accuracy and safety aims.
4. The input is a question and indexed Markdown files covered by configuration rules.
5. The output is an answer with at least one verified quote citation, or exactly `Not in the sources.`
6. It helps you decide whether your notes support an answer you can trace to a source file.
7. My first action would be to check the listed requirements, especially Python 3.12, Ollama, PostgreSQL 16 with pgvector, disk space, and GPU.
8. Key evidence includes the reported 47/60 correct answers for `phi4` with retrieval versus 1/60 without, plus measured results showing `ask` reduces confidently wrong runs while declining more often.
9. It indexes only Markdown, checks that a cited quote exists rather than that it supports the answer, and has only been tested on Ubuntu 24.04 native or under WSL2.
10. The walk-through figure shows one question moving through retrieval of 20 passages, reranking to 8, local answer generation, source re-reading, and the final output gate; it omits indexing and error exits.
11. I found the line “No local model meets it yet” clear, but the results table says Claude Sonnet 5.5 met the aim with plain search; I read the former as referring specifically to local models.

Open from round 3: answer 2 says unsupported answers are withheld, which overstates the gate. The README states the limit in Features and in Results at a glance; the Why section does not. Whether the Why section needs a change is pending the reader check by a person.

Skipped or not checked: the reader check by a person and the signed-out link check above.
