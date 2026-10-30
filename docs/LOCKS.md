# Locks

Each row is a document the owner locked. Recompute the hash with `sha256sum <path>` and compare it before you rely on a document. A changed file needs a new review and a new lock row; an old row never covers new bytes (see `docs/RELEASING.md`).

| Document | Kind | Draft | Path | sha256 of the locked file | Date | Approval |
|---|---|---|---|---|---|---|
| PRD | contract | draft v6 | `docs/design/PRD-cerebrollm-2026-10-30.md` | `622fee4d88bc88bdf7e59d767940b809c6651b72ce343b8075695724f84572f2` | 2026-10-30 | locked by the owner |
| TRD | contract | draft v4 | `docs/design/TRD-cerebrollm-2026-10-30.md` | `37e2cff553aa760385bc8f03d6852f20e82b4b0a896c2e3e517c06e31e2a3e12` | 2026-10-30 | locked by the owner |
| LLD | contract | draft v5 | `docs/design/LLD-cerebrollm-2026-10-30.md` | `38337ffa37140ee6e6ef4af28e9ae80130ddda35129a70f46d4460d78b7c0b60` | 2026-10-30 | locked by the owner |
| POLICY | contract | draft v4 | `docs/design/POLICY-cerebrollm-2026-10-30.md` | `b242589a11e14c2bea669de0b601c4b59c3985d0bcfbd10f88d052f400ad4702` | 2026-10-30 | locked by the owner |

The files are copied byte for byte, and `.gitattributes` stops git from changing their line endings. Two independent reviewers passed each file on the hash shown. After the first lock, the owner approved a header-only edit (the `status:` line now reads LOCKED, and the pins to other documents name the locked PRD and TRD hashes); both reviewers confirmed that no other byte changed, and the owner locked the files again on these hashes. Section 1 of the POLICY records the state of each check before the lock.

Skipped or not checked: the hashes were recomputed on 2026-10-30 from the files in this folder and match the lock records; nothing else was checked.
