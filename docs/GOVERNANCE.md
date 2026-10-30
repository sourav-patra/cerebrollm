# Governance

The repository protects `main`. A change needs a pull request and the local
gate before it merges. The owner verifies the settings after the repository
becomes public and records the date here. Agents open draft pull requests
only; the owner merges.

Settings verified: 2026-10-30. The ruleset `main-security` on the default
branch requires a pull request (no approval count) and passing `unit` and
`package` checks on an up-to-date branch, and blocks force pushes and deletion;
repository admins may bypass it.

Skipped or not checked: the local gate (PostgreSQL and Ollama tests) runs on
the owner's machine, not on GitHub.
