/* ============================================================
   World Cup Scorers — Redesign · interactions
   ============================================================ */
(function () {
  "use strict";
  var D = window.WCS;
  var players = D.players, order = D.order, walk = D.walk, MAXG = D.maxGoals;
  var reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;

  var TIERS = ["elite", "strong", "mid", "weak"];
  var TIER_LABEL = { elite: "Elite", strong: "Strong", mid: "Mid", weak: "Weak" };
  var TIER_NOTE = { elite: "top quarter", weak: "bottom quarter" };

  var ICONS = {
    wc: '<svg viewBox="0 0 24 24"><path d="M7 3v2H4v3a4 4 0 0 0 4 4h.2A5 5 0 0 0 11 14.9V17H8v2h8v-2h-3v-2.1a5 5 0 0 0 2.8-2.9H16a4 4 0 0 0 4-4V5h-3V3H7zM6 7v2.7A2 2 0 0 1 4.6 8 2 2 0 0 1 4 7h2zm12 0h2a2 2 0 0 1-.6 1A2 2 0 0 1 18 9.7V7z"/></svg>',
    ball: '<svg viewBox="0 0 24 24"><circle cx="12" cy="8.4" r="5.4" fill="none" stroke="currentColor" stroke-width="1.6"/><path d="M12 5.3l2.4 1.7-.9 2.8h-3L9.6 7z"/><path d="M11 14h2v2.1h3V18H8v-1.9h3z"/></svg>',
    boot: '<svg viewBox="0 0 24 24"><path d="M3 7c.2 1.8.5 3.8 1 4.8.4.8 1.1 1.2 2.6 1.2H19a2 2 0 0 1 2 2v1.2H4.3A1.3 1.3 0 0 1 3 16V7z"/></svg>'
  };
  var ACC_LABEL = { wc: "World Cup", ball: "Golden Ball", boot: "Golden Boot" };

  function el(tag, cls, html) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (html != null) e.innerHTML = html;
    return e;
  }
  function yearsStr(p) { return p.years[0] === p.years[1] ? "" + p.years[0] : p.years[0] + "–" + p.years[1]; }
  function ease(t) { return 1 - Math.pow(1 - t, 3); }

  /* ---- count-up (rAF animation + guaranteed final value if rAF is throttled) ---- */
  function countUp(node, target, opts) {
    opts = opts || {};
    var suffix = opts.suffix || "";
    var dur = reduce ? 0 : (opts.dur || 900);
    if (dur === 0) { node.textContent = target + suffix; return; }
    var start = null, done = false;
    function finish() { if (done) return; done = true; node.textContent = target + suffix; }
    function step(now) {
      if (start === null) start = now;
      var t = Math.min(1, (now - start) / dur);
      node.textContent = Math.round(ease(t) * target) + suffix;
      if (t < 1) requestAnimationFrame(step); else finish();
    }
    requestAnimationFrame(step);
    setTimeout(finish, dur + 140);
  }

  /* ---- reveal on scroll (rAF check — robust across environments) ---- */
  var revItems = [].slice.call(document.querySelectorAll(".reveal"));
  function fireReveal(t) {
    t.classList.add("in");
    t.querySelectorAll("[data-count]").forEach(function (c) { countUp(c, +c.dataset.count, { dur: 1100 }); });
    if (t.dataset.count) countUp(t, +t.dataset.count, { dur: 1100 });
  }
  function revealCheck() {
    var vh = innerHeight;
    revItems = revItems.filter(function (t) {
      var r = t.getBoundingClientRect();
      if (r.top < vh * 0.88 && r.bottom > 0) { fireReveal(t); return false; }
      return true;
    });
  }
  addEventListener("scroll", revealCheck, { passive: true });
  addEventListener("resize", revealCheck);
  revealCheck();
  requestAnimationFrame(revealCheck);
  setTimeout(revealCheck, 200);

  /* ---- hero legend ---- */
  (function () {
    var wrap = document.getElementById("heroLegend");
    TIERS.forEach(function (t) {
      var note = TIER_NOTE[t] ? '<small>' + TIER_NOTE[t] + '</small>' : "";
      var key = el("a", "tier-key",
        '<i style="background:var(--' + t + ')"></i>' + TIER_LABEL[t] + " " + note);
      key.href = "#g-tier";                         // tier chips reference the tier definition
      wrap.appendChild(key);
    });
  })();

  /* ---- accolade markup ---- */
  function accHTML(acc) {
    if (!acc) return "";
    return ["wc", "ball", "boot"].map(function (k) {
      var yrs = acc[k] || [];
      if (!yrs.length) return "";
      var lab = ACC_LABEL[k] + " — " + yrs.join(", ");   // e.g. "Golden Ball — 2014, 2022"
      return '<span class="acc-pill" tabindex="0" role="img" aria-label="' + lab +
        '" data-acctip="' + lab + '">' + ICONS[k] + " ×" + yrs.length + "</span>";
    }).join("");
  }

  /* ---- tier bar segments (scene) ---- */
  function tierSegs(p) {
    var html = "";
    TIERS.forEach(function (t, i) {
      var c = p.tiers[t]; if (!c) return;
      html += '<div class="tseg tseg-' + t + '" data-tier="' + t + '" style="flex-grow:' + c +
        ';transition-delay:' + (0.15 + i * 0.12) + 's"><span class="c">' + c + "</span></div>";
    });
    return html;
  }
  function tierLegend(p) {
    return TIERS.map(function (t) {
      return '<span><i style="background:var(--' + t + ')"></i>' + p.tiers[t] + " " + TIER_LABEL[t].toLowerCase() + "</span>";
    }).join("");
  }

  /* ============================================================
     WALKTHROUGH SHOWCASE
     ============================================================ */
  var scenesWrap = document.getElementById("scenes");
  var railWrap = document.getElementById("rail");
  var scroller = document.getElementById("scroller");
  var N = walk.length;

  walk.forEach(function (name, idx) {
    var p = players[name];
    var elite = Math.round(p.eliteShare * 100);
    var scene = el("article", "scene");
    scene.dataset.idx = idx;
    scene.innerHTML =
      '<div class="scene-rank">' + (idx + 1) + '</div>' +
      '<div class="scene-photo-wrap">' +
        '<img class="scene-photo" src="' + p.photo + '" alt="' + name + '" loading="lazy">' +
        '<div class="scene-photo-tag">' + p.country + ' · ' + yearsStr(p) + '</div>' +
        '<div class="scene-accolades">' + accHTML(p.acc) + '</div>' +
      '</div>' +
      '<div class="scene-info">' +
        '<div class="scene-nation">' + p.country + '</div>' +
        '<h3 class="scene-name">' + name + '</h3>' +
        '<div class="scene-years num">' + yearsStr(p) + ' · ' + p.tournaments + ' World Cup' + (p.tournaments > 1 ? "s" : "") + '</div>' +
        '<div class="scene-stats">' +
          '<div class="bigstat goals"><div class="v num" data-t="' + p.goals + '">0</div><div class="l">Goals</div></div>' +
          '<div class="bigstat"><div class="v num" data-t="' + elite + '" data-suf="%">0</div><div class="l"><a class="mref" href="#g-elite">Elite share</a>' + (p.flag ? " *" : "") + '</div></div>' +
          '<div class="bigstat"><div class="v num" data-t="' + p.avgElo + '">0</div><div class="l"><a class="mref" href="#g-elo">Avg opp Elo</a></div></div>' +
        '</div>' +
        '<div class="tierbar-block">' +
          '<div class="tierbar-head"><span class="lab">Goals by opponent strength</span><span class="tot num">' + p.goals + ' total</span></div>' +
          '<div class="tierbar">' + tierSegs(p) + '</div>' +
          '<div class="tierbar-legend">' + tierLegend(p) + '</div>' +
        '</div>' +
        '<p class="scene-blurb">' + p.blurb + '</p>' +
      '</div>';
    scenesWrap.appendChild(scene);

    var ri = el("div", "rail-item");
    ri.dataset.idx = idx;
    ri.innerHTML = '<span class="rk num">' + (idx + 1) + '</span><span class="rn">' + name +
      '</span><span class="rg num">' + p.goals + '</span>';
    ri.addEventListener("click", function () {
      var top = scroller.offsetTop + ((idx + 0.5) / N) * (scroller.offsetHeight - innerHeight);
      scrollTo({ top: top, behavior: reduce ? "auto" : "smooth" });
    });
    railWrap.appendChild(ri);
  });

  /* ---- tier-segment tooltip: tap (or hover) a tier block to see the opponents + the World Cup
     each of that tier's goals came against. Clamped on-screen and dismissed on scroll — same rules
     as the deep-dive tip, so it can't stick or run off the edge. ---- */
  (function () {
    var stip = el("div"); stip.id = "sstip"; document.body.appendChild(stip);
    function moveTip(x, y) {
      var pad = 8, r = stip.getBoundingClientRect();
      var nx = x + 14; if (nx + r.width > innerWidth - pad) nx = x - r.width - 14;
      var ny = y - r.height - 12; if (ny < pad) ny = y + 18;
      nx = Math.max(pad, Math.min(nx, innerWidth - r.width - pad));
      ny = Math.max(pad, Math.min(ny, innerHeight - r.height - pad));
      stip.style.left = nx + "px"; stip.style.top = ny + "px";
    }
    function hide() { stip.classList.remove("show"); stip.dataset.key = ""; }
    function show(name, t, x, y) {
      var p = players[name], rows = (p.detail && p.detail[t]) || [];
      var body = rows.map(function (d) {
        return '<div class="sst-row"><span>' + d.opp + '</span><b>' + d.year +
          (d.goals > 1 ? " · ×" + d.goals : "") + '</b></div>';
      }).join("") || '<div class="sst-row"><span>No goals in this tier</span></div>';
      stip.innerHTML = '<div class="sst-hd"><i style="background:var(--' + t + ')"></i>' +
        TIER_LABEL[t] + ' tier<span>' + p.tiers[t] + '</span></div>' + body;
      stip.classList.add("show"); stip.dataset.key = name + "|" + t; moveTip(x, y);
    }
    function info(seg) { var sc = seg.closest(".scene"); return sc ? { name: walk[+sc.dataset.idx], t: seg.dataset.tier } : null; }
    // desktop: hover
    scenesWrap.addEventListener("mouseover", function (e) { if (isMobile()) return; var s = e.target.closest(".tseg"); var i = s && info(s); if (i) show(i.name, i.t, e.clientX, e.clientY); });
    scenesWrap.addEventListener("mousemove", function (e) { if (isMobile()) return; if (stip.classList.contains("show") && e.target.closest(".tseg")) moveTip(e.clientX, e.clientY); });
    scenesWrap.addEventListener("mouseout", function (e) { if (isMobile()) return; if (e.target.closest(".tseg")) hide(); });
    // mobile: tap to toggle
    scenesWrap.addEventListener("click", function (e) {
      if (!isMobile()) return; var s = e.target.closest(".tseg"); var i = s && info(s); if (!i) return;
      var key = i.name + "|" + i.t, r = s.getBoundingClientRect();
      if (stip.classList.contains("show") && stip.dataset.key === key) { hide(); return; }
      show(i.name, i.t, e.clientX || (r.left + r.width / 2), e.clientY || r.top);
    });
    addEventListener("scroll", hide, { passive: true });
    document.addEventListener("click", function (e) { if (!e.target.closest(".tseg") && !e.target.closest("#sstip")) hide(); }, true);
  })();

  var scenes = [].slice.call(scenesWrap.children);
  var railItems = [].slice.call(railWrap.children);
  var cur = -1;
  function isMobile() { return matchMedia("(max-width: 900px)").matches; }

  function activate(i) {
    if (i === cur) return;
    cur = i;
    scenes.forEach(function (s, k) { s.classList.toggle("active", k === i); });
    railItems.forEach(function (r, k) { r.classList.toggle("active", k === i); });
    // count-up the newly active scene's numbers
    var s = scenes[i];
    if (s) s.querySelectorAll("[data-t]").forEach(function (v) {
      countUp(v, +v.dataset.t, { suffix: v.dataset.suf || "", dur: 850 });
    });
    // tint the living background to this scorer's dominant tier
    if (window.WCS_setAmbient && walk[i]) window.WCS_setAmbient(dominantTier(players[walk[i]]));
  }

  function layout() {
    if (isMobile()) { scroller.style.height = "auto"; scenes.forEach(function (s) { s.classList.add("active"); }); return; }
    scroller.style.height = (N * 100) + "vh";
  }
  function onScroll() {
    if (isMobile()) return;
    var vh = innerHeight;
    var travel = scroller.offsetHeight - vh;
    var scrolled = Math.min(Math.max(-scroller.getBoundingClientRect().top, 0), travel);
    var prog = travel > 0 ? scrolled / travel : 0;
    activate(Math.min(N - 1, Math.floor(prog * N + 1e-6)));
  }
  var ticking = false;
  addEventListener("scroll", function () {
    if (ticking) return; ticking = true;
    requestAnimationFrame(function () { onScroll(); ticking = false; });
  }, { passive: true });
  addEventListener("resize", function () { layout(); onScroll(); });
  layout();
  activate(0);
  onScroll();

  /* ---- mobile: the pin is dropped, so onScroll()->activate() never fires for scenes past the first,
     leaving their count-up stats stuck at 0. Count each stacked scene's stats up as it scrolls into
     view (mirrors the revealCheck idiom). Desktop is untouched — isMobile() short-circuits. ---- */
  var mCounted = [];
  function mobileCount() {
    if (!isMobile()) return;
    var vh = innerHeight;
    scenes.forEach(function (s, i) {
      if (mCounted[i]) return;
      var r = s.getBoundingClientRect();
      if (r.top < vh * 0.9 && r.bottom > 0) {
        mCounted[i] = true;
        s.querySelectorAll("[data-t]").forEach(function (v) {
          countUp(v, +v.dataset.t, { suffix: v.dataset.suf || "", dur: 850 });
        });
      }
    });
  }
  addEventListener("scroll", mobileCount, { passive: true });
  addEventListener("resize", mobileCount);
  mobileCount();
  requestAnimationFrame(mobileCount);
  setTimeout(mobileCount, 200);

  /* ============================================================
     COMPARISON DASHBOARD
     ============================================================ */
  var rosterWrap = document.getElementById("roster");
  var vizStage = document.getElementById("vizStage");
  var vizEl = document.getElementById("viz");
  var eraSlot = document.getElementById("eraSlot");
  var modeLabel = document.getElementById("vizModeLabel");
  var selCount = document.getElementById("selCount");
  var selected = ["Lionel Messi", "Kylian Mbappé", "Cristiano Ronaldo", "Sándor Kocsis"];
  var sortKey = "goals";
  var view = "ranking";
  var focusName = null;

  // shared tooltip
  var vtip = el("div"); vtip.id = "vtip"; document.body.appendChild(vtip);
  function moveTip(x, y) {
    var r = vtip.getBoundingClientRect(), nx = x + 16, ny = y + 16;
    if (nx + r.width > innerWidth) nx = x - r.width - 16;
    if (ny + r.height > innerHeight) ny = y - r.height - 16;
    vtip.style.left = nx + "px"; vtip.style.top = ny + "px";
  }
  function tipHTML(n) {
    var p = players[n];
    var tiers = TIERS.map(function (t) { var c = p.tiers[t]; return c ? '<i style="flex-grow:' + c + ';background:var(--' + t + ')"></i>' : ""; }).join("");
    return '<div class="t-nm">' + n + '</div>' +
      '<div class="t-row"><span>Goals</span><b>' + p.goals + '</b></div>' +
      '<div class="t-row"><span>Elite share</span><b>' + Math.round(p.eliteShare * 100) + '%</b></div>' +
      '<div class="t-row"><span>Avg opp Elo</span><b>' + p.avgElo + '</b></div>' +
      '<div class="t-row"><span>Span</span><b>' + yearsStr(p) + '</b></div>' +
      '<div class="t-tiers">' + tiers + '</div>';
  }
  function showTip(n, e) { vtip.innerHTML = tipHTML(n); vtip.classList.add("show"); moveTip(e.clientX, e.clientY); }
  function hideTip() { vtip.classList.remove("show"); }
  addEventListener("scroll", hideTip, { passive: true });   // touch: no mouseleave — dismiss on scroll

  function firstYear(n) { return players[n].years[0]; }
  // THE ranking rule — must stay in lockstep with _rank_key in build_ui.py. goals ↓ → fewest World Cups
  // PLAYED ↑ (players[n].tournaments is now squad membership, not tournaments-scored-in) → earliest
  // first WC year ↑ → name.
  function byGoals(a, b) {
    return players[b].goals - players[a].goals ||
      players[a].tournaments - players[b].tournaments ||
      firstYear(a) - firstYear(b) || a.localeCompare(b);
  }
  function sorted() {
    var ns = order.slice();
    if (sortKey === "az") return ns.sort(function (a, b) { return a.localeCompare(b); });
    if (sortKey === "goals") return ns.sort(byGoals);
    var v = sortKey === "elo" ? function (n) { return players[n].avgElo; } : function (n) { return players[n].eliteShare; };
    return ns.sort(function (a, b) { return v(b) - v(a) || byGoals(a, b); });
  }
  function chipVal(n) {
    var p = players[n];
    if (sortKey === "elite") return [Math.round(p.eliteShare * 100), "%"];
    if (sortKey === "elo") return [p.avgElo, " Elo"];
    return [p.goals, ""];
  }
  function miniBar(p) {
    return TIERS.map(function (t) {
      var c = p.tiers[t]; if (!c) return "";
      return '<i style="flex-grow:' + c + ';background:var(--' + t + ')"></i>';
    }).join("");
  }
  function dominantTier(p) {
    var best = "weak", bc = -1;
    TIERS.forEach(function (t) { if (p.tiers[t] > bc) { bc = p.tiers[t]; best = t; } });
    return best;
  }

  /* ---- cross-highlight ---- */
  function setFocus(n) {
    focusName = n;
    vizEl.classList.toggle("focusing", !!n);
    [].forEach.call(rosterWrap.children, function (t) { t.classList.toggle("dim", !!n && t.dataset.name !== n && selected.indexOf(t.dataset.name) >= 0); });
    [].forEach.call(vizStage.querySelectorAll("[data-name]"), function (nd) { nd.classList.toggle("hot", nd.dataset.name === n); });
  }

  /* ---- roster ---- */
  function buildRoster() {
    rosterWrap.innerHTML = "";
    var ranked = sortKey !== "goals" && sortKey !== "az";
    sorted().forEach(function (n, i) {
      var p = players[n];
      var v = chipVal(n);
      var tile = el("button", "tile" + (selected.indexOf(n) >= 0 ? " on" : ""));
      tile.type = "button"; tile.dataset.name = n;
      tile.innerHTML =
        '<div class="tile-head"><span class="tile-name">' + (ranked ? '<span class="tile-rank num">' + (i + 1) + '</span>' : "") + n +
          (p.flag && sortKey === "elite" ? ' <span style="color:var(--mid)">*</span>' : "") + '</span>' +
          '<span class="tile-val num">' + v[0] + (v[1] ? '<small>' + v[1] + '</small>' : "") + '</span></div>' +
        '<div class="tile-mini">' + miniBar(p) + '</div>';
      tile.addEventListener("click", function () {
        var k = selected.indexOf(n);
        if (k >= 0) selected.splice(k, 1); else selected.push(n);
        buildRoster(); renderViz();
      });
      tile.addEventListener("mouseenter", function () { if (selected.indexOf(n) >= 0) setFocus(n); });
      tile.addEventListener("mouseleave", function () { setFocus(null); });
      rosterWrap.appendChild(tile);
    });
    if (selCount) selCount.textContent = selected.length;
  }

  /* ---- ranking view ---- */
  function renderRanking(crossEra) {
    var picks = selected.slice().sort(byGoals);
    var maxG = Math.max.apply(null, picks.map(function (n) { return players[n].goals; }));
    var html = '<div class="rk-scale"><span>0</span><span>' + maxG + ' goals</span></div>';
    picks.forEach(function (n) {
      var p = players[n];
      var segs = TIERS.map(function (t) {
        var c = p.tiers[t]; if (!c) return "";
        return '<div class="rk-seg ' + t + '" style="flex-grow:' + c + ';background:var(--' + t + ')"><span>' + c + '</span></div>';
      }).join("");
      var pct = (p.goals / maxG) * 100;
      html += '<div class="rk-row" data-name="' + n + '">' +
        '<div class="rk-id"><div class="rk-nm"><span class="n">' + n + '</span>' +
          '<button class="rm" data-rm="' + n + '" aria-label="Remove ' + n + '">×</button></div>' +
          '<div class="rk-meta">' + p.country + ' · ' + yearsStr(p) + ' · ' + p.tournaments + ' WC · ' +
          Math.round(p.eliteShare * 100) + '% elite' + (crossEra ? ' †' : '') + ' · ' + p.avgElo + ' Elo</div></div>' +
        '<div class="rk-track"><div class="rk-bar" style="width:' + pct + '%">' + segs + '</div>' +
          '<span class="rk-goal num">' + p.goals + '<small>goals</small></span></div>' +
        '</div>';
    });
    vizStage.innerHTML = html;
    [].forEach.call(vizStage.querySelectorAll(".rk-row"), function (row) {
      var n = row.dataset.name;
      row.addEventListener("mouseenter", function () { setFocus(n); });
      row.addEventListener("mouseleave", function () { setFocus(null); });
    });
  }

  /* ---- field (scatter) view ---- */
  var ELO = (function () {
    var vals = order.map(function (n) { return players[n].avgElo; });
    return { min: Math.min.apply(null, vals) - 15, max: Math.max.apply(null, vals) + 15 };
  })();
  var ELITE_MAX = 0.75;
  function renderField() {
    var xt = "", grid = "", nodes = "";
    // x ticks (Elo)
    [1750, 1800, 1850, 1900, 1950].forEach(function (e) {
      if (e < ELO.min || e > ELO.max) return;
      var x = ((e - ELO.min) / (ELO.max - ELO.min)) * 100;
      grid += '<div class="field-gl v" style="left:' + x + '%"></div>';
      xt += '<div class="field-tick x" style="left:' + x + '%">' + e + '</div>';
    });
    // y ticks (elite %)
    [0, 25, 50, 75].forEach(function (pc) {
      var y = (pc / 100 / ELITE_MAX) * 100;
      grid += '<div class="field-gl h" style="bottom:' + y + '%"></div>';
      xt += '<div class="field-tick y" style="bottom:' + y + '%">' + pc + '%</div>';
    });
    selected.forEach(function (n) {
      var p = players[n];
      var x = ((p.avgElo - ELO.min) / (ELO.max - ELO.min)) * 100;
      var y = (p.eliteShare / ELITE_MAX) * 100;
      var size = 38 + ((p.goals - 9) / (21 - 9)) * 38;
      var dt = dominantTier(p);
      var initials = n.split(" ").map(function (w) { return w[0]; }).slice(0, 2).join("");
      var bg = p.photo ? 'background-image:url(' + p.photo + ');' : 'background:var(--' + dt + ');';
      var cls = "fnode" + (p.photo ? "" : " noimg");
      nodes += '<div class="' + cls + '" data-name="' + n + '" style="left:' + x + '%;bottom:' + y +
        '%;width:' + size + 'px;height:' + size + 'px;border-color:var(--' + dt + ');' + bg + '">' +
        (p.photo ? "" : '<span class="fg">' + initials + '</span>') +
        '<span class="fnode-badge num" style="border-color:var(--' + dt + ')">' + p.goals + '</span>' +
        '<span class="fnode-label">' + n + '</span></div>';
    });
    vizStage.innerHTML =
      '<div class="field">' +
        '<div class="field-quad"></div>' +
        '<div class="field-grid">' + grid + '</div>' +
        xt +
        '<div class="field-axis x">Average opponent Elo →</div>' +
        '<div class="field-axis y">Elite-tier share ↑</div>' +
        nodes +
      '</div>';
    [].forEach.call(vizStage.querySelectorAll(".fnode"), function (nd) {
      var n = nd.dataset.name;
      // Hover preview is desktop-only: touch has no mouseleave, so a tap-shown tip sticks forever
      // (it did — Compare » The Field). Guard the hover handlers, and clear the tip on the tap that
      // removes the node so nothing is left orphaned on either platform.
      nd.addEventListener("mouseenter", function (e) { if (isMobile()) return; setFocus(n); showTip(n, e); });
      nd.addEventListener("mousemove", function (e) { if (isMobile()) return; moveTip(e.clientX, e.clientY); });
      nd.addEventListener("mouseleave", function () { if (isMobile()) return; setFocus(null); hideTip(); });
      nd.addEventListener("click", function () {
        hideTip(); setFocus(null);
        selected.splice(selected.indexOf(n), 1); buildRoster(); renderViz();
      });
    });
  }

  /* ---- render orchestrator ---- */
  function renderViz() {
    var yrs = []; selected.forEach(function (n) { yrs.push(players[n].years[0], players[n].years[1]); });
    var crossEra = selected.length >= 2 && (Math.max.apply(null, yrs) - Math.min.apply(null, yrs) > 20);
    eraSlot.innerHTML = "";
    if (crossEra) {
      eraSlot.appendChild(el("div", "era-note",
        '<span class="tag">Cross-era</span><div><b>' + Math.min.apply(null, yrs) + '–' + Math.max.apply(null, yrs) +
        '.</b> Percentile tiers are era-fair — each player is judged against their own field. Absolute Elo is era-revealing; read elite share and average Elo together.</div>'));
    }
    modeLabel.textContent = view === "field" ? "Toughness vs elite scoring" : "Goals on a shared scale";
    vizEl.classList.remove("shown");
    if (!selected.length) { vizStage.innerHTML = '<p class="viz-empty">Pick a scorer above to start comparing.</p>'; return; }
    if (view === "field") renderField(); else renderRanking(crossEra);
    if (focusName && selected.indexOf(focusName) < 0) focusName = null;
    setFocus(null);
    (reduce ? function (f) { f(); } : function (f) { requestAnimationFrame(function () { requestAnimationFrame(f); }); })(function () {
      vizEl.classList.add("shown");
    });
    setTimeout(function () { vizEl.classList.add("shown"); }, 60);
  }

  // remove button (delegated for ranking rows)
  vizStage.addEventListener("click", function (e) {
    var b = e.target.closest("[data-rm]"); if (!b) return;
    e.stopPropagation();
    var n = b.dataset.rm; selected.splice(selected.indexOf(n), 1); buildRoster(); renderViz();
  });

  document.getElementById("sortSeg").addEventListener("click", function (e) {
    var b = e.target.closest("button"); if (!b) return;
    sortKey = b.dataset.k;
    [].forEach.call(this.children, function (c) { c.classList.toggle("active", c === b); });
    buildRoster();
  });
  document.getElementById("viewSeg").addEventListener("click", function (e) {
    var b = e.target.closest("button"); if (!b) return;
    view = b.dataset.v;
    [].forEach.call(this.children, function (c) { c.classList.toggle("active", c === b); });
    renderViz();
  });

  buildRoster();
  renderViz();

  /* expose a hook so other visuals (The Arena) can push a scorer into the comparison */
  window.WCS_addCompare = function (n) {
    if (!players[n]) return;
    if (selected.indexOf(n) < 0) selected.push(n);
    buildRoster(); renderViz();
    var y = document.querySelector(".compare").getBoundingClientRect().top + (window.pageYOffset || 0) - 16;
    scrollTo({ top: y, behavior: reduce ? "auto" : "smooth" });
  };
  window.WCS_isSelected = function (n) { return selected.indexOf(n) >= 0; };
})();
