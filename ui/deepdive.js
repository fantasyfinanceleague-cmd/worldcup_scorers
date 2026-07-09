/* ============================================================
   Player Deep-Dive — open up one scorer's every World Cup goal
   ============================================================ */
(function () {
  "use strict";
  var D = window.WCS;
  if (!D) return;
  var players = D.players, order = D.order;
  var reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
  var ORDER = ["elite", "strong", "mid", "weak"];
  var TLABEL = { elite: "Elite", strong: "Strong", mid: "Mid", weak: "Weak" };

  var ICON = {
    wc: '<svg viewBox="0 0 24 24"><path d="M7 3v2H4v3a4 4 0 0 0 4 4h.2A5 5 0 0 0 11 14.9V17H8v2h8v-2h-3v-2.1a5 5 0 0 0 2.8-2.9H16a4 4 0 0 0 4-4V5h-3V3H7zM6 7v2.7A2 2 0 0 1 4.6 8 2 2 0 0 1 4 7h2zm12 0h2a2 2 0 0 1-.6 1A2 2 0 0 1 18 9.7V7z"/></svg>',
    ball: '<svg viewBox="0 0 24 24"><circle cx="12" cy="8.4" r="5.4" fill="none" stroke="currentColor" stroke-width="1.6"/><path d="M12 5.3l2.4 1.7-.9 2.8h-3L9.6 7z"/><path d="M11 14h2v2.1h3V18H8v-1.9h3z"/></svg>',
    boot: '<svg viewBox="0 0 24 24"><path d="M3 7c.2 1.8.5 3.8 1 4.8.4.8 1.1 1.2 2.6 1.2H19a2 2 0 0 1 2 2v1.2H4.3A1.3 1.3 0 0 1 3 16V7z"/></svg>'
  };
  var ALABEL = { wc: "World Cup", ball: "Golden Ball", boot: "Golden Boot" };

  var body = document.getElementById("deepBody");
  var sel = document.getElementById("deepSelect");
  var idx = order.indexOf("Lionel Messi"); if (idx < 0) idx = 0;
  var filter = "all";

  /* tooltip */
  var tip = document.createElement("div"); tip.id = "ddtip"; document.body.appendChild(tip);
  function moveTip(x, y) {
    var r = tip.getBoundingClientRect(), nx = x + 15, ny = y - r.height - 12;
    if (nx + r.width > innerWidth) nx = x - r.width - 15;
    if (ny < 4) ny = y + 18;
    tip.style.left = nx + "px"; tip.style.top = ny + "px";
  }
  function showTip(pill, e) {
    var t = pill.dataset.tier;
    tip.innerHTML = '<div class="ddt-op">' + pill.dataset.opp + (pill.dataset.goals > 1 ? ' <span>×' + pill.dataset.goals + '</span>' : '') + '</div>' +
      '<div class="ddt-row"><span>' + pill.dataset.year + ' World Cup</span></div>' +
      '<div class="ddt-row"><span>Opponent Elo</span><b>' + pill.dataset.elo + '</b></div>' +
      '<div class="ddt-tier"><i style="background:var(--' + t + ')"></i>' + TLABEL[t] + ' tier</div>';
    tip.classList.add("show"); moveTip(e.clientX, e.clientY);
  }
  function hideTip() { tip.classList.remove("show"); }

  order.forEach(function (n) {
    var o = document.createElement("option"); o.value = n;
    o.textContent = n + " — " + players[n].goals + " goals"; sel.appendChild(o);
  });

  function ease(t) { return 1 - Math.pow(1 - t, 3); }
  function countUp(node, target, suffix) {
    var dur = reduce ? 0 : 900; if (dur === 0) { node.textContent = target + (suffix || ""); return; }
    var start = null, done = false;
    function fin() { if (done) return; done = true; node.textContent = target + (suffix || ""); }
    function step(now) { if (start === null) start = now; var t = Math.min(1, (now - start) / dur);
      node.textContent = Math.round(ease(t) * target) + (suffix || ""); if (t < 1) requestAnimationFrame(step); else fin(); }
    requestAnimationFrame(step); setTimeout(fin, dur + 140);
  }
  function dom(p) { var b = "weak", bc = -1; ORDER.forEach(function (t) { if (p.tiers[t] > bc) { bc = p.tiers[t]; b = t; } }); return b; }
  function yrs(p) { return p.years[0] === p.years[1] ? "" + p.years[0] : p.years[0] + "–" + p.years[1]; }

  function byTournament(p) {
    var map = {};
    ORDER.forEach(function (t) { (p.detail[t] || []).forEach(function (g) { (map[g.year] = map[g.year] || []).push({ opp: g.opp, tier: t, goals: g.goals, elo: g.elo, year: g.year }); }); });
    return Object.keys(map).map(Number).sort(function (a, b) { return a - b; }).map(function (y) {
      var list = map[y].sort(function (a, b) { return ORDER.indexOf(a.tier) - ORDER.indexOf(b.tier); });
      return { year: y, list: list, total: list.reduce(function (s, g) { return s + g.goals; }, 0) };
    });
  }
  // "Most punished" is precomputed server-side (build_breakdown.py): all WC goals grouped by
  // ERA-CORRECT opponent code, summed, ranked by goals then highest opponent Elo faced. See
  // p.mostPunished = {opponent, goals}. (Was a client-side name-group that mis-broke ties.)

  function accHTML(p) {
    if (!p.acc) return "";
    return ["wc", "ball", "boot"].map(function (k) {
      var y = (p.acc[k] || []); if (!y.length) return "";
      var lab = ALABEL[k] + " — " + y.join(", ");
      return '<span class="dd-acc" tabindex="0" role="img" aria-label="' + lab +
        '" data-acctip="' + lab + '">' + ICON[k] + " ×" + y.length + "</span>";
    }).join("");
  }

  function render(animate) {
    var n = order[idx], p = players[n];
    sel.value = n;
    var dt = dom(p), mp = p.mostPunished;
    // "Most punished" = opponent(s) a player scored the MOST career WC goals against (era-correct
    // grouping, precomputed in build_breakdown.py). Ties list every opponent, no winner picked; when
    // no opponent was scored against more than once, mp is null and we render "—".
    var mpVal = mp
      ? '<b>' + mp.opponents.join(", ") + '</b> · ' + mp.goals + ' goals' + (mp.opponents.length > 1 ? " each" : "")
      : '<b>—</b>';
    var bars = ORDER.map(function (t) { var c = p.tiers[t]; if (!c) return "";
      return '<div class="dd-seg" data-tier="' + t + '" style="flex-grow:' + c + ';background:var(--' + t + ')"><span>' + c + '</span></div>'; }).join("");
    var chips = '<button class="dd-chip' + (filter === "all" ? " on" : "") + '" data-f="all">All ' + p.goals + '</button>' +
      ORDER.map(function (t) { return p.tiers[t] ? '<button class="dd-chip t-' + t + (filter === t ? " on" : "") +
        '" data-f="' + t + '"><i style="background:var(--' + t + ')"></i>' + TLABEL[t] + ' ' + p.tiers[t] + '</button>' : ""; }).join("");
    var tours = byTournament(p).map(function (tr) {
      var pills = tr.list.map(function (g) {
        var hide = filter !== "all" && filter !== g.tier;
        return '<span class="dd-pill t-' + g.tier + (hide ? " dim" : "") + '" data-tier="' + g.tier +
          '" data-opp="' + g.opp + '" data-year="' + g.year + '" data-elo="' + g.elo + '" data-goals="' + g.goals + '">' +
          g.opp + (g.goals > 1 ? ' <b>×' + g.goals + '</b>' : '') + '</span>';
      }).join("");
      return '<div class="dd-tour"><div class="dd-year"><span class="num">' + tr.year + '</span><small>' + tr.total + ' goal' + (tr.total > 1 ? 's' : '') + '</small></div>' +
        '<div class="dd-pills">' + pills + '</div></div>';
    }).join("");

    body.innerHTML =
      '<div class="dd-profile">' +
        '<div class="dd-photo-wrap">' +
          (p.photo ? '<img class="dd-photo" src="' + p.photo + '" alt="' + n + '">' : '<div class="dd-photo dd-noimg" style="background:var(--' + dt + ')">' + n.split(" ").map(function (w) { return w[0]; }).slice(0, 2).join("") + '</div>') +
          '<div class="dd-acc-row">' + accHTML(p) + '</div>' +
        '</div>' +
        '<div class="dd-id">' +
          '<div class="dd-nation">' + p.country + '</div>' +
          '<h3 class="dd-name">' + n + '</h3>' +
          '<div class="dd-span num">' + yrs(p) + ' · ' + p.tournaments + ' World Cup' + (p.tournaments > 1 ? 's' : '') + '</div>' +
        '</div>' +
        '<div class="dd-stats">' +
          '<div class="dd-stat"><div class="v num" data-t="' + p.goals + '">0</div><div class="l">Goals</div></div>' +
          '<div class="dd-stat"><div class="v num" data-t="' + Math.round(p.eliteShare * 100) + '" data-suf="%">0</div><div class="l"><a class="mref" href="#g-elite">Elite share</a></div></div>' +
          '<div class="dd-stat"><div class="v num" data-t="' + p.avgElo + '">0</div><div class="l"><a class="mref" href="#g-elo">Avg opp Elo</a></div></div>' +
          '<div class="dd-stat"><div class="v num" data-t="' + p.tournaments + '">0</div><div class="l">Tournaments</div></div>' +
        '</div>' +
        '<div class="dd-fact">Most punished — ' + mpVal + '</div>' +
      '</div>' +
      '<div class="dd-goals">' +
        '<div class="dd-goals-head"><span class="dd-gk">Goals by opponent strength</span><span class="dd-gt num">' + p.goals + ' total</span></div>' +
        '<div class="dd-bar">' + bars + '</div>' +
        '<div class="dd-chips">' + chips + '</div>' +
        '<div class="dd-ledger' + (animate && !reduce ? ' anim' : '') + '">' + tours + '</div>' +
      '</div>';

    body.querySelectorAll("[data-t]").forEach(function (v) { countUp(v, +v.dataset.t, v.dataset.suf || ""); });
    body.querySelectorAll(".dd-chip").forEach(function (c) {
      c.addEventListener("click", function () { filter = c.dataset.f; render(false); });
    });
    if (window.WCS_setAmbient) window.WCS_setAmbient(dt);
  }

  function go(d) { idx = (idx + d + order.length) % order.length; filter = "all"; render(true); }
  document.getElementById("deepPrev").addEventListener("click", function () { go(-1); });
  document.getElementById("deepNext").addEventListener("click", function () { go(1); });
  sel.addEventListener("change", function () { idx = order.indexOf(sel.value); filter = "all"; render(true); });

  body.addEventListener("mouseover", function (e) { var p = e.target.closest(".dd-pill"); if (p) showTip(p, e); });
  body.addEventListener("mousemove", function (e) { if (tip.classList.contains("show")) moveTip(e.clientX, e.clientY); });
  body.addEventListener("mouseout", function (e) { if (e.target.closest(".dd-pill")) hideTip(); });

  render(false);
})();
