#!/usr/bin/env python3
"""
Generate sitemap.xml for Loiter Point from the filesystem.

Run from the repo root:

    python3 generate_sitemap.py            # write sitemap.xml
    python3 generate_sitemap.py --check    # exit 1 if sitemap.xml is stale, write nothing
    python3 generate_sitemap.py --diff     # show what would change, write nothing

The sitemap is DERIVED, never hand-edited. Add an article, re-run this, commit both.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape

SITE = "https://loiterpoint.com"
OUT = "sitemap.xml"

# Pages that exist but must stay out of the sitemap.
# account.html is an auth surface; site-map.html IS included (it links everything).
EXCLUDE_FILES = {
    "account.html",
    "404.html",
    "nav.js",
}

# Directories that are not category sections.
NOT_CATEGORIES = {"articles", "guides", ".git", ".github", "node_modules"}

# (priority, changefreq) by page kind.
RULES = {
    "home":     ("1.0", "weekly"),
    "category": ("0.8", "weekly"),
    "article":  ("0.9", "monthly"),
    "guide":    ("0.9", "monthly"),
    "deals":    ("0.7", "weekly"),
    "about":    ("0.5", "monthly"),
    "legal":    ("0.3", "yearly"),
    "sitemap":  ("0.5", "monthly"),
}

LEGAL = {"privacy-policy.html", "terms.html", "affiliate-disclosure.html"}


def existing_lastmods(repo: Path) -> dict[str, str]:
    """Map loc -> lastmod from the current sitemap.xml.

    These dates are EDITORIAL and are not recoverable from anywhere else: git
    dates reflect when the repo was populated (all ~2026-07-11), not when the
    content was written or revised. So existing values are always carried
    forward; only genuinely new URLs get a fresh date. Pass --reseed to
    override, which will flatten real publication history -- you almost
    certainly do not want that.
    """
    p = repo / OUT
    if not p.exists():
        return {}
    import re

    text = p.read_text(encoding="utf-8")
    out: dict[str, str] = {}
    for block in re.findall(r"<url>.*?</url>", text, re.S):
        loc = re.search(r"<loc>([^<]+)</loc>", block)
        mod = re.search(r"<lastmod>([^<]+)</lastmod>", block)
        if loc and mod:
            out[loc.group(1)] = mod.group(1)
    return out


def git_lastmod(path: Path, repo: Path) -> str:
    """Last commit date for a file, YYYY-MM-DD. Falls back to file mtime."""
    try:
        out = subprocess.run(
            ["git", "log", "-1", "--format=%cs", "--", str(path.relative_to(repo))],
            cwd=repo,
            capture_output=True,
            text=True,
            timeout=10,
        )
        stamp = out.stdout.strip()
        if stamp:
            return stamp
    except (subprocess.SubprocessError, OSError, ValueError):
        pass
    ts = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    return ts.date().isoformat()


def collect(repo: Path, reseed: bool = False) -> list[tuple[str, str, str, str]]:
    """Return (loc, lastmod, changefreq, priority) tuples in stable order."""
    urls: list[tuple[str, str, str, str]] = []
    known = {} if reseed else existing_lastmods(repo)

    def add(url_path: str, file: Path, kind: str) -> None:
        pri, cf = RULES[kind]
        loc = SITE + url_path
        lastmod = known.get(loc) or git_lastmod(file, repo)
        urls.append((loc, lastmod, cf, pri))

    # Homepage
    index = repo / "index.html"
    if index.exists():
        add("/", index, "home")

    # Top-level static pages
    for f in sorted(repo.glob("*.html")):
        if f.name in EXCLUDE_FILES or f.name == "index.html":
            continue
        if f.name in LEGAL:
            kind = "legal"
        elif f.name == "deals.html":
            kind = "deals"
        elif f.name == "site-map.html":
            kind = "sitemap"
        else:
            kind = "about"
        add(f"/{f.name}", f, kind)

    # Category sections: any top-level dir with an index.html
    for d in sorted(p for p in repo.iterdir() if p.is_dir()):
        if d.name.startswith(".") or d.name in NOT_CATEGORIES:
            continue
        idx = d / "index.html"
        if idx.exists():
            add(f"/{d.name}/", idx, "category")

    # Guides index + guide pages
    guides = repo / "guides"
    if (guides / "index.html").exists():
        add("/guides/", guides / "index.html", "guide")
    for f in sorted(guides.glob("*.html")) if guides.is_dir() else []:
        if f.name == "index.html" or f.name in EXCLUDE_FILES:
            continue
        add(f"/guides/{f.name}", f, "guide")

    # Articles
    articles = repo / "articles"
    for f in sorted(articles.glob("*.html")) if articles.is_dir() else []:
        if f.name in EXCLUDE_FILES:
            continue
        add(f"/articles/{f.name}", f, "article")

    return urls


def render(urls: list[tuple[str, str, str, str]]) -> str:
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for loc, lastmod, cf, pri in urls:
        lines.append(
            f"<url><loc>{escape(loc)}</loc><lastmod>{lastmod}</lastmod>"
            f"<changefreq>{cf}</changefreq><priority>{pri}</priority></url>"
        )
    lines.append("</urlset>")
    return "\n".join(lines) + "\n"


def existing_locs(repo: Path) -> set[str]:
    p = repo / OUT
    if not p.exists():
        return set()
    import re

    return set(re.findall(r"<loc>([^<]+)</loc>", p.read_text(encoding="utf-8")))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="exit 1 if stale, write nothing")
    ap.add_argument("--diff", action="store_true", help="show changes, write nothing")
    ap.add_argument("--repo", default=".", help="repo root (default: cwd)")
    ap.add_argument(
        "--reseed",
        action="store_true",
        help="DESTRUCTIVE: recompute every lastmod from git, discarding editorial dates",
    )
    args = ap.parse_args()

    repo = Path(args.repo).resolve()
    if not (repo / "index.html").exists():
        print(f"error: {repo} does not look like the site root (no index.html)", file=sys.stderr)
        return 2

    urls = collect(repo, reseed=args.reseed)
    new_locs = {u[0] for u in urls}
    old_locs = existing_locs(repo)

    added = sorted(new_locs - old_locs)
    removed = sorted(old_locs - new_locs)

    # Guard: carried-forward dates must survive untouched.
    if not args.reseed:
        prior = existing_lastmods(repo)
        changed = [
            (loc, prior[loc], lm)
            for loc, lm, _, _ in urls
            if loc in prior and prior[loc] != lm
        ]
        if changed:
            print("error: refusing to rewrite existing lastmod values:", file=sys.stderr)
            for loc, was, now in changed[:10]:
                print(f"  {loc}: {was} -> {now}", file=sys.stderr)
            return 3

    if args.check or args.diff:
        for u in added:
            print(f"+ {u}")
        for u in removed:
            print(f"- {u}")
        if not added and not removed:
            print(f"sitemap.xml is current ({len(urls)} URLs)")
            return 0
        print(f"\n{len(added)} to add, {len(removed)} to remove, {len(urls)} URLs total")
        return 1 if args.check else 0

    (repo / OUT).write_text(render(urls), encoding="utf-8")
    print(f"wrote {OUT}: {len(urls)} URLs ({len(added)} added, {len(removed)} removed)")
    for u in added:
        print(f"  + {u}")
    for u in removed:
        print(f"  - {u}")
    print(f"\nGenerated {date.today().isoformat()}. Commit sitemap.xml to main.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
