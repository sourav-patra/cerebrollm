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

Skipped or not checked: the reader check by a person and the signed-out link check above.
