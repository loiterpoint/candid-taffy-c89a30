/* Loiter Point — global mobile navigation.
   Self-injecting: adds a hamburger + full-screen jump menu on phones (<=768px),
   and renders one canonical nav bar (see TOPNAV) on every page.
   Load once per page with:  <script src="/nav.js" defer></script>
   Uses the site's existing CSS variables, so it inherits the dark/lime theme. */
(function () {
  var LINKS = [
{ ic: "🚁", label: "Drones & Aerial", href: "/drones/", ct: "13" },
{ ic: "🎧", label: "Headphones & Audio", href: "/audio/", ct: "8" },
{ ic: "🏠", label: "Home & Cleaning", href: "/home-tech/", ct: "10" },
{ ic: "🍳", label: "Kitchen", href: "/kitchen/", ct: "3" },
{ ic: "🚗", label: "Automotive", href: "/automotive/", ct: "2" },
{ ic: "⌨️", label: "Computing & Desk", href: "/computing/", ct: "15" },
{ ic: "📶", label: "Networking", href: "/networking/", ct: "2" },
{ ic: "📱", label: "Tablets & Wearables", href: "/mobile-tech/", ct: "6" },
{ ic: "💡", label: "Smart Home", href: "/smart-home/", ct: "6" },
{ ic: "🔋", label: "Power & Charging", href: "/power/", ct: "4" },
{ ic: "📺", label: "TVs & Streaming", href: "/streaming/", ct: "4" },
{ ic: "🔥", label: "Today's Deals", href: "/deals.html", ct: "↗" }
];

  // Canonical desktop nav, rendered identically on every page. Before this,
  // the site had 25 different nav variants — category lists on 11 pages, bare
  // back-links on ~50 articles ("← All reviews", "← back to reviews", and 16
  // other wordings), a lone wordmark on deals.html, nothing at all on 30.
  // Edit this array to change the nav sitewide.
  var TOPNAV = [
    { label: "Home", href: "/" },
    { label: "Deals", href: "/deals.html" },
    { label: "Buyer Guides", href: "/guides/" },
    { label: "Compare", href: "/articles/mini-4-pro-vs-air-3.html" }
  ];

  var css = [
    "#lpBurger{display:none;position:fixed;top:11px;right:14px;z-index:1000;width:40px;height:40px;align-items:center;justify-content:center;background:var(--surface,#141418);border:1px solid var(--border,#26262e);border-radius:8px;color:var(--text,#e2e2e8);cursor:pointer;padding:0;}",
    "#lpBurger svg{width:20px;height:20px;}",
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
    "#lpMenu a.lp-row.lp-acct-row{background:rgba(232,255,71,0.07);margin:0 -16px;padding-left:16px;padding-right:16px;}",
    "#lpMenu a.lp-row.lp-acct-row .ic{color:var(--accent,#e8ff47);}",
    ".lp-signout{background:transparent;border:1px solid var(--border,#26262e);color:var(--muted,#7a7a8a);font-family:'Inter',sans-serif;font-size:0.8rem;font-weight:600;padding:4px 11px;border-radius:5px;cursor:pointer;line-height:1.4;}",
    ".lp-signout:hover{color:var(--text,#e2e2e8);border-color:var(--muted,#7a7a8a);}",
    "#lpMenu .lp-signout-row{display:block;width:100%;text-align:center;background:transparent;border:1px solid var(--border,#26262e);border-radius:8px;color:var(--muted,#7a7a8a);font-family:'Inter',sans-serif;font-size:15px;font-weight:600;padding:13px;margin-top:10px;cursor:pointer;}",
    "#lpMenu .lp-signout-row:hover{color:var(--text,#e2e2e8);}"
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
      row.innerHTML = '<span class="ic">\uD83D\uDC64</span>Account<span class="ct">\u2197</span>';
      menuBody.insertBefore(row, menuBody.firstChild);
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

    var rows = LINKS.map(function (l) {
      return '<a class="lp-row" href="' + l.href + '"><span class="ic">' + l.ic + '</span>' + l.label + '<span class="ct">' + l.ct + '</span></a>';
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
