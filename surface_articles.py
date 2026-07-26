#!/usr/bin/env python3
"""
Surface every article on Loiter Point — the inverse of check_surfaced.py.

check_surfaced.py *reports* what is unreachable. This *fixes* it: for each
articles/*.html it makes sure there is (1) a card on the correct category page,
(2) an entry in site-map.html, and then recomputes every homepage tile count and
site-map branch count from the real card counts so they can never lie.

It also keeps /guides/ honest in the markup itself: the picks/price fields in
nav.js's GUIDES array are re-derived from each guide page, and that same array
is written into guides/index.html as a static list, so the hub ships real links
rather than an empty div waiting on JavaScript.

Same idea for the footer, on every page: nav.js's FOOTER object is written into
each page's markup between LP:FOOTER-FALLBACK markers, replacing whatever
hand-written footer was there. nav.js still removes it and renders its own at
load, so nothing changes in a browser — but the HTML now carries one footer,
one disclosure and one copyright year sitewide instead of twenty drifting
variants.

Run it after adding articles (any agent, any batch):

    python3 surface_articles.py            # surface + fix counts, then regen sitemap
    python3 surface_articles.py --dry-run  # show what it WOULD do, change nothing
    python3 surface_articles.py --skip-sitemap   # don't shell out to generate_sitemap.py

Edits are surgical (per AGENTS.md): it inserts the specific card/leaf strings it
needs and rewrites only the count numbers — it never regenerates a page wholesale.

How each article's category is decided, in order:
    1. <meta name="lp:category" content="streaming"> in the article  (preferred)
    2. where the article is already carded (keeps existing placement stable)
    3. a keyword guess from the slug (logged as a guess — verify it)
    4. otherwise: reported as UNCATEGORIZED and the script exits non-zero, so a
       new article is never silently dropped. Add the meta tag (or a keyword) and
       re-run.

Stdlib only — no pip install, safe to call from CI.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from html import escape as hesc
from html.parser import HTMLParser
from pathlib import Path

# ── Category config — the 12 real category pages. `label` matches the homepage
# tile name, `icon`/`meta` are used when building a new card. Edit here to add a
# category (also create its /<slug>/index.html and homepage tile).
CATEGORIES: dict[str, dict[str, str]] = {
    "drones":      {"label": "Drones & Aerial",            "icon": "🚁", "meta": "Drones"},
    "audio":       {"label": "Headphones & Audio",         "icon": "🎧", "meta": "Audio"},
    "home-tech":   {"label": "Home & Cleaning",            "icon": "🏠", "meta": "Home Tech"},
    "automotive":  {"label": "Automotive",                 "icon": "🚗", "meta": "Automotive"},
    "computing":   {"label": "Computing & Desk",           "icon": "⌨️", "meta": "Computing"},
    "mobile-tech": {"label": "Tablets, Wearables & Media", "icon": "📱", "meta": "Mobile Tech"},
    "kitchen":     {"label": "Kitchen",                    "icon": "🍳", "meta": "Kitchen"},
    "smart-home":  {"label": "Smart Home",                 "icon": "💡", "meta": "Smart Home"},
    "streaming":   {"label": "TVs & Streaming",            "icon": "📺", "meta": "Streaming"},
    "power":       {"label": "Power & Charging",           "icon": "🔋", "meta": "Power & Charging"},
    "cameras":     {"label": "Cameras",                    "icon": "📸", "meta": "Cameras"},
    "networking":  {"label": "Networking",                 "icon": "📶", "meta": "Networking"},
    "smartphones": {"label": "Smartphones",                "icon": "📲", "meta": "Smartphones"},
    "tools":       {"label": "Tools & DIY",                "icon": "🔧", "meta": "Tools"},
    "outdoors":    {"label": "Outdoors",                   "icon": "🏕️", "meta": "Outdoors"},
}


def cat_meta(cat: str) -> dict:
    """Return display config for a category, synthesizing a sane default for any
    category dir not explicitly listed in CATEGORIES (keeps this tool
    category-agnostic so brand-new category pages are handled automatically)."""
    c = CATEGORIES.get(cat)
    if c:
        return c
    nice = cat.replace("-", " ").title()
    return {"label": nice, "icon": "📄", "meta": nice}

# ── Keyword guesser (fallback only). First matching (substring-in-slug) wins, so
# order matters: put the more specific patterns first. This is a safety net for
# articles with no lp:category meta and no existing card — always verify a guess.
KEYWORD_RULES: list[tuple[tuple[str, ...], str]] = [
    (("smart-speaker", "smart-bulb", "smart-plug", "smart-lock", "smart-thermostat",
      "video-doorbell", "baby-monitor"), "smart-home"),
    (("security-camera", "action-camera", "mirrorless", "dslr"), "cameras"),
    (("dash-cam", "car-vacuum", "electric-scooter"), "automotive"),
    (("power-bank", "power-station", "solar-charger", "wireless-charger",
      "ups-battery"), "power"),
    (("apple-tv", "roku", "streaming-device", "oled-tv", "tvs-under", "tvs-for",
      "projector", "-tv-", "google-tv", "fire-tv"), "streaming"),
    (("nas", "wifi", "wi-fi", "router", "mesh", "ethernet", "network"), "networking"),
    (("vacuum", "air-purifier", "humidifier", "dehumidifier", "toothbrush",
      "tower-fan", "air-conditioner"), "home-tech"),
    (("espresso", "coffee", "air-fryer", "sous-vide", "kitchen"), "kitchen"),
    (("headphone", "earbud", "open-ear", "noise-canceling", "soundbar",
      "bluetooth-speaker", "sony-wh"), "audio"),
    (("smartphone", "iphone", "galaxy-s", "pixel-", "-phones"), "smartphones"),
    (("tablet", "smartwatch", "fitness-tracker", "sleep-tracker",
      "ereader", "e-reader", "bluetooth-tracker", "handheld-gaming", "vr-headset"), "mobile-tech"),
    (("drone", "dji", "fpv", "faa", "nd-filter", "mavic", "betafpv", "autel"), "drones"),
    (("laptop", "monitor", "keyboard", "mouse", "mice", "ssd", "usb-c-hub", "mini-pc",
      "chromebook", "3d-printer", "printer", "gaming-headset", "webcam", "microphone",
      "nas-for-home", "graphics-card", "desktop"), "computing"),
]

ARTICLE_HREF = re.compile(r"(?<![A-Za-z0-9._-])/?articles/([A-Za-z0-9._-]+\.html)")
LP_CATEGORY = re.compile(r'<meta\s+name=["\']lp:category["\']\s+content=["\']([a-z-]+)["\']', re.I)
TITLE_RE = re.compile(r"<title>(.*?)</title>", re.I | re.S)
DESC_RE = re.compile(r'<meta\s+name=["\']description["\']\s+content=["\'](.*?)["\']', re.I | re.S)

NOT_CATEGORIES = {"articles", "guides", ".git", ".github", "node_modules"}


class CardParser(HTMLParser):
    """Collect article hrefs grouped by the .article-card that contains them
    (same logic as check_surfaced.py, so the two agree on what a 'card' is)."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.cards: list[list[str]] = []
        self._open: list[str] | None = None
        self._stack: list[str] = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        classes = (a.get("class") or "").split()
        if self._open is None and "article-card" in classes:
            self._open = []
            self._stack = [tag]
        elif self._open is not None:
            self._stack.append(tag)
        if self._open is not None and tag == "a":
            m = ARTICLE_HREF.search(a.get("href") or "")
            if m:
                self._open.append(m.group(1))

    def handle_endtag(self, tag):
        if self._open is None:
            return
        if self._stack:
            self._stack.pop()
        if not self._stack:
            self.cards.append(self._open)
            self._open = None


def cards_on(path: Path) -> list[list[str]]:
    p = CardParser()
    p.feed(path.read_text(encoding="utf-8"))
    return p.cards


def category_dirs(repo: Path) -> list[str]:
    out = []
    for d in sorted(repo.iterdir()):
        if (d.is_dir() and not d.name.startswith(".")
                and d.name not in NOT_CATEGORIES and (d / "index.html").exists()):
            out.append(d.name)
    return out


def article_meta(path: Path) -> tuple[str, str, str | None]:
    """Return (title, description, lp_category|None) from an article file."""
    html = path.read_text(encoding="utf-8")
    lp = LP_CATEGORY.search(html)
    tm = TITLE_RE.search(html)
    dm = DESC_RE.search(html)
    title = (tm.group(1).strip() if tm else "")
    # strip the site suffix ("Foo — Loiter Point" / "Foo | Loiter Point")
    title = re.split(r"\s+[—|]\s+Loiter\s*Point", title)[0].strip()
    desc = (dm.group(1).strip() if dm else "")
    return title, desc, (lp.group(1) if lp else None)


def title_from_slug(slug: str) -> str:
    return slug.replace("-", " ").title()


def guess_category(slug: str) -> str | None:
    for keys, cat in KEYWORD_RULES:
        if any(k in slug for k in keys):
            return cat
    return None


def featured_close_index(html: str) -> int | None:
    """Index of the </div> that closes the first `.featured` grid, by depth."""
    m = re.search(r'<div class="featured"', html)
    if not m:
        return None
    start = m.start()
    depth = 0
    for tok in re.finditer(r"<div\b|</div>", html[start:]):
        if tok.group() == "</div>":
            depth -= 1
            if depth == 0:
                return start + tok.start()
        else:
            depth += 1
    return None


def build_card(slug: str, title: str, desc: str, cat: str) -> str:
    c = cat_meta(cat)
    title = title or title_from_slug(slug)
    if not desc:
        desc = f"Our evidence-first pick roundup: {title}."
    return (
        '<div class="article-card">\n'
        f'<div class="card-thumb">{c["icon"]}\n'
        '<span class="card-badge badge-guide">Buyer Guide</span>\n'
        '</div>\n'
        '<div class="card-body">\n'
        f'<div class="card-meta">{c["meta"]} · Guide</div>\n'
        f'<div class="card-title"><a href="/articles/{slug}.html">{title}</a></div>\n'
        f'<div class="card-excerpt">{desc}</div>\n'
        '<div class="card-footer">\n'
        f'<a href="/articles/{slug}.html" class="read-more">Read guide →</a>\n'
        '</div>\n'
        '</div>\n'
        '</div>\n'
    )


def add_card(repo: Path, cat: str, card_html: str, dry: bool) -> bool:
    path = repo / cat / "index.html"
    html = path.read_text(encoding="utf-8")
    idx = featured_close_index(html)
    if idx is None:
        print(f"  ! {cat}/index.html has no .featured grid — cannot insert card", file=sys.stderr)
        return False
    if not dry:
        path.write_text(html[:idx] + card_html + html[idx:], encoding="utf-8")
    return True


# ── site-map.html ────────────────────────────────────────────────────────────
def sitemap_leaf(slug: str, title: str) -> str:
    return (f'          <li><a href="/articles/{slug}.html">{title}</a>'
            f'<span class="tag">guide</span></li>\n')


def leaf_sort_key(title: str) -> str:
    """Sort key for site-map leaves: case-insensitive title, ignoring a leading
    article word ("The"/"A"/"An") so "The Best…" sorts with the rest. Must match
    the ordering the site-map was cleaned to, so inserts land in the right spot."""
    t = title.replace("&amp;", "&").strip().lower()
    return re.sub(r"^(the |a |an )", "", t)


def add_sitemap_leaf(repo: Path, cat: str, slug: str, title: str, dry: bool) -> bool:
    smap = repo / "site-map.html"
    html = smap.read_text(encoding="utf-8")
    # find the branch whose head links /<cat>/, then its <ul class="leaves"> … </ul>
    head = re.search(r'<a href="/' + re.escape(cat) + r'/">', html)
    if not head:
        print(f"  ! site-map.html has no branch for /{cat}/ — cannot add leaf", file=sys.stderr)
        return False
    ul = re.search(r'<ul class="leaves">', html[head.end():])
    if not ul:
        return False
    ul_start = head.end() + ul.end()
    close = html.find("</ul>", ul_start)
    if close == -1:
        return False

    # Insert in alphabetical position (before the first existing leaf whose title
    # sorts after the new one); fall back to end-of-list if it sorts last. Keeps
    # each branch A–Z instead of appending new leaves and re-introducing drift.
    block = html[ul_start:close]
    new_key = leaf_sort_key(title)
    insert_at = close
    for m in re.finditer(r"[^\n]*<li>.*?</li>[^\n]*\n?", block, flags=re.S):
        tm = re.search(r"<a [^>]*>(.*?)</a>", m.group(0), flags=re.S)
        if tm and new_key < leaf_sort_key(tm.group(1)):
            insert_at = ul_start + m.start()
            break

    if not dry:
        smap.write_text(html[:insert_at] + sitemap_leaf(slug, title) + html[insert_at:],
                        encoding="utf-8")
    return True


def recount_sitemap_branches(repo: Path, dry: bool) -> int:
    """Set each site-map branch-count to the number of leaves in that branch."""
    smap = repo / "site-map.html"
    html = smap.read_text(encoding="utf-8")
    changed = 0

    def fix(m: re.Match) -> str:
        nonlocal changed
        block = m.group(0)
        n = len(re.findall(r"<li>", block))
        new = re.sub(r'(<span class="branch-count">)\d+(</span>)', rf"\g<1>{n}\g<2>", block, count=1)
        if new != block:
            changed += 1
        return new

    # a branch spans from its head through its </ul>
    html2 = re.sub(r'<div class="branch-head">.*?</ul>', fix, html, flags=re.S)
    if changed and not dry:
        smap.write_text(html2, encoding="utf-8")
    return changed


# ── homepage tiles ───────────────────────────────────────────────────────────
def recount_homepage(repo: Path, real_counts: dict[str, int], dry: bool) -> list[str]:
    # The homepage AND the buyer-guides page (/guides/) use the same
    # .cat-card / .cat-count tiles, so recompute both from the real category
    # counts — neither can then show a stale, hand-typed number.
    fixes: list[str] = []

    # each tile: <a href="/cat/" class="cat-card"> … <div class="cat-count">N articles</div>
    tile = re.compile(
        r'(<a href="/([a-z-]+)/" class="cat-card">.*?<div class="cat-count">)(\d+)( articles?</div>)',
        re.S)

    for rel in ("index.html", "guides/index.html"):
        page = repo / rel
        if not page.exists():
            continue
        html = page.read_text(encoding="utf-8")
        page_fixes: list[str] = []

        def fix(m: re.Match) -> str:
            pre, cat, shown, post = m.group(1), m.group(2), int(m.group(3)), m.group(4)
            actual = real_counts.get(cat)
            if actual is not None and actual != shown:
                page_fixes.append(f"{rel} {cat}: {shown} → {actual}")
                return f"{pre}{actual}{post}"
            return m.group(0)

        html2 = tile.sub(fix, html)
        if page_fixes and not dry:
            page.write_text(html2, encoding="utf-8")
        fixes.extend(page_fixes)

    return fixes


# ── buyer-guide cards (pick count + price range) ─────────────────────────────
def guide_meta(path: Path) -> tuple[int, str]:
    """Read one /guides/best-*.html and derive its pick count and price range.

    A "pick" is a <div class="card"> block; each carries a <span class="price">.
    Prices are free text (~$130 · 5.5 qt, ~$199–$499), so we pull every $ figure
    out and take the min/max. A guide whose .price tags hold qualifiers rather
    than figures (home-cleaning does this) yields "" and simply shows no price
    chip — that's a fallback, not an error.
    """
    html = path.read_text(encoding="utf-8")
    body = re.sub(r"<style.*?</style>", "", html, flags=re.S)
    body = re.sub(r"<script.*?</script>", "", body, flags=re.S)

    picks = len(re.findall(r'class="card"', body))

    nums: list[int] = []
    for raw in re.findall(r'class="price"[^>]*>(.*?)</', body, flags=re.S):
        for v in re.findall(r"\$([\d,]+)", re.sub(r"<[^>]+>", "", raw)):
            nums.append(int(v.replace(",", "")))

    if not nums:
        return picks, ""
    lo, hi = min(nums), max(nums)
    if lo == hi:
        return picks, f"${lo:,}"
    return picks, f"${lo:,}–${hi:,}"


def resync_guide_cards(repo: Path, dry: bool) -> list[str]:
    """Rewrite the derived picks/price fields in nav.js's GUIDES array.

    GUIDES is the single source of truth for the /guides/ cards, the site map's
    Buyer Guides branch and the home hero count. href/label/icon/blurb are
    hand-maintained; picks and price are derived here so the cards can never
    advertise a stale number the way the category tiles used to.
    """
    fixes: list[str] = []
    nav = repo / "nav.js"
    if not nav.exists():
        return fixes

    src = nav.read_text(encoding="utf-8")
    m = re.search(r"(  var GUIDES = \[\n)(.*?)(\n  \];)", src, flags=re.S)
    if not m:
        print("  ! nav.js has no GUIDES array — cannot resync guide cards",
              file=sys.stderr)
        return fixes

    out_lines: list[str] = []
    for line in m.group(2).split("\n"):
        href = re.search(r'href: "([^"]+)"', line)
        if not href:
            out_lines.append(line)
            continue
        page = repo / href.group(1).lstrip("/")
        if not page.exists():
            print(f"  ! {href.group(1)} listed in GUIDES but missing on disk",
                  file=sys.stderr)
            out_lines.append(line)
            continue

        picks, price = guide_meta(page)
        name = page.name

        shown = re.search(r"picks: (\d+)", line)
        if shown is None:
            print(f"  ! {name}: GUIDES entry has no picks field — skipping",
                  file=sys.stderr)
            out_lines.append(line)
            continue
        if int(shown.group(1)) != picks:
            fixes.append(f"nav.js {name}: {shown.group(1)} → {picks} picks")
            line = re.sub(r"picks: \d+", f"picks: {picks}", line)

        shown_p = re.search(r'price: "([^"]*)"', line)
        if shown_p is None:
            print(f"  ! {name}: GUIDES entry has no price field — skipping",
                  file=sys.stderr)
        elif shown_p.group(1) != price:
            fixes.append(
                f"nav.js {name}: price {shown_p.group(1) or '(none)'} → {price or '(none)'}")
            line = re.sub(r'price: "[^"]*"', f'price: "{price}"', line)

        out_lines.append(line)

    if fixes and not dry:
        nav.write_text(
            src[:m.start(2)] + "\n".join(out_lines) + src[m.end(2):],
            encoding="utf-8")

    return fixes


# ── Static guide list on /guides/
#
# /guides/ is the site's highest-value hub, and until now its HTML shipped an
# empty <div id="lpGuidesGrid"> — every link on it was created in the browser.
# Google runs JS, but link unfurlers, reader modes and most other crawlers do
# not, and neither does a visitor whose nav.js request fails. So we write the
# same list into the markup, between these markers, from the same GUIDES array
# nav.js reads. nav.js sets grid.innerHTML on load, which replaces this block
# outright — there is never a moment with two copies in the DOM.
FB_START = "<!-- LP:GUIDES-FALLBACK -->"
FB_END = "<!-- /LP:GUIDES-FALLBACK -->"

FB_NOTE = ("<!-- Generated by surface_articles.py from the GUIDES array in nav.js.\n"
           "     Do not hand-edit: nav.js replaces this block on load, and\n"
           "     check_surfaced.py fails the commit if it drifts. -->")


def guides_sort_key(label: str) -> str:
    """Match the gkey() sort inside nav.js so the static and live order agree."""
    return re.sub(r"^(the |a |an )", "", label.lower())


def parse_guides(nav: Path) -> list[dict[str, str]]:
    """Read the GUIDES entries out of nav.js as plain dicts.

    Deliberately regex, not a JS parser: GUIDES is one flat object literal per
    line by convention, and resync_guide_cards() above already relies on that
    shape. A line that doesn't carry an href isn't an entry and is skipped.
    """
    src = nav.read_text(encoding="utf-8")
    m = re.search(r"(  var GUIDES = \[\n)(.*?)(\n  \];)", src, flags=re.S)
    if not m:
        return []

    guides: list[dict[str, str]] = []
    for line in m.group(2).split("\n"):
        href = re.search(r'href: "([^"]+)"', line)
        if not href:
            continue
        def field(name: str) -> str:
            f = re.search(name + r': "([^"]*)"', line)
            return f.group(1) if f else ""
        picks = re.search(r"picks: (\d+)", line)
        guides.append({
            "href": href.group(1),
            "label": field("label"),
            "icon": field("icon"),
            "blurb": field("blurb"),
            "price": field("price"),
            "picks": picks.group(1) if picks else "",
        })
    return guides


def guides_fallback_html(guides: list[dict[str, str]]) -> str:
    """Build the static card list — same markup shape and order as nav.js.

    Classes are lp-gfb-* rather than nav.js's lp-g*: these cards are styled by
    the <style> block inside guides/index.html, which is the whole point, since
    nav.js's stylesheet is exactly the thing that might not arrive.
    """
    rows: list[str] = []
    for g in sorted(guides, key=lambda g: guides_sort_key(g["label"])):
        chips = ""
        if g["picks"] and g["picks"] != "0":
            n = int(g["picks"])
            chips += ('<span class="lp-gfb-chip lp-gfb-chip-n">'
                      f'{n} pick{"" if n == 1 else "s"}</span>')
        if g["price"]:
            chips += f'<span class="lp-gfb-chip">{hesc(g["price"])}</span>'
        if not chips:
            chips = '<span class="lp-gfb-chip">Buyer&#39;s guide</span>'
        blurb = (f'<span class="lp-gfb-blurb">{hesc(g["blurb"])}</span>'
                 if g["blurb"] else "")
        rows.append(
            f'<a class="lp-gfb-card" href="{hesc(g["href"])}">'
            f'<span class="lp-gfb-ic">{g["icon"] or "📖"}</span>'
            f'<span class="lp-gfb-body">'
            f'<span class="lp-gfb-title">{hesc(g["label"])}</span>'
            f'{blurb}<span class="lp-gfb-meta">{chips}</span></span>'
            f'<span class="lp-gfb-arrow">&rarr;</span></a>'
        )
    return FB_NOTE + '\n<div class="lp-gfb">\n' + "\n".join(rows) + "\n</div>"


def sync_guides_fallback(repo: Path, dry: bool) -> list[str]:
    """Rewrite the static guide list in guides/index.html between the markers.

    Call this after resync_guide_cards(), which may have just corrected the
    picks/price fields — we re-read nav.js from disk to pick those up. (Under
    --dry-run nothing has been written, so a dry run shows the list as it would
    be built from the *current* fields; the following real run settles both.)
    """
    fixes: list[str] = []
    page = repo / "guides" / "index.html"
    nav = repo / "nav.js"
    if not page.exists() or not nav.exists():
        return fixes

    guides = parse_guides(nav)
    if not guides:
        print("  ! nav.js has no GUIDES array — cannot write the static guide list",
              file=sys.stderr)
        return fixes

    html = page.read_text(encoding="utf-8")
    i, j = html.find(FB_START), html.find(FB_END)
    if i == -1 or j == -1 or j < i:
        print("  ! guides/index.html is missing its LP:GUIDES-FALLBACK markers — "
              "the static guide list was not written", file=sys.stderr)
        return fixes

    wanted = "\n" + guides_fallback_html(guides) + "\n"
    if html[i + len(FB_START):j] == wanted:
        return fixes

    fixes.append(f"guides/index.html: static guide list rebuilt ({len(guides)} guides)")
    if not dry:
        page.write_text(html[:i + len(FB_START)] + wanted + html[j:],
                        encoding="utf-8")
    return fixes


# ── The static footer, on every page ─────────────────────────────────────────
#
# nav.js owns the rendered footer: synthesizeFooter() deletes every <footer> on
# the page and appends its own, built from the FOOTER object. That made each
# page's hand-written footer invisible in a browser — but not in the HTML, and
# not to anyone whose nav.js request never arrives. Across the site those
# hand-written footers had drifted into twenty structural shapes and ten
# wordings, several with stale copyright years and Associates tags that FOOTER
# does not carry. So we generate them too, from the same FOOTER object, into
# every page between these markers.
#
# The generated block is a plain <footer class="lp-ffb">, which nav.js removes
# at load exactly like the hand-written ones it replaces — nav.js needs no
# change and there is never a moment with two footers in the DOM.
#
# Why it carries its own <style>: there is no shared stylesheet on this site.
# Every page has its own inline CSS, 142 of them define their own footer{} rules
# and 10 define none at all, so an unstyled block would render 143 different
# ways. Every rule below is class-scoped (.lp-ffb beats a bare footer selector
# on specificity) and resets every property a page footer might have set, so the
# fallback looks the same on all of them.
FF_START = "<!-- LP:FOOTER-FALLBACK -->"
FF_END = "<!-- /LP:FOOTER-FALLBACK -->"

FF_NOTE = ("<!-- Generated by surface_articles.py from the FOOTER object in nav.js.\n"
           "     Do not hand-edit: nav.js replaces this block on load, and\n"
           "     check_surfaced.py fails the commit if it drifts. Edit FOOTER. -->")

# Not every .html in the repo is a page of the site. The UX review docs are
# standalone write-ups that happen to live here; they have their own chrome and
# must not be given the site footer. Matched by prefix so ux-review_6.html and
# whatever comes after are covered without editing this line again.
FF_SKIP_PREFIXES = ("ux-review",)

FF_CSS = (
    ".lp-ffb{all:unset;display:block;box-sizing:border-box;"
    "border-top:1px solid var(--border,#26262e);background:var(--bg,#0c0c0e);"
    "color:var(--text,#e2e2e8);padding:2.5rem 2rem 2rem;margin:2rem 0 0;"
    "font-family:'Inter',system-ui,sans-serif;font-size:16px;line-height:1.6;"
    "text-align:left;}"
    ".lp-ffb *{box-sizing:border-box;margin:0;padding:0;}"
    ".lp-ffb a{text-decoration:none;color:inherit;}"
    ".lp-ffb .lp-ffb-inner{max-width:1040px;margin:0 auto;display:grid;"
    "grid-template-columns:auto auto auto;justify-content:space-between;"
    "column-gap:3rem;row-gap:2rem;align-items:start;}"
    ".lp-ffb .lp-ffb-brand{max-width:360px;}"
    ".lp-ffb .lp-ffb-mark{display:flex;align-items:center;gap:0.6rem;"
    "font-size:1rem;font-weight:800;color:var(--text,#e2e2e8);"
    "letter-spacing:-0.02em;}"
    ".lp-ffb .lp-ffb-mark i{width:28px;height:28px;background:var(--accent,#e8ff47);"
    "color:#000;border-radius:6px;display:flex;align-items:center;"
    "justify-content:center;font-style:normal;font-size:0.9rem;}"
    ".lp-ffb .lp-ffb-mark b{color:var(--accent,#e8ff47);font-weight:800;}"
    ".lp-ffb .lp-ffb-brand p{font-size:0.8rem;color:var(--muted,#7a7a8a);"
    "margin-top:0.6rem;line-height:1.6;}"
    ".lp-ffb .lp-ffb-col h4{font-size:0.75rem;font-weight:600;"
    "text-transform:uppercase;letter-spacing:0.05em;color:var(--muted,#7a7a8a);"
    "margin-bottom:0.75rem;}"
    ".lp-ffb .lp-ffb-col a{display:block;font-size:0.85rem;"
    "color:var(--muted,#7a7a8a);margin-bottom:0.45rem;}"
    ".lp-ffb .lp-ffb-col a:hover{color:var(--text,#e2e2e8);}"
    ".lp-ffb .lp-ffb-bottom{max-width:1040px;margin:1.75rem auto 0;"
    "padding-top:1.5rem;border-top:1px solid var(--border,#26262e);display:flex;"
    "justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:1rem;}"
    ".lp-ffb .lp-ffb-bottom p{font-size:0.75rem;color:var(--muted,#7a7a8a);}"
    ".lp-ffb .lp-ffb-copy{display:flex;flex-direction:column;gap:0.45rem;}"
    ".lp-ffb .lp-ffb-copy a{font-size:0.75rem;color:var(--accent,#e8ff47);"
    "width:fit-content;}"
    ".lp-ffb .lp-ffb-copy a:hover{text-decoration:underline;}"
    ".lp-ffb .lp-ffb-disc{opacity:0.7;max-width:520px;line-height:1.5;"
    "font-size:0.72rem;}"
    "@media(max-width:760px){.lp-ffb .lp-ffb-inner{grid-template-columns:1fr 1fr;"
    "justify-content:normal;column-gap:2rem;row-gap:1.75rem;}"
    ".lp-ffb .lp-ffb-brand{grid-column:1 / -1;max-width:none;}}"
    "@media(max-width:460px){.lp-ffb .lp-ffb-inner{grid-template-columns:1fr;}}"
)

# One <footer>…</footer>, non-greedy. Verified against the whole repo: no page
# nests a footer inside another, so there is nothing for this to swallow.
FOOTER_EL = re.compile(r"<footer\b[^>]*>.*?</footer>", re.S | re.I)

# nav.js deletes an <hr class="divider"> sitting immediately above the footer so
# its border-top doesn't double up. Do the same statically, so the pre-rendered
# footer and the runtime one look alike.
# Anchored at the end of everything before the footer, so it can only ever match
# a divider that is genuinely the last thing above it.
FOOTER_HR = re.compile(r"<hr\b[^>]*class=\"[^\"]*\bdivider\b[^\"]*\"[^>]*>\s*\Z", re.I)

# If someone deletes the marker comments but leaves the block, the footer itself
# is found and replaced by FOOTER_EL above — but the note and <style> that came
# with it would be stranded there, and the fresh block brings its own copy of
# both. Harmless to look at (the CSS is identical) but it accumulates. Anchored
# the same way as FOOTER_HR, so it can only match a note+style that is genuinely
# the last thing before the footer being replaced.
FF_ORPHAN = re.compile(r"<!-- Generated by surface_articles\.py.*?-->\s*"
                       r"<style>\.lp-ffb\{.*?</style>\s*\Z", re.S)

# Most pages load "/nav.js"; a handful load "../nav.js". Match either, so a page
# with no footer gets its generated one above the script rather than dumped at
# the very end of <body>.
NAVJS_TAG = re.compile(r"[ \t]*<script[^>]+src=\"(?:/|\.\./)?nav\.js\"[^>]*>\s*</script>",
                       re.I)


def parse_footer(nav: Path) -> dict | None:
    """Read the FOOTER object out of nav.js.

    Same deliberate regex approach as parse_guides(): FOOTER is a hand-edited
    literal with one field per line and one link object per line, and keeping
    the parser dumb keeps the failure mode loud (returns None) rather than
    subtly wrong.
    """
    src = nav.read_text(encoding="utf-8")
    m = re.search(r"  var FOOTER = \{\n(.*?)\n  \};", src, flags=re.S)
    if not m:
        return None
    body = m.group(1)

    def scalar(name: str) -> str:
        f = re.search(name + r': "((?:[^"\\]|\\.)*)"', body)
        return f.group(1).replace('\\"', '"') if f else ""

    def links(name: str) -> list[dict[str, str]]:
        blk = re.search(name + r": \[\n(.*?)\n    \]", body, flags=re.S)
        if not blk:
            return []
        out = []
        for line in blk.group(1).split("\n"):
            lab = re.search(r'label: "([^"]*)"', line)
            href = re.search(r'href: "([^"]*)"', line)
            if lab and href:
                out.append({"label": lab.group(1), "href": href.group(1)})
        return out

    f = {
        "tagline": scalar("tagline"),
        "guides": links("guides"),
        "site": links("site"),
        "copyright": scalar("copyright"),
        "disclosure": scalar("disclosure"),
    }
    return f if f["copyright"] and (f["guides"] or f["site"]) else None


def footer_fallback_html(f: dict) -> str:
    """Build the static footer — same content and shape as synthesizeFooter().

    Classes are lp-ffb-* rather than nav.js's lpf-*: nav.js's stylesheet is
    exactly the thing that might not arrive, so this block cannot borrow from
    it. The two are compared by meaning, not markup, so this can be restyled
    freely without breaking check_surfaced.py.
    """
    def col(title: str, items: list[dict[str, str]]) -> str:
        links = "".join(f'<a href="{hesc(l["href"])}">{l["label"]}</a>' for l in items)
        return f'<div class="lp-ffb-col"><h4>{title}</h4>{links}</div>'

    return (
        FF_NOTE
        + f"\n<style>{FF_CSS}</style>\n"
        + '<footer class="lp-ffb">'
        + '<div class="lp-ffb-inner">'
        + '<div class="lp-ffb-brand">'
        + '<a class="lp-ffb-mark" href="/"><i>&#8853;</i>Loiter<b>Point</b></a>'
        + f'<p>{f["tagline"]}</p>'
        + "</div>"
        + col("Popular Guides", f["guides"])
        + col("Site", f["site"])
        + "</div>"
        + '<div class="lp-ffb-bottom">'
        + f'<div class="lp-ffb-copy"><p>{f["copyright"]}</p>'
        + '<a href="/sitemap.xml">Sitemap (XML)</a></div>'
        + f'<p class="lp-ffb-disc">{f["disclosure"]}</p>'
        + "</div></footer>"
    )


def site_pages(repo: Path) -> list[Path]:
    """Every page that should carry the site footer, in a stable order."""
    pages = [p for p in repo.glob("*.html")]
    for d in sorted(repo.iterdir()):
        if d.is_dir() and not d.name.startswith(".") and d.name not in {"node_modules"}:
            pages += sorted(d.glob("*.html"))
    return sorted(p for p in pages
                  if not p.name.startswith(FF_SKIP_PREFIXES))


def sync_footer_fallback(repo: Path, dry: bool) -> tuple[list[str], list[str]]:
    """Write the generated footer into every page. Returns (fixes, warnings).

    Three cases per page, in order:
      1. markers already present  -> rewrite what's between them
      2. a hand-written <footer>  -> replace it (and a divider <hr> above it)
      3. no footer at all         -> insert above the nav.js tag, else </body>
    After the first run every page is case 1, which is what makes this idempotent.
    """
    fixes: list[str] = []
    warnings: list[str] = []
    nav = repo / "nav.js"
    if not nav.exists():
        return fixes, ["nav.js not found — the static footers were not written"]

    f = parse_footer(nav)
    if f is None:
        return fixes, ["nav.js has no readable FOOTER object — "
                       "the static footers were not written"]

    block = footer_fallback_html(f)
    added = replaced = updated = 0

    for page in site_pages(repo):
        rel = page.relative_to(repo).as_posix()
        html = page.read_text(encoding="utf-8")
        i, j = html.find(FF_START), html.find(FF_END)

        if i != -1 and j != -1 and j > i:
            wanted = "\n" + block + "\n"
            if html[i + len(FF_START):j] == wanted:
                continue
            new = html[:i + len(FF_START)] + wanted + html[j:]
            updated += 1
        else:
            marked = f"{FF_START}\n{block}\n{FF_END}"
            m = FOOTER_EL.search(html)
            if m:
                # Orphaned note+style first, then a divider that may sit above it.
                before = FF_ORPHAN.sub("", html[:m.start()])
                new = FOOTER_HR.sub("", before) + marked + html[m.end():]
                replaced += 1
            else:
                s = NAVJS_TAG.search(html)
                at = s.start() if s else html.lower().rfind("</body>")
                if at == -1:
                    warnings.append(f"{rel}: no <footer>, no nav.js tag and no "
                                    "</body> — left alone")
                    continue
                new = html[:at] + marked + "\n" + html[at:]
                added += 1

        if not dry:
            page.write_text(new, encoding="utf-8")

    if replaced:
        fixes.append(f"{replaced} page(s): hand-written footer replaced with the "
                     "generated one")
    if added:
        fixes.append(f"{added} page(s) had no footer at all: generated one added")
    if updated:
        fixes.append(f"{updated} page(s): generated footer refreshed from FOOTER")
    return fixes, warnings


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--skip-sitemap", action="store_true",
                    help="don't run generate_sitemap.py afterward")
    args = ap.parse_args()
    repo = Path(args.repo).resolve()
    dry = args.dry_run

    arts_dir = repo / "articles"
    if not arts_dir.is_dir():
        print("error: no articles/ directory", file=sys.stderr)
        return 2

    cats = category_dirs(repo)

    # reverse-map: slug -> category it is already carded on
    carded: dict[str, str] = {}
    for cat in cats:
        for card in cards_on(repo / cat / "index.html"):
            for slug in card:
                carded.setdefault(slug, cat)

    articles = sorted(p.name for p in arts_dir.glob("*.html"))
    added_cards = 0
    added_leaves = 0
    guessed: list[str] = []
    uncategorized: list[str] = []

    smap_listed = set(ARTICLE_HREF.findall((repo / "site-map.html").read_text(encoding="utf-8")))

    for name in articles:
        slug = name[:-5]
        title, desc, lp = article_meta(arts_dir / name)

        # 1) explicit meta  2) existing placement  3) keyword guess
        cat = None
        if lp and lp in CATEGORIES:
            cat = lp
        elif name in carded:
            cat = carded[name]
        else:
            cat = guess_category(slug)
            if cat:
                guessed.append(f"{slug} → {cat}")

        if not cat:
            uncategorized.append(slug)
            continue

        # ensure a card on the category page
        if name not in carded or carded[name] != cat:
            already = any(name in card for card in cards_on(repo / cat / "index.html"))
            if not already:
                if add_card(repo, cat, build_card(slug, title, desc, cat), dry):
                    added_cards += 1
                    carded[name] = cat
                    print(f"  + card: {slug}  →  /{cat}/")

        # ensure a site-map leaf
        if name not in smap_listed:
            if add_sitemap_leaf(repo, cat, slug, title or title_from_slug(slug), dry):
                added_leaves += 1
                smap_listed.add(name)
                print(f"  + site-map: {slug}  (under {cat})")

    # recompute all counts from the real cards now on disk
    real_counts = {cat: len(cards_on(repo / cat / "index.html")) for cat in cats}
    home_fixes = recount_homepage(repo, real_counts, dry)
    branch_fixes = recount_sitemap_branches(repo, dry)
    guide_fixes = resync_guide_cards(repo, dry)
    # after resync, so the static list carries the corrected picks/price
    fallback_fixes = sync_guides_fallback(repo, dry)
    footer_fixes, footer_warnings = sync_footer_fallback(repo, dry)
    for f in home_fixes:
        print(f"  ~ {f}")
    for f in guide_fixes:
        print(f"  ~ {f}")
    for f in fallback_fixes:
        print(f"  ~ {f}")
    for f in footer_fixes:
        print(f"  ~ {f}")
    for w in footer_warnings:
        print(f"  ! {w}", file=sys.stderr)

    print()
    verb = "would add" if dry else "added"
    print(f"{verb}: {added_cards} card(s), {added_leaves} site-map entr(y/ies); "
          f"fixed {len(home_fixes)} homepage count(s), {branch_fixes} site-map count(s), "
          f"{len(guide_fixes)} guide-card field(s), "
          f"{len(fallback_fixes)} static guide list(s), "
          f"{len(footer_fixes)} static-footer group(s).")
    if guessed:
        print("\nGUESSED categories from slug keywords — verify these are right:")
        for g in guessed:
            print(f"  {g}")
    if uncategorized:
        print("\nUNCATEGORIZED — could not place these; add "
              '<meta name="lp:category" content="…"> to each (or a keyword rule):',
              file=sys.stderr)
        for s in uncategorized:
            print(f"  {s}", file=sys.stderr)
        return 1

    # regenerate sitemap.xml with the project's own tool (uses git for lastmod)
    if not args.skip_sitemap and not dry:
        gs = repo / "generate_sitemap.py"
        if gs.exists():
            try:
                subprocess.run([sys.executable, str(gs)], cwd=str(repo), check=True)
            except Exception as e:  # noqa: BLE001
                print(f"  (could not run generate_sitemap.py: {e} — run it yourself)",
                      file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
