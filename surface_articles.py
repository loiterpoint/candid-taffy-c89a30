#!/usr/bin/env python3
"""
Surface every article on Loiter Point — the inverse of check_surfaced.py.

check_surfaced.py *reports* what is unreachable. This *fixes* it: for each
articles/*.html it makes sure there is (1) a card on the correct category page,
(2) an entry in site-map.html, and then recomputes every homepage tile count and
site-map branch count from the real card counts so they can never lie.

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
    index = repo / "index.html"
    html = index.read_text(encoding="utf-8")
    fixes: list[str] = []

    # each tile: <a href="/cat/" class="cat-card"> … <div class="cat-count">N articles</div>
    tile = re.compile(
        r'(<a href="/([a-z-]+)/" class="cat-card">.*?<div class="cat-count">)(\d+)( articles?</div>)',
        re.S)

    def fix(m: re.Match) -> str:
        pre, cat, shown, post = m.group(1), m.group(2), int(m.group(3)), m.group(4)
        actual = real_counts.get(cat)
        if actual is not None and actual != shown:
            fixes.append(f"homepage {cat}: {shown} → {actual}")
            return f"{pre}{actual}{post}"
        return m.group(0)

    html2 = tile.sub(fix, html)
    if fixes and not dry:
        index.write_text(html2, encoding="utf-8")
    return fixes


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
    for f in home_fixes:
        print(f"  ~ {f}")

    print()
    verb = "would add" if dry else "added"
    print(f"{verb}: {added_cards} card(s), {added_leaves} site-map entr(y/ies); "
          f"fixed {len(home_fixes)} homepage count(s), {branch_fixes} site-map count(s).")
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
