Status: repository adoption decision dated 2026-11-07.

# 0001: Adopt the Agentic Engineering Philosophy v3 r9 and lock-then-run r2

| Field | Value |
|---|---|
| Question | Which engineering rule and which authority policy does cerebrollm follow, and at which revision? |
| Status | Adopted on the owner's instruction, 7 Nov 2026 |
| Sources | Agentic Engineering Philosophy v3 r9 (adapted copy of 2026-10-27), SHA-256 `cabfdae6e047461285acdf1a087b63b18760036767380a9c65ea03563b5eae08`. Lock-then-run (LTR) r2 (adapted copy of 2026-10-27), SHA-256 `4e58630a626b1bfcb1f343721d44908433a822abe2c3757ab529801804a6287d`. Both copies are kept outside this repository; each hash matched its sidecar file on 2026-11-07. |
| Related | [LOCKS.md](../LOCKS.md) (the locked contracts), [GOVERNANCE.md](../GOVERNANCE.md) |

## Decision

1. cerebrollm follows the philosophy at r9: its floor (F1 to F5) and its principles apply to the code, the evaluation and the documents in this repository.
2. cerebrollm follows LTR r2 as its authority policy. Sections 1 to 7 take precedence. Section 8 is a set of preferences; its lines marked "binding" only restate sections 1 to 7 or the philosophy's floor.
3. A copy whose hash does not match the hash above is not the adopted text. A later revision of either document is adopted only by a new decision record that names its SHA-256.
4. The locked contracts in `docs/LOCKS.md` (PRD, TRD, LLD and POLICY of 2026-10-30) keep their bytes and hashes. Where a contract and r9 or LTR r2 differ, the stricter rule applies, and the difference is recorded in `docs/LOCKS.md` until the owner revises that contract in its next lock.

Skipped or not checked: the four contracts were not compared line by line against r9 or LTR r2; no owner signature or runtime check occurred.
