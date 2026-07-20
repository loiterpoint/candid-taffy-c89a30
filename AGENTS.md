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
- New articles: add the article file + one sitemap <url> entry + (optionally) one
  homepage card. Never rewrite the whole sitemap or homepage to do this.
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
- Article pattern: TLDR box first with quick-buy links ("Grab your pick:" strip),
  then How We Evaluate, pick-cards, nerd-box, comparison table, Bottom Line,
  footer with affiliate disclosure ("© 2026 Loiter Point — Consumer tech reviews
  built on real evidence.").
- When evidence is thin or conflicting, say so in the article. That is the brand.

## 4. Category prioritization — revenue-first (follow the money)
- /category-priorities.json is the SINGLE SOURCE OF TRUTH for what to build next. Read it
  before choosing any new article topic, homepage placement, nav ordering, or internal link.
- Allocate effort in descending priorityScore order. Current order: smartphones (95, ZERO
  coverage — top gap), computing (83), TVs/entertainment (68), smart home (64), wearables
  (54), gaming (51), security (44), networking (43), audio (43), home-energy (36), cameras
  (35), robotics (33), drones (20 — overweighted already; maintain, do not expand).
- Homepage sections, nav.js LINKS, and category-grid tiles should be ORDERED by
  priorityScore, not alphabetically or by legacy placement.
- New articles: pick the highest-priority category with the thinnest coverage first.
  Internal links in new articles should point up-priority (e.g. a drone article may link
  to smartphone/computing guides, not only other drone pages).
- Do not hardcode the ranking anywhere else. If market data changes, edit the JSON scores;
  everything downstream follows.
- EDITORIAL FIREWALL (unchanged by this section): prioritization is CATEGORY-level only.
  Within a guide, pick order is evidence-based per §1 — never commission-based. The
  affiliate disclosure's "never influences scores" claim must stay literally true.
