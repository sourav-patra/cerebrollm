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

## Writing docs

The README is the front door: a stranger decides in a minute whether to try the project.

- Order: the project name and a one-line promise, status badges from GitHub, and a figure of the project working, all before the first section. Then the headings "Why", "Features", "Quick start" and "Docs". Under "Why", state the reader's problem with one line of evidence. Number the quick-start steps; run each one and end it on a check the reader can run. Put reference detail behind links.
- Keep paragraphs to at most 60 words, most under 25. Put detail in lists, tables or linked pages.
- Each sentence states one thing a reader can check. Name who does what, and state errors as cause and fix. No filler words, no "etc.", no dashes joining clauses, no "not X but Y", no sales adjectives.
- Explain a technical term the first time it appears, or link to where it is explained. Keep each fact in one place and link to it elsewhere.
- Every number is measured, or marked "not measured" with the command that would measure it. Name the source of each claim, and keep observed, reported and planned behaviour apart.
- Use at least two distinct rendered figures that answer different questions, in one style. Badges, logos and repeated images do not count. Give each figure labels, alt text and a caption stating its conclusion and limits; colour never carries meaning alone. Use animation when motion explains the task. Keep each diagram as one plain-text SVG in the repository, edited directly, with system fonts and no external resources; update any derived image when its SVG changes. Never paste diagram source or ASCII boxes into the README.
- Check what each figure shows against the source revision, and look at it at reading size. Record both checks; keep unperformed checks pending.
- Keep the status, the key evidence and the main limits next to the claims they qualify. Never include secrets, tokens, personal data or paths outside the project.

Before opening a pull request, run `python scripts/readme_lint.py README.md`; CI runs it on every pull request. Passing the lint does not mean the README follows every rule above. A reviewer checks every rule above and that links open without signing in. Then someone unfamiliar with the project, without help, says its audience, problem and status within a minute, and after reading, its input, output, the decision it supports, the first action, the evidence and the main limits, and explains the figures. Record their answers and what they misread, fix it and ask again. Keep the GitHub sidebar current: description, a working website or docs link, 5 to 10 relevant topics, a social preview image, and a release for each published version. If the lint rejects correct text, open an issue about the lint; do not rewrite correct text to pass it.

Skipped or not checked: the "Closes #N" behaviour on the real repository, and the local gate on a fresh checkout.
