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

Skipped or not checked: nothing skipped.
