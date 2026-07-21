# Rules for AI agents working on this repo (loiterpoint.com)

Multiple agents and scheduled tasks work on this site. These rules exist because we have
had real incidents: a wholesale homepage regeneration silently reverted newer fixes and
reintroduced fabricated claims, and a batch of articles shipped with 18 invented Amazon
ASINs (every buy link 404'd). Follow these rules exactly.

## 1. Honesty — non-negotiable
- NEVER fabricate first-hand testing. No "we tested", "we measured", "our lab",
  "hours of field testing", "X products tested", "we flew N sessions", "no press
  loaners — retail purchases only". Loiter Point does not run a lab and says so.
- Real-world figures must come from published independent testing or verified owner
  reports, attributed that way. Spec rows are labeled "(lab-tested)" only with a real
  source, else "(est. real-world)" or "(reported)". Methodology sections are titled
  "How We Evaluate ..." and describe synthesizing published evidence.
- Never invent ASINs, prices, statistics, or review counts. Verify an ASIN by opening
  amazon.com/dp/<ASIN> and confirming the product before using it. If unverified, use
  https://www.amazon.com/s?k=PRODUCT+NAME&tag=loiterpoint20-20 instead.
- Affiliate links: ?tag=loiterpoint20-20 with rel="sponsored nofollow".

## 2. Edit discipline — prevent clobbering
- SURGICAL EDITS ONLY on shared files (index.html, sitemap.xml, about.html). Change the
  specific strings you need. NEVER regenerate or re-upload these files wholesale.
- Re-fetch the CURRENT file from main immediately before editing. If your editor tab or
  local copy has been open more than a few minutes, reload it — committing a stale
  buffer reverts other agents' work.
- One logical change per commit, descriptive commit message. Commit only the files your
  task owns; don't "helpfully" touch neighbors.
- deals.html is owned by the daily deal-radar task. Other agents: hands off.
- New articles: (1) write the article file, and put `<meta name="lp:category"
  content="<slug>">` in its `<head>` (slug = one of the 12 category dirs, e.g.
  `streaming`, `networking`, `audio`). (2) Run `python3 surface_articles.py`. It
  inserts the category-page card + the site-map.html entry, recomputes every
  homepage tile and site-map count from the real cards, and regenerates
  sitemap.xml — all as surgical edits. Do NOT hand-edit index.html / site-map.html
  / sitemap.xml to surface an article; let the script do it. `check_surfaced.py`
  fails CI if any article is left unsurfaced, so run the script before committing.
- Filenames: no year suffixes (best-webcams.html, not best-webcams-2024.html). It is 2026.
- EVERY page must load `<script src="/nav.js" defer></script>` before `</body>`. nav.js
  self-injects the nav bar, mobile menu, and Account/Sign out buttons — a page without it
  ships with no navigation at all. If the page has no `<nav>`, nav.js builds a minimal one.
  generate_content.py emits this line; hand-written pages must include it too.

## 3. Site conventions
- Hosting: GitHub Pages from main (Netlify is paused — ignore netlify.toml).
- Dark theme CSS vars: --bg:#0c0c0e; --surface:#141418; --surface2:#1c1c22;
  --accent:#e8ff47; --text:#e2e2e8; --muted:#7a7a8a; --border:#26262e.
  Fonts: IBM Plex Mono + Inter. Favicon: /favicon.svg.
- SHARED NAV/FOOTER: every page (articles, guides, root pages) must load the shared
  nav script exactly once, immediately before </body>:
  <script src="/nav.js" defer></script>
  nav.js renders the canonical top nav, the mobile hamburger menu and the site
  footer, so pages do not hand-roll their own. It guards against double-execution,
  but a second tag is still a bug — never add one if the page already has it.
- Article pattern: TLDR box first with quick-buy links ("Grab your pick:" strip),
  then How We Evaluate, pick-cards, nerd-box, comparison table, Bottom Line,
  footer with affiliate disclosure ("© 2026 Loiter Point — Consumer tech reviews
  built on real evidence.").
- When evidence is thin or conflicting, say so in the article. That is the brand.

## 4. Category prioritization — revenue-first (follow the money)
`category-priorities.json` in the repo root is the SINGLE SOURCE OF TRUTH for what to build next. Read it before choosing any topic; never hardcode the order anywhere else.
- Allocate effort by descending `priorityScore`. Current order: smartphones (95), computing (83), tv-entertainment (68), smart-home (64), wearables (54), gaming (51), security (44), networking (43), audio (43), home-energy (36), cameras (35), robotics (33), drones (20).
- Homepage placement, nav ordering, category tiles and internal linking are ORDERED BY priorityScore — not alphabetically, not by legacy placement.
- New articles: pick the highest-priority category with the thinnest coverage. Internal links should point up-priority.
- DRONES ARE OVERWEIGHTED relative to their market. Maintain existing drone content; do NOT expand it.
- If market data changes, edit the JSON scores — everything downstream follows.
- EDITORIAL FIREWALL: this governs CATEGORY-level coverage and placement only. It NEVER affects the ranking of picks inside a guide, which stays strictly evidence-based. This is what keeps the affiliate disclosure literally true.

## 5. Encoding safety — the atob() trap (caused a live incident 2026-07-20)
When editing a repo file through the browser, NEVER use `atob(content)` alone. `atob` returns a Latin-1 byte string, so every multi-byte UTF-8 character (em dash, en dash, copyright sign, curly quotes) becomes several separate characters. Committing that re-encodes each one and corrupts the file — the live homepage title rendered as garbage bytes this way.
- ALWAYS decode with: `new TextDecoder('utf-8').decode(Uint8Array.from(atob(b64), c => c.charCodeAt(0)))`
- Before committing, assert ZERO occurrences of the mojibake markers, i.e. the code-point sequences \u00e2\u0080\u0094 and \u00c2\u00a9, in the new content. (Written escaped here on purpose so this file stays scan-clean.)
- Byte-size is the tripwire: a pure reorder or small text edit must not change file size by hundreds of bytes. If the committed size does not match what you produced, you corrupted the encoding — restore from the last good commit and redo.
- GitHub's Copilot auto-suggests commit messages that are frequently WRONG (it labelled an unrelated edit "Correct character encoding"). Always overwrite the suggested message with what you actually did.

## 6. Affiliate link durability
Dead or gouging affiliate links cost more than missing ones.
- Prefer `https://www.amazon.com/s?k=QUERY&tag=loiterpoint20-20` (search links) by DEFAULT. They never 404, never go out of stock, and always reflect current pricing.
- Only use a direct `/dp/ASIN` link when you have loaded that ASIN and confirmed it is the right product AND the offer is sold/shipped by Amazon or the brand — not a marginal third-party listing. A verified-but-gouging listing is still a bad link (an iPhone ASIN sold at $1,429 against a $1,199 list price was replaced with a search link on 2026-07-20).
- Every Amazon link carries `?tag=loiterpoint20-20` and `rel="sponsored nofollow"`.
- Every pick also gets a `.compare` row of plain retailer SEARCH links (no fake tracking) for the retailers that actually sell that product type.
- State prices as "list" or "recently seen" with the footer price disclaimer. Never present a scraped price as a guaranteed one.

## 7. PROTECTED HEAD ELEMENTS — never drop these (regression 2026-07-20 and 2026-07-21)
Automated rewrites of `index.html` have twice silently deleted verification tags that took real effort to obtain. Anything in this list must SURVIVE every rewrite of every page it appears on. If you regenerate a page, re-insert these first and verify them after committing.
- `<meta name="impact-site-verification" value="a6881370-e20e-4608-bb1b-1c9175c548ab">` in the `<head>` of index.html. Required for the Impact affiliate application.
- Any `google-site-verification` or `msvalidate.01` meta tag, if present.
- `<link rel="canonical">`, the Open Graph tags, and `<link rel="icon" type="image/svg+xml" href="/favicon.svg" />`.
- `robots.txt` must keep `Allow: /` and its `Sitemap:` line. The IndexNow key file in the repo root must not be deleted or renamed — it is what authorizes Bing/Yandex URL submission.
BEFORE committing any regenerated page, diff your `<head>` against the live one and confirm no tag from this list disappeared. Losing one is a silent failure: nothing breaks visibly, but an affiliate application or search-engine verification quietly stops working.

## 8. SEO reality check (2026-07-21)
Google Search Console (a DNS-verified DOMAIN property) reports 24 indexed pages and 27 not indexed, against 158 HTML files in the repo — meaning roughly 100 pages have not been discovered at all. Publishing volume is NOT the constraint; discovery is.
- The single highest-leverage action is keeping sitemap.xml complete and submitted, and pinging IndexNow on publish. Publishing another article that never gets crawled adds nothing.
- Impact declined the affiliate application on 2026-07-21 citing insufficient domain traffic — not content quality. Traffic and indexing are therefore the priority over raw article count until that changes.
- Do not inflate the homepage stat counters to look bigger. The counters are computed from the repo and honesty is the brand.
