# README checks

Records of the checks that the "Writing docs" section of `CONTRIBUTING.md` asks for. A check not yet done is listed as pending.

| Check | Revision | Who | Result |
|---|---|---|---|
| `python scripts/readme_lint.py README.md` (version 7) | this pull request | author | 0 fail, 0 warn; 4 figures |
| Every rule in "Writing docs" | 93c3349 | GPT-6.1 Sol, a reviewer from another provider | changes requested: two undefined terms, a target claim without its sample-size limit, a 49-word paragraph, no record of these checks; all four fixed in the next commit |
| Figures read against the source at reading size (900 px): `context.svg`, `parts.svg`, `ask-flow.svg` | 93c3349 | GPT-6.1 Sol | labels legible, one style, three distinct views |
| Figures against the code | 3125f76 (pull request 3) | GPT-6.1 Sol, three rounds | approved |
| Uncoached reader, a model | pull request 3 | a model that had not seen the page | found three faults (an internet claim beside the MCP link, "checks every quote", one-way MCP arrows); all three fixed |
| Uncoached reader, a person | none | none | pending |
| Links open without signing in | none | none | pending |

Skipped or not checked: the reader check by a person and the signed-out link check above.
