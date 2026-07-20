#!/usr/bin/env python3
"""
Verify every article on Loiter Point is reachable by a human, not just by a crawler.

An article can be present in the repo, and even in sitemap.xml, while being
invisible to anyone browsing the site. That is the failure this catches.

Checks, run from the repo root:

  1. every articles/*.html has a card on at least one category page
  2. every articles/*.html has an entry in site-map.html
  3. every article link on a category page or site-map.html resolves to a real file
  4. each homepage category tile's count equals that category page's real card count
  5. each homepage category tile links to a category page that exists

    python3 check_surfaced.py           # report and exit 1 on any failure
    python3 check_surfaced.py --quiet   # exit code only

Stdlib only -- no pip install in CI.
"""

from __future__ import annotations

import argparse
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

NOT_CATEGORIES = {"articles", "guides", ".git", ".github", "node_modules"}

# site-map.html uses relative hrefs ("articles/x.html"); category pages use
# absolute ("/articles/x.html"). The lookbehind accepts both without also
# matching something like "myarticles/x.html".
ARTICLE_HREF = re.compile(r"(?<![A-Za-z0-9._-])articles/([A-Za-z0-9._-]+\.html)")


class CardParser(HTMLParser):
    """Collect article hrefs grouped by the card element that contains them.

    Tracks nesting depth so a card ends at its own closing tag rather than the
    first </div> encountered, which would truncate every card with children.
    """

    def __init__(self, card_class: str) -> None:
        super().__init__(convert_charrefs=True)
        self.card_class = card_class
        self.cards: list[list[str]] = []
        self._depth = 0
        self._open: list[str] | None = None
        self._tagstack: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = dict(attrs)
        classes = (a.get("class") or "").split()
        if self._open is None and self.card_class in classes:
            self._open = []
            self._depth = 0
            self._tagstack = [tag]
        elif self._open is not None:
            self._tagstack.append(tag)
        if self._open is not None and tag == "a":
            m = ARTICLE_HREF.search(a.get("href") or "")
            if m:
                self._open.append(m.group(1))

    def handle_endtag(self, tag: str) -> None:
        if self._open is None:
            return
        if self._tagstack:
            self._tagstack.pop()
        if not self._tagstack:
            self.cards.append(self._open)
            self._open = None


class TileParser(HTMLParser):
    """Homepage category tiles: (href, count) from .cat-card / .cat-count."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tiles: list[tuple[str, str]] = []
        self._href: str | None = None
        self._in_count = False
        self._buf = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = dict(attrs)
        classes = (a.get("class") or "").split()
        if "cat-card" in classes:
            self._href = a.get("href") or ""
            self._buf = ""
        if self._href is not None and "cat-count" in classes:
            self._in_count = True
            self._buf = ""

    def handle_data(self, data: str) -> None:
        if self._in_count:
            self._buf += data

    def handle_endtag(self, tag: str) -> None:
        if self._in_count:
            self._in_count = False
            if self._href is not None:
                self.tiles.append((self._href, self._buf.strip()))
                self._href = None


def cards_on(path: Path, card_class: str = "article-card") -> list[list[str]]:
    p = CardParser(card_class)
    p.feed(path.read_text(encoding="utf-8"))
    return p.cards


def category_dirs(repo: Path) -> list[Path]:
    return sorted(
        d
        for d in repo.iterdir()
        if d.is_dir()
        and not d.name.startswith(".")
        and d.name not in NOT_CATEGORIES
        and (d / "index.html").exists()
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--repo", default=".")
    args = ap.parse_args()
    repo = Path(args.repo).resolve()

    articles_dir = repo / "articles"
    if not articles_dir.is_dir():
        print("error: no articles/ directory", file=sys.stderr)
        return 2

    articles = {f.name for f in articles_dir.glob("*.html")}
    failures: list[str] = []
    say = (lambda *a: None) if args.quiet else print

    # --- category pages
    surfaced: set[str] = set()
    real_counts: dict[str, int] = {}
    for d in category_dirs(repo):
        cards = cards_on(d / "index.html")
        real_counts[d.name] = len(cards)
        # a card links the same slug twice (title + "read more"); dedupe per page
        for slug in sorted({s for card in cards for s in card}):
            surfaced.add(slug)
            if slug not in articles:
                failures.append(f"/{d.name}/ links to missing article: {slug}")

    for slug in sorted(articles - surfaced):
        failures.append(f"article has no card on any category page: {slug}")

    # --- site-map.html
    smap = repo / "site-map.html"
    if smap.exists():
        listed = set(ARTICLE_HREF.findall(smap.read_text(encoding="utf-8")))
        for slug in sorted(articles - listed):
            failures.append(f"article missing from site-map.html: {slug}")
        for slug in sorted(listed - articles):
            failures.append(f"site-map.html links to missing article: {slug}")
    else:
        failures.append("site-map.html not found")

    # --- homepage tiles
    index = repo / "index.html"
    if index.exists():
        tp = TileParser()
        tp.feed(index.read_text(encoding="utf-8"))
        for href, count_text in tp.tiles:
            name = href.strip("/")
            if name not in real_counts:
                failures.append(f"homepage tile links to missing category page: {href}")
                continue
            m = re.search(r"\d+", count_text)
            if not m:
                failures.append(f"homepage tile {href} has unreadable count: {count_text!r}")
                continue
            shown, actual = int(m.group()), real_counts[name]
            if shown != actual:
                failures.append(
                    f"homepage tile {href} says {shown} but /{name}/ has {actual} cards"
                )
    else:
        failures.append("index.html not found")

    if failures:
        say(f"{len(failures)} problem(s):\n")
        for f in failures:
            say(f"  {f}")
        say("")
        say('Fix:  add <meta name="lp:category" content="<slug>"> to any new '
            "article, then run  python3 surface_articles.py")
        return 1

    say(
        f"all {len(articles)} articles surfaced "
        f"({len(real_counts)} category pages, counts match, no dead links)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
