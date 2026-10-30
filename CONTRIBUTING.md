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

Skipped or not checked: the "Closes #N" behaviour on the real repository, and the local gate on a fresh checkout.
