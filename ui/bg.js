/* ============================================================
   Living background — particle field, cursor glow, ambient tint,
   scroll progress. Tuned for the light broadcast theme.
   ============================================================ */
(function () {
  "use strict";
  var reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ---------- ambient tint (reacts to content) ---------- */
  var TIER_RGB = { elite: "0,184,102", strong: "154,206,31", mid: "255,171,29", weak: "255,68,92" };
  var DEFAULT_AMB = "37,99,235";
  var root = document.documentElement;
  root.style.setProperty("--amb", DEFAULT_AMB);
  window.WCS_setAmbient = function (key) {
    root.style.setProperty("--amb", TIER_RGB[key] || key || DEFAULT_AMB);
  };

  /* ---------- scroll progress ---------- */
  var bar = document.getElementById("progress");
  function onProg() {
    if (!bar) return;
    var h = document.documentElement.scrollHeight - innerHeight;
    var p = h > 0 ? (window.pageYOffset || document.documentElement.scrollTop) / h : 0;
    bar.style.transform = "scaleX(" + Math.min(1, Math.max(0, p)) + ")";
  }
  addEventListener("scroll", onProg, { passive: true });
  addEventListener("resize", onProg);
  onProg();

  /* ---------- cursor glow ---------- */
  var glow = document.getElementById("cursorGlow");
  var mx = -999, my = -999, gx = -999, gy = -999, hasMouse = false;
  addEventListener("pointermove", function (e) {
    if (e.pointerType === "touch") return;
    mx = e.clientX; my = e.clientY; hasMouse = true;
  }, { passive: true });

  /* ---------- particle field ---------- */
  var cv = document.getElementById("bgCanvas");
  if (!cv) return;
  var ctx = cv.getContext("2d");
  var W = 0, H = 0, DPR = Math.min(2, window.devicePixelRatio || 1);
  var arcs = [], pitch = null;

  function rnd(a, b) { return a + Math.random() * (b - a); }
  function makeArc() {
    // a pass/shot: curved path across the field with a ball travelling along it
    var x0 = rnd(-0.1, 1.1) * W, y0 = rnd(0, 1) * H;
    var x1 = x0 + rnd(-0.5, 0.5) * W, y1 = y0 + rnd(-0.35, 0.35) * H;
    var mxp = (x0 + x1) / 2, myp = (y0 + y1) / 2;
    // perpendicular bow for the curve
    var dx = x1 - x0, dy = y1 - y0, len = Math.hypot(dx, dy) || 1;
    var bow = rnd(-0.28, 0.28) * len;
    return { x0: x0, y0: y0, x1: x1, y1: y1,
      cx: mxp - (dy / len) * bow, cy: myp + (dx / len) * bow,
      t: Math.random(), sp: rnd(0.0009, 0.0022), r: rnd(1.6, 2.6) };
  }
  function bez(a, b, c, t) { var u = 1 - t; return u * u * a + 2 * u * t * b + t * t * c; }

  function buildPitch() {
    // faint tactics-board markings, viewport-sized (goals left & right)
    var cx = W / 2, cy = H / 2, r = Math.min(W, H) * 0.14;
    var boxW = W * 0.11, boxH = H * 0.42, arcR = r * 0.72;
    pitch = { cx: cx, cy: cy, r: r, boxW: boxW, boxH: boxH, arcR: arcR };
  }
  function resize() {
    W = cv.clientWidth; H = cv.clientHeight;
    cv.width = W * DPR; cv.height = H * DPR;
    ctx.setTransform(DPR, 0, 0, DPR, 0, 0);
    var target = Math.max(4, Math.min(9, Math.round((W * H) / 260000)));
    arcs = []; for (var i = 0; i < target; i++) arcs.push(makeArc());
    buildPitch();
  }
  resize();
  addEventListener("resize", resize);

  var MOUSE = 210;
  function ambRGB() { return (getComputedStyle(root).getPropertyValue("--amb") || DEFAULT_AMB).trim(); }

  function drawPitch() {
    var p = pitch, ink = "rgba(10,14,23,.05)";
    ctx.strokeStyle = ink; ctx.lineWidth = 1.5;
    ctx.beginPath(); ctx.moveTo(p.cx, p.cy - p.r * 3.2); ctx.lineTo(p.cx, p.cy + p.r * 3.2); ctx.stroke(); // halfway line
    ctx.beginPath(); ctx.arc(p.cx, p.cy, p.r, 0, 6.2832); ctx.stroke();                                   // centre circle
    ctx.beginPath(); ctx.arc(p.cx, p.cy, 3, 0, 6.2832); ctx.fillStyle = ink; ctx.fill();                  // centre spot
    // penalty boxes L / R
    ctx.strokeRect(0, p.cy - p.boxH / 2, p.boxW, p.boxH);
    ctx.strokeRect(W - p.boxW, p.cy - p.boxH / 2, p.boxW, p.boxH);
    ctx.beginPath(); ctx.arc(p.boxW, p.cy, p.arcR, -1.0, 1.0); ctx.stroke();
    ctx.beginPath(); ctx.arc(W - p.boxW, p.cy, p.arcR, Math.PI - 1.0, Math.PI + 1.0); ctx.stroke();
  }

  // dribble trail
  var trail = [];
  function frame() {
    if (reduce) return;
    ctx.clearRect(0, 0, W, H);
    drawPitch();
    if (hasMouse) { gx += (mx - gx) * 0.14; gy += (my - gy) * 0.14; }
    var amb = ambRGB();
    if (glow) {
      glow.style.opacity = hasMouse ? "1" : "0";
      glow.style.transform = "translate(" + (gx - 250) + "px," + (gy - 250) + "px)";
      glow.style.background = "radial-gradient(closest-side, rgba(" + amb + ",.15), rgba(" + amb + ",0) 70%)";
    }
    // dribble trail (recent cursor path)
    if (hasMouse) {
      var lastT = trail[trail.length - 1];
      if (!lastT || Math.hypot(gx - lastT.x, gy - lastT.y) > 7) trail.push({ x: gx, y: gy, a: 1 });
    }
    for (var k = trail.length - 1; k >= 0; k--) {
      var tp = trail[k]; tp.a -= 0.03;
      if (tp.a <= 0) { trail.splice(k, 1); continue; }
      ctx.fillStyle = "rgba(" + amb + "," + (tp.a * 0.5).toFixed(3) + ")";
      ctx.beginPath(); ctx.arc(tp.x, tp.y, 2.5 * tp.a + 0.5, 0, 6.2832); ctx.fill();
    }
    if (trail.length > 40) trail.splice(0, trail.length - 40);

    // pass trajectories
    for (var i = 0; i < arcs.length; i++) {
      var A = arcs[i];
      A.t += A.sp; if (A.t >= 1) { arcs[i] = makeArc(); arcs[i].t = 0; continue; }
      var bx = bez(A.x0, A.cx, A.x1, A.t), by = bez(A.y0, A.cy, A.y1, A.t);
      var near = hasMouse && Math.hypot(bx - gx, by - gy) < MOUSE;
      var f = near ? (1 - Math.hypot(bx - gx, by - gy) / MOUSE) : 0;
      // dotted travelled path (a fading tail behind the ball)
      ctx.setLineDash([2, 6]); ctx.lineWidth = 1;
      ctx.strokeStyle = near ? "rgba(" + amb + "," + (0.10 + f * 0.4).toFixed(3) + ")" : "rgba(10,14,23,.07)";
      ctx.beginPath();
      var start = Math.max(0, A.t - 0.5), steps = 14;
      for (var s = 0; s <= steps; s++) {
        var tt = start + (A.t - start) * (s / steps);
        var px = bez(A.x0, A.cx, A.x1, tt), py = bez(A.y0, A.cy, A.y1, tt);
        if (s === 0) ctx.moveTo(px, py); else ctx.lineTo(px, py);
      }
      ctx.stroke(); ctx.setLineDash([]);
      // the ball
      ctx.fillStyle = near ? "rgba(" + amb + "," + (0.55 + f * 0.4).toFixed(3) + ")" : "rgba(10,14,23,.28)";
      ctx.beginPath(); ctx.arc(bx, by, A.r, 0, 6.2832); ctx.fill();
      if (near) { ctx.strokeStyle = "rgba(" + amb + "," + (f * 0.6).toFixed(3) + ")"; ctx.lineWidth = 1.5;
        ctx.beginPath(); ctx.arc(bx, by, A.r + 4, 0, 6.2832); ctx.stroke(); }
    }
    requestAnimationFrame(frame);
  }
  if (!reduce) requestAnimationFrame(frame);

  /* ---------- default ambient by section (walkthrough overrides per-scorer) ---------- */
  var secAmb = [
    ["hero", DEFAULT_AMB], ["arena", DEFAULT_AMB], ["compare", DEFAULT_AMB], ["deep", DEFAULT_AMB]
  ];
  var obs = new IntersectionObserver(function (ents) {
    ents.forEach(function (en) {
      if (!en.isIntersecting) return;
      var cls = en.target.className;
      if (cls.indexOf("showcase") >= 0 || cls.indexOf("deep") >= 0) return; // driven per active scorer
      secAmb.forEach(function (s) { if (cls.indexOf(s[0]) >= 0) root.style.setProperty("--amb", s[1]); });
    });
  }, { threshold: 0.4 });
  ["hero", "arena", "compare"].forEach(function (c) {
    var e = document.querySelector("." + c); if (e) obs.observe(e);
  });

  /* ---------- top nav: active-link tracking ---------- */
  (function () {
    var links = [].slice.call(document.querySelectorAll("#navLinks a"));
    var map = {};
    links.forEach(function (a) { map[a.getAttribute("href").slice(1)] = a; });
    var ids = ["scorers", "player", "arena", "compare"];
    var navObs = new IntersectionObserver(function (ents) {
      ents.forEach(function (en) {
        if (!en.isIntersecting) return;
        var id = en.target.id;
        links.forEach(function (a) { a.classList.toggle("active", map[id] === a); });
      });
    }, { threshold: 0.01, rootMargin: "-45% 0px -45% 0px" });
    ids.forEach(function (id) { var e = document.getElementById(id); if (e) navObs.observe(e); });
  })();

  /* ---------- hero drifting name ticker ---------- */
  (function () {
    var t = document.getElementById("heroTicker");
    if (!t || !window.WCS) return;
    var names = window.WCS.order.map(function (n) { return n.split(" ").slice(-1)[0].toUpperCase(); });
    function row(dir) {
      var r = document.createElement("div");
      r.className = "ht-row" + (dir < 0 ? " rev" : "");
      var seq = names.concat(names);
      r.innerHTML = seq.map(function (s) { return '<span>' + s + '</span>'; }).join('<i>·</i>');
      return r;
    }
    t.appendChild(row(1)); t.appendChild(row(-1)); t.appendChild(row(1));
  })();
})();
