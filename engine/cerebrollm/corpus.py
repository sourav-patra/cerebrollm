"""Enumerate and read the corpus under the configured roots."""
import datetime
import hashlib
import os
import subprocess
from collections import Counter

from . import rules


def _git(root, *args):
    return subprocess.run(["git", "-C", root["path"], *args], check=True,
                          capture_output=True).stdout


def read_source(root, rel_path, ref=None):
    """Exact bytes of a source file; FileNotFoundError when it is absent."""
    if root["kind"] == "git":
        try:
            return _git(root, "show", "%s:%s" % (ref or root["ref"], rel_path))
        except subprocess.CalledProcessError as exc:
            raise FileNotFoundError(rel_path) from exc
    top = os.path.realpath(root["path"])
    full = os.path.realpath(os.path.join(top, rel_path))
    if os.path.commonpath([top, full]) != top:
        raise PermissionError("path outside registered root: " + rel_path)
    with open(full, "rb") as f:
        return f.read()


def _list_paths(root):
    if root["kind"] == "git":
        raw = _git(root, "ls-tree", "-r", "--name-only", "-z", root["ref"])
        return [p for p in raw.decode("utf-8", "replace").split("\0") if p]
    top = root["path"]
    out = []
    for dirpath, dirnames, filenames in os.walk(top, followlinks=False):
        for name in filenames:
            full = os.path.join(dirpath, name)
            rel = os.path.relpath(full, top)
            out.append(("L:" if os.path.islink(full) else "") + rel)
    return out


def _mtime(root, rel_path, commit_date):
    if root["kind"] == "git":
        return commit_date
    ts = os.stat(os.path.join(root["path"], rel_path)).st_mtime
    return datetime.datetime.fromtimestamp(ts).astimezone().isoformat(timespec="seconds")


def enumerate_corpus(cfg):
    """Return (entries, stats). Each entry is a dict ready for the indexer."""
    entries, stats = [], Counter()
    skipped_secret, skipped_rule = [], Counter()
    for root in cfg.roots.values():
        commit_date = None
        if root["kind"] == "git":
            commit_date = _git(root, "show", "-s", "--format=%cI", root["ref"]).decode().strip()
        for item in _list_paths(root):
            stats["seen"] += 1
            if item.startswith("L:"):
                skipped_rule["symlink"] += 1
                continue
            rel = item
            reason = rules.never_reason(rel, cfg.never)
            if reason:
                skipped_rule[reason] += 1
                continue
            hit = rules.classify(root["name"], rel, cfg.rules)
            if hit is None:
                stats["no_rule"] += 1
                continue
            data = read_source(root, rel)
            text = data.decode("utf-8", "replace")
            secret = rules.secret_hit(text)
            if secret:
                skipped_secret.append(root["name"] + ":" + rel)
                continue
            tier, status = hit
            entries.append({
                "root": root["name"], "domain": cfg.domain,
                "project": cfg.project_for(root, rel), "tier": tier, "status": status,
                "path": rel, "ref": root["ref"], "sha256": hashlib.sha256(data).hexdigest(),
                "mtime": _mtime(root, rel, commit_date), "text": text,
            })
    rules.apply_supersession(entries, cfg.default_year)
    entries, stats["duplicates_collapsed"] = rules.collapse_duplicates(entries)
    stats["selected"] = len(entries)
    return entries, {"counts": dict(stats), "skipped_rule": dict(skipped_rule),
                     "skipped_secret": skipped_secret}


def doc_id(entry):
    return "%s:%s:%s:%s" % (entry["domain"], entry["project"], entry["ref"], entry["path"])
