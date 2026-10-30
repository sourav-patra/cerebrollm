# Security policy

Report a suspected vulnerability through private vulnerability reporting on
the repository's Security tab: https://github.com/sourav-patra/cerebrollm/security/advisories/new
Keep details out of public issues. Include the affected version, what you
observed and a minimal reproduction.

What counts as a vulnerability here:

- The engine, the MCP server or `verify` reads or writes a file outside the
  registered roots and the state folder.
- A tool of the MCP server writes anything, or runs a command.
- `ask` prints an answer that carries no citation that `verify` confirmed.
- The secret scan lets a file with a credential into the index.
- Retrieved text makes a program run a command or send data out.

A wrong or missing answer is not a vulnerability. Open a normal issue.

| Version | Security fixes |
|---|---|
| 0.1.x | supported |
| earlier | not applicable (no earlier release) |

The maintainers aim to reply within 7 days of a report. This target promises
nothing about a reply or a fix. The maintainers assess the report, agree a disclosure date with the
reporter, then publish a fix and an advisory together.

Skipped or not checked: whether the private reporting route works (the owner enables it once the repository exists).
