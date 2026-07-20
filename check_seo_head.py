#!/usr/bin/env python3
# Verify every page ships the SEO head block search engines need.
#
# An article can be generated, committed, and listed in sitemap.xml while
# missing its canonical link, Open Graph tags, or JSON-LD. Nothing about
# the page looks broken to a human. It just quietly loses rich results
# and splits duplicate-content signals. That is the failure this catches.
#
# Checks, run from the repo root
#   1. exactly one application/ld+json block that parses as valid JSON
#   2. a canonical link inside head
#   3. at least 4 og: meta tags
#   4. articles/*.html carry more than 1000 chars of body text
#
# Exit 0 = clean. Exit 1 = at least one page needs fixing.

import json
import re
import sys
from pathlib import Path

MIN_OG = 4
MIN_BODY = 1000

LD_RE = re.compile(r'<script[^>]*application/ld\+json[^>]*>(.*?)</script>', re.S | re.I)
CANON_RE = re.compile(r'<link[^>]*rel=.?canonical', re.I)
OG_RE = re.compile(r'<meta[^>]*property=.?og:', re.I)
HEAD_RE = re.compile(r'<head\b.*?</head>', re.S | re.I)
BODY_RE = re.compile(r'<body\b.*?</body>', re.S | re.I)
TAG_RE = re.compile(r'<(script|style)\b.*?</\1>|<[^>]+>', re.S | re.I)


def body_text(src):
    match = BODY_RE.search(src)
    raw = match.group(0) if match else src
    return re.sub(r'\s+', ' ', TAG_RE.sub(' ', raw)).strip()


def problems(path, src):
    out = []
    head_match = HEAD_RE.search(src)
    head = head_match.group(0) if head_match else ''
    blocks = LD_RE.findall(src)
    if len(blocks) != 1:
        out.append('%d JSON-LD blocks, want exactly 1' % len(blocks))
    for block in blocks:
        try:
            json.loads(block)
        except ValueError as err:
            out.append('JSON-LD does not parse: %s' % err)
    if not CANON_RE.search(head):
        out.append('no canonical link in head')
    found_og = len(OG_RE.findall(head))
    if found_og < MIN_OG:
        out.append('%d og: tags, want at least %d' % (found_og, MIN_OG))
    if path.parent.name == 'articles':
        size = len(body_text(src))
        if size < MIN_BODY:
            out.append('body text %d chars, want more than %d' % (size, MIN_BODY))
    return out


def main():
    repo = Path(__file__).resolve().parent
    pages = sorted(p for p in repo.rglob('*.html') if '.git' not in p.parts)
    broken = 0
    for page in pages:
        src = page.read_text(encoding='utf-8', errors='replace')
        found = problems(page, src)
        if found:
            broken += 1
            print('FAIL %s' % page.relative_to(repo))
            for item in found:
                print('       - %s' % item)
    print('checked %d pages, %d need fixing' % (len(pages), broken))
    return 1 if broken else 0


if __name__ == '__main__':
    sys.exit(main())
  
