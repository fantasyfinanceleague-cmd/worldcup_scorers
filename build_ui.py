#!/usr/bin/env python3
"""Build the self-contained index.html from data/player_breakdown.json.
Reproducible: re-run after any data change. Hero = stacked tier-bands subdivided by tournament."""
import json, sys

data = json.load(open("data/player_breakdown.json"))
# THE ranking rule (mirrored verbatim by the JS `byGoals`): goals ↓ → fewest tournaments ↑ (concentrated
# scoring first — a stated value, surfaced in the walkthrough intro) → earliest first WC year ↑ → name
# (exhaustive deterministic fallback, never the operative tie-break). Total, so tied tallies can never
# silently degrade to insertion order — the class of bug that let alphabetical creep in unnoticed.
def _first_year(p): return min(t["year"] for t in p["per_tournament"])
roster = sorted(data.items(), key=lambda kv: (-kv[1]["goals"], kv[1]["tournaments"], _first_year(kv[1]), kv[0]))
roster_names = [n for n, _ in roster]
max_goals = max(p["goals"] for _, p in roster)
DATA_JS = json.dumps({n: data[n] for n in roster_names}, ensure_ascii=False)
photos = json.load(open("data/photos.json"))
PHOTOS_JS = json.dumps(photos, ensure_ascii=False)
# Accolade years per category: World Cup wins (all eras), Golden Balls, Golden Boots.
# CONVENTION (retroactive): Golden Boots include FIFA's backdated top-scorer recognitions for every
# World Cup 1930–1978; the Golden Ball (best player) is awarded only from 1982 and was never
# officially backdated, so pre-1982 Balls are intentionally absent. Vavá's 1962 Boot is omitted —
# 1962 was a six-way tie at 4 goals, so there is no solo Golden Boot to credit (no picking through ties).
# These are HAND-SOURCED static values (World Cup history is settled, so they sit outside the daily
# data gates). Source: FIFA World Cup awards / official top-scorer list, verified 2026 against
# https://en.wikipedia.org/wiki/FIFA_World_Cup_awards .
ACCOLADES = {
    "Lionel Messi":         {"wc": [2022],             "ball": [2014, 2022], "boot": []},
    "Kylian Mbappé":        {"wc": [2018],             "ball": [],           "boot": [2022]},
    "Miroslav Klose":       {"wc": [2014],             "ball": [],           "boot": [2006]},
    "Ronaldo":              {"wc": [1994, 2002],       "ball": [1998],       "boot": [2002]},
    "Gerd Müller":          {"wc": [1974],             "ball": [],           "boot": [1970]},
    "Just Fontaine":        {"wc": [],                 "ball": [],           "boot": [1958]},
    "Pelé":                 {"wc": [1958, 1962, 1970], "ball": [],           "boot": []},
    "Harry Kane":           {"wc": [],                 "ball": [],           "boot": [2018]},
    "Jürgen Klinsmann":     {"wc": [1990],             "ball": [],           "boot": []},
    "Sándor Kocsis":        {"wc": [],                 "ball": [],           "boot": [1954]},
    "Cristiano Ronaldo":    {"wc": [],                 "ball": [],           "boot": []},
    "Gabriel Batistuta":    {"wc": [],                 "ball": [],           "boot": []},
    "Gary Lineker":         {"wc": [],                 "ball": [],           "boot": [1986]},
    "Grzegorz Lato":        {"wc": [],                 "ball": [],           "boot": [1974]},
    "Helmut Rahn":          {"wc": [1954],             "ball": [],           "boot": []},
    "Teófilo Cubillas":     {"wc": [],                 "ball": [],           "boot": []},
    "Thomas Müller":        {"wc": [2014],             "ball": [],           "boot": [2010]},
    "Ademir de Menezes":    {"wc": [],                 "ball": [],           "boot": [1950]},
    "Christian Vieri":      {"wc": [],                 "ball": [],           "boot": []},
    "David Villa":          {"wc": [2010],             "ball": [],           "boot": []},
    "Eusébio":              {"wc": [],                 "ball": [],           "boot": [1966]},
    "Jairzinho":            {"wc": [1970],             "ball": [],           "boot": []},
    "Karl-Heinz Rummenigge":{"wc": [],                 "ball": [],           "boot": []},
    "Paolo Rossi":          {"wc": [1982],             "ball": [],           "boot": [1982]},
    "Roberto Baggio":       {"wc": [],                 "ball": [],           "boot": []},
    "Uwe Seeler":           {"wc": [],                 "ball": [],           "boot": []},
    "Vavá":                 {"wc": [1958, 1962],       "ball": [],           "boot": []},
}
ACCOLADES_JS = json.dumps(ACCOLADES, ensure_ascii=False)

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>World Cup Scorers — by Opponent Strength</title>
<style>
:root{
  --cream:#f4ecd6; --panel:#fbf5e6; --ink:#1c1a16; --muted:#6f6857; --line:#d9cdac;
  /* tier palette = continuous elite→weak intensity ramp (green → yellow-green → amber → red),
     with rising lightness so it also reads as a gradient in grayscale */
  --elite:#1f7a44; --strong:#7c9b3b; --mid:#cd9a30; --weak:#cb5d39;
  --maxg:%%MAXG%%;
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--cream);color:var(--ink);
  font:16px/1.5 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;}
.num{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-variant-numeric:tabular-nums}
.wrap{max-width:980px;margin:0 auto;padding:28px 20px 80px}
header h1{font-size:clamp(22px,4.6vw,34px);letter-spacing:.06em;text-transform:uppercase;
  font-weight:800;margin:0 0 6px;line-height:1.1}
/* body paragraphs share the H1's width boundary (full container), per owner preference over the ch-cap */
.sub{color:var(--muted);max-width:none;margin:0 0 4px}
.conv{color:var(--muted);font-size:13px;max-width:none}
.conv b{color:var(--ink);font-weight:600}
hr.rule{border:0;border-top:2px solid var(--ink);margin:20px 0}
.legend{display:flex;flex-wrap:wrap;gap:14px 22px;align-items:center;margin:0 0 18px;font-size:13px}
.legend .sw{display:inline-flex;align-items:center;gap:7px}
.legend i{width:16px;height:16px;border-radius:3px;display:inline-block}
.legend small{color:var(--muted)}
h2.section{font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);
  margin:0 0 10px;font-weight:700}
.roster{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 8px}
.chip{border:1px solid var(--line);background:var(--panel);color:var(--ink);border-radius:999px;
  padding:6px 13px;font-size:13.5px;cursor:pointer;display:inline-flex;gap:8px;align-items:center;
  box-shadow:0 1px 2px rgba(40,30,10,.06);transition:border-color .15s,background .15s,box-shadow .15s,transform .15s}
.chip:hover{box-shadow:0 4px 10px rgba(40,30,10,.11);transform:translateY(-1px)}
.chip .g{color:var(--muted);font-size:12px}
.chip[aria-pressed="true"]{border-color:var(--ink);background:#efe4c4;font-weight:600;
  box-shadow:inset 0 1px 3px rgba(40,30,10,.14);transform:none}
.chip:focus-visible{outline:3px solid var(--strong);outline-offset:2px}
.roster-head{display:flex;justify-content:space-between;align-items:baseline;flex-wrap:wrap;gap:8px}
.sortctl{font-size:12px;color:var(--muted);display:inline-flex;align-items:center;gap:6px}
.sortctl select{font:inherit;font-size:13px;color:var(--ink);background:var(--panel);border:1px solid var(--line);
  border-radius:8px;padding:3px 9px;cursor:pointer;box-shadow:0 1px 2px rgba(40,30,10,.06)}
.crank{color:var(--muted);font-size:11px;min-width:15px;text-align:right;font-weight:600}
.cflag{color:#a8761f;font-weight:700}
.ct{color:var(--muted);font-size:11px;border-left:1px solid var(--line);padding-left:7px}
.hint{color:var(--muted);font-size:12.5px;margin:2px 0 22px}
.era{display:none;border:1.5px solid var(--ink);background:#efe4c4;border-radius:10px;
  padding:11px 14px;margin:0 0 22px;font-size:13.5px}
.era.show{display:block}
.era b{letter-spacing:.04em;text-transform:uppercase;font-size:11.5px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:16px;
  padding:18px 18px 16px;margin:0 0 16px;box-shadow:0 4px 16px rgba(40,30,10,.08);
  transition:box-shadow .25s,transform .25s}
.card:hover{box-shadow:0 9px 26px rgba(40,30,10,.13);transform:translateY(-1px)}
.card .top{display:flex;justify-content:space-between;align-items:baseline;gap:12px;flex-wrap:wrap}
.card .name{font-size:20px;font-weight:700;margin:0}
.card .meta{color:var(--muted);font-size:13px}
.bartrack{margin:14px 0 6px;width:100%}
.bar{display:flex;height:38px;width:calc(var(--w) / var(--maxg) * 100%);min-width:42px;
  border:1px solid rgba(0,0,0,.18);border-radius:5px;overflow:hidden;background:#fff}
.cell{position:relative;cursor:default;border-right:1.5px solid var(--cream)}
.cell:last-child{border-right:0}
.cell:focus-visible{outline:3px solid var(--ink);outline-offset:-3px;z-index:2}
.scale{display:flex;justify-content:space-between;color:var(--muted);font-size:11px;margin-top:3px}
.tiers{display:flex;gap:16px;flex-wrap:wrap;margin:8px 0 0;font-size:12.5px;color:var(--muted)}
.tiers b{color:var(--ink)}
.stats{display:flex;flex-wrap:wrap;gap:10px 26px;margin-top:13px;padding-top:12px;border-top:1px dashed var(--line)}
.stat .k{font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
a.k{text-decoration:none;border-bottom:1px dotted var(--line)}
a.k:hover{color:var(--ink);border-bottom-color:var(--ink)}
a.k:focus-visible{outline:2px solid var(--strong);outline-offset:2px;border-radius:2px}
details.methodology{margin:0 0 4px}
details.methodology>summary{cursor:pointer;list-style:none;display:inline-flex;align-items:center;gap:8px}
details.methodology>summary::-webkit-details-marker{display:none}
details.methodology>summary::after{content:"▸";font-size:11px;color:var(--muted);transition:transform .2s}
details.methodology[open]>summary::after{transform:rotate(90deg)}
details.methodology>summary:focus-visible{outline:2px solid var(--strong);outline-offset:3px;border-radius:3px}
.glossary{display:grid;grid-template-columns:repeat(2,1fr);gap:11px 24px;margin:14px 0 0;padding:0}
.glossary>div{padding:11px 13px;border:1px solid var(--line);border-radius:9px;background:var(--panel)}
.glossary dt{font-weight:700;font-size:13.5px;margin-bottom:3px}
.glossary dt .mark{color:#a8761f}
.glossary dd{margin:0;font-size:12.5px;color:#433d30;line-height:1.5}
.glossary>div:target{animation:gflash 1.4s ease}   /* flash only — no persistent :target background */
@keyframes gflash{from{background:#e6d48b;border-color:var(--ink)}to{background:var(--panel);border-color:var(--line)}}
@media(max-width:640px){.glossary{grid-template-columns:1fr}}
.stat .v{font-size:21px;font-weight:700}
.stat .v sup{color:var(--weak);font-size:13px}
.dagger{color:var(--weak);cursor:help;border-bottom:1px dotted var(--weak)}
.bflag{font:600 12px/1 system-ui;vertical-align:super;margin-left:5px;padding:0 2px;border:0;
  background:none;color:#a8761f;cursor:help}
.bflag:focus-visible{outline:2px solid var(--ink);outline-offset:1px;border-radius:3px}
.empty{color:var(--muted);font-style:italic;padding:20px 0}
#tip{position:fixed;z-index:50;pointer-events:none;background:var(--ink);color:#f7efda;
  padding:9px 11px;border-radius:8px;font-size:12.5px;max-width:260px;opacity:0;transition:opacity .12s;
  box-shadow:0 6px 20px rgba(0,0,0,.25)}
#tip.show{opacity:1}
#tip .th{font-weight:700;margin-bottom:3px;text-transform:capitalize}
#tip .tr{display:flex;justify-content:space-between;gap:14px}
#tip .tt{color:#cdbf9a;font-size:11px;margin-top:4px}
footer{color:var(--muted);font-size:12px;margin-top:30px;line-height:1.7}
/* ---- Section 2 walkthrough ---- */
/* pinned step-scroller: the CARD is pinned and swaps in place as you scroll; the rail is the moving spine */
.wt-scroller{position:relative}                       /* height set inline = (number of players)*100vh */
.wt-stage{position:sticky;top:0;min-height:82vh;display:grid;grid-template-columns:212px 1fr;
  gap:32px;align-items:start;padding-top:4vh}
.wt-railwrap{position:relative;align-self:start;padding-top:8px}
#wt-rail{list-style:none;margin:0;padding:0;border-left:2px solid var(--line)}
.wt-railitem{display:flex;align-items:baseline;gap:9px;padding:11px 12px;cursor:pointer;color:var(--muted);
  transition:color .25s}
.wt-railitem .rk{font-size:11px;width:13px}
.wt-railitem .rn{flex:1;font-size:14px}
.wt-railitem .rg{font-size:12px}
.wt-railitem.active{color:var(--ink);font-weight:600}
.wt-railitem:focus-visible{outline:2px solid var(--strong);outline-offset:2px}
.wt-progress{position:absolute;left:-2px;top:0;width:3px;height:44px;background:var(--ink);
  border-radius:3px;transition:top .12s ease-out}      /* slides down with scroll progress */
.wt-cardholder{position:relative;min-height:430px;display:flex;align-items:flex-start}
.wt-card{position:relative;display:none;width:100%;grid-template-columns:170px 1fr;gap:20px;
  background:var(--panel);border:1px solid var(--line);border-radius:16px;padding:20px;
  box-shadow:0 12px 32px rgba(40,30,10,.14)}
.wt-card.active{display:grid;animation:wtin .42s ease}
@keyframes wtin{from{opacity:0;transform:translateY(12px) scale(.99)}to{opacity:1;transform:none}}
.wt-badge{position:absolute;top:12px;left:12px;font-size:11px;color:var(--muted);
  background:var(--cream);border:1px solid var(--line);border-radius:20px;padding:1px 9px;z-index:1}
/* accolades: quiet gold reference cluster, top-right, secondary to the tier bar (the hero) */
.wt-accolades{position:absolute;top:16px;right:18px;display:flex;gap:13px;align-items:center}
.acc{display:inline-flex;align-items:center;gap:3px;color:#a8842e;cursor:help}
.acc:focus-visible{outline:2px solid var(--strong);outline-offset:2px;border-radius:3px}
.acc-ic{width:19px;height:19px;fill:currentColor;display:block}
.acc-n{font-size:12px;color:var(--muted);font-weight:600;letter-spacing:-.02em}
.acc-empty{color:var(--line);font-size:15px;font-weight:600}
.wt-photo{width:170px;height:212px;object-fit:cover;border-radius:11px;border:1px solid rgba(40,30,10,.18);
  box-shadow:0 1px 4px rgba(40,30,10,.12);background:#e9dec0;align-self:start}
.wt-name{margin:2px 0 1px;font-size:22px;font-weight:700}
.wt-sub{color:var(--muted);font-size:13px;margin-bottom:10px}
.wt-blurb{margin:12px 0 0;font-size:13.5px;line-height:1.55;color:#343024}
.seam{text-align:center;margin:22px 0 8px;display:flex;flex-direction:column;gap:2px;align-items:center}
.seam-end{font-size:11px;letter-spacing:.16em;text-transform:uppercase;color:var(--muted)}
.seam strong{font-size:17px}
.seam-arrow{font-size:20px;color:var(--mid)}
.credits{margin-top:14px}
.credits ul{margin:5px 0 0;padding-left:18px}
.credits li{margin:2px 0}
.credits a{color:inherit}
@media(max-width:760px){                                /* mobile: drop the pin — stacked cards, all shown */
  #wt-scroller{height:auto!important}
  .wt-stage{position:static;display:block;min-height:0}
  .wt-railwrap{display:none}
  .wt-cardholder{display:flex;flex-direction:column;gap:22px;min-height:0}
  .wt-card{display:grid!important;animation:none;grid-template-columns:112px 1fr;gap:14px;
    box-shadow:0 2px 8px rgba(40,30,10,.1)}
  .wt-photo{width:112px;height:140px}
}
@media(max-width:430px){.wt-card{grid-template-columns:1fr}.wt-photo{width:100%;height:240px;object-position:50% 25%}}
@media (max-width:560px){.bar{height:32px}.stat .v{font-size:18px}}
@media (prefers-reduced-motion:reduce){*{transition:none!important}}
</style>
</head>
<body>
<svg width="0" height="0" style="position:absolute" aria-hidden="true"><defs>
  <symbol id="ic-trophy" viewBox="0 0 24 24"><path d="M7 3v2H4v3a4 4 0 0 0 4 4h.2A5 5 0 0 0 11 14.9V17H8v2h8v-2h-3v-2.1a5 5 0 0 0 2.8-2.9H16a4 4 0 0 0 4-4V5h-3V3H7zM6 7v2.7A2 2 0 0 1 4.6 8 2 2 0 0 1 4 7h2zm12 0h2a2 2 0 0 1-.6 1A2 2 0 0 1 18 9.7V7z"/></symbol>
  <symbol id="ic-ball" viewBox="0 0 24 24"><circle cx="12" cy="8.4" r="5.4" fill="none" stroke="currentColor" stroke-width="1.5"/><path d="M12 5.3l2.4 1.7-.9 2.8h-3L9.6 7z"/><path d="M11 14h2v2.1h3V18H8v-1.9h3z"/></symbol>
  <symbol id="ic-boot" viewBox="0 0 24 24"><path d="M3 7c.2 1.8.5 3.8 1 4.8.4.8 1.1 1.2 2.6 1.2H19a2 2 0 0 1 2 2v1.2H4.3A1.3 1.3 0 0 1 3 16V7z"/><path d="M5.5 17v1.5M8.5 17v1.5M11.5 17v1.5M14.5 17v1.5M17.5 17v1.5" stroke="currentColor" stroke-width="1.3"/></symbol>
</defs></svg>
<div class="wrap">
<header>
  <h1>World Cup Scorers — by Opponent Strength</h1>
  <p class="sub">For each top scorer, how strong were the teams they scored against? Strength is the
  opponent's World Football Elo, frozen before each tournament. The metric describes <em>who a player
  happened to face</em> — shaped by the draw and the knockout structure as much as the player.</p>
  <p class="conv"><b>Tiers:</b> each tournament's qualified field is ranked by Elo; the top quarter is
  <b>elite</b>, then strong, mid, weak. <b>Elo as of Dec 31 of the year before the tournament.</b>
  Bar length is proportional to goals, so a longer bar means more goals.</p>
</header>
<hr class="rule">

<details class="methodology" id="methodology">
  <summary class="section">How to read this</summary>
  <p class="sub">This page measures, for the World Cup's top scorers, <em>how strong the teams they
  scored against were</em> — by each opponent's World Football Elo. It describes <em>which opponents a
  player happened to face</em>, which is shaped by the draw and the knockout structure as much as by
  the player. Every term below is defined once here; metric labels elsewhere link back to it.</p>
  <dl class="glossary">
    <div id="g-elo"><dt>Elo — World Football Elo</dt><dd>A single team-strength number, chess-style:
      every result moves it, adjusted for goal margin, match importance and home advantage. From
      eloratings.net. Studies have found Elo-based ratings predict results better than the old FIFA
      ranking (Lasek et al., 2013); FIFA itself adopted an Elo-based method in 2018.</dd></div>
    <div id="g-frozen"><dt>Frozen pre-tournament</dt><dd>Each opponent's Elo is taken as of Dec 31 of
      the year <em>before</em> the tournament, so the tournament's own results can't contaminate the
      rating.</dd></div>
    <div id="g-tier"><dt>Tier / percentile</dt><dd>Each tournament's qualified field is ranked by
      frozen Elo; the top quarter is <strong>elite</strong>, then strong, mid, weak. Tiers are
      relative to <em>that</em> tournament's field — era-fair, so a 16-team and a 48-team edition
      compare fairly.</dd></div>
    <div id="g-elite"><dt>Elite share</dt><dd>Share of a player's goals scored against elite
      (top-quarter) opponents. One stat among several, and boundary-sensitive — see the
      <span class="mark">*</span> mark.</dd></div>
    <div id="g-avgelo"><dt>Avg opp Elo</dt><dd>Mean frozen Elo of the teams a player scored against —
      raw and era-revealing (not adjusted across eras). The companion lens to elite share.</dd></div>
    <div id="g-marks"><dt>The <span class="mark">*</span> and <span class="dagger">†</span> marks</dt>
      <dd><span class="mark">*</span> — a goal sits within ~3.5 Elo of a tier boundary, so that one
      goal's tier hinges on a near-tie (the percentage is exact; that single input is fragile).
      <span class="dagger">†</span> — a cross-era comparison; read elite share alongside absolute
      Elo.</dd></div>
  </dl>
</details>
<hr class="rule">

<section id="walkthrough">
  <h2 class="section">The 11-plus club — a guided tour</h2>
  <p class="sub">The players with 11 or more World Cup goals, ranked by tally — and where tallies tie, the
  more concentrated first (fewer tournaments), so a haul packed into one World Cup ranks above the same
  haul spread across several. Scroll through them; each card shows not <em>how many</em> they scored but
  <em>how strong the teams were</em>.</p>
  <div class="wt-scroller" id="wt-scroller">
    <div class="wt-stage">
      <nav class="wt-railwrap" aria-label="Scorers ranked by goals">
        <ol id="wt-rail"></ol>
        <div class="wt-progress" id="wt-progress" aria-hidden="true"></div>
      </nav>
      <div class="wt-cardholder" id="wt-cardholder"></div>
    </div>
  </div>
</section>

<div class="seam" role="separator">
  <strong>Now compare any of the %%ROSTER_N%% scorers with 9+ World Cup goals</strong>
  <span class="seam-arrow" aria-hidden="true">↓</span>
</div>
<hr class="rule">

<div class="legend" aria-hidden="false">
  <a class="sw k" href="#g-tier"><i style="background:var(--elite)"></i> Elite <small>top quarter of field</small></a>
  <span class="sw"><i style="background:var(--strong)"></i> Strong</span>
  <span class="sw"><i style="background:var(--mid)"></i> Mid</span>
  <span class="sw"><i style="background:var(--weak)"></i> Weak <small>bottom quarter</small></span>
</div>

<div class="roster-head">
  <h2 class="section">Choose players to compare</h2>
  <label class="sortctl">Rank by
    <select id="sortby" aria-label="Rank scorers by">
      <option value="goals">Goals</option>
      <option value="elo">Avg opp Elo</option>
      <option value="elite">Elite share</option>
      <option value="az">A–Z</option>
    </select>
  </label>
</div>
<div class="roster" id="roster" role="group" aria-label="Player roster"></div>
<p class="hint">Click to add or remove. Two or more players stack for direct comparison.</p>

<div class="era" id="era" role="note"></div>
<div id="cards"></div>
</div>
<div id="tip" role="status" aria-live="polite"></div>

<script>
const DATA = %%DATA%%;
const PHOTOS = %%PHOTOS%%;
const ACCOLADES = %%ACCOLADES%%;
const ORDER = ["elite","strong","mid","weak"];
const TIERCOL = {elite:"var(--elite)",strong:"var(--strong)",mid:"var(--mid)",weak:"var(--weak)"};
const MAXG = %%MAXG%%;
const NAMES = Object.keys(DATA);
let selected = ["Lionel Messi","Kylian Mbappé"];

// THE ranking rule, total & deterministic, used everywhere "by goals" appears (walkthrough + comparison
// tool) so a tied tally orders identically in both — never a same-list-two-orders discrepancy, and never
// a silent fall-back to insertion order. goals ↓ → fewest tournaments ↑ (concentrated scoring first, a
// stated value — see the walkthrough intro) → earliest first WC year ↑ → name (exhaustive fallback,
// never the operative tie-break). Mirrors the Python roster key in build_ui.py.
function firstYear(n){ return Math.min(...DATA[n].per_tournament.map(t=>t.year)); }
function byGoals(a,b){
  return DATA[b].goals-DATA[a].goals
      || DATA[a].tournaments-DATA[b].tournaments
      || firstYear(a)-firstYear(b)
      || a.localeCompare(b);
}

let sortKey="goals";   // goals | elo | elite | az
function sortedNames(){
  const ns=[...NAMES];
  if(sortKey==="az")    return ns.sort((a,b)=>a.localeCompare(b));
  if(sortKey==="goals") return ns.sort(byGoals);
  const v={elo:n=>DATA[n].avg_opp_elo, elite:n=>DATA[n].elite_share}[sortKey];
  return ns.sort((a,b)=> v(b)-v(a) || byGoals(a,b));   // elo/elite ties break by the same total rule
}
// chip metric text. When ranking by a single metric, the honesty context rides along — the boundary
// flag (*) and the sample size (tournaments spanned) stay visible, so a high elite% from one flagged
// tournament can't read as a clean leaderboard number.
function chipMeta(name){
  const p=DATA[name];
  const flag=p.boundary_flag ? '<span class="cflag" title="boundary-fragile elite share">*</span>' : '';
  const t=`<span class="ct num">${p.tournaments} WC</span>`;
  if(sortKey==="elite") return `<span class="g num">${Math.round(p.elite_share*100)}%</span>${flag}${t}`;
  if(sortKey==="elo")   return `<span class="g num">${Math.round(p.avg_opp_elo)}</span>${t}`;
  return `<span class="g num">${p.goals}</span>`;   // goals / A–Z
}
function buildRoster(){
  const r=document.getElementById("roster");
  r.innerHTML="";
  const ranked=sortKey!=="goals"&&sortKey!=="az";
  sortedNames().forEach((name,i)=>{
    const b=document.createElement("button");
    b.className="chip"+(ranked?" chip-ranked":""); b.type="button";
    b.setAttribute("aria-pressed", selected.includes(name));
    const rank=ranked?`<span class="crank num">${i+1}</span>`:"";
    b.innerHTML=`${rank}${name} ${chipMeta(name)}`;
    b.onclick=()=>{ selected.includes(name) ? selected=selected.filter(n=>n!==name)
                                             : selected=[...selected,name]; render(); };
    r.appendChild(b);
  });
}

function eraSpan(){
  let yrs=[];
  selected.forEach(n=>DATA[n].per_tournament.forEach(t=>yrs.push(t.year)));
  if(!yrs.length) return null;
  return [Math.min(...yrs), Math.max(...yrs)];
}

function buildBar(p){   // ONE block per tier, fixed order elite→strong→mid→weak (best Elo left → weakest
                       // right). No per-tournament subdivision — that detail lives in the hover.
  let cells="";       // shared by comparison + walkthrough so they can't drift.
  ORDER.forEach(tier=>{
    const cnt=p.career_tiers[tier];
    if(!cnt) return;                                   // skip empty tiers (≤4 blocks per scorer)
    const rows=p.per_tournament.filter(t=>t.by_tier[tier]).sort((a,b)=>a.year-b.year).map(t=>{
      const opps=t.by_tier[tier].opponents.map(o=>`${o.name}${o.goals>1?' ×'+o.goals:''}`).join(", ");
      return `${t.year} — ${opps}`;
    });
    const lab=`${cnt} ${tier}: `+rows.join("; ");
    cells+=`<div class="cell" tabindex="0" role="img" aria-label="${lab.replace(/"/g,'&quot;')}" `+
      `style="flex:${cnt} 0 0;background:${TIERCOL[tier]}" `+
      `data-tier="${tier}" data-count="${cnt}" data-rows="${rows.join('§').replace(/"/g,'&quot;')}"></div>`;
  });
  return `<div class="bar" style="--w:${p.goals};--maxg:${MAXG}">${cells}</div>`;
}
function eliteMarks(p, crossEra){
  const dagger = crossEra ? '<sup class="dagger" title="Cross-era: read with absolute Elo">†</sup>' : '';
  const bf=p.boundary_flag;
  const bflag = bf ? `<button class="bflag" tabindex="0" data-note="${bf.note.replace(/"/g,'&quot;')}" `+
      `aria-label="Boundary note: ${bf.note.replace(/"/g,'&quot;')}">*</button>` : '';
  return dagger+bflag;
}

function render(){
  buildRoster();
  const span=eraSpan();
  // cross-era is inherently a comparison concept: require 2+ players before flagging an era gap.
  // (A lone long-career player must never be flagged "cross-era against himself".)
  const crossEra = selected.length >= 2 && span && (span[1]-span[0] > 20);
  const era=document.getElementById("era");
  if(crossEra){
    era.classList.add("show");
    era.innerHTML=`<b>Cross-era comparison · ${span[0]}–${span[1]}</b><br>`+
      `Percentile tiers are era-fair (each player judged against their own field). Absolute Elo is `+
      `era-revealing (raw rating, not adjusted across eras). Read elite% and avg Elo together — `+
      `the elite% is marked <span class="dagger">†</span> below as a reminder.`;
  } else era.classList.remove("show");

  const cards=document.getElementById("cards");
  cards.innerHTML="";
  if(!selected.length){ cards.innerHTML='<p class="empty">Select a player above to begin.</p>'; return; }

  selected.forEach(name=>{
    const p=DATA[name];
    const card=document.createElement("section"); card.className="card";
    const ct=p.career_tiers;
    const elitePct=Math.round(p.elite_share*100);
    const marks=eliteMarks(p, crossEra);
    card.innerHTML=`
      <div class="top">
        <h3 class="name">${name}</h3>
        <span class="meta num">${COUNTRY[name]||''} · ${yearsOf(p)}</span>
      </div>
      <div class="bartrack">${buildBar(p)}</div>
      <div class="tiers">
        <span><b class="num">${ct.elite}</b> elite</span>
        <span><b class="num">${ct.strong}</b> strong</span>
        <span><b class="num">${ct.mid}</b> mid</span>
        <span><b class="num">${ct.weak}</b> weak</span>
      </div>
      <div class="stats">
        <div class="stat"><a class="k" href="#g-elite">Elite share</a><div class="v num">${elitePct}%${marks}</div></div>
        <div class="stat"><a class="k" href="#g-avgelo">Avg opp Elo</a><div class="v num">${Math.round(p.avg_opp_elo)}</div></div>
        <div class="stat"><div class="k">Goals</div><div class="v num">${p.goals}</div></div>
        <div class="stat"><div class="k">Tournaments</div><div class="v num">${p.tournaments}</div></div>
      </div>`;
    cards.appendChild(card);
  });
  wireTips();
}

const tip=document.getElementById("tip");
function showTip(el){   // tier block -> that tier's goals broken down by tournament
  const tier=el.dataset.tier, cnt=el.dataset.count, rows=(el.dataset.rows||"").split("§");
  tip.innerHTML=`<div class="th">${cnt} ${tier}</div>`+rows.map(r=>`<div class="tt">${r}</div>`).join("");
  tip.classList.add("show");
}
function moveTip(x,y){
  const r=tip.getBoundingClientRect();
  let nx=x+14, ny=y+14;
  if(nx+r.width>innerWidth) nx=x-r.width-14;
  if(ny+r.height>innerHeight) ny=y-r.height-14;
  tip.style.left=nx+"px"; tip.style.top=ny+"px";
}
function showNote(el){
  tip.innerHTML=`<div class="th">Boundary note</div><div class="tt">${el.dataset.note}</div>`;
  tip.classList.add("show");
}
function showAcc(el){ tip.innerHTML=`<div class="th">${el.dataset.tip}</div>`; tip.classList.add("show"); }
function wireTips(root){   // root-scoped so re-rendering the comparison never double-wires walkthrough cells
  (root||document).querySelectorAll(".cell").forEach(el=>{
    el.addEventListener("mouseenter",e=>{showTip(el);moveTip(e.clientX,e.clientY);});
    el.addEventListener("mousemove",e=>moveTip(e.clientX,e.clientY));
    el.addEventListener("mouseleave",()=>tip.classList.remove("show"));
    el.addEventListener("focus",()=>{const r=el.getBoundingClientRect();showTip(el);moveTip(r.left,r.bottom);});
    el.addEventListener("blur",()=>tip.classList.remove("show"));
  });
  (root||document).querySelectorAll(".acc").forEach(el=>{   // trophy/ball/boot -> custom tooltip (award + year)
    el.addEventListener("mouseenter",e=>{showAcc(el);moveTip(e.clientX,e.clientY);});
    el.addEventListener("mousemove",e=>moveTip(e.clientX,e.clientY));
    el.addEventListener("mouseleave",()=>tip.classList.remove("show"));
    el.addEventListener("focus",()=>{const r=el.getBoundingClientRect();showAcc(el);moveTip(r.left,r.bottom);});
    el.addEventListener("blur",()=>tip.classList.remove("show"));
  });
  (root||document).querySelectorAll(".bflag").forEach(el=>{
    el.addEventListener("mouseenter",e=>{showNote(el);moveTip(e.clientX,e.clientY);});
    el.addEventListener("mousemove",e=>moveTip(e.clientX,e.clientY));
    el.addEventListener("mouseleave",()=>tip.classList.remove("show"));
    el.addEventListener("focus",()=>{const r=el.getBoundingClientRect();showNote(el);moveTip(r.left,r.bottom);});
    el.addEventListener("blur",()=>tip.classList.remove("show"));
    el.addEventListener("click",e=>e.preventDefault());
  });
}

// ---------- Section 2: top-scorer walkthrough (data-driven from the live ≥11-goal roster) ----------
// WALK is computed after COUNTRY/BLURB (it depends on them) — see the crosser-rule block below.
const COUNTRY = {"Lionel Messi":"Argentina","Kylian Mbappé":"France","Miroslav Klose":"Germany",
  "Ronaldo":"Brazil","Gerd Müller":"West Germany","Just Fontaine":"France","Pelé":"Brazil",
  "Jürgen Klinsmann":"Germany","Sándor Kocsis":"Hungary","Harry Kane":"England",
  "Cristiano Ronaldo":"Portugal","Gabriel Batistuta":"Argentina","Gary Lineker":"England",
  "Grzegorz Lato":"Poland","Helmut Rahn":"West Germany","Teófilo Cubillas":"Peru",
  "Thomas Müller":"Germany","Ademir de Menezes":"Brazil","Christian Vieri":"Italy",
  "David Villa":"Spain","Eusébio":"Portugal","Jairzinho":"Brazil",
  "Karl-Heinz Rummenigge":"West Germany","Paolo Rossi":"Italy","Roberto Baggio":"Italy",
  "Uwe Seeler":"West Germany","Vavá":"Brazil"};
const BLURB = {
  "Lionel Messi":"Five World Cups, 2006–2026 — the all-time record, and the widest spread on this page. "+
    "His elite-tier goals, both in the 2022 final against France, sit at the head of a long tail of mid- "+
    "and weak-tier goals built up across five tournaments.",
  "Kylian Mbappé":"Three World Cups, 2018–2026 — a tally weighted toward the top tiers, elite and strong "+
    "together making up most of the bar. Five of those goals came against Argentina (twice in 2018, "+
    "three times in the 2022 final); the lower-tier goals come mostly from his 2026 run.",
  "Harry Kane":"England, three World Cups (2018–2026). The bar splits to the extremes — a run of "+
    "weak-tier goals from the 2018 group stage (Panama, Tunisia) set against elite-tier strikes on "+
    "France (2022) and Croatia twice (2026), with little in the middle tiers. The * on his elite share "+
    "marks a 2018 goal against Colombia that sits exactly on the quartile line.",
  "Cristiano Ronaldo":"Portugal, across six World Cups (2006–2026) — more editions than any other "+
    "scorer here. His elite tier is a single burst: the 2018 hat-trick against Spain. Everything else "+
    "spreads thin down the tiers over two decades — strong against Iran (2006), mid against Uzbekistan "+
    "(2026), and weak against North Korea, Ghana and Morocco.",
  "Miroslav Klose":"Four World Cups, 2002–2014, 16 goals split almost evenly across the tiers (five "+
    "elite, five mid, five weak). The elite goals span three tournaments — Argentina in 2006 and 2010, "+
    "England in 2010, Brazil in 2014 — while the 2002 haul came against weaker sides.",
  "Ronaldo":"Three World Cups, 1998–2006, 15 goals. The bar is dominated by the mid tier (nine goals) — "+
    "the 2002 winning run came largely against Turkey, China and Costa Rica. His one elite-tier goal, "+
    "marked *, sits just inside the quartile cut.",
  "Gerd Müller":"Two World Cups, 1970–1974, 14 goals in a notably even spread — four each in the elite, "+
    "strong and mid tiers. The elite goals came against Italy (twice) and England in 1970, and Poland in "+
    "the 1974 semi-final.",
  "Just Fontaine":"One World Cup, 1958 — all 13 goals in a single edition, still the record for one "+
    "tournament. The distribution leans strong (six goals); the lone elite goal, against that year's "+
    "fourth-ranked side Brazil, sits right on the quartile line.",
  "Pelé":"Four World Cups, 1958–1970, 12 goals — a bar dominated by the mid tier (nine goals), "+
    "reflecting the opponents drawn across four tournaments. His single elite-tier goal came against "+
    "Italy in the 1970 final.",
  "Jürgen Klinsmann":"Three World Cups, 1990–1998, 11 goals weighted toward the lower tiers (five weak, "+
    "three mid). His one elite-tier goal came against the Netherlands in 1990, the tournament he won "+
    "with West Germany.",
  "Sándor Kocsis":"One World Cup, 1954 — eleven goals in a single edition, the bulk in the strong tier "+
    "(six) with none in the mid tier. Both elite-tier goals came against Brazil, in the quarter-final.",
};
// Boundary-crosser rule: the walkthrough = every player with ≥11 WC goals, ranked by goals — BUT only
// those with a staged photo AND blurb AND country. Anyone who crosses without all three is HELD (never
// render a photoless/blurbless card); held names are logged so the build/workflow can flag them.
const WALK_ELIGIBLE = Object.keys(DATA).filter(n=>DATA[n].goals>=11).sort(byGoals);
const WALK = WALK_ELIGIBLE.filter(n=>PHOTOS[n] && BLURB[n] && COUNTRY[n]);
const WALK_HELD = WALK_ELIGIBLE.filter(n=>!(PHOTOS[n] && BLURB[n] && COUNTRY[n]));
if(WALK_HELD.length) console.warn('Walkthrough HELD (missing photo/blurb/country):', WALK_HELD);
function yearsOf(p){ const ys=p.per_tournament.map(t=>t.year), a=Math.min(...ys), b=Math.max(...ys);
  return a===b ? (''+a) : (a+'–'+b); }

const ACC_DEF=[["wc","ic-trophy","World Cup"],["ball","ic-ball","Golden Ball"],["boot","ic-boot","Golden Boot"]];
function accoladeHTML(name){   // top-right cluster; omit empty categories; all-zero → a quiet "—".
  const a=ACCOLADES[name]||{};   // hover shows award + year(s), e.g. "Golden Ball — 2014, 2022"
  const parts=ACC_DEF.map(([key,sym,label])=>{
    const yrs=a[key]||[];
    if(!yrs.length) return "";
    const t=`${label} — ${yrs.join(", ")}`;
    return `<span class="acc" tabindex="0" role="img" aria-label="${t}" data-tip="${t}"><svg class="acc-ic"><use href="#${sym}"/></svg><span class="acc-n num">×${yrs.length}</span></span>`;
  }).filter(Boolean);
  return parts.length
    ? `<div class="wt-accolades">${parts.join("")}</div>`
    : `<div class="wt-accolades acc-empty" title="No World Cup win, Golden Ball or Golden Boot">—</div>`;
}
function wtCardHTML(name,idx,total){
  const p=DATA[name], ph=PHOTOS[name]||{};
  return `
    <div class="wt-badge num">${idx+1} / ${total}</div>
    ${accoladeHTML(name)}
    <img class="wt-photo" src="${ph.b64||''}" alt="${name}, ${ph.era||''}" width="170" height="212">
    <div class="wt-body">
      <h3 class="wt-name">${name}</h3>
      <div class="wt-sub num">${COUNTRY[name]||''} · ${yearsOf(p)}</div>
      <div class="bartrack">${buildBar(p)}</div>
      <div class="tiers">
        <span><b class="num">${p.career_tiers.elite}</b> elite</span>
        <span><b class="num">${p.career_tiers.strong}</b> strong</span>
        <span><b class="num">${p.career_tiers.mid}</b> mid</span>
        <span><b class="num">${p.career_tiers.weak}</b> weak</span>
      </div>
      <div class="stats">
        <div class="stat"><a class="k" href="#g-elite">Elite share</a><div class="v num">${Math.round(p.elite_share*100)}%${eliteMarks(p,false)}</div></div>
        <div class="stat"><a class="k" href="#g-avgelo">Avg opp Elo</a><div class="v num">${Math.round(p.avg_opp_elo)}</div></div>
        <div class="stat"><div class="k">Goals</div><div class="v num">${p.goals}</div></div>
        <div class="stat"><div class="k">Tournaments</div><div class="v num">${p.tournaments}</div></div>
      </div>
      <p class="wt-blurb">${BLURB[name]||''}</p>
    </div>`;
}

// Pinned step-scroller: card stays put and SWAPS as you scroll; rail spine + marker show progress.
function renderWalkthrough(){
  const order=[...WALK].sort(byGoals);
  const N=order.length;
  const rail=document.getElementById("wt-rail");
  const holder=document.getElementById("wt-cardholder");
  const scroller=document.getElementById("wt-scroller");
  const marker=document.getElementById("wt-progress");
  const reduced=()=>matchMedia("(prefers-reduced-motion:reduce)").matches;
  const mobile=()=>matchMedia("(max-width:760px)").matches;
  scroller.style.height=(N*100)+"vh";          // N viewport-heights of scroll = N steps
  rail.innerHTML=""; holder.innerHTML="";
  order.forEach((name,idx)=>{
    const li=document.createElement("li");
    li.className="wt-railitem"; li.dataset.idx=idx; li.tabIndex=0;
    li.innerHTML=`<span class="rk num">${idx+1}</span><span class="rn">${name}</span><span class="rg num">${DATA[name].goals}</span>`;
    const go=()=>scrollTo({top:scroller.offsetTop+((idx+0.5)/N)*scroller.offsetHeight-innerHeight/2, behavior:reduced()?"auto":"smooth"});
    li.onclick=go; li.onkeydown=e=>{if(e.key==="Enter")go();};
    rail.appendChild(li);
    const art=document.createElement("article");
    art.className="wt-card"; art.dataset.idx=idx;
    art.innerHTML=wtCardHTML(name,idx,N);
    holder.appendChild(art);
  });
  wireTips(holder);
  const cards=[...holder.children], items=[...rail.children];
  let cur=-1;
  function setActive(i){
    if(i===cur)return; cur=i;
    cards.forEach(c=>c.classList.toggle("active",+c.dataset.idx===i));
    items.forEach(it=>it.classList.toggle("active",+it.dataset.idx===i));
  }
  function onScroll(){
    if(mobile()){ cards.forEach(c=>c.classList.add("active")); return; }   // mobile: all shown, no pin
    const vh=innerHeight, total=scroller.offsetHeight-vh;
    const scrolled=Math.min(Math.max(-scroller.getBoundingClientRect().top,0),total);
    const prog=total>0?scrolled/total:0;
    setActive(Math.min(N-1,Math.floor(prog*N+1e-6)));
    marker.style.top=(prog*(rail.offsetHeight-marker.offsetHeight))+"px";
  }
  let ticking=false;
  addEventListener("scroll",()=>{ if(!ticking){ticking=true;requestAnimationFrame(()=>{onScroll();ticking=false;});} },{passive:true});
  addEventListener("resize",onScroll);
  onScroll();
}

// footer photo credits, built from the embedded metadata
function renderCredits(){
  const el=document.getElementById("credits");
  const seen=new Set(); let html="";
  WALK.forEach(name=>{
    const ph=PHOTOS[name]; if(!ph||seen.has(name))return; seen.add(name);
    html+=`<li>${name} — photo: ${ph.author}, <a href="${ph.license_url}">${ph.license}</a> `+
      `(<a href="${ph.source}">Wikimedia Commons</a>)</li>`;
  });
  el.innerHTML=html;
}

// init after full parse so footer elements (#credits) exist when referenced
// the methodology is collapsible; a glossary reference link (#g-…) must still work when it's closed —
// open it on any such click (delegated, covers dynamic card links) and on direct hash navigation.
document.addEventListener("click",e=>{
  if(e.target.closest('a[href^="#g-"]')){ const m=document.getElementById("methodology"); if(m) m.open=true; }
});
document.addEventListener("DOMContentLoaded",()=>{
  render(); renderWalkthrough(); renderCredits();
  document.getElementById("sortby").addEventListener("change",e=>{ sortKey=e.target.value; buildRoster(); });
  if(location.hash.startsWith("#g-")){ const m=document.getElementById("methodology"); if(m){ m.open=true; document.querySelector(location.hash)?.scrollIntoView(); } }
});
</script>
<footer>
  <details class="methodology">
    <summary class="section">Sources &amp; credits</summary>
    <div class="foot-body">
  Goals & scorers: martj42/international_results. Opponent strength: World Football Elo
  (eloratings.net), frozen Dec 31 of the year before each tournament. Own goals excluded; penalties
  counted. Roster: all %%ROSTER_N%% players with ≥ 9 World Cup goals — provisional while the 2026 tournament is
  in progress. Defunct nations kept era-correct (West Germany, East Germany, USSR, Czechoslovakia,
  Yugoslavia, Serbia &amp; Montenegro, Zaire as separate entities).
  <br><b>*</b> on an elite-share figure marks a goal sitting within ~3.5 Elo of a tier boundary — the
  percentage is exact, but that one goal's tier hinges on a near-tie. Hover the mark for the specific
  goal. <b>†</b> marks a cross-era comparison (read elite% with absolute Elo).
  <br>Accolade icons (World Cup wins, Golden Ball, Golden Boot): Golden Boots include FIFA's backdated
  top-scorer recognitions (1930–1978); the Golden Ball is awarded only from 1982.
  <div class="credits"><b>Player photos</b> (Wikimedia Commons, reused under each stated licence):
  <ul id="credits"></ul></div>
    </div>
  </details>
</footer>
</body>
</html>
"""

# Boundary-crosser rule (server-side): every ≥11 player must have a staged photo + blurb + country.
# A held crosser is a HALT, not a warning — refusing to ship a walkthrough that silently drops a
# qualifying player. Better one day stale than incomplete-and-green. Mirrors the JS WALK filter.
import re as _re
_blurb   = set(_re.findall(r'"([^"]+)":"', _re.search(r'const BLURB = \{(.*?)\n\};', HTML, _re.S).group(1)))
_country = set(_re.findall(r'"([^"]+)":"', _re.search(r'const COUNTRY = \{(.*?)\};', HTML, _re.S).group(1)))
_eligible = sorted([n for n in roster_names if data[n]["goals"] >= 11],
                   key=lambda n: (-data[n]["goals"], data[n]["tournaments"], _first_year(data[n]), n))
_held = [n for n in _eligible if not (n in photos and n in _blurb and n in _country)]
if _held:
    print(f"HALT: {len(_held)} player(s) crossed ≥11 without full staging (photo+blurb+country): {_held}")
    print("Refusing to write index.html — a qualifying player would be silently dropped from the "
          "walkthrough. Stage the missing assets, then rebuild. (No file written; last-good stays live.)")
    sys.exit(1)

out = (HTML.replace("%%DATA%%", DATA_JS)
           .replace("%%PHOTOS%%", PHOTOS_JS)
           .replace("%%MAXG%%", str(max_goals))
           .replace("%%ACCOLADES%%", ACCOLADES_JS)
           .replace("%%ROSTER_N%%", str(len(roster_names))))   # dynamic ≥9 roster size (seam + footer)
open("index.html", "w", encoding="utf-8").write(out)
print(f"wrote index.html ({len(out):,} bytes) · {len(roster_names)} players · max goals {max_goals}")
print(f"walkthrough: {len(_eligible)} eligible (≥11), all staged · rendered {_eligible}")
