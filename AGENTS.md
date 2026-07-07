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
