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
  6. guides/index.html ships the static guide list in its markup, and that list
     still agrees with the GUIDES array in nav.js (href, label, picks, price)

    python3 check_surfaced.py           # report and exit 1 on any failure
    python3 check_surfaced.py --quiet   # exit code only

Stdlib only -- no pip install in CI.
"""

from __future__ import annotations

import argparse
import re
import sys
from html import unescape
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


# ── The static guide list on /guides/
#
# /guides/ builds its cards in the browser from the GUIDES array in nav.js.
# surface_articles.py also writes that list into the markup between the
# LP:GUIDES-FALLBACK markers, so crawlers, link unfurlers and anyone whose
# nav.js request fails still get the guides. That copy can drift the moment
# someone edits GUIDES without re-running surface_articles.py — which is what
# this check is for. It compares meaning (href, label, chip text), not markup,
# so the generator's HTML can be restyled without breaking the check.
FB_BLOCK = re.compile(r"<!-- LP:GUIDES-FALLBACK -->(.*?)<!-- /LP:GUIDES-FALLBACK -->",
                      re.S)


def guides_sort_key(label: str) -> str:
    """Match gkey() in nav.js and guides_sort_key() in surface_articles.py."""
    return re.sub(r"^(the |a |an )", "", label.lower())


def nav_guides(nav: Path) -> list[tuple[str, str, list[str]]] | None:
    """(href, label, chips) per GUIDES entry, in the order the page shows them."""
    m = re.search(r"  var GUIDES = \[\n(.*?)\n  \];",
                  nav.read_text(encoding="utf-8"), flags=re.S)
    if not m:
        return None

    out: list[tuple[str, str, list[str]]] = []
    for line in m.group(1).split("\n"):
        href = re.search(r'href: "([^"]+)"', line)
        if not href:
            continue
        label = re.search(r'label: "([^"]*)"', line)
        picks = re.search(r"picks: (\d+)", line)
        price = re.search(r'price: "([^"]*)"', line)

        chips: list[str] = []
        if picks and int(picks.group(1)):
            n = int(picks.group(1))
            chips.append(f"{n} pick" if n == 1 else f"{n} picks")
        if price and price.group(1):
            chips.append(price.group(1))
        if not chips:
            chips = ["Buyer's guide"]
        out.append((href.group(1), label.group(1) if label else "", chips))

    out.sort(key=lambda g: guides_sort_key(g[1]))
    return out


def static_guides(page: Path) -> list[tuple[str, str, list[str]]] | None:
    """The same triples read back out of guides/index.html, or None if unmarked."""
    m = FB_BLOCK.search(page.read_text(encoding="utf-8"))
    if not m:
        return None

    def text(s: str) -> str:
        return unescape(re.sub(r"<[^>]+>", "", s)).strip()

    out: list[tuple[str, str, list[str]]] = []
    for card in re.findall(r'<a class="lp-gfb-card".*?</a>', m.group(1), flags=re.S):
        href = re.search(r'href="([^"]+)"', card)
        title = re.search(r'class="lp-gfb-title">(.*?)</span>', card, flags=re.S)
        chips = re.findall(r'class="lp-gfb-chip[^"]*">(.*?)</span>', card, flags=re.S)
        out.append((unescape(href.group(1)) if href else "",
                    text(title.group(1)) if title else "",
                    [text(c) for c in chips]))
    return out


def check_static_guides(repo: Path) -> list[str]:
    nav, page = repo / "nav.js", repo / "guides" / "index.html"
    if not page.exists():
        return []
    if not nav.exists():
        return ["nav.js not found — cannot check the static guide list"]

    want = nav_guides(nav)
    if want is None:
        return ["nav.js has no GUIDES array — cannot check the static guide list"]

    got = static_guides(page)
    if got is None:
        return ["guides/index.html has no LP:GUIDES-FALLBACK markers, so its HTML "
                "ships no guide links — restore the markers and run surface_articles.py"]

    failures: list[str] = []
    for href, _, _ in want:
        if not (repo / href.lstrip("/")).exists():
            failures.append(f"GUIDES lists a guide that is missing on disk: {href}")

    if got != want:
        w, g = {x[0] for x in want}, {x[0] for x in got}
        for href in sorted(w - g):
            failures.append(f"guides/index.html static list is missing {href}")
        for href in sorted(g - w):
            failures.append(f"guides/index.html static list has a stale entry: {href}")
        for a, b in zip(want, got):
            if a != b and a[0] == b[0]:
                failures.append(
                    f"guides/index.html static list is out of date for {a[0]}: "
                    f"shows {b[1]!r} {b[2]} — nav.js says {a[1]!r} {a[2]}")
        if not failures:
            failures.append("guides/index.html static list no longer matches nav.js "
                            "GUIDES (order differs)")

    return failures


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

    # --- the static guide list on /guides/
    failures.extend(check_static_guides(repo))

    if failures:
        say(f"{len(failures)} problem(s):\n")
        for f in failures:
            say(f"  {f}")
        say("")
        say('Fix:  add <meta name="lp:category" content="<slug>"> to any new '
            "article, then run  python3 surface_articles.py")
        say("      (surface_articles.py also rebuilds the static guide list "
            "on /guides/)")
        return 1

    say(
        f"all {len(articles)} articles surfaced "
        f"({len(real_counts)} category pages, counts match, no dead links)"
    )
    listed = static_guides(repo / "guides" / "index.html")
    if listed:
        say(f"{len(listed)} buyer guides linked from /guides/ in the HTML itself")
    return 0


if __name__ == "__main__":
    sys.exit(main())
