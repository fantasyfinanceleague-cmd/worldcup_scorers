/* ============================================================
   The Arena — every 9+ goal scorer on one morphing plot
   Layouts: field (Elo × elite%), time (era × goals), lanes (by dominant tier)
   ============================================================ */
(function () {
  "use strict";
  var D = window.WCS;
  if (!D) return;
  var players = D.players, order = D.order;
  var reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
  var TIERS = ["elite", "strong", "mid", "weak"];
  var TIER_LABEL = { elite: "Elite", strong: "Strong", mid: "Mid", weak: "Weak" };

  var plot = document.getElementById("arenaPlot");
  var statsEl = document.getElementById("arenaStats");
  var capEl = document.getElementById("arenaCaption");
  var seg = document.getElementById("arenaSeg");
  var layout = "field";

  function dom(p) { var b = "weak", bc = -1; TIERS.forEach(function (t) { if (p.tiers[t] > bc) { bc = p.tiers[t]; b = t; } }); return b; }
  function mid(p) { return (p.years[0] + p.years[1]) / 2; }
  function isM() { return matchMedia("(max-width: 720px)").matches; }
  function clamp(v, lo, hi) { return v < lo ? lo : (v > hi ? hi : v); }
  // Node diameter scales with goals. On mobile the nodes render as plain tier-coloured DOTS with the
  // goal count centred (not photo bubbles — a ~30px face is illegible, #5), so a compact 26–48px ramp
  // stays readable and keeps the cluster tractable; the photo moves to a tap card. Desktop unchanged.
  function nodeSize(goals) { var t = (goals - 9) / (21 - 9); return isM() ? 26 + t * 22 : 34 + t * 40; }
  function sizeNodes() { order.forEach(function (n) { var s = nodeSize(players[n].goals); nodes[n].style.width = nodes[n].style.height = s + "px"; }); }

  var ELO = (function () {
    var v = order.map(function (n) { return players[n].avgElo; });
    return { min: Math.min.apply(null, v) - 15, max: Math.max.apply(null, v) + 15 };
  })();
  var EMAX = 0.75, GMIN = 8, GMAX = 22, YMIN = 1950, YMAX = 2030;

  /* ---- tooltip ---- */
  var tip = document.getElementById("atip");
  if (!tip) { tip = document.createElement("div"); tip.id = "atip"; document.body.appendChild(tip); }
  tip.style.cssText = "position:fixed;z-index:60;pointer-events:none;opacity:0;transform:translateY(4px);background:var(--ink);color:#fff;padding:11px 13px;border-radius:10px;font-size:12.5px;max-width:240px;box-shadow:0 10px 30px rgba(0,0,0,.3);transition:opacity .14s,transform .14s";
  function moveTip(x, y) {
    var r = tip.getBoundingClientRect(), nx = x + 16, ny = y + 16;
    if (nx + r.width > innerWidth) nx = x - r.width - 16;
    if (ny + r.height > innerHeight) ny = y - r.height - 16;
    tip.style.left = nx + "px"; tip.style.top = ny + "px";
  }
  function showTip(n, e) {
    var p = players[n];
    var tiers = TIERS.map(function (t) { var c = p.tiers[t]; return c ? '<i style="flex:' + c + ';background:var(--' + t + ')"></i>' : ""; }).join("");
    tip.innerHTML = '<div style="font-family:var(--display);font-weight:800;text-transform:uppercase;font-size:14px;margin-bottom:6px">' + n + '</div>' +
      '<div style="color:#c8cdd8;display:flex;justify-content:space-between;gap:18px"><span>' + p.country + '</span><b style="color:#fff">' + p.goals + ' goals</b></div>' +
      '<div style="color:#c8cdd8;display:flex;justify-content:space-between;gap:18px"><span>Elite share</span><b style="color:#fff">' + Math.round(p.eliteShare * 100) + '%</b></div>' +
      '<div style="color:#c8cdd8;display:flex;justify-content:space-between;gap:18px"><span>Avg opp Elo</span><b style="color:#fff">' + p.avgElo + '</b></div>' +
      '<div style="color:#c8cdd8;display:flex;justify-content:space-between;gap:18px"><span>Span</span><b style="color:#fff">' + (p.years[0] === p.years[1] ? p.years[0] : p.years[0] + "–" + p.years[1]) + '</b></div>' +
      '<div style="display:flex;gap:3px;height:6px;margin-top:8px;border-radius:3px;overflow:hidden">' + tiers + '</div>' +
      '<div style="color:#7c8494;font-size:11px;margin-top:8px">Click to compare →</div>';
    tip.style.opacity = "1"; tip.style.transform = "none"; moveTip(e.clientX, e.clientY);
  }
  function hideTip() { tip.style.opacity = "0"; tip.style.transform = "translateY(4px)"; }

  /* ---- mobile tap card: on mobile each node is just a numbered dot, so a tap reveals the photo +
     name + quick stats (photo-on-tap, #5). Interactive (Compare button); an outside tap dismisses it. ---- */
  var card = document.getElementById("acard");
  if (!card) { card = document.createElement("div"); card.id = "acard"; document.body.appendChild(card); }
  function closeCard() { card.classList.remove("show"); document.removeEventListener("click", cardOutside, true); }
  function cardOutside(e) { if (!card.contains(e.target)) closeCard(); }
  function openCard(n) {
    var p = players[n], dt = dom(p);
    var initials = n.split(" ").map(function (w) { return w[0]; }).slice(0, 2).join("");
    var bar = TIERS.map(function (t) { var c = p.tiers[t]; return c ? '<i style="flex:' + c + ';background:var(--' + t + ')"></i>' : ""; }).join("");
    var photo = p.photo
      ? '<div class="ac-photo" style="background-image:url(' + p.photo + ')"></div>'
      : '<div class="ac-photo" style="background:var(--' + dt + ')">' + initials + '</div>';
    card.innerHTML = photo +
      '<div class="ac-body">' +
        '<div class="ac-name">' + n + '</div>' +
        '<div class="ac-row"><span>' + p.country + '</span><b>' + p.goals + ' goals</b></div>' +
        '<div class="ac-row"><span>Elite share</span><b>' + Math.round(p.eliteShare * 100) + '%</b></div>' +
        '<div class="ac-row"><span>Avg opp Elo</span><b>' + p.avgElo + '</b></div>' +
        '<div class="ac-bar">' + bar + '</div>' +
        '<div class="ac-actions"><button class="ac-add">+ Compare</button><button class="ac-close">Close</button></div>' +
      '</div>';
    card.querySelector(".ac-add").addEventListener("click", function (ev) { ev.stopPropagation(); if (window.WCS_addCompare) window.WCS_addCompare(n); nodes[n].classList.add("picked"); closeCard(); });
    card.querySelector(".ac-close").addEventListener("click", function (ev) { ev.stopPropagation(); closeCard(); });
    card.classList.add("show");
    setTimeout(function () { document.addEventListener("click", cardOutside, true); }, 0);  // defer so the opening tap doesn't close it
  }

  /* ---- stats strip ---- */
  (function () {
    var sum = 0, byTier = { elite: 0, strong: 0, mid: 0, weak: 0 };
    order.forEach(function (n) { var p = players[n]; sum += p.goals; TIERS.forEach(function (t) { byTier[t] += p.tiers[t]; }); });
    var html = '<div class="arena-stat"><span class="v num">' + order.length + '</span><span class="l">scorers</span></div>' +
      '<div class="arena-stat"><span class="v num">' + sum + '</span><span class="l">World Cup goals</span></div>';
    TIERS.forEach(function (t) {
      html += '<div class="arena-stat"><span class="v num">' + Math.round(byTier[t] / sum * 100) + '%</span>' +
        '<span class="l"><i style="background:var(--' + t + ')"></i>' + TIER_LABEL[t] + '</span></div>';
    });
    statsEl.innerHTML = html;
  })();

  /* ---- build nodes once ---- */
  var inner = document.createElement("div"); inner.className = "aplot-inner";
  var axis = document.createElement("div"); axis.style.cssText = "position:absolute;inset:0";
  inner.appendChild(axis);
  plot.appendChild(inner);
  var nodes = {};
  order.forEach(function (n) {
    var p = players[n];
    var size = nodeSize(p.goals);
    var dt = dom(p);
    var nd = document.createElement("div");
    nd.className = "anode" + (p.photo ? "" : " noimg") + (window.WCS_isSelected && window.WCS_isSelected(n) ? " picked" : "");
    nd.dataset.name = n;
    nd.style.width = nd.style.height = size + "px";
    nd.style.borderColor = "var(--" + dt + ")";
    nd.style.setProperty("--nt", "var(--" + dt + ")");   // tier fill for the mobile dot (CSS reads --nt)
    if (p.photo) nd.style.backgroundImage = "url(" + p.photo + ")";
    else nd.style.background = "var(--" + dt + ")";
    var initials = n.split(" ").map(function (w) { return w[0]; }).slice(0, 2).join("");
    nd.innerHTML = (p.photo ? "" : '<span class="ag">' + initials + '</span>') +
      '<span class="anode-badge num" style="border-color:var(--' + dt + ')">' + p.goals + '</span>' +
      '<span class="anode-tag">' + n + '</span>';
    nd.addEventListener("mouseenter", function (e) { if (isM()) return; setFocus(n); showTip(n, e); });
    nd.addEventListener("mousemove", function (e) { if (isM()) return; moveTip(e.clientX, e.clientY); });
    nd.addEventListener("mouseleave", function () { if (isM()) return; setFocus(null); hideTip(); });
    nd.addEventListener("click", function (e) {
      if (isM()) { e.stopPropagation(); openCard(n); return; }   // mobile: tap → photo card (#5)
      if (window.WCS_addCompare) window.WCS_addCompare(n);
      nd.classList.add("picked"); hideTip();
    });
    inner.appendChild(nd);
    nodes[n] = nd;
  });

  function setFocus(n) {
    plot.classList.toggle("focusing", !!n);
    order.forEach(function (m) { nodes[m].classList.toggle("hot", m === n); });
  }

  /* ---- positions per layout (x, top in %) ---- */
  function pos(n) {
    var p = players[n];
    if (layout === "time") {
      return { x: (mid(p) - YMIN) / (YMAX - YMIN) * 100, y: (1 - (p.goals - GMIN) / (GMAX - GMIN)) * 100 };
    }
    // field
    return { x: (p.avgElo - ELO.min) / (ELO.max - ELO.min) * 100, y: (1 - p.eliteShare / EMAX) * 100 };
  }
  function place() {
    if (layout === "lanes") { placeLanes(); return; }
    var mobile = isM();
    var rect = inner.getBoundingClientRect(), iw = rect.width || 1, ih = rect.height || 1;
    order.forEach(function (n) {
      var q = pos(n), x = q.x, y = q.y;
      if (mobile) {
        // Keep every node fully inside the plot box: the ticks, tick-labels and axis titles all live
        // in the padding OUTSIDE this box, so a node that doesn't overhang an edge can't overlap them.
        // Hard constraint from the mobile bug report (#5). Desktop is left exactly as-was.
        var half = nodeSize(players[n].goals) / 2, mx = half / iw * 100, my = half / ih * 100;
        x = clamp(x, mx, 100 - mx); y = clamp(y, my, 100 - my);
      }
      nodes[n].style.left = x + "%"; nodes[n].style.top = y + "%";
    });
  }
  function placeLanes() {
    var mobile = isM();
    var rect = inner.getBoundingClientRect(), iw = rect.width || 1;
    var groups = { elite: [], strong: [], mid: [], weak: [] };
    order.forEach(function (n) { groups[dom(players[n])].push(n); });
    TIERS.forEach(function (t, i) {
      var lane = groups[t].slice().sort(function (a, b) { return players[b].goals - players[a].goals; });
      var cy = (i + 0.5) / 4 * 100;
      var k = lane.length;
      lane.forEach(function (n, j) {
        var x;
        if (mobile) {
          // Reserve a left gutter (76px) the nodes cannot enter, so the tier label (left:0, INSIDE the
          // box) is never covered (#6); inset the right end by the node radius so it stays fully inside.
          var half = nodeSize(players[n].goals) / 2;
          var lo = (76 + half) / iw * 100, hi = 100 - half / iw * 100;
          x = k > 1 ? lo + (j / (k - 1)) * (hi - lo) : (lo + hi) / 2;
        } else {
          x = 20 + (k > 1 ? (j / (k - 1)) * 76 : 38);
        }
        nodes[n].style.left = x + "%"; nodes[n].style.top = cy + "%";
      });
    });
  }

  /* ---- axis layer per layout ---- */
  function renderAxis() {
    var h = "";
    if (layout === "field") {
      h += '<div class="a-quad"></div>';
      [1750, 1800, 1850, 1900, 1950].forEach(function (e) {
        if (e < ELO.min || e > ELO.max) return;
        var x = (e - ELO.min) / (ELO.max - ELO.min) * 100;
        h += '<div class="a-axis-line v" style="left:' + x + '%"></div><div class="a-tick x" style="left:' + x + '%">' + e + '</div>';
      });
      [0, 25, 50, 75].forEach(function (pc) {
        var y = 100 - (pc / 100 / EMAX) * 100;
        h += '<div class="a-axis-line h" style="top:' + y + '%"></div><div class="a-tick y" style="top:' + y + '%">' + pc + '%</div>';
      });
      h += '<div class="a-axis-label x">Average opponent Elo →</div><div class="a-axis-label y">Elite-tier share ↑</div>';
    } else if (layout === "time") {
      [1954, 1970, 1986, 2002, 2018].forEach(function (yr) {
        var x = (yr - YMIN) / (YMAX - YMIN) * 100;
        h += '<div class="a-axis-line v" style="left:' + x + '%"></div><div class="a-tick x" style="left:' + x + '%">' + yr + '</div>';
      });
      [10, 15, 20].forEach(function (g) {
        var y = (1 - (g - GMIN) / (GMAX - GMIN)) * 100;
        h += '<div class="a-axis-line h" style="top:' + y + '%"></div><div class="a-tick y" style="top:' + y + '%">' + g + '</div>';
      });
      h += '<div class="a-axis-label x">World Cup era (career midpoint) →</div><div class="a-axis-label y">Career goals ↑</div>';
    } else {
      TIERS.forEach(function (t, i) {
        var cy = (i + 0.5) / 4 * 100;
        if (i > 0) h += '<div class="a-lane-rule" style="top:' + (i / 4 * 100) + '%"></div>';
        h += '<div class="a-lane-label" style="top:' + cy + '%;color:var(--' + t + ')"><i style="background:var(--' + t + ')"></i>' + TIER_LABEL[t] + '</div>';
      });
    }
    axis.innerHTML = h;
  }

  var CAPTION = {
    field: 'Up and to the right — scored often <b>against the strongest fields</b>. Down and left — tallies built against weaker opponents.',
    time: 'Seven decades of scorers. Height is <b>career goals</b>; horizontal position is <b>when they played</b>.',
    lanes: 'Each scorer sorted into the <b>tier they scored against most often</b> — their signature opponent strength.'
  };

  function render() {
    renderAxis();
    place();
    capEl.innerHTML = CAPTION[layout];
  }

  seg.addEventListener("click", function (e) {
    var b = e.target.closest("button"); if (!b) return;
    layout = b.dataset.l;
    [].forEach.call(this.children, function (c) { c.classList.toggle("active", c === b); });
    render();
  });

  render();
  // Re-size (mobile↔desktop ramp) and re-place (px-based clamps depend on live plot dimensions) on
  // resize / orientation change.
  var rz;
  addEventListener("resize", function () { clearTimeout(rz); rz = setTimeout(function () { sizeNodes(); place(); }, 150); });
  (reduce ? function (f) { f(); } : function (f) { requestAnimationFrame(function () { requestAnimationFrame(f); }); })(function () {
    plot.classList.add("shown");
  });
  setTimeout(function () { plot.classList.add("shown"); }, 80);
})();
