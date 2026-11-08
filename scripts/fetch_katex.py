# -*- coding: utf-8 -*-
"""Download KaTeX into static/vendor/katex (offline / no-CDN deployments).

Usage:  python scripts/fetch_katex.py
Then set MATH14_LOCAL_KATEX=1 before starting the app.
"""
import os
import re
import sys
import urllib.request

VERSION = "0.16.11"
BASE = "https://cdn.jsdelivr.net/npm/katex@%s/dist/" % VERSION
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "static", "vendor", "katex")


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "math14-fetch-katex"})
    with urllib.request.urlopen(req, timeout=30) as res:
        return res.read()


def main():
    os.makedirs(os.path.join(OUT, "fonts"), exist_ok=True)
    css = fetch(BASE + "katex.min.css").decode("utf-8")
    js = fetch(BASE + "katex.min.js")
    with open(os.path.join(OUT, "katex.min.js"), "wb") as fh:
        fh.write(js)

    urls = sorted(set(re.findall(r"url\(([^)]+)\)", css)))
    saved = 0
    for raw in urls:
        name = raw.strip("'\"")
        if name.startswith("data:"):
            continue
        target = os.path.join(OUT, "fonts", os.path.basename(name))
        try:
            data = fetch(BASE + name)
        except Exception as exc:  # noqa: BLE001
            print("skip %s (%s)" % (name, exc))
            continue
        with open(target, "wb") as fh:
            fh.write(data)
        saved += 1
        css = css.replace(raw, "fonts/%s" % os.path.basename(name))

    with open(os.path.join(OUT, "katex.min.css"), "w", encoding="utf-8") as fh:
        fh.write(css)

    print("KaTeX %s -> %s (%d fonts)" % (VERSION, OUT, saved))
    print("set MATH14_LOCAL_KATEX=1 to use the local copy")


if __name__ == "__main__":
    sys.exit(main())
