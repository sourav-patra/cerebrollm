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
   after `git fetch --prune origin`, so that remote branches match GitHub,
   `git log --all --format='%ae%n%ce' | sort -u` lists only the project's noreply
   address `61248036+sourav-patra@users.noreply.github.com`, `noreply@github.com`
   (the committer of merges made on GitHub) and `noreply@anthropic.com`;
   `git log --all --format='%H %ae %ce' | grep -F noreply@anthropic.com` prints one
   line, for `6ff229626d2215033ef705007fc818a3efeff8a9`. The check compares
   addresses, because the project address appears under two names (`sourav-patra`
   and `Sourav Patra`) that are one account. That one commit (project plan, code of
   conduct and launch post drafts, 2026-11-10) has an agent's public noreply
   address as author and committer; it holds no private address, and rewriting
   `main` to change it would change every later commit hash. Any other commit with
   that address fails the check; `grep -rIFf NEEDLES . | grep -vxFf ACCEPTED` prints
   nothing and neither `grep` reports an error. NEEDLES is the owner's file of
   private names and paths. ACCEPTED is the owner's file of complete scan lines
   already read and accepted as upstream text. Both stay outside the repository.
   As of 0.1.1, ACCEPTED holds three LlamaIndex lines: a package heading and two
   manifest paths. A changed line that still matches NEEDLES prints again unless
   ACCEPTED holds the new line. From 0.2.0 the `release-gate` check runs these
   scans with the settings in `.github/release-gate.toml`, so NEEDLES and ACCEPTED
   stay in the gate's secrets and no agent sees them. A successful check from the
   `agent-release-gate` App on the release commit passes step 2, and
   `.github/workflows/publish.yml` refuses a release without one. The scheduled
   gate scans only open pull request heads and `v*` tags, so before the tag run
   `gh workflow run gate.yml --repo sourav-patra/release-gate -f
   repo=sourav-patra/cerebrollm -f sha=<full release commit>` and wait for that
   commit's `release-gate` check to succeed. Without the
   gate, the owner saves the four outputs and attaches them to the release pull
   request.
3. `python -m build` makes the sdist and wheel; the wheel installs into a new
   virtual environment, and `cerebrollm --help` and `cerebrollm ask --help` exit 0.
4. The PRD, TRD, LLD and POLICY are locked and `docs/LOCKS.md` is current.

After the owner creates the tag: `git rev-parse v<version>^{commit}` equals the commit
that passed step 2. Publish from that tag, then install the published version into a
new environment and run `cerebrollm --help`.

Locks: `docs/LOCKS.md` lists each locked file with its path, sha256 and lock date.
Recompute with `sha256sum <path>` and compare before relying on a document. A changed
file needs a new review and a new lock row; an old row never covers new bytes.

Skipped or not checked: nothing skipped.
