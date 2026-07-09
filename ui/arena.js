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
    var size = 34 + ((p.goals - 9) / (21 - 9)) * 40;
    var dt = dom(p);
    var nd = document.createElement("div");
    nd.className = "anode" + (p.photo ? "" : " noimg") + (window.WCS_isSelected && window.WCS_isSelected(n) ? " picked" : "");
    nd.dataset.name = n;
    nd.style.width = nd.style.height = size + "px";
    nd.style.borderColor = "var(--" + dt + ")";
    if (p.photo) nd.style.backgroundImage = "url(" + p.photo + ")";
    else nd.style.background = "var(--" + dt + ")";
    var initials = n.split(" ").map(function (w) { return w[0]; }).slice(0, 2).join("");
    nd.innerHTML = (p.photo ? "" : '<span class="ag">' + initials + '</span>') +
      '<span class="anode-badge num" style="border-color:var(--' + dt + ')">' + p.goals + '</span>' +
      '<span class="anode-tag">' + n + '</span>';
    nd.addEventListener("mouseenter", function (e) { setFocus(n); showTip(n, e); });
    nd.addEventListener("mousemove", function (e) { moveTip(e.clientX, e.clientY); });
    nd.addEventListener("mouseleave", function () { setFocus(null); hideTip(); });
    nd.addEventListener("click", function () {
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
    order.forEach(function (n) {
      var q = pos(n);
      nodes[n].style.left = q.x + "%"; nodes[n].style.top = q.y + "%";
    });
  }
  function placeLanes() {
    var groups = { elite: [], strong: [], mid: [], weak: [] };
    order.forEach(function (n) { groups[dom(players[n])].push(n); });
    TIERS.forEach(function (t, i) {
      var lane = groups[t].slice().sort(function (a, b) { return players[b].goals - players[a].goals; });
      var cy = (i + 0.5) / 4 * 100;
      var k = lane.length;
      lane.forEach(function (n, j) {
        var x = 20 + (k > 1 ? (j / (k - 1)) * 76 : 38);
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
  (reduce ? function (f) { f(); } : function (f) { requestAnimationFrame(function () { requestAnimationFrame(f); }); })(function () {
    plot.classList.add("shown");
  });
  setTimeout(function () { plot.classList.add("shown"); }, 80);
})();
