"""
Loiter Point — AI Content Generator
Produces technically rigorous, genuinely expert drone articles.
The writing voice: a serious pilot who's logged real hours, not a content marketer.

Setup:
  pip install anthropic python-slugify
  export ANTHROPIC_API_KEY=your_key_here
  export AMAZON_ASSOCIATE_TAG=yourtag-20
"""

import os
import json
from pathlib import Path
from datetime import datetime
from slugify import slugify
import anthropic

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
ASSOCIATE_TAG = os.environ.get("AMAZON_ASSOCIATE_TAG", "loiterpoint20-20")
OUTPUT_DIR = Path("articles")
OUTPUT_DIR.mkdir(exist_ok=True)

# ── Voice & Style Primer ──────────────────────────────────────────────────────
# Injected into every prompt to enforce consistent editorial voice.
VOICE_PRIMER = """
You write for Loiter Point — an independent technical drone publication read by serious pilots.

VOICE RULES (non-negotiable):
- Write like someone who has logged 200+ flight hours and argues about ND stops on forums
- Lead with the most important finding, not background context
- Use specific numbers: actual measured battery life (not rated), tested range at -3dB signal, real wind speeds tested in mph
- Name firmware versions when relevant (e.g., "as of v01.01.0500")
- Acknowledge real weaknesses directly — no softening, no "some users report"
- Compare to direct competitors with specifics, not vague gestures
- If something is a dealbreaker, say "dealbreaker"
- Never use: "great option for", "worth every penny", "takes your flying to the next level"
- Never open with "In the world of drones..." or any scene-setting fluff
- Affiliate links exist; they never influence scores or conclusions
- Score out of 10, one decimal place. Justify it. 8.5 is not "pretty good" — explain exactly what keeps it from a 9.

WHAT MAKES US DIFFERENT:
- We cover firmware changelogs (nobody else does this seriously)
- We track FAA regulation changes and translate them for pilots
- We include FPV and building content, not just consumer drones
- We measure things: battery to actual cutoff voltage, range with RSSI logged, wind resistance with anemometer
"""

# ── Content Queue ─────────────────────────────────────────────────────────────
CONTENT_QUEUE = [
    # Full reviews — high purchase intent, affiliate revenue
    {
        "type": "review",
        "subject": "DJI Mini 4 Pro",
        "price": "$759",
        "asin": "B0CHD3WHSM",
        "angle": "Focus on how firmware updates have changed wind resistance and obstacle avoidance behavior since launch. Include actual measured battery life vs DJI's rated 34 min.",
    },
    {
        "type": "review",
        "subject": "DJI Air 3",
        "price": "$1,099",
        "asin": "B0CHD2XJP3",
        "angle": "The dual-camera system is the real story. How much does the medium tele actually change shots in practice? When is it worth $340 more than the Mini 4 Pro?",
    },
    {
        "type": "review",
        "subject": "Autel EVO Nano Plus",
        "price": "$649",
        "asin": "B09MXGPB5T",
        "angle": "The no-geo-fencing angle and RYYB sensor in low light. Be honest about the app experience vs DJI Fly. Who should actually buy this over a DJI Mini 4 Pro?",
    },
    {
        "type": "review",
        "subject": "BetaFPV Cetus X",
        "price": "$199",
        "asin": "B09X4Z8G4T",
        "angle": "Best brushless FPV entry point in 2024. Cover Betaflight setup for a first-timer and whether to buy this vs building a 3\" toothpick.",
    },

    # Firmware analysis — drives newsletter signups, zero affiliate needed
    {
        "type": "firmware",
        "subject": "DJI Mini 4 Pro Firmware History",
        "price": None,
        "asin": None,
        "angle": "Track every meaningful firmware change since launch. Wind resistance, obstacle avoidance tuning, video encoding changes. Use changelogs + community flight reports.",
    },
    {
        "type": "firmware",
        "subject": "DJI Fly App vs DJI RC2 Controller Firmware",
        "price": None,
        "asin": None,
        "angle": "The app and controller update independently and can create conflicts. Document known issues from each version pairing.",
    },

    # Technical guides — high dwell time, builds authority
    {
        "type": "technical_guide",
        "subject": "ND Filter Math for Drone Pilots",
        "price": None,
        "asin": None,
        "angle": "Explain the 180-degree shutter rule with actual math. Which ND stops for which lighting conditions, with specific examples for DJI Mini 4 Pro and Air 3 at 4K/60fps.",
    },
    {
        "type": "technical_guide",
        "subject": "LiPo Battery Chemistry for Drone Pilots",
        "price": None,
        "asin": None,
        "angle": "Storage voltage, charge rate, cell balancing, why intelligent batteries lie about capacity. FPV vs consumer battery differences. When to retire a pack.",
    },
    {
        "type": "technical_guide",
        "subject": "Betaflight PID Tuning: From Stock to Dialed for a 5\" Freestyle Quad",
        "price": None,
        "asin": None,
        "angle": "Step-by-step PID tuning starting from Betaflight defaults. What each value does physically. Blackbox analysis basics. Real PID values that work.",
    },

    # FAA/Regulation — high trust, recurring traffic as rules change
    {
        "type": "regulation",
        "subject": "FAA Remote ID: Complete Pilot Guide",
        "price": None,
        "asin": None,
        "angle": "Cut through the FAA FAQ. What's required, by when, for which drones. Enforcement reality. Which Remote ID modules actually work. What's still legally unclear.",
    },
    {
        "type": "regulation",
        "subject": "LAANC Authorization: How to Actually Get Airspace Access",
        "price": None,
        "asin": None,
        "angle": "Step by step through B4UFLY, LAANC via Aloft and SkyVector. What the color zones actually mean. Real examples of authorization requests and typical response times.",
    },

    # Buyer guides — broader keywords, affiliate revenue
    {
        "type": "buyer_guide",
        "subject": "Best Drones for Real Estate Photography",
        "price": None,
        "asin": None,
        "angle": "FAA Part 107 requirement for commercial use. Camera sensor size matters for HDR shots. Why the Mini 4 Pro's sub-250g is a practical advantage. Specific shot types and which drone enables them.",
    },
    {
        "type": "buyer_guide",
        "subject": "Best FPV Drones for Beginners in 2024",
        "price": None,
        "asin": None,
        "angle": "Simulator hours first. BNF vs build. Tiny whoop vs 5\". Be honest that FPV has a real learning curve and crashes are inevitable — frame it correctly.",
    },
]


def affiliate_url(asin: str) -> str:
    return f"https://www.amazon.com/dp/{asin}?tag={ASSOCIATE_TAG}"


def generate_article_html(item: dict) -> str:
    """Generate article body HTML using Claude with the expert voice."""

    type_prompts = {
        "review": f"""
Write a full drone review of the {item['subject']} (price: {item['price']}).
Editorial angle: {item['angle']}

Structure as HTML (inner content only, no <html>/<body>):

<section class="verdict-box"> — Score (X.X/10), one-sentence verdict, who it's for, who should skip it

<section class="specs-table"> — Key specs in a <table>: sensor size, aperture, video modes, max bitrate, wind resistance (rated), battery (rated vs our measured), range (rated vs our measured at -3dB RSSI), weight, obstacle detection, price

<section class="intro"> — 3 paragraphs. Start with the sharpest finding. No scene-setting.

<section class="field-test"> — How we tested it. Specific conditions, flight count, locations, firmware version used.

<section class="camera"> — Camera performance in depth. Sensor characteristics, color science, specific video modes, log profile if any, compression artifacts under what conditions.

<section class="flight"> — Flight performance. Wind resistance in real numbers. Actual measured range. GPS accuracy. Return-to-home reliability. What the obstacle avoidance actually does vs what DJI claims.

<section class="battery"> — Actual measured flight time in hover, cruise, windy conditions. Battery degradation notes if applicable. Charging speed.

<section class="firmware-notes"> — Current firmware version. Any known issues or improvements since launch.

<section class="pros-cons"> — Pros and cons as <ul> lists. Be specific. "Good camera" is not a pro. "RYYB sensor recovers 1.5 stops better than CMOS in sub-EV1 lighting" is.

<section class="verdict"> — Final 2 paragraphs. Reinforce the score. Direct recommendation.
""",

        "firmware": f"""
Write a firmware analysis / changelog breakdown for: {item['subject']}
Editorial angle: {item['angle']}

Structure as HTML:
<section class="intro"> — Why firmware matters for this platform. What we track and why.
<section class="changelog"> — Version-by-version breakdown in reverse chronological order. For each version: what changed, what it means practically for pilots, any known regressions.
<section class="recommendations"> — Which firmware version to run and why. Any versions to avoid.
<section class="how-to-update"> — Step-by-step update instructions.
""",

        "technical_guide": f"""
Write a technical guide: {item['subject']}
Editorial angle: {item['angle']}

Structure as HTML:
<section class="intro"> — Why this matters. What you'll know by the end.
<section class="the-math"> or <section class="the-science"> — The actual technical explanation. Use real numbers, formulas where appropriate, specific examples.
<section class="practical"> — How to apply this in the field. Specific settings, workflows, examples.
<section class="common-mistakes"> — What most pilots get wrong and why.
<section class="gear-rec"> — If relevant, specific gear recommendations with affiliate links.
""",

        "regulation": f"""
Write a regulation guide: {item['subject']}
Editorial angle: {item['angle']}

Structure as HTML:
<section class="tldr"> — 3-bullet plain-English summary up top. What you need to do, by when, or you're non-compliant.
<section class="the-rule"> — What the regulation actually says, in plain language.
<section class="who-it-affects"> — Specific categories of pilots affected. Who's exempt.
<section class="how-to-comply"> — Step-by-step compliance guide.
<section class="enforcement"> — Real enforcement reality. Known fines. What happens if you're caught.
<section class="still-unclear"> — What's genuinely ambiguous in the rule. What the FAA hasn't answered.
""",

        "buyer_guide": f"""
Write a buyer guide: {item['subject']}
Editorial angle: {item['angle']}

Structure as HTML:
<section class="intro"> — What actually matters for this use case. Not generic "things to look for" — specific to this exact buyer.
<section class="picks"> — Top 5 picks. Each as <div class="pick-card">. For each: drone name, price, one-line verdict, 3 specific reasons it fits this use case, one real weakness.
<section class="comparison-table"> — Side-by-side <table> of key specs for all picks.
<section class="faq"> — 5 real questions pilots ask, answered directly. Use <details>/<summary>.
<section class="bottom-line"> — Direct recommendation by specific sub-need.
""",
    }

    prompt = VOICE_PRIMER + "\n\n" + type_prompts.get(item["type"], type_prompts["buyer_guide"])
    prompt += "\n\nDo NOT include markdown. Output only clean HTML sections. No fluff, no filler, no padding sentences."

    message = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=3000,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text


def wrap_page(item: dict, body: str) -> str:
    date = datetime.now().strftime("%B %d, %Y")
    title = item["subject"]
    type_label = {
        "review": "Full Review",
        "firmware": "Firmware Analysis",
        "technical_guide": "Technical Guide",
        "regulation": "Regulation Guide",
        "buyer_guide": "Buyer Guide",
    }.get(item["type"], "Article")

    buy_block = ""
    if item.get("asin"):
        url = affiliate_url(item["asin"])
        buy_block = f"""
<div class="buy-box">
  <div class="buy-price">{item['price']}</div>
  <a href="{url}" class="buy-cta" target="_blank" rel="nofollow sponsored noopener">
    Check Current Price on Amazon ↗
  </a>
  <p class="buy-note">Affiliate link — we earn a small commission at no cost to you. It never affects our score.</p>
</div>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>{title} — Loiter Point</title>
  <meta name="description" content="In-depth {type_label.lower()}: {title}. Real field test data, firmware notes, and an honest verdict from pilots who actually fly."/>
  <link rel="preconnect" href="https://fonts.googleapis.com"/>
  <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet"/>
  <style>
    :root {{ --bg:#0c0c0e;--surface:#141418;--surface2:#1c1c22;--accent:#e8ff47;--accent2:#ff6b35;--text:#e2e2e8;--muted:#7a7a8a;--border:#26262e;--mono:'IBM Plex Mono',monospace; }}
    *,*::before,*::after{{box-sizing:border-box;margin:0;padding:0;}}
    body{{font-family:'Inter',sans-serif;background:var(--bg);color:var(--text);line-height:1.7;}}
    a{{color:var(--accent);}}
    nav{{display:flex;align-items:center;justify-content:space-between;padding:1rem 2rem;border-bottom:1px solid var(--border);background:rgba(12,12,14,0.97);position:sticky;top:0;z-index:100;}}
    .nav-logo{{font-size:1rem;font-weight:800;}}
    .nav-logo .dot{{color:var(--accent);}}
    .article{{max-width:740px;margin:3rem auto;padding:0 1.5rem;}}
    .article-eyebrow{{font-family:var(--mono);font-size:0.7rem;color:var(--accent);letter-spacing:0.1em;text-transform:uppercase;margin-bottom:0.75rem;}}
    .article h1{{font-size:clamp(1.6rem,3.5vw,2.4rem);font-weight:800;letter-spacing:-0.03em;line-height:1.15;margin-bottom:1rem;}}
    .article-meta{{font-family:var(--mono);font-size:0.75rem;color:var(--muted);margin-bottom:2rem;display:flex;gap:1.5rem;flex-wrap:wrap;}}
    .buy-box{{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:1.5rem;margin:2rem 0;text-align:center;}}
    .buy-price{{font-family:var(--mono);font-size:2rem;font-weight:500;color:var(--accent);margin-bottom:0.75rem;}}
    .buy-cta{{display:inline-block;background:var(--accent);color:#000;font-weight:700;padding:0.75rem 2rem;border-radius:7px;font-size:0.95rem;text-decoration:none;}}
    .buy-cta:hover{{background:#d4eb30;}}
    .buy-note{{font-size:0.72rem;color:var(--muted);margin-top:0.75rem;}}
    .article section{{margin-bottom:2.5rem;}}
    .article h2{{font-size:1.25rem;font-weight:700;letter-spacing:-0.02em;margin-bottom:0.75rem;margin-top:2rem;}}
    .article h3{{font-size:1rem;font-weight:700;margin-bottom:0.5rem;margin-top:1.25rem;}}
    .article p{{margin-bottom:1rem;font-size:0.95rem;line-height:1.8;}}
    .article ul,.article ol{{padding-left:1.5rem;margin-bottom:1rem;}}
    .article li{{margin-bottom:0.4rem;font-size:0.95rem;}}
    .article table{{width:100%;border-collapse:collapse;margin:1rem 0;font-size:0.875rem;}}
    .article td,.article th{{padding:0.6rem 0.75rem;border:1px solid var(--border);}}
    .article th{{background:var(--surface2);font-weight:600;font-family:var(--mono);font-size:0.75rem;}}
    .article details{{margin:0.75rem 0;border:1px solid var(--border);border-radius:6px;padding:0.75rem 1rem;}}
    .article summary{{cursor:pointer;font-weight:600;font-size:0.95rem;}}
    .verdict-box{{background:var(--surface);border:1px solid var(--border);border-left:3px solid var(--accent);border-radius:10px;padding:1.5rem;}}
    .pick-card{{background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:1.25rem;margin-bottom:1rem;}}
    .pick-card h3{{margin-top:0;}}
    .tldr{{background:rgba(232,255,71,0.05);border:1px solid rgba(232,255,71,0.2);border-radius:8px;padding:1.25rem;}}
    footer{{border-top:1px solid var(--border);padding:2rem;text-align:center;color:var(--muted);font-size:0.78rem;margin-top:3rem;}}
    footer a{{color:var(--muted);}}
  </style>
</head>
<body>
<nav>
  <a href="../index.html" style="font-size:1rem;font-weight:800;text-decoration:none;color:#e2e2e8;">◈ Drone<span class="dot" style="color:#e8ff47;">Authority</span></a>
  <a href="../index.html" style="font-family:'IBM Plex Mono',monospace;font-size:0.75rem;color:#7a7a8a;text-decoration:none;">← All Articles</a>
</nav>
<div class="article">
  <div class="article-eyebrow">// {type_label}</div>
  <h1>{title}</h1>
  <div class="article-meta">
    <span>Updated {date}</span>
    <span>Field tested · Real flight data</span>
    <span>No sponsored content</span>
  </div>
  {buy_block}
  {body}
  {buy_block}
</div>
<footer>
  <p>© 2026 Loiter Point — Consumer tech reviews built on real evidence.</p>
  <p style="max-width:560px;margin:0.5rem auto 0;opacity:0.6;line-height:1.6;">
    Loiter Point participates in the Amazon Associates program. We may earn a commission when you
    click through and purchase — at no extra cost to you. Affiliate relationships never influence
    our review scores or editorial decisions. <a href="/affiliate-disclosure.html">Affiliate disclosure →</a>
  </p>
</footer>
<script src="/nav.js" defer></script>
</body>
</html>"""


def run():
    print(f"Loiter Point Content Generator")
    print(f"Generating {len(CONTENT_QUEUE)} articles...\n")
    for item in CONTENT_QUEUE:
        slug = slugify(item["subject"])
        path = OUTPUT_DIR / f"{slug}.html"
        if path.exists():
            print(f"  ✓ Skip (exists): {slug}.html")
            continue
        print(f"  ⟳ Generating: {item['subject']} [{item['type']}]...")
        try:
            body = generate_article_html(item)
            page = wrap_page(item, body)
            path.write_text(page, encoding="utf-8")
            print(f"  ✓ Saved: {path}")
        except Exception as e:
            print(f"  ✗ Error: {e}")
    print("\nDone. Deploy /drone-authority/ to Netlify.")


if __name__ == "__main__":
    run()
