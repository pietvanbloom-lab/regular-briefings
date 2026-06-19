/* Shared enhancement for every AI Brief page: light/dark theme, sticky topbar,
   jump-to-section nav, and prev/next archive navigation. Self-contained, no deps. */
(function () {
  "use strict";
  // Cloudflare Web Analytics (cookieless) for every brief page.
  (function () { var cf = document.createElement("script"); cf.defer = true;
    cf.src = "https://static.cloudflareinsights.com/beacon.min.js";
    cf.setAttribute("data-cf-beacon", '{"token": "497e5edd8f4a4b1e96619f0f85da49fc"}'); document.head.appendChild(cf); })();

  var ACCENT_KEY = "brief-theme";
  // Location-aware base: brief pages may live at site root (latest) or under /briefs/.
  var IN_BRIEFS = /\/briefs\//.test(location.pathname);
  var ROOT = IN_BRIEFS ? "../" : "./";
  var HUB = ROOT + "archive.html";

  // 1) Inject theme + topbar styles (briefs share the same CSS variable names).
  var css = document.createElement("style");
  css.textContent =
    'html[data-theme="light"]{--bg:#f6f5f2;--panel:#ffffff;--panel2:#efede8;--text:#1c1e24;' +
    '--mute:#6a7079;--line:#e2ded6;--accent:#b3741f;--accent2:#2f6fb0;--tag-bg:#eceae4;}' +
    'html,body{transition:background .25s ease,color .25s ease;}' +
    // Light-mode fixes for brief colors hardcoded for dark backgrounds:
    'html[data-theme=\"light\"] .bucket .item p{color:#353a42;}' +
    'html[data-theme=\"light\"] h1,html[data-theme=\"light\"] .card h3,html[data-theme=\"light\"] .item h4,' +
    'html[data-theme=\"light\"] .upcoming-list li strong,html[data-theme=\"light\"] .rumors-list li strong{color:#1c1e24;}' +
    'html[data-theme=\"light\"] a:hover{color:#2f6fb0;}' +
    '.bx-bar{position:sticky;top:0;z-index:60;background:color-mix(in srgb,var(--bg) 86%,transparent);' +
    'backdrop-filter:blur(10px);border-bottom:1px solid var(--line);}' +
    '.bx-in{max-width:980px;margin:0 auto;display:flex;align-items:center;gap:14px;padding:9px 24px;}' +
    '.bx-back{font-family:ui-monospace,monospace;font-size:12.5px;color:var(--mute);white-space:nowrap;' +
    'border:1px solid var(--line);padding:5px 11px;border-radius:7px;text-decoration:none;}' +
    '.bx-back:hover{color:var(--text);border-color:var(--accent);}' +
    '.bx-nav{flex:1;display:flex;gap:3px;flex-wrap:wrap;overflow:hidden;max-height:30px;}' +
    '.bx-nav a{color:var(--mute);font-size:12px;font-family:ui-monospace,monospace;padding:5px 9px;' +
    'border-radius:6px;text-decoration:none;white-space:nowrap;}' +
    '.bx-nav a:hover{color:var(--text);background:var(--panel);}' +
    '.bx-step{font-family:ui-monospace,monospace;font-size:13px;color:var(--mute);text-decoration:none;' +
    'border:1px solid var(--line);width:30px;height:28px;border-radius:7px;display:grid;place-items:center;}' +
    '.bx-step:hover{color:var(--text);border-color:var(--accent);}' +
    '.bx-step.off{opacity:.3;pointer-events:none;}' +
    '.bx-tog{background:var(--panel);border:1px solid var(--line);color:var(--text);width:32px;height:28px;' +
    'border-radius:7px;cursor:pointer;font-size:13px;}' +
    '.bx-tog:hover{border-color:var(--accent);}' +
    '.card,.item{scroll-margin-top:64px;}' +
    '@keyframes bxflash{0%{box-shadow:0 0 0 2px var(--accent);background:color-mix(in srgb,var(--accent) 14%,transparent);}100%{box-shadow:none;background:transparent;}}' +
    '.bx-flash{animation:bxflash 2.2s ease;border-radius:6px;}' +
    '@media(max-width:640px){.bx-nav{display:none;}}';
  document.head.appendChild(css);

  // 2) Apply saved theme.
  try { var t = localStorage.getItem(ACCENT_KEY); if (t) document.documentElement.dataset.theme = t; } catch (e) {}

  // 3) Build jump nav from the page's h2 headings.
  var heads = Array.prototype.slice.call(document.querySelectorAll(".wrap h2, .wrap > .top3"));
  var navLinks = "";
  // anchor the top3 block
  var top3 = document.querySelector(".wrap .top3");
  if (top3) { top3.id = "top3"; navLinks += '<a href="#top3">Top 3</a>'; }
  document.querySelectorAll(".wrap h2").forEach(function (h, i) {
    var id = "sec-" + i;
    h.id = id;
    var label = h.textContent.replace(/,.*$/, "").trim();
    navLinks += '<a href="#' + id + '">' + label + "</a>";
  });

  // 4) Determine back link (root archive) and current date.
  var dateMatch = (location.pathname.match(/(\d{4}-\d{2}-\d{2})/) || document.title.match(/(\d{4}-\d{2}-\d{2})/));
  var curDate = dateMatch ? dateMatch[1] : "";

  var bar = document.createElement("div");
  bar.className = "bx-bar";
  bar.innerHTML =
    '<div class="bx-in">' +
    '<a class="bx-back" href="' + HUB + '">&larr; Archive &amp; stats</a>' +
    '<nav class="bx-nav">' + navLinks + "</nav>" +
    '<a class="bx-step off" id="bx-prev" title="Previous brief">&lsaquo;</a>' +
    '<a class="bx-step off" id="bx-next" title="Next brief">&rsaquo;</a>' +
    '<button class="bx-tog" id="bx-tog" title="Toggle light and dark">◑</button>' +
    "</div>";
  document.body.insertBefore(bar, document.body.firstChild);

  // If arriving via a deep link (#aN), re-scroll past the sticky bar and flash the target.
  if (location.hash && /^#a\d+$/.test(location.hash)) {
    var tgt = document.querySelector(location.hash);
    if (tgt) {
      setTimeout(function () {
        tgt.scrollIntoView({ block: "start" });
        tgt.classList.add("bx-flash");
        setTimeout(function () { tgt.classList.remove("bx-flash"); }, 2300);
      }, 60);
    }
  }

  document.getElementById("bx-tog").onclick = function () {
    var h = document.documentElement;
    var n = h.dataset.theme === "light" ? "dark" : "light";
    h.dataset.theme = n;
    try { localStorage.setItem(ACCENT_KEY, n); } catch (e) {}
  };

  // 5) Prev/next from the archive index (degrades silently if unavailable).
  if (curDate) {
    fetch(ROOT + "data/briefs.json").then(function (r) { return r.json(); }).then(function (d) {
      var dates = d.briefs.map(function (b) { return b.date; }).sort(); // ascending
      var i = dates.indexOf(curDate);
      var prev = document.getElementById("bx-prev"), next = document.getElementById("bx-next");
      if (i > 0) { prev.href = ROOT + "briefs/" + dates[i - 1] + ".html"; prev.classList.remove("off"); prev.title = "Previous: " + dates[i - 1]; }
      if (i >= 0 && i < dates.length - 1) { next.href = ROOT + "briefs/" + dates[i + 1] + ".html"; next.classList.remove("off"); next.title = "Next: " + dates[i + 1]; }
    }).catch(function () {});
  }
})();

/* Audio-aware source links + sticky mini-player.
   Keeps the brief's audio playing when a source link is followed, and keeps the
   player reachable while scrolling. Safe no-op on briefs without an audio player. */
(function () {
  "use strict";
  var audio = document.querySelector(".listen audio");

  // Sticky mini-player: keep the audio control visible under the top bar.
  if (audio) {
    var st = document.createElement("style");
    st.textContent =
      ".listen{position:sticky;z-index:50;top:var(--bx-bar-h,46px);" +
      "box-shadow:0 6px 18px -10px rgba(0,0,0,.55);}";
    document.head.appendChild(st);
    var setOffset = function () {
      var bar = document.querySelector(".bx-bar");
      var h = bar ? Math.round(bar.getBoundingClientRect().height) : 46;
      document.documentElement.style.setProperty("--bx-bar-h", (h - 1) + "px");
    };
    setOffset();
    window.addEventListener("resize", setOffset);
  }

  // While audio is playing, open external links in a new tab so the brief tab
  // (and its audio) keeps running. Normal navigation otherwise.
  function playing() { return audio && !audio.paused && !audio.ended; }
  document.addEventListener("click", function (e) {
    if (e.defaultPrevented || e.button !== 0) return;
    if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
    var a = e.target.closest && e.target.closest("a[href]");
    if (!a) return;
    var href = a.getAttribute("href") || "";
    if (!/^https?:\/\//i.test(href)) return;          // external links only
    if (a.target === "_blank") return;                // already opens a new tab
    try { if (new URL(href).host === location.host) return; } catch (err) { return; }
    if (!playing()) return;                           // only intervene while listening
    e.preventDefault();
    window.open(href, "_blank", "noopener");
  });
})();
