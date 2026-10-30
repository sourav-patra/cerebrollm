---
id: POLICY-cerebrollm
kind: contract
governs: 0.1.0 (first public release) and the 0.1.x line
status: LOCKED 2026-10-30 by the owner (content of draft v4; the states in section 1 are as observed at the checked-at revision, before the lock)
upstream: PRD-cerebrollm-2026-10-30.md (pin: PRD as locked 2026-10-30, sha256 622fee4d88bc88bdf7e59d767940b809c6651b72ce343b8075695724f84572f2); TRD and LLD follow
published-files: SECURITY.md, CONTRIBUTING.md, docs/DATA.md, docs/RELEASING.md, LICENSE, NOTICE, docs/GOVERNANCE.md
checked-at: source revision 02a00dd, 2026-10-30
---

Check section 1 to see which rules are in place and which wait on an owner step; copy the blocks in sections 2 to 7 into the files named in each heading; answer the owner questions in section 8.

# cerebrollm POLICY: how to report, contribute, release and reuse

Marks: E observed at the checked-at revision; P proposed; N not measured, with the command; D deferred to a named owner step.

## 1. Rules and checks

| ID | Rule | Check | Evidence and state |
|---|---|---|---|
| PL-01 | `SECURITY.md` names a reporting route an outsider can use, the supported versions and a response target | the owner opens the repository Security tab and confirms private reporting is enabled; a reader checks the file | D: the route is not enabled until the repository exists |
| PL-02 | No public file describes an unfixed weakness | dated read of every published file before each release | N: first read happens at lock |
| PL-03 | `CONTRIBUTING.md` states DCO sign-off, independent review, draft-only agent pull requests, closing keywords and the local gate | reader checks each of the five statements | P: text in section 3 |
| PL-04 | The local gate passes on a fresh Linux checkout, with each skipped test named | `cd engine && python -m pytest -q -rs` exits 0 and prints the skip reasons | N: not run on a fresh checkout; the 2026-10-29 run was in the development checkout (`eval/runs/retrieval/n7-evidence/engine-suite.log`) |
| PL-05 | The data statement matches the code: no telemetry, and every outbound path is listed | `grep -rnE "https?://" engine/cerebrollm` lists only the loopback default; a network capture during `ask` and `index` lists loopback only | E: the grep shows one loopback default (`engine/cerebrollm/__init__.py`). E: reading `engine/cerebrollm/answer.py` shows one request built from the configured Ollama address, and `store.py` builds the embedding client from the same address. E: `engine/cerebrollm/__init__.py` sets four opt-out defaults. N: no capture; no audit of dependency telemetry |
| PL-06 | Only the owner merges, tags and publishes; agents open draft pull requests | repository settings and `docs/RELEASING.md` | D: settings exist only after publication |
| PL-07 | Before a tag, tests, the leak scan, the build and a fresh-environment install pass | commands in section 5 | N: not run; the release work item runs them |
| PL-08 | A lock record names each covered file and its sha256, and a changed file needs a new lock | recompute with `sha256sum` and compare | N: no lock exists yet |
| PL-09 | `LICENSE` is MIT and the package metadata says `MIT` | file read; `pip show cerebrollm` after install | P: owner ruling of 2026-10-30 (code is MIT); file and metadata written by the release work item |
| PL-10 | `NOTICE` credits copied third-party text, and the licence of each source is read from its repository | open each source repository licence file | N: licences of the three release-note sources are not yet read |
| PL-11 | Branch protection on `main` needs a pull request and the local gate | the owner reads the repository settings once public | D: owner step after publication |

## 2. Security reporting (SECURITY.md)

```markdown
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
```

Check: PL-01 and PL-02. The route is a GitHub feature the owner must enable, so the link works only after publication. The 7-day target is a proposal (question 1).

## 3. Contributions and review (CONTRIBUTING.md)

```markdown
# Contributing

Sign off every commit under the Developer Certificate of Origin
(https://developercertificate.org). Use `git commit -s`. Submit only changes
you have the right to contribute.

Open an issue before a large change. Keep one change per pull request and
write "Closes #N" only when the pull request meets that issue's acceptance
check. For partial work write "Refs #N".

Run the local gate from the repository root before you open a pull request:

    cd engine && python -m pytest -q -rs

Prerequisites: Python 3.12, `pip install -r engine/requirements.txt`. Tests that
need PostgreSQL or Ollama skip with a message when those are down. The
`-rs` flag prints each skip reason. Put the command, exit code and skip
reasons in the pull request. Linux, including
WSL2, is the tested platform; macOS and native Windows are untested.

Review: the builder of a change never reviews it. A pull request names who
built it and who reviewed it. A reviewer from a different tool provider is
welcome and never required.

Changes written with an AI agent follow the same rules, and also:

- The person who submits the change is responsible for it and says in the pull
  request that an agent wrote part of it.
- An agent opens draft pull requests only. The owner merges, tags and publishes.
- An agent adds no credential, no private note and no real user document to a
  test, a fixture, an issue or a pull request. Fixtures use synthetic or
  public text.
- An agent does not review a change it wrote.

Documentation follows DOC-PHILOSOPHY.md at the repository root.
```

Check: PL-03, PL-04. Closing-keyword behaviour: GitHub closes the issue when a pull request with "Closes #N" merges into the default branch; the text relies on that and was not tested here (N).

## 4. Data, network use and telemetry (docs/DATA.md)

```markdown
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
```

Check: PL-05. The table follows `engine/cerebrollm/answer.py` (the generator call goes to the configured Ollama address), `engine/cerebrollm/store.py` (`embed_model` uses the same address), `engine/cerebrollm/__init__.py` (the environment defaults), `engine/cerebrollm/mcp_server.py` (two read-only tools), `eval/run_v2.py` (hosted arms) and `research/model-study/model_guard.py` (registry manifest). The Postgres cluster created by `engine/setup/user.sh` uses trust authentication on a Unix socket inside the state folder (N: folder mode not checked).

## 5. Releases, tags and locks (docs/RELEASING.md)

```markdown
# Releasing

The owner merges, creates tags and publishes. Agents open draft pull requests
and never merge, tag, sign a lock or publish.

Versions: 0.x releases may change the index layout, the configuration and the
command options. `CHANGELOG.md` lists every such change and says whether a full
`cerebrollm index` is needed. The tag is `v<version>` and matches `pyproject.toml`
and the top entry of `CHANGELOG.md`.

Before a tag, all of these pass:

1. `(cd engine && python -m pytest -q -rs)` exits 0 and prints each skip reason. Run
   steps 2 and 3 from the repository root.
2. The leak scan over the release tree passes: `gitleaks dir . --redact` exits 0;
   `git log --all --format='%an <%ae>%n%cn <%ce>' | sort -u` lists only the
   project's noreply identity; `grep -rIFf NEEDLES .` prints nothing, where
   NEEDLES is the owner's file of private names and paths, kept outside the
   repository. The owner saves the three outputs and attaches them to the
   release pull request.
3. `python -m build` makes the sdist and wheel; the wheel installs into a new
   virtual environment, and `cerebrollm --help` and `cerebrollm ask --help` exit 0.
4. The PRD, TRD, LLD and POLICY are locked and `docs/LOCKS.md` is current.

After the owner creates the tag: `git rev-parse v<version>^{commit}` equals the commit
that passed step 2. Publish from that tag, then install the published version into a
new environment and run `cerebrollm --help`.

Locks: `docs/LOCKS.md` lists each locked file with its path, sha256 and lock date.
Recompute with `sha256sum <path>` and compare before relying on a document. A changed
file needs a new review and a new lock row; an old row never covers new bytes.
```

Check: PL-07, PL-08. The owner approval for a lock is the owner's own commit that adds the row; the owner's own signed approval records are private and are not part of the public rule (question 3).

## 6. Licence and notices (LICENSE, NOTICE, package metadata)

Ruling: the owner ruled on 2026-10-30 that the code is MIT. The copyright holder line is open (question 4).

| File | Content | Check |
|---|---|---|
| LICENSE | the MIT licence text, year 2026, holder as ruled | file read; matches `pyproject.toml` |
| NOTICE | credit for copied third-party text: the release notes in `eval/v2-sources/` come from three public projects, each file records its URL, publication date and fetch date; the licence of each project is stated after it is read from that project's licence file | open each licence file; N until read |
| package metadata | `license = "MIT"` | `pip show cerebrollm` shows MIT after install |

Model licences are separate. The engine's allow-list in `engine/models.toml` admits only Apache-2.0 or MIT models, and the reranker (Apache-2.0) is downloaded by the user and never bundled. A model the user pulls outside the allow-list keeps its own licence terms. The package does not bundle `psycopg2-binary` (LGPL-3.0 with exceptions); `pip` installs it as a dependency and cerebrollm links it unmodified (question 5).

## 7. Branch protection (docs/GOVERNANCE.md)

```markdown
# Governance

The repository protects `main`. A change needs a pull request and the local
gate before it merges. The owner verifies the settings after the repository
becomes public and records the date here. Agents open draft pull requests
only; the owner merges.

Settings verified: not yet (owner step after publication).
```

Check: PL-11. A draft file does not prove the setting is on.

## 8. Owner questions

A. Reporting and contribution
1. Reporting route and target: private vulnerability reporting with a 7-day reply target? Recommended: yes, 7 days; the maintainers are one person, so a shorter target would be a promise the project cannot keep.
2. Sign-off: require DCO sign-off on every commit? Recommended: yes; it needs no signing service and records the right to contribute.

B. Locks and licence
3. Lock approval: accept the owner's own commit adding the row to `docs/LOCKS.md` as the public proof of approval? Recommended: yes; the signed-receipt system stays private.
4. Copyright holder line in `LICENSE`: the GitHub handle `sourav-patra`, or "the cerebrollm authors"? Recommended: the handle, which is the only identity in the published files.
5. The earlier ruling that accepted `psycopg2-binary` rested on the tool not being distributed. The package is now published, though the library is installed by pip and not bundled. Does the ruling still stand? Recommended: yes, state the dependency in `NOTICE`.

Skipped or not checked: figures (none needed; the tables carry the data flow, and the TRD holds the diagrams); the licence of each copied release-note source; closing-keyword behaviour on the real repository; whether the Security tab route works; the folder mode of the PostgreSQL socket; dependency telemetry; the local gate on a fresh checkout.
