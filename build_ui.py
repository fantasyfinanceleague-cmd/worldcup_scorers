#!/usr/bin/env python3
"""Build the self-contained index.html from data/player_breakdown.json.

Reproducible: re-run after any data change. The front-end is the "broadcast-dashboard" redesign —
its markup/CSS/JS live as editable source in ui/ (styles.css + bg/app/deepdive/arena.js); this script
transforms the repo's data layer into the window.WCS shape those modules consume and inlines everything
into ONE self-contained index.html (single deployable file, as before).

Data flow: player_breakdown.json (+ base64 photos + hand-sourced ACCOLADES/COUNTRY/BLURB) -> window.WCS.
The ranking rule, the ≥11 walkthrough roster, and the boundary "*" flag all carry over verbatim from the
previous build, so the numbers the page shows are exactly the repo pipeline's own."""
import json, sys, os, re

ROOT = os.path.dirname(os.path.abspath(__file__))
def _read(rel): return open(os.path.join(ROOT, rel), encoding="utf-8").read()

data = json.load(open(os.path.join(ROOT, "data/player_breakdown.json"), encoding="utf-8"))
photos = json.load(open(os.path.join(ROOT, "data/photos.json"), encoding="utf-8"))

# THE ranking rule (mirrored verbatim by the JS `byGoals` in ui/app.js): goals ↓ → fewest tournaments ↑
# (concentrated scoring first — a stated value, surfaced in the walkthrough intro) → earliest first WC
# year ↑ → name (exhaustive deterministic fallback, never the operative tie-break). Total, so tied
# tallies can never silently degrade to insertion order.
def _first_year(p): return min(t["year"] for t in p["per_tournament"])
def _rank_key(kv): p = kv[1]; return (-p["goals"], p["tournaments"], _first_year(p), kv[0])
roster = sorted(data.items(), key=_rank_key)
roster_names = [n for n, _ in roster]
max_goals = max(p["goals"] for _, p in roster)

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

# Nationality per scorer (defunct nations kept era-correct). Hand-sourced, like ACCOLADES.
COUNTRY = {
    "Lionel Messi": "Argentina", "Kylian Mbappé": "France", "Miroslav Klose": "Germany",
    "Ronaldo": "Brazil", "Gerd Müller": "West Germany", "Just Fontaine": "France", "Pelé": "Brazil",
    "Jürgen Klinsmann": "Germany", "Sándor Kocsis": "Hungary", "Harry Kane": "England",
    "Cristiano Ronaldo": "Portugal", "Gabriel Batistuta": "Argentina", "Gary Lineker": "England",
    "Grzegorz Lato": "Poland", "Helmut Rahn": "West Germany", "Teófilo Cubillas": "Peru",
    "Thomas Müller": "Germany", "Ademir de Menezes": "Brazil", "Christian Vieri": "Italy",
    "David Villa": "Spain", "Eusébio": "Portugal", "Jairzinho": "Brazil",
    "Karl-Heinz Rummenigge": "West Germany", "Paolo Rossi": "Italy", "Roberto Baggio": "Italy",
    "Uwe Seeler": "West Germany", "Vavá": "Brazil",
}

# Hand-authored walkthrough blurbs — one per ≥11-goal scorer. Written against THIS repo's data snapshot,
# so every figure they cite matches the numbers the page renders. (The design mock shipped its own,
# slightly reworded, blurbs authored against a fresher data pull; we keep the repo's for consistency.)
BLURB = {
    "Lionel Messi": "Five World Cups, 2006–2026 — the all-time record, and the widest spread on this "
        "page. His elite-tier goals, both in the 2022 final against France, sit at the head of a long "
        "tail of mid- and weak-tier goals built up across five tournaments.",
    "Kylian Mbappé": "Three World Cups, 2018–2026 — a tally weighted toward the top tiers, elite and "
        "strong together making up most of the bar. Five of those goals came against Argentina (twice "
        "in 2018, three times in the 2022 final); the lower-tier goals come mostly from his 2026 run.",
    "Harry Kane": "England, three World Cups (2018–2026). The bar splits to the extremes — a run of "
        "weak-tier goals from the 2018 group stage (Panama, Tunisia) set against elite-tier strikes on "
        "France (2022) and Croatia twice (2026), with little in the middle tiers. The * on his elite "
        "share marks a 2018 goal against Colombia that sits exactly on the quartile line.",
    "Cristiano Ronaldo": "Portugal, across six World Cups (2006–2026) — more editions than any other "
        "scorer here. The bar splits to the extremes: the elite and weak tiers are its two heaviest "
        "blocks, with little between them. The elite goals are the 2018 hat-trick against Spain and a "
        "2026 strike on Croatia; the weak-tier goals gather against North Korea (2010), Ghana (2014 and "
        "2022) and Morocco (2018), either side of a lone strong goal against Iran (2006) and a mid pair "
        "against Uzbekistan (2026).",
    "Miroslav Klose": "Four World Cups, 2002–2014, 16 goals split almost evenly across the tiers (five "
        "elite, five mid, five weak). The elite goals span three tournaments — Argentina in 2006 and "
        "2010, England in 2010, Brazil in 2014 — while the 2002 haul came against weaker sides.",
    "Ronaldo": "Three World Cups, 1998–2006, 15 goals. The bar is dominated by the mid tier (nine "
        "goals) — the 2002 winning run came largely against Turkey, China and Costa Rica. His one "
        "elite-tier goal, marked *, sits just inside the quartile cut.",
    "Gerd Müller": "Two World Cups, 1970–1974, 14 goals in a notably even spread — four each in the "
        "elite, strong and mid tiers. The elite goals came against Italy (twice) and England in 1970, "
        "and Poland in the 1974 semi-final.",
    "Just Fontaine": "One World Cup, 1958 — all 13 goals in a single edition, still the record for one "
        "tournament. The distribution leans strong (six goals); the lone elite goal, against that "
        "year's fourth-ranked side Brazil, sits right on the quartile line.",
    "Pelé": "Four World Cups, 1958–1970, 12 goals — a bar dominated by the mid tier (nine goals), "
        "reflecting the opponents drawn across four tournaments. His single elite-tier goal came "
        "against Italy in the 1970 final.",
    "Jürgen Klinsmann": "Three World Cups, 1990–1998, 11 goals weighted toward the lower tiers (five "
        "weak, three mid). His one elite-tier goal came against the Netherlands in 1990, the "
        "tournament he won with West Germany.",
    "Sándor Kocsis": "One World Cup, 1954 — eleven goals in a single edition, the bulk in the strong "
        "tier (six) with none in the mid tier. Both elite-tier goals came against Brazil, in the "
        "quarter-final.",
}

ORDER = ["elite", "strong", "mid", "weak"]

# ---- WORLD CUP APPEARANCES (matches played) — hand-sourced static data, like ACCOLADES ----
# Definition: appearances INCLUDING substitute apps ("games played" = played). Per-tournament split in
# each comment is the checkable basis. Sourced from each player's Wikipedia "Career statistics →
# International" + match-by-match listings at thesoccerworldcups.com, cross-checked against ESPN/FIFA
# record pages (Pelé 14, Jairzinho 16, Ronaldo 19 double-checked against ESPN/Britannica).
# NOT YET USED BY THE RANKING — see the TODO below. The tie-break stays tournaments-played (derived
# from gated data, so it can never silently rot) until the 2026 final freezes these counts.
# RETIRED = career-final (frozen). ACTIVE (2026) = through the 2022 World Cup only, PROVISIONAL — those
# five MUST be updated with their 2026 matches before the tie-break is switched on.
APPEARANCES = {
    # --- retired: career-final, settled ---
    "Miroslav Klose":        24,   # 2002:7 2006:7 2010:5 2014:5
    "Ronaldo":               19,   # 1994:0 (in squad, unused) 1998:7 2002:7 2006:5
    "Gerd Müller":           13,   # 1970:6 1974:7
    "Just Fontaine":          6,   # 1958:6
    "Pelé":                  14,   # 1958:4 1962:2 1966:2 1970:6 (injury-shortened '62 & '66)
    "Sándor Kocsis":          5,   # 1954:5
    "Jürgen Klinsmann":      17,   # 1990:7 1994:5 1998:5
    "Helmut Rahn":           10,   # 1954:4 1958:6
    "Teófilo Cubillas":      13,   # 1970:4 1978:6 1982:3
    "Gary Lineker":          12,   # 1986:5 1990:7
    "Thomas Müller":         19,   # 2010:6 2014:7 2018:3 2022:3
    "Grzegorz Lato":         20,   # 1974:7 1978:6 1982:7
    "Gabriel Batistuta":     12,   # 1994:4 1998:5 2002:3
    "Ademir de Menezes":      6,   # 1950:6
    "Eusébio":                6,   # 1966:6
    "Vavá":                  10,   # 1958:4 1962:6
    "Jairzinho":             16,   # 1966:3 1970:6 1974:7
    "Paolo Rossi":           14,   # 1978:7 1982:7 1986:0 (in squad, unused — injured)
    "Christian Vieri":        9,   # 1998:5 2002:4
    "Karl-Heinz Rummenigge": 19,   # 1978:5 1982:7 1986:7 (incl. sub apps; starts-only would be ~14)
    "Roberto Baggio":        16,   # 1990:5 1994:7 1998:4
    "David Villa":           12,   # 2006:4 2010:7 2014:1
    "Uwe Seeler":            21,   # 1958:5 1962:4 1966:6 1970:6
    # --- ACTIVE in 2026: PROVISIONAL, through the 2022 World Cup only. UPDATE with 2026 apps before wiring in. ---
    "Lionel Messi":          26,   # 2006:3 2010:5 2014:7 2018:4 2022:7  + 2026 TBD
    "Kylian Mbappé":         14,   # 2018:7 2022:7  + 2026 TBD
    "Harry Kane":            11,   # 2018:6 2022:5  + 2026 TBD
    "Cristiano Ronaldo":     22,   # 2006:6 2010:4 2014:3 2018:4 2022:5  + 2026 TBD
    "Neymar":                13,   # 2014:5 2018:5 2022:3  + 2026 TBD
}
# TODO(after the 2026 final, 2026-07-19): wire appearances into the ranking tie-break — "fewest games
# played" is a truer density measure than fewest tournaments (13 goals in 8 matches beats 13 in 5).
#   1. Update the 5 ACTIVE counts above with their final 2026 appearances (they are through-2022 now).
#   2. In _rank_key (below) AND the JS byGoals (ui/app.js), replace the `tournaments` tie-break term
#      with APPEARANCES[name]; keep the two in lockstep, and thread APPEARANCES into window.WCS so
#      byGoals can read it client-side.
#   3. Freeze the pipeline: disable the daily-build cron (.github/workflows/daily-build.yml) — the data
#      is settled post-tournament, so there is nothing left to re-pull and no way for the hand-sourced
#      counts to drift again.
# Doing this BEFORE the final would rank on through-2022 counts that ignore live 2026 matches (e.g. Kane
# above Müller on a number missing his whole 2026), and it would keep shifting every match — the exact
# silent-staleness failure the gates exist to prevent. So: not yet.

# ---- Boundary-crosser rule (server-side HALT): every player with ≥11 WC goals must have a staged
# photo + blurb + country, or the build refuses to write index.html — never silently drop a qualifying
# scorer from the walkthrough. Better one day stale than incomplete-and-green. Mirrors the ui/app.js WALK
# filter. This runs BEFORE any output is produced. ----
eligible = [n for n in roster_names if data[n]["goals"] >= 11]  # roster_names is already rank-sorted
held = [n for n in eligible if not (n in photos and n in BLURB and n in COUNTRY)]
if held:
    print(f"HALT: {len(held)} player(s) crossed ≥11 without full staging (photo+blurb+country): {held}")
    print("Refusing to write index.html — a qualifying player would be silently dropped from the "
          "walkthrough. Stage the missing assets, then rebuild. (No file written; last-good stays live.)")
    sys.exit(1)
walk = eligible[:]  # all staged (guaranteed by the gate above), already in rank order

# ---- Appearances staleness guard (server-side HALT). Active NOW even though appearances are unused by
# the ranking yet, so a wrong/stale hand-entered count is caught the day it's wrong, not the day it's
# wired in. NOTE: `goals > appearances` is NOT the check — a player scores multiple goals per match
# (Fontaine 13 in 6, Gerd Müller 14 in 13), so that would false-halt half the list. The real invariant
# is `appearances >= distinct WC matches the player scored in` (scoring_matches, from gated goal data):
# you cannot score in a match you did not play. Also require every roster player to have an entry, so a
# new ≥9 crosser can't slip in un-sourced. ----
_missing_apps = [n for n in roster_names if n not in APPEARANCES]
_bad_apps = [(n, APPEARANCES[n], data[n]["scoring_matches"])
             for n in roster_names if n in APPEARANCES and APPEARANCES[n] < data[n]["scoring_matches"]]
if _missing_apps or _bad_apps:
    for n in _missing_apps:
        print(f"HALT: '{n}' is on the ≥9 roster but has no APPEARANCES entry — hand-source it (matches played).")
    for n, ap, sm in _bad_apps:
        print(f"HALT: '{n}' appearances {ap} < {sm} distinct WC matches scored in — count is stale or wrong.")
    print("Refusing to write index.html. (No file written; last-good stays live.)")
    sys.exit(1)


def build_detail(p):
    """Flatten per_tournament -> {tier: [{year, opp, goals, elo}, ...]} for the deep-dive ledger."""
    detail = {t: [] for t in ORDER}
    for t in sorted(p["per_tournament"], key=lambda x: x["year"]):
        for tier, td in t.get("by_tier", {}).items():
            for o in td["opponents"]:
                detail[tier].append({"year": t["year"], "opp": o["name"],
                                     "goals": o["goals"], "elo": o["elo"]})
    return detail


def build_player(name):
    p = data[name]
    ys = [t["year"] for t in p["per_tournament"]]
    ph = photos.get(name)
    return {
        "goals": p["goals"],
        "tournaments": p["tournaments"],
        "tiers": p["career_tiers"],
        "eliteShare": p["elite_share"],
        "avgElo": round(p["avg_opp_elo"]),
        "flag": p.get("boundary_flag"),            # object (truthy) or null — drives the elite-share "*"
        "years": [min(ys), max(ys)],
        "country": COUNTRY.get(name, ""),
        "acc": ACCOLADES.get(name),                # {wc,ball,boot} or null
        "blurb": BLURB.get(name, ""),              # only the ≥11 walkthrough uses this
        "mostPunished": p.get("most_punished"),    # {opponent, goals} — era-correct, precomputed
        "detail": build_detail(p),
        "photo": (ph or {}).get("b64", ""),        # inline data URI -> self-contained
        "photoEra": (ph or {}).get("era", ""),
    }

WCS = {
    "players": {n: build_player(n) for n in roster_names},
    "order": roster_names,
    "walk": walk,
    "maxGoals": max_goals,
}
WCS_JS = json.dumps(WCS, ensure_ascii=False, separators=(",", ":"))

# ---- Per-photo CC attribution (repo requirement, not in the mock). Built for every roster player who
# has a photo, in roster order. CC BY / CC BY-SA legally require crediting author + licence per image. ----
def credits_html():
    items = []
    for name in roster_names:
        ph = photos.get(name)
        if not ph:
            continue
        items.append(
            f'<li>{name} — {ph["author"]}, '
            f'<a href="{ph["license_url"]}">{ph["license"]}</a> '
            f'(<a href="{ph["source"]}">Wikimedia Commons</a>)</li>')
    if not items:
        return ""
    # Collapsed by default (same pattern as the methodology panel). CC BY / CC BY-SA legally require
    # author + licence + link per image, so the attributions are kept in full — never abbreviated.
    return ('<details class="foot-credits"><summary>Player photo credits (' + str(len(items)) +
            ') — Wikimedia Commons, reused under each stated licence, cropped for display</summary>'
            '<ul>' + "".join(items) + "</ul></details>")

CREDITS = credits_html()

# ---- Front-end sources (vendored, editable) inlined into the single self-contained file ----
CSS = _read("ui/styles.css")
JS_MODULES = "\n".join(_read(f"ui/{m}.js") for m in ("bg", "app", "deepdive", "arena"))

# Inline the self-hosted fonts as base64 data URIs so index.html carries no external CDN dependency.
# The @font-face rules in ui/styles.css reference url("fonts/NAME.woff2"); swap each for its data URI.
import base64
def _inline_fonts(css):
    def sub(m):
        rel = m.group(1)
        blob = open(os.path.join(ROOT, "ui", rel), "rb").read()
        b64 = base64.b64encode(blob).decode()
        return f'url(data:font/woff2;base64,{b64}) format("woff2")'
    css2, n = re.subn(r'url\("(fonts/[^"]+\.woff2)"\) format\("woff2"\)', sub, css)
    if n == 0:
        print("HALT: no self-hosted @font-face url() found to inline — fonts would not be self-contained.")
        sys.exit(1)
    print(f"inlined {n} self-hosted font file(s)")
    return css2
CSS = _inline_fonts(CSS)

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>World Cup Scorers — By Opponent Strength</title>
<meta name="description" content="Not just how many you score — who you score against. The World Cup's greatest goalscorers ranked by the strength of the teams they scored against: each opponent's World Football Elo, frozen before every tournament and sorted into four era-fair tiers.">
<style>
%%CSS%%
</style>
</head>
<body>

<!-- living background -->
<div id="fx" aria-hidden="true">
  <canvas id="bgCanvas"></canvas>
  <div id="ambient"></div>
  <div id="cursorGlow"></div>
</div>
<div id="progress"></div>

<!-- top navigation -->
<nav class="topnav" id="topnav">
  <a class="nav-brand" href="#top">WC<span>SCORERS</span></a>
  <div class="nav-links" id="navLinks">
    <a href="#scorers">Top scorers</a>
    <a href="#player">Player</a>
    <a href="#arena">Arena</a>
    <a href="#compare">Compare</a>
  </div>
</nav>

<!-- ============ HERO ============ -->
<header class="hero" id="top">
  <div class="hero-ticker" id="heroTicker" aria-hidden="true"></div>
  <div class="wrap">
    <div class="hero-kicker kicker reveal">FIFA World Cup · 1930 – 2026</div>
    <h1 class="reveal d1">Not just how many<br>you score.<br><span class="stroke">Who you score<br>against.</span></h1>
    <p class="hero-sub reveal d2">A ranking of the World Cup's greatest goalscorers measured by the strength of the teams they scored against — each opponent's World Football Elo, frozen before every tournament and sorted into four era-fair tiers.</p>
    <div class="hero-metrics">
      <div class="hm reveal d2"><span class="v num" data-count="%%ROSTER_N%%">0</span><span class="l">Top scorers</span></div>
      <div class="hm reveal d3"><span class="v num" data-count="96">0</span><span class="l">Years of data</span></div>
      <div class="hm reveal d3"><span class="v num" data-count="22">0</span><span class="l">World Cups</span></div>
      <div class="hm reveal d4"><span class="v num" data-count="4">0</span><span class="l">Strength tiers</span></div>
    </div>
    <div class="hero-legend reveal d4" id="heroLegend"></div>

    <!-- pre-scroll explainer: tier legend (above) + a one-line Elo definition stay visible; the full
         "how this is measured" panel is collapsed. Metric labels across the page anchor back here
         (#g-elo / #g-tier / #g-elite) — define once, reference everywhere. -->
    <div class="hero-measure reveal d4">
      <p class="measure-line">Strength = each opponent's <b>World Football Elo</b>, frozen before the tournament.
        <a class="gref measure-toggle" href="#measure">How this is measured</a></p>
      <details id="measure" class="measure">
        <summary>How this is measured</summary>
        <dl class="measure-defs">
          <div id="g-elo"><dt>Elo</dt><dd><b>World Football Elo</b> is a chess-style team rating that moves
            with every result, adjusting for goal margin, match importance and home advantage. Studies have
            found Elo-type ratings predict results better than the old FIFA ranking (Lasek et al., 2013).
            Each opponent's rating is <b>frozen at Dec 31 of the year before</b> the tournament, so the
            tournament's own results can't inflate it.</dd></div>
          <div id="g-tier"><dt>Tiers</dt><dd>Each tournament's qualified field is ranked by that frozen Elo;
            the top quarter is <b>elite</b>, then strong, mid, weak. Tiers are a <b>percentile of that
            edition's field</b> — era-fair, so a 16-team 1958 and a 48-team 2026 compare honestly.</dd></div>
          <div id="g-elite"><dt>Elite share</dt><dd>The share of a player's goals scored against elite
            (top-quarter) opponents. Boundary-sensitive: a goal within ~3.5 Elo of the cut is marked
            <b>*</b> — the percentage is exact, but that one goal's tier hinges on a near-tie.</dd></div>
        </dl>
        <p class="measure-src">Opponent strength: World Football Elo, <a href="https://eloratings.net">eloratings.net</a>. Own goals excluded; penalties counted.</p>
      </details>
    </div>

    <div class="scrollcue reveal d4">
      <span class="dot"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M12 5v14M6 13l6 6 6-6"/></svg></span>
      Scroll to begin the countdown
    </div>
  </div>
</header>

<!-- ============ WALKTHROUGH SHOWCASE ============ -->
<section class="showcase" id="scorers">
  <div class="wrap showcase-intro">
    <div class="kicker reveal">The 11-plus club</div>
    <h2 class="reveal d1">Eleven goals or more</h2>
    <p class="reveal d2">The only players with eleven or more World Cup goals, counted down by tally. Watch not the number — but the colour of the teams behind it.</p>
  </div>
  <div class="scroller" id="scroller">
    <div class="stage">
      <div class="scenes" id="scenes"></div>
      <nav class="rail" id="rail" aria-label="Scorers ranked by goals"></nav>
    </div>
  </div>
</section>

<!-- ============ PLAYER DEEP-DIVE ============ -->
<section class="deep" id="player">
  <div class="wrap">
    <div class="deep-head">
      <div>
        <div class="kicker">Deep dive</div>
        <h2>Inside one career</h2>
        <p class="deep-lead">Pick a scorer and open up every World Cup goal they scored — who they beat, in which tournament, and how the tally splits by opponent strength.</p>
      </div>
      <div class="deep-nav">
        <button class="deep-arrow" id="deepPrev" aria-label="Previous player">‹</button>
        <select id="deepSelect" aria-label="Choose a player"></select>
        <button class="deep-arrow" id="deepNext" aria-label="Next player">›</button>
      </div>
    </div>
    <div class="deep-body" id="deepBody"></div>
  </div>
</section>

<!-- ============ THE ARENA (all scorers) ============ -->
<section class="arena" id="arena">
  <div class="wrap">
    <div class="arena-head">
      <div>
        <div class="kicker">Every scorer, one picture</div>
        <h2>The arena</h2>
        <p class="arena-lead">All %%ROSTER_N%% players with 9+ World Cup goals, on a single field. Switch the lens to re-tell the story — the same faces move to find their place. Click any scorer to send them to the comparison below.</p>
      </div>
      <div class="seg arena-toggle" id="arenaSeg">
        <button data-l="field" class="active">Strength field</button>
        <button data-l="time">Across the eras</button>
        <button data-l="lanes">By tier profile</button>
      </div>
    </div>
    <div class="arena-stats" id="arenaStats"></div>
    <div class="arena-plot" id="arenaPlot"></div>
    <div class="arena-caption" id="arenaCaption"></div>
  </div>
</section>

<!-- ============ COMPARISON DASHBOARD ============ -->
<section class="compare" id="compare">
  <div class="wrap">
    <div class="compare-head">
      <div>
        <div class="kicker">The full board</div>
        <h2>Compare any scorers</h2>
      </div>
      <div class="seg" id="sortSeg">
        <button data-k="goals" class="active">Goals</button>
        <button data-k="elo">Avg opp Elo</button>
        <button data-k="elite">Elite share</button>
        <button data-k="az">A–Z</button>
      </div>
    </div>
    <div class="roster" id="roster"></div>
    <p class="roster-hint">Tap any scorer to add them to the comparison · <b id="selCount">2</b> selected. All %%ROSTER_N%% players with 9+ World Cup goals are here.</p>

    <div class="viz" id="viz">
      <div class="viz-bar">
        <div class="viz-title">
          <span class="viz-kick">The comparison</span>
          <span class="viz-mode" id="vizModeLabel">Goals on a shared scale</span>
        </div>
        <div class="seg viz-toggle" id="viewSeg">
          <button data-v="ranking" class="active">Ranking</button>
          <button data-v="field">The Field</button>
        </div>
      </div>
      <div id="eraSlot"></div>
      <div class="viz-stage" id="vizStage"></div>
    </div>
  </div>
</section>

<!-- ============ FOOTER ============ -->
<footer class="foot">
  <div class="wrap">
    <div class="foot-grid">
      <div>
        <h3>How this is measured</h3>
        <p>Opponent strength is <b style="color:#fff">World Football Elo</b> (eloratings.net) — a chess-style team rating adjusting for result, goal margin, importance and home advantage. Each opponent's rating is frozen at Dec 31 of the year <em style="color:#fff;font-style:normal">before</em> the tournament, so its own results can't contaminate the number.</p>
        <p>Each tournament's qualified field is ranked by that frozen Elo; the top quarter is <b>elite</b>, then strong, mid and weak. Tiers are relative to that edition's field — era-fair, so a 16-team 1958 and a 48-team 2026 compare honestly.</p>
        <p class="marks">A tier distribution reflects the draw and the knockout structure as much as the player — it measures <b>who they faced, not agency</b>. Own goals excluded; penalties counted; totals provisional while 2026 is in progress. Goals &amp; matches: martj42/international_results.</p>
        <p class="foot-legal">A redesign concept — data and photos courtesy of the worldcup_scorers project. Player photos from Wikimedia Commons under the licences credited below.</p>
        %%CREDITS%%
      </div>
      <div>
        <h3>Sources</h3>
        <ul class="foot-src">
          <li>Opponent strength <span>World Football Elo</span></li>
          <li>Goals &amp; matches <span>martj42 / results</span></li>
          <li>Awards <span>FIFA World Cup</span></li>
          <li>Portraits <span>Wikimedia Commons</span></li>
        </ul>
      </div>
    </div>
  </div>
</footer>

<script>
window.WCS = %%WCS%%;
</script>
<script>
%%JS%%
</script>
</body>
</html>
"""

out = (HTML.replace("%%CSS%%", CSS)
           .replace("%%WCS%%", WCS_JS)
           .replace("%%JS%%", JS_MODULES)
           .replace("%%CREDITS%%", CREDITS)
           .replace("%%ROSTER_N%%", str(len(roster_names))))
open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(out)
print(f"wrote index.html ({len(out):,} bytes) · {len(roster_names)} players · max goals {max_goals}")
print(f"walkthrough: {len(walk)} scorers (≥11), all staged · {walk}")
