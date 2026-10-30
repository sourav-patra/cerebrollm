"""Path rules: never-index, tier and status, supersession, secret scan. Pure functions, no I/O."""
import re
from datetime import date
from fnmatch import fnmatchcase
from pathlib import PurePosixPath

MONTHS = {m: i + 1 for i, m in enumerate(
    "jan feb mar apr may jun jul aug sep oct nov dec".split())}

_B = r"(?<![a-z0-9])"          # token boundaries inside a lower-cased file stem
_E = r"(?![a-z0-9])"
ISO_DATE = re.compile(_B + r"(\d{4})-(\d{2})-(\d{2})" + _E)
DAY_MONTH = re.compile(_B + r"(\d{1,2})-(" + "|".join(MONTHS) + r")[a-z]*(?:-(\d{4}))?" + _E)
REVISION = re.compile(_B + r"(?:rev|r)(\d+)" + _E)

# Status lines are matched on lower-cased text. A `Status:` value that starts with "superseded",
# or a line that starts with "Superseded by", declares the whole file superseded.
STATUS_SUPERSEDED = re.compile(r"^[\s>*_#-]*status\b[\s*_]*:[\s*_]*superseded")
SUPERSEDED_BY = re.compile(r"^[\s>*_#-]*superseded by\b")
STATUS_WINDOW = 30                 # lines read from the top of a file
APPEND_ONLY_PREFIX = "JOURNAL"     # daily records: never revisions of one another

SECRET_PATTERNS = [
    re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH |PGP )?PRIVATE KEY"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"gh[pousr]_[A-Za-z0-9]{30,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{30,}"),
    re.compile(r"xox[abprs]-[A-Za-z0-9-]{10,}"),
    re.compile(r"sk-(?=[A-Za-z0-9_-]*\d)(?=[A-Za-z0-9_-]*[A-Za-z])[A-Za-z0-9_-]{24,}"),
    re.compile(r"AIza[0-9A-Za-z_-]{35}"),
    re.compile(r"eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"),
    re.compile(r"(?i)\b(?:api[_-]?key|secret|token|passw(?:or)?d)\b[\"']?\s*[:=]\s*[\"']?"
               r"(?=[A-Za-z0-9/+_-]*\d)(?=[A-Za-z0-9/+_-]*[A-Za-z])[A-Za-z0-9/+_-]{24,}"),
]


def never_reason(rel_path, never):
    """Return why a relative path is never indexed, or None. Pure: decides from the path alone,
    so the caller can skip the file before reading it."""
    for pre in never.get("path_prefixes", []):
        if rel_path.startswith(pre):
            return "path:" + pre
    p = PurePosixPath(rel_path)
    for part in p.parts[:-1]:
        low = part.lower()
        if low in never["dirs"]:
            return "dir:" + low
        for pre in never["dir_prefixes"]:
            if low.startswith(pre):
                return "dir:" + pre + "*"
    for pre in never.get("file_prefixes", []):
        if p.name.startswith(pre):
            return "file:" + pre + "*"
    suffix = p.suffix.lower()
    if suffix in never["suffixes"]:
        return "suffix:" + suffix
    return None


def _glob_parts(parts, pats):
    if not pats:
        return not parts
    if pats[0] == "**":   # spans zero or more directories
        return any(_glob_parts(parts[i:], pats[1:]) for i in range(len(parts) + 1))
    return bool(parts) and fnmatchcase(parts[0], pats[0]) and _glob_parts(parts[1:], pats[1:])


def full_match(path, glob):
    """PurePath.full_match(glob, case_sensitive=True), which exists only from Python 3.13."""
    return _glob_parts(path.parts, PurePosixPath(glob).parts)


def classify(root_name, rel_path, rules):
    """First matching tier rule for (root, relative path) -> (tier, status) or None."""
    p = PurePosixPath(rel_path)
    for rule in rules:
        if rule["root"] == root_name and full_match(p, rule["glob"]):
            return rule["tier"], rule["status"]
    return None


def secret_hit(text):
    """Name of the first secret pattern that matches, or None."""
    for i, pat in enumerate(SECRET_PATTERNS):
        if pat.search(text):
            return "pattern%d" % i
    return None


def status_line_superseded(text):
    """True when one of the first STATUS_WINDOW lines declares the whole file superseded: a line
    starting `Status:` (any case) whose value starts with "superseded", or a line starting
    "Superseded by". A phrase inside another status value does not count, so
    "Status: current; individual details may be superseded by a later note" is not superseded."""
    for line in text.splitlines()[:STATUS_WINDOW]:
        low = line.lower()
        if STATUS_SUPERSEDED.match(low) or SUPERSEDED_BY.match(low):
            return True
    return False


def family(filename, default_year=2026):
    """Split a file name into (family key, ordering key).

    The family key is the lower-cased stem with revision tokens (rev16, r7, -r2) and date
    tokens (2026-10-24, 18-oct, 17-oct-2026) removed. The ordering key is
    (highest revision number, latest date ordinal); absent parts count as 0.
    """
    stem = PurePosixPath(filename).stem.lower()
    rev, when = 0, 0

    def take_iso(m):
        nonlocal when
        try:
            when = max(when, date(int(m[1]), int(m[2]), int(m[3])).toordinal())
        except ValueError:
            pass
        return " "

    def take_dm(m):
        nonlocal when
        try:
            when = max(when, date(int(m[3] or default_year), MONTHS[m[2]], int(m[1])).toordinal())
        except ValueError:
            pass
        return " "

    def take_rev(m):
        nonlocal rev
        rev = max(rev, int(m[1]))
        return " "

    stem = ISO_DATE.sub(take_iso, stem)
    stem = DAY_MONTH.sub(take_dm, stem)
    stem = REVISION.sub(take_rev, stem)
    key = re.sub(r"[\s._-]+", "-", stem).strip("-")
    return key, (rev, when)


def apply_supersession(entries, default_year=2026):
    """Mark older family members superseded.

    entries: list of dicts with keys root, path, status, text. Mutates status. A family is the
    set of files in one root and one directory with the same family key. Files whose name starts
    with APPEND_ONLY_PREFIX (JOURNAL) never form a family. Within a family of two or more, every
    member whose ordering key is below the maximum becomes `superseded`; members tied at the
    maximum all stay. A status line that declares the file superseded also sets it.
    """
    groups = {}
    for e in entries:
        p = PurePosixPath(e["path"])
        key, order = family(p.name, default_year)
        e["_order"] = order
        if key and not p.name.startswith(APPEND_ONLY_PREFIX):
            groups.setdefault((e["root"], str(p.parent), key), []).append(e)
    for members in groups.values():
        if len(members) < 2:
            continue
        newest = max(m["_order"] for m in members)
        for m in members:
            if m["_order"] < newest:
                m["status"] = "superseded"
    for e in entries:
        if status_line_superseded(e["text"]):
            e["status"] = "superseded"
        e.pop("_order", None)
    return entries


ACTIVE_RANK = {"locked": 2, "current": 2, "draft": 1, "superseded": 0}


def collapse_duplicates(entries):
    """Keep one entry per distinct sha256.

    The kept copy has the highest authority: an active status (locked or current) before draft
    before superseded, then the lower tier number (T1 first), then the folder that sorts last, then
    the full path. Lock copies all share a tier and status, so the newest lock folder wins. A
    current file that also sits under drafts/ therefore keeps its T2 entry, and the draft copy is
    recorded in `also_at` rather than demoting the text. Every other copy is listed in the kept
    entry's `also_at` as "root:path". Every returned entry has `also_at`, a sorted list that is
    empty when there is no copy. Returns (kept entries, number of copies removed).
    """
    groups = {}
    for e in entries:
        groups.setdefault(e["sha256"], []).append(e)
    kept, removed = [], 0
    for members in groups.values():
        keep = max(members, key=lambda m: (
            ACTIVE_RANK.get(m["status"], 0), -int(m["tier"][1:]),
            PurePosixPath(m["path"]).parent.as_posix(), m["path"]))
        others = sorted("%s:%s" % (m["root"], m["path"]) for m in members if m is not keep)
        keep["also_at"] = others
        removed += len(others)
        kept.append(keep)
    return kept, removed
