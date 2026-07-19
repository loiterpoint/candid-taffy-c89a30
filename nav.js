/* Loiter Point — global mobile navigation.
   Self-injecting: adds a hamburger + full-screen jump menu on phones (<=768px),
   and appends a "Site Map" link to the desktop nav where one exists.
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
    ".lp-map-desktop{color:var(--muted,#7a7a8a);font-size:0.875rem;font-weight:500;}",
    ".lp-map-desktop:hover{color:var(--text,#e2e2e8);}",
    "@media(max-width:768px){#lpBurger{display:flex;} .nav-tag{display:none!important;}}"
  ].join("");

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

    var navLinks = document.querySelector(".nav-links");
    if (navLinks && !navLinks.querySelector('a[href*="site-map"]')) {
      var a = document.createElement("a");
      a.className = "lp-map-desktop";
      a.href = "/site-map.html";
      a.textContent = "Site Map";
      navLinks.appendChild(a);
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", build);
  } else {
    build();
  }
})();
