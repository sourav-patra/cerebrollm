#!/usr/bin/env python3
"""Re-fetch every release note saved in eval/v2-sources/ and compare it with the saved copy (development step N5).
A saved file is a 4-line header (URL, Published, Fetched, Via) and a blank line, then the release body with CRLF
turned into LF. Prints one line per file (match or the difference) and a summary; exits 1 on any difference.
Usage: python3 eval/verify_v2_sources.py   (needs network access to api.github.com)
"""
import json
import os
import re
import sys
import time
import urllib.request

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "v2-sources")


def fetch(url):
    for i in range(5):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "verify-v2-sources"})
            return json.load(urllib.request.urlopen(req, timeout=60))
        except Exception:
            time.sleep(2 * (i + 1))
    raise SystemExit("could not fetch " + url)


def main():
    bad = n = 0
    for dp, _, fs in sorted(os.walk(ROOT)):
        for fn in sorted(fs):
            path = os.path.join(dp, fn)
            text = open(path, encoding="utf-8", newline="").read()
            head, body = text.split("\n\n", 1)
            kv = dict(l.split(": ", 1) for l in head.split("\n") if ": " in l)
            m = re.match(r"https://github\.com/([^/]+/[^/]+)/releases/tag/(.+)$", kv.get("URL", ""))
            rel = os.path.relpath(path, ROOT).replace(os.sep, "/")
            if not m:
                print("DIFF %s: URL header not a GitHub release URL" % rel)
                bad += 1
                continue
            r = fetch("https://api.github.com/repos/%s/releases/tags/%s" % m.groups())
            want = (r.get("body") or "").replace("\r\n", "\n").replace("\r", "\n").rstrip("\n")
            problems = []
            if want != body.rstrip("\n"):
                problems.append("body differs")
            if r["published_at"][:10] != kv.get("Published"):
                problems.append("Published header %s, API %s" % (kv.get("Published"), r["published_at"][:10]))
            n += 1
            bad += bool(problems)
            print(("DIFF " if problems else "OK   ") + rel + (": " + "; ".join(problems) if problems else ""))
    print("%d files checked, %d differ" % (n, bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
