#!/usr/bin/env python3
"""Re-fetch every release note saved in the sources folder of an item set (default v2: eval/v2-sources/) and compare it
with the saved copy (development step N5).
A saved file is a 4-line header (URL, Published, Fetched, Via) and a blank line, then the release body with CRLF
turned into LF. Prints one line per file (match or the difference) and a summary; exits 1 on any difference, and when
the folder is missing or holds no file.
Usage: python3 eval/verify_v2_sources.py [--set NAME]   (needs network access to api.github.com; set GITHUB_TOKEN to
lift the anonymous rate limit of 60 requests an hour, which the 68 files of v3 exceed in one run with the v2 ones;
the token is sent to https://api.github.com only and dropped from every redirect)
"""
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import itemset as IS  # noqa: E402

API_HOST = "api.github.com"


class _KeepTokenAtTheApi(urllib.request.HTTPRedirectHandler):
    """urllib forwards request headers across a redirect. The token is sent to the API at https only, so the request
    that follows any redirect, to any host and scheme, goes without it."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        new = super().redirect_request(req, fp, code, msg, headers, newurl)
        if new is not None:
            new.headers.pop("Authorization", None)
            new.unredirected_hdrs.pop("Authorization", None)
        return new


OPENER = urllib.request.build_opener(_KeepTokenAtTheApi)


def request_for(url, token=None):
    """The request for `url`; the token is attached only to a https request to the API host."""
    headers = {"User-Agent": "verify-v2-sources"}
    parts = urllib.parse.urlsplit(url)
    if token and parts.scheme == "https" and parts.hostname == API_HOST:
        headers["Authorization"] = "Bearer " + token
    return urllib.request.Request(url, headers=headers)


def fetch(url):
    for i in range(5):
        try:
            with OPENER.open(request_for(url, os.environ.get("GITHUB_TOKEN")), timeout=60) as r:
                return json.load(r)
        except Exception:
            time.sleep(2 * (i + 1))
    raise SystemExit("could not fetch " + url)


def check_folder(root, fetcher=fetch):
    """(files checked, files that differ) for the saved release notes under root. Raises SystemExit when root is not a
    folder or holds no file, so that a wrong path does not pass as 0 files, 0 differences."""
    if not os.path.isdir(root):
        raise SystemExit("sources folder not found: %s" % root)
    bad = n = 0
    for dp, _, fs in sorted(os.walk(root)):
        for fn in sorted(fs):
            path = os.path.join(dp, fn)
            with open(path, encoding="utf-8") as f:   # universal newlines: a CRLF checkout compares as LF
                text = f.read()
            head, body = text.split("\n\n", 1)
            kv = dict(l.split(": ", 1) for l in head.split("\n") if ": " in l)
            m = re.match(r"https://github\.com/([^/]+/[^/]+)/releases/tag/(.+)$", kv.get("URL", ""))
            rel = os.path.relpath(path, root).replace(os.sep, "/")
            n += 1
            if not m:
                print("DIFF %s: URL header not a GitHub release URL" % rel)
                bad += 1
                continue
            r = fetcher("https://%s/repos/%s/releases/tags/%s" % ((API_HOST,) + m.groups()))
            want = (r.get("body") or "").replace("\r\n", "\n").replace("\r", "\n").rstrip("\n")
            problems = []
            if want != body.rstrip("\n"):
                problems.append("body differs")
            if r["published_at"][:10] != kv.get("Published"):
                problems.append("Published header %s, API %s" % (kv.get("Published"), r["published_at"][:10]))
            bad += bool(problems)
            print(("DIFF " if problems else "OK   ") + rel + (": " + "; ".join(problems) if problems else ""))
    if n == 0:
        raise SystemExit("no file under %s: nothing was checked" % root)
    return n, bad


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    name = argv[1] if len(argv) == 2 and argv[0] == "--set" else None
    if argv and name is None:
        print(__doc__)
        return 2
    n, bad = check_folder(IS.load(name).sources)
    print("%d files checked, %d differ" % (n, bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
