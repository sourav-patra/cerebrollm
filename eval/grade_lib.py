"""Code grading exactly as eval/GRADING.md (frozen). Stdlib only.

No retuning after the first scored run (GRADING.md, last paragraph).
"""
import re
import unicodedata

STOP = set("a an and are as at be by for from has have in is it its of on or that the this to was were will with".split())
CLAUSE_WORDS = {"but", "however", "whereas", "while"}
PRE_SKIP = {"the", "a", "an", "use", "using", "to"}
PRE_CUE = set("not never avoid without formerly previously earlier old older former legacy previous outdated "
              "obsolete from was were".split())
CUE_PREFIX = ("deprecat", "supersed", "replac", "renam", "remov", "dropp")
POST_SKIP = set("is are was were been be being has have had now also since already officially currently long "
                "considered marked flagged labelled labeled upstream by a an the and or all both class classes "
                "object objects field fields parameter parameters option options alias flag flags property term "
                "terms name names strategy provider endpoint endpoints method methods".split())
POST_PREFIX = ("deprecat", "supersed", "replac", "renam", "remov", "dropp", "obsolet", "outdat", "unsupport",
               "sunset", "legacy")


def tokens(text):
    t = unicodedata.normalize("NFKC", text).lower()
    t = t.replace("*", " times ").replace("×", " times ").replace("+", " plus ")
    t = re.sub(r"(?<=\s)[-–−](?=\s)", " minus ", t)
    t = t.replace("–", " minus ").replace("−", " minus ")
    return re.sub(r"[^0-9a-z]+", " ", t).split()


def strip_think(answer):
    return re.sub(r"<think>.*?</think>", "", answer, flags=re.S | re.I)


def _contains(hay, needle):
    n = len(needle)
    return n > 0 and any(hay[i:i + n] == needle for i in range(len(hay) - n + 1))


# Implementation of GRADING.md line 15 ("an answer that only says it does not know is incorrect"): when the answer
# contains one of these phrases, the 80 percent content-word fallback is off and only a contiguous match (rule 1) passes.
DISCLAIMERS = [tokens(p) for p in (
    "I don't know", "I do not know", "not sure", "cannot determine", "can't determine", "unable to determine",
    "no information", "does not say", "doesn't say", "not mentioned", "not specified")]


def has_disclaimer(atoks):
    return any(_contains(atoks, d) for d in DISCLAIMERS)


def alt_present(alt, atoks, aset, strict=False):
    exact = alt.startswith("=") or strict
    at = tokens(alt[1:] if alt.startswith("=") else alt)
    if not at:
        return False
    if _contains(atoks, at):
        return True
    if exact:
        return False
    content = {t for t in at if t not in STOP}
    return bool(content) and len(content & aset) / len(content) >= 0.8


def key_facts_ok(item, atoks):
    aset = set(atoks)
    strict = has_disclaimer(atoks)
    missing = []
    for kf in item["key_facts"]:
        alts = [kf] if isinstance(kf, str) else kf
        if not any(alt_present(a, atoks, aset, strict) for a in alts):
            missing.append(kf)
    return not missing, missing


def clauses(text):
    parts = []
    for line in text.split("\n"):
        for seg in re.split(r";|(?<=[.!?])\s+", line):
            toks = tokens(seg)
            cur = []
            for t in toks:
                if t in CLAUSE_WORDS:
                    parts.append(cur)
                    cur = []
                else:
                    cur.append(t)
            parts.append(cur)
    return [p for p in parts if p]


def _exempt(clause, i, n, quote_runs, other_tokens):
    # 1. verbatim quote: a run of >= 5 tokens (the shortest such window around the marker) found in a quoted line
    m = max(5, n)
    for a in range(max(0, i + n - m), min(i, len(clause) - m) + 1):
        if any(_contains(q, clause[a:a + m]) for q in quote_runs):
            return True
    # 2. cue before
    j = i - 1
    for _ in range(3):
        if j >= 0 and clause[j] in PRE_SKIP:
            j -= 1
        else:
            break
    if j >= 0:
        t = clause[j]
        prev = clause[j - 1] if j >= 1 else ""
        if (t in PRE_CUE or t.startswith(CUE_PREFIX) or (prev, t) in {("no", "longer"), ("instead", "of"),
                                                                       ("rather", "than")}):
            return True
    # 3. cue after
    j = i + n
    skip = other_tokens | POST_SKIP
    for _ in range(8):
        if j < len(clause) and clause[j] in skip:
            j += 1
        else:
            break
    if j < len(clause) and (clause[j].startswith(POST_PREFIX) or clause[j] in ("old", "older")):
        return True
    return False


def stated_markers(item, answer):
    """Marker occurrences that count as stated (empty list = the answer does not state the stale fact)."""
    st = item.get("stale")
    if not st:
        return []
    markers = [tokens(m) for m in st["markers"]]
    quote_runs = [tokens(q) for q in [x["text"] for x in item["quotes"]] + [st["current"]["text"]]]
    hits = []
    for c in clauses(strip_think(answer)):
        for mt in markers:
            n = len(mt)
            if not n:
                continue
            other = {t for m2 in markers if m2 != mt for t in m2}
            for i in range(len(c) - n + 1):
                if c[i:i + n] == mt and not _exempt(c, i, n, quote_runs, other):
                    hits.append(" ".join(mt))
    return hits


def grade(item, answer):
    """Return (correct, detail)."""
    text = strip_think(answer or "").strip()
    if not text:
        return False, {"reason": "empty"}
    atoks = tokens(text)
    ok, missing = key_facts_ok(item, atoks)
    detail = {"missing_key_facts": missing, "disclaimer": has_disclaimer(atoks)}
    if ok and item["kind"] == "stale":
        st = stated_markers(item, text)
        detail["stale_markers_stated"] = st
        ok = not st
    return ok, detail
