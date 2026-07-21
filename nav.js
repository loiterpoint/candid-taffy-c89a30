/* Idempotency guard: some pages include nav.js twice, which previously
   rendered two hamburgers/menus. Run the whole script only once. */
if (!window.__lpNavInit) {
  window.__lpNavInit = true;

/* Loiter Point — global navigation + footer.
   Self-injecting: adds a hamburger + full-screen jump menu on phones (<=768px),
   renders one canonical nav bar (see TOPNAV) on every page, and renders one
   canonical footer (see FOOTER) at the bottom of every page.
   Load once per page with:  <script src="/nav.js" defer></script>
   Uses the site's existing CSS variables, so it inherits the dark/lime theme.
   Build marker: nav-2026-07-20b (TOPNAV bar + FOOTER + mobile back-to-top). */
(function () {
  // Canonical desktop nav, rendered identically on every page. Before this,
  // the site had 25 different nav variants — category lists on 11 pages, bare
  // back-links on ~50 articles ("← All reviews", "← back to reviews", and 16
  // other wordings), a lone wordmark on deals.html, nothing at all on 30.
  // Edit this array to change the nav sitewide.
  var TOPNAV = [
    { label: "Home", href: "/" },
    { label: "Deals", href: "/deals.html" },
    { label: "Buyer Guides", href: "/guides/" },
    { label: "Short List", href: "/short-list.html" },
    { label: "Rated vs. Real", href: "/rated-vs-real.html" },
    { label: "Don't Buy Yet", href: "/dont-buy-yet.html" },
    { label: "Categories", href: "/site-map.html" }
  ];

  // Canonical footer, rendered identically on every page (existing and future).
  // nav.js owns the footer outright: each page's own <footer> is removed and
  // replaced with this one, so it can never drift. Edit these arrays to change
  // the footer sitewide. Keep "Popular Guides" pointed at evergreen guides so it
  // does not go stale as new articles are added.
  var FOOTER = {
    tagline: "Independent tech coverage based on published testing and owner reports. No sponsored reviews, no brand deals on our scores.",
    guides: [
      { label: "Best Drones for Beginners", href: "/articles/best-drones-for-beginners.html" },
      { label: "Best Wireless Earbuds Under $100", href: "/articles/best-wireless-earbuds-under-100.html" },
      { label: "Best Robot Vacuums", href: "/articles/best-robot-vacuums-2024.html" },
      { label: "Best Smart Bulbs", href: "/articles/best-smart-bulbs.html" },
      { label: "Best Portable Power Stations", href: "/articles/best-portable-power-stations.html" }
    ],
    site: [
      { label: "About", href: "/about.html" },
      { label: "How We Score", href: "/methodology.html" },
      { label: "Affiliate Disclosure", href: "/affiliate-disclosure.html" },
      { label: "Privacy Policy", href: "/privacy-policy.html" },
      { label: "Terms of Service", href: "/terms.html" }
    ],
    copyright: "© 2026 Loiter Point. All rights reserved.",
    disclosure: "Loiter Point participates in the Amazon Associates program and other affiliate programs. We may earn a commission when you click through and purchase — at no extra cost to you. Affiliate relationships never influence our review scores or editorial decisions."
  };

  var css = [
    "#lpBurger{display:none;position:fixed;top:11px;right:14px;z-index:1000;width:40px;height:40px;align-items:center;justify-content:center;background:var(--surface,#141418);border:1px solid var(--border,#26262e);border-radius:8px;color:var(--text,#e2e2e8);cursor:pointer;padding:0;}",
    "#lpBurger svg{width:20px;height:20px;}",
    // Wide comparison tables were overflowing the page on phones, which pushed
    // the fixed hamburger off-screen to the right. Let any table scroll inside
    // its own box instead of stretching the page wider than the screen.
    "table{display:block;overflow-x:auto;max-width:100%;-webkit-overflow-scrolling:touch;}",
    "#lpMenu{display:none;position:fixed;inset:0;z-index:1001;background:rgba(12,12,14,0.985);overflow-y:auto;font-family:'Inter',sans-serif;}",
    "#lpMenu.open{display:block;}",
    "#lpMenu .lp-top{display:flex;align-items:center;justify-content:space-between;padding:13px 16px;border-bottom:1px solid var(--border,#26262e);}",
    "#lpMenu .lp-logo{display:flex;align-items:center;gap:8px;font-weight:800;font-size:15px;color:var(--text,#e2e2e8);}",
    "#lpMenu .lp-logo i{width:24px;height:24px;background:var(--accent,#e8ff47);color:#000;border-radius:6px;display:flex;align-items:center;justify-content:center;font-style:normal;}",
    "#lpMenu .lp-logo b{color:var(--accent,#e8ff47);font-weight:800;}",
    "#lpMenu .lp-x{background:transparent;border:1px solid var(--border,#26262e);border-radius:8px;width:38px;height:38px;color:var(--text,#e2e2e8);font-size:19px;line-height:1;cursor:pointer;}",
    "#lpMenu .lp-body{padding:6px 16px 44px;}",
    "#lpMenu a.lp-row{display:flex;align-items:center;gap:12px;padding:15px 4px;border-bottom:1px solid var(--border,#26262e);font-size:16px;font-weight:600;color:var(--text,#e2e2e8);text-decoration:none;}",
    "#lpMenu a.lp-row .ic{font-size:18px;}",
    "#lpMenu a.lp-row .ct{margin-left:auto;font-family:var(--mono,monospace);font-size:12px;color:var(--muted,#7a7a8a);}",
    "#lpMenu a.lp-cta{display:block;text-align:center;margin-top:18px;background:var(--accent,#e8ff47);color:#000;font-weight:700;padding:14px;border-radius:8px;font-size:15px;text-decoration:none;}",
    "@media(max-width:768px){#lpBurger{display:flex;}}",
    ".lp-acct{color:#0c0c0e;background:var(--accent,#e8ff47);font-size:0.8rem;font-weight:700;padding:5px 12px;border-radius:5px;line-height:1.4;}",
    ".lp-acct:hover{opacity:0.88;}",
    ".lp-navlinks-fallback{display:flex;align-items:center;gap:10px;}",
    "#lpSynthNav{display:flex;align-items:center;justify-content:space-between;padding:1rem 2rem;border-bottom:1px solid var(--border,#26262e);position:sticky;top:0;background:rgba(12,12,14,0.97);z-index:100;font-family:'Inter',sans-serif;}",
    "#lpSynthNav .lp-mark{display:flex;align-items:center;gap:0.6rem;font-size:1rem;font-weight:800;color:var(--text,#e2e2e8);text-decoration:none;letter-spacing:-0.02em;}",
    "#lpSynthNav .lp-mark i{width:28px;height:28px;background:var(--accent,#e8ff47);color:#000;border-radius:6px;display:flex;align-items:center;justify-content:center;font-style:normal;font-size:0.9rem;}",
    "#lpSynthNav .lp-mark b{color:var(--accent,#e8ff47);font-weight:800;}",
    "#lpSynthNav .lp-right{display:flex;align-items:center;gap:1.6rem;}",
    "#lpSynthNav .lp-right a.lp-top{color:var(--muted,#7a7a8a);font-size:0.875rem;font-weight:500;text-decoration:none;transition:color .15s;}",
    "#lpSynthNav .lp-right a.lp-top:hover{color:var(--text,#e2e2e8);}",
    "@media(max-width:900px){#lpSynthNav .lp-right a.lp-top{display:none;}}",
    "@media(max-width:768px){#lpSynthNav{padding:1rem 1.25rem;}}",
    // On phones the fixed hamburger overlaps the top bar's right edge. The
    // account/sign-out controls also live in the mobile overlay menu, so hide
    // the desktop-bar copies here rather than let them collide with the burger.
    "@media(max-width:768px){#lpSynthNav .lp-acct,#lpSynthNav .lp-signout{display:none;}}",
    "#lpMenu a.lp-row.lp-acct-row{background:rgba(232,255,71,0.07);margin:0 -16px;padding-left:16px;padding-right:16px;}",
    "#lpMenu a.lp-row.lp-acct-row .ic{color:var(--accent,#e8ff47);}",
    ".lp-signout{background:transparent;border:1px solid var(--border,#26262e);color:var(--muted,#7a7a8a);font-family:'Inter',sans-serif;font-size:0.8rem;font-weight:600;padding:4px 11px;border-radius:5px;cursor:pointer;line-height:1.4;}",
    ".lp-signout:hover{color:var(--text,#e2e2e8);border-color:var(--muted,#7a7a8a);}",
    "#lpMenu .lp-signout-row{display:block;width:100%;text-align:center;background:transparent;border:1px solid var(--border,#26262e);border-radius:8px;color:var(--muted,#7a7a8a);font-family:'Inter',sans-serif;font-size:15px;font-weight:600;padding:13px;margin-top:10px;cursor:pointer;}",
    "#lpMenu .lp-signout-row:hover{color:var(--text,#e2e2e8);}",
    // Canonical footer (see synthesizeFooter). Scoped under #lpFooter with its
    // own classes so it never depends on — or collides with — a page's own
    // .footer-* styles. Three content-width columns, evenly distributed.
    "#lpFooter{border-top:1px solid var(--border,#26262e);background:var(--bg,#0c0c0e);padding:2.5rem 2rem 2rem;margin-top:2rem;font-family:'Inter',sans-serif;line-height:1.6;}",
    "#lpFooter a{text-decoration:none;color:inherit;}",
    "#lpFooter .lpf-inner{max-width:1040px;margin:0 auto;display:grid;grid-template-columns:auto auto auto;justify-content:space-between;column-gap:3rem;row-gap:2rem;align-items:start;}",
    "#lpFooter .lpf-brand{max-width:360px;}",
    "#lpFooter .lpf-mark{display:flex;align-items:center;gap:0.6rem;font-size:1rem;font-weight:800;color:var(--text,#e2e2e8);letter-spacing:-0.02em;}",
    "#lpFooter .lpf-mark i{width:28px;height:28px;background:var(--accent,#e8ff47);color:#000;border-radius:6px;display:flex;align-items:center;justify-content:center;font-style:normal;font-size:0.9rem;}",
    "#lpFooter .lpf-mark b{color:var(--accent,#e8ff47);font-weight:800;}",
    "#lpFooter .lpf-brand p{font-size:0.8rem;color:var(--muted,#7a7a8a);margin-top:0.6rem;line-height:1.6;}",
    "#lpFooter .lpf-col h4{font-size:0.75rem;font-weight:600;text-transform:uppercase;letter-spacing:0.05em;color:var(--muted,#7a7a8a);margin-bottom:0.75rem;}",
    "#lpFooter .lpf-col a{display:block;font-size:0.85rem;color:var(--muted,#7a7a8a);margin-bottom:0.45rem;transition:color .15s;}",
    "#lpFooter .lpf-col a:hover{color:var(--text,#e2e2e8);}",
    "#lpFooter .lpf-bottom{max-width:1040px;margin:1.75rem auto 0;padding-top:1.5rem;border-top:1px solid var(--border,#26262e);display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:1rem;}",
    "#lpFooter .lpf-bottom p{font-size:0.75rem;color:var(--muted,#7a7a8a);}",
    "#lpFooter .lpf-bottom .lpf-disc{opacity:0.7;max-width:520px;line-height:1.5;font-size:0.72rem;}",
    "@media(max-width:760px){#lpFooter .lpf-inner{grid-template-columns:1fr 1fr;justify-content:normal;column-gap:2rem;row-gap:1.75rem;}#lpFooter .lpf-brand{grid-column:1 / -1;max-width:none;}}",
    "@media(max-width:460px){#lpFooter .lpf-inner{grid-template-columns:1fr;}}",
    // Back-to-top button (see build). Mobile-only: display:none on desktop where
    // the sticky nav already covers this; on phones it fades in past ~600px of
    // scroll. Bottom-right so it never collides with the top-right hamburger.
    "#lpTop{position:fixed;bottom:18px;right:16px;z-index:999;width:46px;height:46px;border-radius:50%;background:var(--surface,#141418);border:1px solid var(--border,#26262e);color:var(--accent,#e8ff47);display:none;align-items:center;justify-content:center;cursor:pointer;padding:0;box-shadow:0 6px 18px rgba(0,0,0,0.45);opacity:0;transform:translateY(10px);pointer-events:none;transition:opacity .22s ease,transform .22s ease,border-color .15s;-webkit-tap-highlight-color:transparent;}",
    "#lpTop svg{width:20px;height:20px;}",
    "#lpTop:hover{border-color:var(--accent,#e8ff47);}",
    "#lpTop.lp-show{opacity:1;transform:translateY(0);pointer-events:auto;}",
    "@media(max-width:768px){#lpTop{display:flex;}}",
    "@media(prefers-reduced-motion:reduce){#lpTop{transition:none;}}"
  ].join("");

  // Removes the hardcoded "Evidence-first" nav tag wherever it appears.
  // Matches on TEXT, not on the class: dji-mini-5-pro-review.html uses
  // <span class="nav-tag">FULL REVIEW</span> for something unrelated, and a
  // class-based selector would silently eat it.
  function retireEvidenceTag() {
    Array.prototype.forEach.call(document.querySelectorAll(".nav-tag"), function (el) {
      if (el.textContent.trim().toLowerCase() === "evidence-first") {
        el.parentNode.removeChild(el);
      }
    });
  }

  // Account link: appended to the desktop nav, and inserted as the first row
  // of the mobile overlay (it is the only non-category item).
  // Where the desktop account controls go. index.html and the article pages
  // have a .nav-links div; deals.html uses a different shell (nav.topnav with
  // only a sitemark) and has none. Rather than edit deals.html — which AGENTS.md
  // assigns to the deal-radar task — create a holder inside whatever nav exists.
  // .topnav .wrap is already flex with space-between, so it lands on the right.
  // 30 pages (15 guides, 15 articles) have no <nav> element at all — they have
  // never had site navigation, which is a bigger problem than the account link.
  // Build a minimal one rather than leaving them orphaned.
  // nav.js owns the bar outright: the page's own <nav> is removed and replaced
  // with one canonical bar. Editing 110 pages into agreement was never going to
  // hold — the next generated article would drift again.
  function synthesizeNav() {
    var existing = document.getElementById("lpSynthNav");
    if (existing) return existing;

    Array.prototype.forEach.call(document.querySelectorAll("nav"), function (el) {
      if (el.id !== "lpSynthNav" && el.parentNode) el.parentNode.removeChild(el);
    });

    var links = TOPNAV.map(function (l) {
      return '<a class="lp-top" href="' + l.href + '">' + l.label + '</a>';
    }).join("");

    var bar = document.createElement("nav");
    bar.id = "lpSynthNav";
    bar.innerHTML =
      '<a class="lp-mark" href="/"><i>&#8853;</i>Loiter<b>Point</b></a>' +
      '<div class="lp-right nav-links">' + links + '</div>';
    document.body.insertBefore(bar, document.body.firstChild);
    return bar;
  }

  function navLinksHost() {
    var bar = synthesizeNav();
    return bar ? bar.querySelector(".lp-right") : null;
  }

  function addAccountLink(menuBody) {
    var navLinks = navLinksHost();
    if (navLinks && !navLinks.querySelector(".lp-acct")) {
      var a = document.createElement("a");
      a.className = "lp-acct";
      a.href = "/account.html";
      a.textContent = "Account";
      navLinks.appendChild(a);
    }
    if (menuBody && !menuBody.querySelector(".lp-acct-row")) {
      var row = document.createElement("a");
      row.className = "lp-row lp-acct-row";
      row.href = "/account.html";
      row.textContent = "Account";
      // Place Account after the nav rows (before the site-map CTA), matching
      // the desktop bar where Account sits at the end.
      var acctCta = menuBody.querySelector(".lp-cta");
      menuBody.insertBefore(row, acctCta || menuBody.firstChild);
    }

    maybeAddSignOut(menuBody);
  }

  // Sitewide sign-out, without making every anonymous visitor download the
  // Firebase SDK.
  //
  // account.html sets localStorage "lp_auth" on sign-in and clears it on
  // sign-out. Reading that is free and needs no SDK, so logged-out traffic
  // (nearly all of it) pays nothing.
  //
  // Deliberately NOT reading Firebase's own persistence: it lives in IndexedDB,
  // the schema is internal, and reading it is async. An earlier version of this
  // checked for a "firebase:authUser:" localStorage key, which does not exist
  // in current SDK versions — the button silently never appeared.
  //
  // The flag means "probably signed in", not proof; it can be stale if the
  // token was revoked. onAuthStateChanged below is the authority, and clears
  // the flag if it disagrees.
  var menuBodyRef = null;

  function maybeAddSignOut(menuBody) {
    try {
      if (localStorage.getItem("lp_auth") !== "1") return;
    } catch (e) { return; }

    var navLinks = navLinksHost();
    var deskBtn = null;
    if (navLinks && !navLinks.querySelector(".lp-signout")) {
      deskBtn = document.createElement("button");
      deskBtn.className = "lp-signout";
      deskBtn.type = "button";
      deskBtn.textContent = "Sign out";
      deskBtn.disabled = true;
      navLinks.appendChild(deskBtn);
    }

    var menuBtn = null;
    if (menuBody && !menuBody.querySelector(".lp-signout-row")) {
      menuBtn = document.createElement("button");
      menuBtn.className = "lp-signout-row";
      menuBtn.type = "button";
      menuBtn.textContent = "Sign out";
      menuBtn.disabled = true;
      // Appended last, below the site-map CTA. Sign out is destructive and the
      // menu is opened constantly for browsing — keeping it away from the
      // category rows avoids thumb-slip sign-outs.
      menuBody.appendChild(menuBtn);
    }

    var V = "https://www.gstatic.com/firebasejs/12.16.0/";
    Promise.all([import(V + "firebase-app.js"), import(V + "firebase-auth.js")])
      .then(function (mods) {
        // account.html already creates the default app. Calling initializeApp
        // again there throws "duplicate-app" unless the options match exactly,
        // so reuse whatever exists and only create one if there is none.
        var appMod = mods[0];
        var app = appMod.getApps().length
          ? appMod.getApp()
          : appMod.initializeApp({
              apiKey: "AIzaSyBK0BtlKD1ye06vqlZQbLC_oLepD_z9hS4",
              authDomain: "loiterpoint.firebaseapp.com",
              projectId: "loiterpoint",
              storageBucket: "loiterpoint.firebasestorage.app",
              messagingSenderId: "720833786375",
              appId: "1:720833786375:web:5a064020a9ccef596ab0a2",
              measurementId: "G-4B11NT8CR4"
            });
        var authMod = mods[1];
        var auth = authMod.getAuth(app);

        function remove(el) { if (el && el.parentNode) el.parentNode.removeChild(el); }

        authMod.onAuthStateChanged(auth, function (user) {
          if (!user) {
            try { localStorage.removeItem("lp_auth"); } catch (e) {}
            remove(deskBtn); remove(menuBtn);
            return;
          }
          [deskBtn, menuBtn].forEach(function (b) {
            if (!b) return;
            b.disabled = false;
            b.title = "Signed in as " + user.email;
            b.onclick = function () {
              b.disabled = true;
              b.textContent = "Signing out\u2026";
              authMod.signOut(auth).then(function () {
                try { localStorage.removeItem("lp_auth"); } catch (e) {}
                location.reload();
              });
            };
          });
        });
      })
      .catch(function (err) {
        // Offline or CDN blocked. Leave the buttons out rather than showing
        // a control that silently does nothing.
        console.warn("Sign-out unavailable:", err);
        if (deskBtn && deskBtn.parentNode) deskBtn.parentNode.removeChild(deskBtn);
        if (menuBtn && menuBtn.parentNode) menuBtn.parentNode.removeChild(menuBtn);
      });
  }

  // nav.js owns the footer outright, same as the nav bar: remove the page's own
  // <footer> (and a divider immediately above it, so the border-top doesn't
  // double up) and append one canonical footer. Pages that never had a footer
  // get one too. check_surfaced.py reads the static HTML, not this runtime DOM,
  // so removing per-page footer link lists here does not affect surfacing.
  function synthesizeFooter() {
    if (document.getElementById("lpFooter")) return;

    Array.prototype.forEach.call(document.querySelectorAll("footer"), function (el) {
      if (el.id === "lpFooter") return;
      var prev = el.previousElementSibling;
      if (prev && prev.tagName === "HR" &&
          (prev.className || "").indexOf("divider") !== -1 && prev.parentNode) {
        prev.parentNode.removeChild(prev);
      }
      if (el.parentNode) el.parentNode.removeChild(el);
    });

    function linkList(items) {
      return items.map(function (l) {
        return '<a href="' + l.href + '">' + l.label + '</a>';
      }).join("");
    }

    var f = document.createElement("footer");
    f.id = "lpFooter";
    f.innerHTML =
      '<div class="lpf-inner">' +
        '<div class="lpf-brand">' +
          '<a class="lpf-mark" href="/"><i>&#8853;</i>Loiter<b>Point</b></a>' +
          '<p>' + FOOTER.tagline + '</p>' +
        '</div>' +
        '<div class="lpf-col"><h4>Popular Guides</h4>' + linkList(FOOTER.guides) + '</div>' +
        '<div class="lpf-col"><h4>Site</h4>' + linkList(FOOTER.site) + '</div>' +
      '</div>' +
      '<div class="lpf-bottom">' +
        '<p>' + FOOTER.copyright + '</p>' +
        '<p class="lpf-disc">' + FOOTER.disclosure + '</p>' +
      '</div>';
    document.body.appendChild(f);
    return f;
  }

  function build() {
    var style = document.createElement("style");
    style.textContent = css;
    document.head.appendChild(style);

    var burger = document.createElement("button");
    burger.id = "lpBurger";
    burger.setAttribute("aria-label", "Open menu");
    burger.setAttribute("aria-expanded", "false");
    burger.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/></svg>';
    document.body.appendChild(burger);

    // Belt-and-suspenders: also toggle the burger by viewport width in JS, so
    // it still appears on narrow screens even if the CSS media query is
    // overridden by page styles or a stale cached stylesheet.
    function syncBurger() {
      burger.style.display = (window.innerWidth <= 768) ? "flex" : "none";
    }
    syncBurger();
    window.addEventListener("resize", syncBurger);

    // Mobile menu mirrors the desktop bar (TOPNAV) rather than listing every
    // category — the two navs were showing different things, which read as a
    // bug. Categories are still reachable via Buyer Guides and the site map.
    var rows = TOPNAV.map(function (l) {
      return '<a class="lp-row" href="' + l.href + '">' + l.label + '</a>';
    }).join("");

    var menu = document.createElement("div");
    menu.id = "lpMenu";
    menu.innerHTML =
      '<div class="lp-top"><a class="lp-logo" href="/"><i>⊕</i>Loiter<b>Point</b></a>' +
      '<button class="lp-x" aria-label="Close menu">✕</button></div>' +
      '<div class="lp-body">' + rows +
      '<a class="lp-cta" href="/site-map.html">View full site map →</a></div>';
    document.body.appendChild(menu);

    function setOpen(open) {
      menu.classList.toggle("open", open);
      burger.setAttribute("aria-expanded", open ? "true" : "false");
      document.body.style.overflow = open ? "hidden" : "";
    }
    burger.addEventListener("click", function () { setOpen(!menu.classList.contains("open")); });
    menu.querySelector(".lp-x").addEventListener("click", function () { setOpen(false); });
    // Close the overlay on any link tap — same-page hash jumps don't reload,
    // so without this the menu stays open and body scrolling stays locked.
    Array.prototype.forEach.call(menu.querySelectorAll("a"), function (a) {
      a.addEventListener("click", function () { setOpen(false); });
    });

    retireEvidenceTag();
    synthesizeFooter();

    // Back-to-top: CSS keeps it display:none above 768px, so this only ever
    // shows on mobile. Reveal it past ~600px of scroll; smooth-scroll on tap
    // unless the visitor prefers reduced motion.
    var toTop = document.createElement("button");
    toTop.id = "lpTop";
    toTop.type = "button";
    toTop.setAttribute("aria-label", "Back to top");
    toTop.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="19" x2="12" y2="6"/><polyline points="6 11 12 5 18 11"/></svg>';
    document.body.appendChild(toTop);
    var lpReduceMotion = false;
    try { lpReduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches; } catch (e) {}
    function syncToTop() {
      var y = window.pageYOffset || document.documentElement.scrollTop || 0;
      toTop.classList.toggle("lp-show", y > 600);
    }
    window.addEventListener("scroll", syncToTop, { passive: true });
    syncToTop();
    toTop.addEventListener("click", function () {
      window.scrollTo({ top: 0, behavior: lpReduceMotion ? "auto" : "smooth" });
    });

    menuBodyRef = menu.querySelector(".lp-body");
    addAccountLink(menuBodyRef);

    // account.html calls this after sign-in so the Sign out button appears
    // straight away instead of only after the next page load.
    window.lpAuthChanged = function () { maybeAddSignOut(menuBodyRef); };
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", build);
  } else {
    build();
  }
})();

}
