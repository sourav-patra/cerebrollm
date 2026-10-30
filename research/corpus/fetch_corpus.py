#!/usr/bin/env python3
"""Build the public corpus for issues #10 and #12 (ruling R-1). Stdlib only.

Every source is pinned to a commit recorded here. External sources are shallow-fetched
at that commit into ~/cerebrollm-scratch/corpus-src/ and their Markdown is copied into
~/cerebrollm-corpus/<source>/. This repository is read at OWN_COMMIT with git show and
written with LF line endings into ~/cerebrollm-corpus/cerebrollm/. Only that subtree is
rebuilt. External files already present are verified against their pinned hash and never
rewritten. Fetched text is copied as bytes. It is never executed or interpreted.

Run inside Ubuntu:
  wsl -d Ubuntu-24.04 -- python3 <repo>/research/corpus/fetch_corpus.py
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
HOME = Path.home()
CORPUS = HOME / "cerebrollm-corpus"
SCRATCH = HOME / "cerebrollm-scratch" / "corpus-src"
MANIFEST = HERE / "manifest.json"

MD_SUFFIXES = (".md", ".mdx")
MAX_FILES = 1500
MIN_FILES = 300
LICENCE_NAMES = ("LICENSE", "LICENSE.md", "LICENSE.txt", "COPYING")

# This repository, read with git show at this commit (not the working copy).
OWN_COMMIT = "abd558470b373a10d679db4098cddf2f573b8778"
OWN_EXCLUDE = ("eval/", "research/model-study/selection/", "research/corpus/")
OWN_RESEARCH_PUBLIC = "research/model-study/"   # any other file under research/ belongs to the private working repository and is never copied

# External sources, each pinned to the commit fetched for the first corpus build.
UPSTREAM = [
    {"name": "llama_index", "url": "https://github.com/run-llama/llama_index",
     "commit": "619d74664e8404612038bc15a1a40c686037277c", "roots": ["docs"]},
    {"name": "ollama", "url": "https://github.com/ollama/ollama",
     "commit": "46d2e4e8fbf9329601452ede6d21b4030faa5607", "roots": ["docs", "README.md"]},
    {"name": "pgvector", "url": "https://github.com/pgvector/pgvector",
     "commit": "3fc275dab27818f4b327ddf8b85b90b274584540", "roots": ["README.md", "CHANGELOG.md", "docs"]},
    {"name": "promptfoo", "url": "https://github.com/promptfoo/promptfoo",
     "commit": "bfe97095b6d9eabd424021f004b13038068881d3", "roots": ["site/docs"]},
]

# LlamaIndex API reference. Trimmed only if the total exceeds MAX_FILES.
LLAMA_API_ROOT = "docs/api_reference/api_reference"

# SPDX identifier -> phrases that must all appear (after whitespace normalisation).
SPDX_RULES = {
    "MIT": ["Permission is hereby granted, free of charge", "THE SOFTWARE IS PROVIDED"],
    "Apache-2.0": ["Apache License", "Version 2.0, January 2004"],
    "PostgreSQL": ["Permission to use, copy, modify, and distribute this software and its documentation "
                   "for any purpose, without fee, and without a written agreement is hereby granted"],
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_run(args: tuple[str, ...], cwd: Path) -> bytes:
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0")
    result = subprocess.run(["git", "-c", "safe.directory=*", *args], cwd=cwd, env=env,
                            capture_output=True, check=False)
    if result.returncode != 0:
        sys.exit(f"git {' '.join(args)} failed in {cwd} ({result.returncode}): "
                 f"{result.stderr.decode(errors='replace').strip()}")
    return result.stdout


def git(*args: str, cwd: Path) -> str:
    return git_run(args, cwd).decode("utf-8")


def classify_licence(text: str) -> str | None:
    """Return the one SPDX identifier whose phrases all appear, else None."""
    norm = " ".join(text.split())
    hits = [spdx for spdx, phrases in SPDX_RULES.items() if all(p in norm for p in phrases)]
    return hits[0] if len(hits) == 1 else None


def licence_from_dir(base: Path) -> dict:
    for name in LICENCE_NAMES:
        path = base / name
        if path.is_file():
            data = path.read_bytes()
            text = data.decode("utf-8", errors="replace")
            first = next((line.strip() for line in text.splitlines() if line.strip()), "")
            return {"file": name, "sha256": sha256_bytes(data),
                    "spdx": classify_licence(text) or "unclear", "first_line": first}
    return {"file": None, "spdx": "unclear", "first_line": "", "note": "no licence file at repository root"}


def md_under(base: Path, root: str) -> list[str]:
    """Relative POSIX paths of Markdown files under root (a file or a directory)."""
    start = base / root
    if start.is_file():
        return [root] if root.lower().endswith(MD_SUFFIXES) else []
    if not start.is_dir():
        return []
    return [p.relative_to(base).as_posix() for p in sorted(start.rglob("*"))
            if p.is_file() and not p.is_symlink() and p.name.lower().endswith(MD_SUFFIXES)]


def fetch_pinned(source: dict) -> dict:
    if not source["url"].startswith("https://github.com/"):
        sys.exit(f"refusing non-GitHub HTTPS source: {source['url']}")
    dest = SCRATCH / source["name"]
    shutil.rmtree(dest, ignore_errors=True)
    dest.mkdir(parents=True)
    git("init", "-q", cwd=dest)
    git("remote", "add", "origin", source["url"], cwd=dest)
    git("fetch", "-q", "--depth", "1", "--no-tags", "origin", source["commit"], cwd=dest)
    git("checkout", "-q", "--detach", "FETCH_HEAD", cwd=dest)
    commit = git("rev-parse", "HEAD", cwd=dest).strip()
    if commit != source["commit"]:
        sys.exit(f"{source['name']}: fetched {commit}, pinned {source['commit']}")
    found, missing = [], []
    for root in source["roots"]:
        hits = md_under(dest, root)
        if not hits:
            missing.append(root)
        found.extend(hits)
    files = [(rel, (dest / rel).read_bytes()) for rel in found]
    return {"name": source["name"], "url": source["url"], "commit": commit,
            "licence": licence_from_dir(dest), "roots": source["roots"], "missing_roots": missing,
            "files": files}


def own_commit_available() -> bool:
    """False in a clone of the public repository, which does not contain the history OWN_COMMIT belongs to."""
    r = subprocess.run(["git", "-c", "safe.directory=*", "cat-file", "-e", OWN_COMMIT + "^{commit}"],
                       cwd=REPO, capture_output=True, check=False)
    return r.returncode == 0


def cerebrollm_source() -> dict:
    listed = [p for p in git("ls-tree", "-r", "--name-only", "-z", OWN_COMMIT, cwd=REPO).split("\0") if p]
    files, crlf = [], 0
    for rel in listed:
        if not rel.lower().endswith(MD_SUFFIXES) or rel.startswith(OWN_EXCLUDE):
            continue
        if rel.startswith("research/") and not rel.startswith(OWN_RESEARCH_PUBLIC):
            continue
        data = git_run(("show", f"{OWN_COMMIT}:{rel}"), cwd=REPO)
        if b"\r\n" in data:
            crlf += 1
            data = data.replace(b"\r\n", b"\n")
        files.append((rel, data))
    return {"name": "cerebrollm", "url": "local:" + str(REPO), "commit": OWN_COMMIT,
            "licence": {"file": None, "spdx": "none", "first_line": "",
                        "note": "no licence file at repository root"},
            "roots": ["*.md at OWN_COMMIT, minus eval/, research/model-study/selection/, research/corpus/"],
            "missing_roots": [], "files": files, "crlf_files_converted": crlf}


def dest_rel(rel: str, taken: set[str]) -> str:
    """foo.mdx is renamed to foo.md; if that name is taken, foo.mdx.md keeps both."""
    if rel.endswith(".mdx"):
        renamed = rel[:-1]
        return renamed if renamed not in taken else rel + ".md"
    return rel


def plan_records(sources: list[dict]) -> list[dict]:
    records = []
    for src in sources:
        taken = {rel for rel, _ in src["files"]}
        for rel, data in src["files"]:
            records.append({"source": src["name"], "url": src["url"], "commit": src["commit"],
                            "licence": src["licence"]["spdx"], "upstream_path": rel,
                            "path": f"{src['name']}/{dest_rel(rel, taken)}",
                            "bytes": len(data), "sha256": sha256_bytes(data), "data": data})
    return sorted(records, key=lambda r: r["path"])


def subtree_of(upstream_path: str) -> str | None:
    """The API subtree a record belongs to: a directory with a trailing slash, or a loose file."""
    prefix = LLAMA_API_ROOT + "/"
    if not upstream_path.startswith(prefix):
        return None
    head, sep, _ = upstream_path[len(prefix):].partition("/")
    return prefix + head + sep


def trim_to_cap(records: list[dict], cap: int = MAX_FILES) -> tuple[list[dict], list[dict]]:
    """Drop whole LlamaIndex API subtrees, largest file count first, until at most cap records remain."""
    need = len(records) - cap
    if need <= 0:
        return records, []
    groups: dict[str, list[dict]] = defaultdict(list)
    for rec in records:
        key = subtree_of(rec["upstream_path"]) if rec["source"] == "llama_index" else None
        if key:
            groups[key].append(rec)
    chosen = []
    for key in sorted(groups, key=lambda k: (-len(groups[k]), k)):
        if need <= 0:
            break
        chosen.append(key)
        need -= len(groups[key])
    if need > 0:
        raise RuntimeError(f"still {need} records over the cap after dropping every API subtree")
    drop = set(chosen)
    kept = [r for r in records
            if not (r["source"] == "llama_index" and subtree_of(r["upstream_path"]) in drop)]
    dropped = [{"subtree": k, "files": len(groups[k]), "bytes": sum(r["bytes"] for r in groups[k])}
               for k in chosen]
    assert len(records) - len(kept) == sum(d["files"] for d in dropped)
    assert len(kept) <= cap
    return kept, dropped


def self_check() -> None:
    def rec(source: str, path: str, size: int = 10) -> dict:
        return {"source": source, "upstream_path": path, "path": f"{source}/{path}", "bytes": size}

    api = LLAMA_API_ROOT + "/"
    # 1,501 records; the 900-file subtree is the largest API subtree and alone brings the total under the cap.
    case = [rec("llama_index", api + "index.md")]
    case += [rec("llama_index", api + f"big/f{i}.md") for i in range(900)]
    case += [rec("llama_index", api + f"small/f{i}.md") for i in range(300)]
    case += [rec("ollama", f"docs/f{i}.md") for i in range(1501 - len(case))]
    assert len(case) == 1501
    kept, dropped = trim_to_cap(case)
    assert len(kept) <= MAX_FILES
    assert [d["subtree"] for d in dropped] == [api + "big/"], dropped
    assert len(case) - len(kept) == 900
    assert all(subtree_of(r["upstream_path"]) != api + "big/" for r in kept)

    # 1,501 records; the only API record is the loose index.md, so it alone is dropped.
    case2 = [rec("llama_index", api + "index.md")] + [rec("ollama", f"docs/f{i}.md") for i in range(1500)]
    kept2, dropped2 = trim_to_cap(case2)
    assert len(kept2) == MAX_FILES
    assert [d["subtree"] for d in dropped2] == [api + "index.md"], dropped2
    assert all(r["upstream_path"] != api + "index.md" for r in kept2)

    # Licence identification: a clear MIT text matches, unrelated text does not.
    mit = ("The MIT License\n\nPermission is hereby granted, free of charge, to any person\n"
           "THE SOFTWARE IS PROVIDED \"AS IS\"")
    assert classify_licence(mit) == "MIT"
    assert classify_licence("Some other licence text") is None


def external_pairs(manifest: dict) -> tuple[set, dict]:
    pairs = {(f["path"], f["sha256"]) for f in manifest["files"] if f["source"] != "cerebrollm"}
    commits = {s["name"]: s["commit"] for s in manifest["sources"] if s["name"] != "cerebrollm"}
    return pairs, commits


def write_corpus(records: list[dict]) -> None:
    if any(r["source"] == "cerebrollm" for r in records):
        shutil.rmtree(CORPUS / "cerebrollm", ignore_errors=True)
    for rec in records:
        if rec["source"] == "cerebrollm":
            target = CORPUS / rec["path"]
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(rec["data"])
        else:
            target = CORPUS / rec["path"]
            if target.exists():
                if sha256_bytes(target.read_bytes()) != rec["sha256"]:
                    sys.exit(f"existing external file differs from its pinned content, not rewritten: {target}")
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(rec["data"])
        if sha256_bytes(target.read_bytes()) != rec["sha256"]:
            sys.exit(f"hash mismatch after write: {target}")


def main() -> int:
    self_check()
    previous = json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else None

    own = [cerebrollm_source()] if own_commit_available() else []
    if not own:
        print("note: the cerebrollm source (this repository at OWN_COMMIT) is not in this clone; the corpus has the upstream sources only")
    sources = own + [fetch_pinned(s) for s in UPSTREAM]
    records = plan_records(sources)
    records, dropped = trim_to_cap(records)
    if dropped:
        sys.exit(f"trimming would remove external files ({sum(d['files'] for d in dropped)}); "
                 "not written. Decide the cap before rebuilding.")

    if previous is not None:
        old_pairs, old_commits = external_pairs(previous)
        new_pairs = {(r["path"], r["sha256"]) for r in records if r["source"] != "cerebrollm"}
        new_commits = {s["name"]: s["commit"] for s in sources if s["name"] != "cerebrollm"}
        if old_pairs != new_pairs or old_commits != new_commits:
            sys.exit("external sources differ from the previous manifest; nothing was written")
        external_unchanged = True
    else:
        external_unchanged = None

    write_corpus(records)

    total_bytes = sum(r["bytes"] for r in records)
    summary = []
    for src in sources:
        mine = [r for r in records if r["source"] == src["name"]]
        entry = {"name": src["name"], "url": src["url"], "commit": src["commit"],
                 "licence": src["licence"], "roots": src["roots"], "missing_roots": src["missing_roots"],
                 "files": len(mine), "bytes": sum(r["bytes"] for r in mine)}
        if "crlf_files_converted" in src:
            entry["crlf_files_converted"] = src["crlf_files_converted"]
        summary.append(entry)
    manifest = {"fetched_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "corpus_root": str(CORPUS), "min_files": MIN_FILES, "max_files": MAX_FILES,
                "external_unchanged_from_previous_manifest": external_unchanged,
                "total_files": len(records), "total_bytes": total_bytes,
                "trimmed": dropped, "sources": summary,
                "files": [{k: v for k, v in r.items() if k != "data"} for r in records]}
    MANIFEST.write_text(json.dumps(manifest, indent=1) + "\n", encoding="utf-8", newline="\n")

    for entry in summary:
        print(f"{entry['name']}: {entry['files']} files, {entry['bytes']} bytes, commit {entry['commit']}, "
              f"licence {entry['licence']['spdx']}")
    print(f"total: {len(records)} files, {total_bytes} bytes")
    print(f"external unchanged from previous manifest: {external_unchanged}")
    print(f"manifest: {MANIFEST} sha256 {sha256_bytes(MANIFEST.read_bytes())}")
    if len(records) < MIN_FILES:
        print(f"WARNING: below the {MIN_FILES}-file target")
    return 0


if __name__ == "__main__":
    sys.exit(main())
