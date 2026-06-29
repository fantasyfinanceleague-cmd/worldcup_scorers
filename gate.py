#!/usr/bin/env python3
"""Verification gate for the unattended daily build. Runs EVERY check and exits 0 (all pass) or
1 (any fail). On failure the workflow must NOT commit or deploy — last-good stays live, the job
fails visibly. On pass, updates data/last_totals.json (the monotonic baseline for next run).

Gate design (load-bearing): RETIRED players = strict exact-match — their WC totals are settled, so any
change is a real bug/source regression and HALTS. ACTIVE players (still scoring in 2026) = monotonic
floor only — count may rise, never drop, never jump implausibly. A strict-equality gate would
false-halt the build every single day a live player scores, making the automation useless."""
import sys, json
import pandas as pd
from build_map import wc, field_gate     # importing build_map no longer prints (demo guarded by __main__)

FAILS = []
def check(ok, msg):
    print(("PASS  " if ok else "FAIL  ") + msg)
    if not ok:
        FAILS.append(msg)

RES_HDR = "date,home_team,away_team,home_score,away_score,tournament,city,country,neutral"
GS_HDR  = "date,home_team,away_team,team,scorer,minute,own_goal,penalty"
MAX_PER_MATCH = 5   # most goals one player has scored in a WC match (Salenko, 1994). >5 ⇒ join fan-out.
JUMP_CAP = 10       # per-run BACKSTOP only: one player gaining >10 between runs is impossible even on a
                    # multi-day catch-up — it's the full-duplication signature. Real per-match plausibility
                    # is enforced by MAX_PER_MATCH (which is immune to catch-up days and blowouts).

# 1. PULL SANITY + SCHEMA -----------------------------------------------------------------
try:
    res_hdr = open("data/results.csv", encoding="utf-8").readline().strip()
    gs_hdr  = open("data/goalscorers.csv", encoding="utf-8").readline().strip()
except FileNotFoundError as e:
    print(f"FAIL  CSV missing (failed/404 pull?): {e}\n\nGATE: FAIL — HALT.")
    sys.exit(1)
check(res_hdr == RES_HDR, "results.csv schema unchanged" if res_hdr == RES_HDR else f"results.csv SCHEMA CHANGED: {res_hdr}")
check(gs_hdr  == GS_HDR,  "goalscorers.csv schema unchanged" if gs_hdr == GS_HDR else f"goalscorers.csv SCHEMA CHANGED: {gs_hdr}")
res_rows = sum(1 for _ in open("data/results.csv", encoding="utf-8"))
check(res_rows > 40000, f"results.csv row count sane ({res_rows} rows)")

# 2. FULL-FIELD ELO COMPLETENESS / ORPHAN NAMES / UNMAPPED 2026 CODE -----------------------
orphans, _ = field_gate()
check(len(orphans) == 0, f"full-field Elo completeness — {len(orphans)} orphan(s)")
for yr, team, why in orphans:
    print(f"      ORPHAN {yr} {team}: {why}")
o2026 = [o for o in orphans if o[0] == 2026]
check(len(o2026) == 0, f"every 2026 opponent code mapped — {len(o2026)} unmapped")

# 3. GOAL-COUNT GATE: retired exact-match + active monotonic + jump cap --------------------
goals = pd.read_csv("data/goalscorers.csv"); key = ["date", "home_team", "away_team"]
gw = goals.merge(wc[key].drop_duplicates(), on=key, how="inner")     # all WC goal rows

# DUPLICATE-ROW DETECTOR: an exact-identical source row inflates a scorer's total by a quiet +1 that
# the monotonic / jump-cap checks can't see (it's not a jump). With daily auto-pulls during a live
# tournament, a source-side dup is a plausible failure. FLAG-AND-HALT, never auto-dedup — two goals
# legitimately logged in the SAME minute (a stoppage-time brace) are real; dropping one erases a goal.
# Keyed on the full tuple incl. minute + flags, so a normal brace (different minutes) does NOT trip it.
DUP_KEY = ["date", "home_team", "away_team", "scorer", "minute", "own_goal", "penalty"]
dups = gw[gw.duplicated(DUP_KEY, keep=False)].sort_values(DUP_KEY)
check(len(dups) == 0, f"no exact-duplicate goal rows (full tuple) — {len(dups)} row(s) in {len(dups)//2} suspected pair(s)")
for _, x in dups.iterrows():
    print(f"      DUP: {x.date} {x.home_team} v {x.away_team} | {x.scorer} {x.minute}' og={x.own_goal} pen={x.penalty} — human-judge: real same-minute brace or true duplicate?")

g = gw[~gw["own_goal"].astype(str).str.lower().isin(["true", "1"])]
g["yr"] = g["date"].str[:4].astype(int)
totals = g.groupby("scorer").size().to_dict()
active2026 = set(g[g["yr"] == 2026]["scorer"])     # has a 2026 WC goal => still accumulating

# settled, immutable WC totals for clearly-retired roster players (NOT 2026-active)
RETIRED = {
    "Miroslav Klose": 16, "Ronaldo": 15, "Gerd Müller": 14, "Just Fontaine": 13, "Pelé": 12,
    "Sándor Kocsis": 11, "Jürgen Klinsmann": 11, "Gary Lineker": 10, "Gabriel Batistuta": 10,
    "Grzegorz Lato": 10, "Helmut Rahn": 10, "Teófilo Cubillas": 10, "Thomas Müller": 10,
    "Ademir de Menezes": 9, "Christian Vieri": 9, "David Villa": 9, "Eusébio": 9, "Jairzinho": 9,
    "Karl-Heinz Rummenigge": 9, "Paolo Rossi": 9, "Roberto Baggio": 9, "Uwe Seeler": 9, "Vavá": 9,
}
for name, exp in RETIRED.items():
    if name in active2026:        # a "retired" name scoring in 2026 is itself an anomaly worth halting
        check(False, f"retired-list player '{name}' has a 2026 goal — unexpected, investigate")
    else:
        check(totals.get(name) == exp, f"retired exact-match {name}: {totals.get(name)} (immutable {exp})")

# per-match sanity — catch-up-IMMUNE: a knockout blowout or a missed-day catch-up just adds more
# matches, each still <= MAX_PER_MATCH. >5 by one player in one match is the join fan-out/dup signature.
per_match = g.groupby(["scorer", "date", "home_team", "away_team"]).size()
worst = int(per_match.max())
check(worst <= MAX_PER_MATCH, f"per-match sanity (worst = {worst} goals by one player in one match, ceiling {MAX_PER_MATCH})")
if worst > MAX_PER_MATCH:
    for (s, d, h, a), c in per_match[per_match > MAX_PER_MATCH].items():
        print(f"      {s}: {c} goals in {d} {h} v {a} (impossible — likely join duplication)")

# monotonic (no decrease) + wide per-run backstop, vs last successful run (covers ALL players)
try:
    last = json.load(open("data/last_totals.json", encoding="utf-8"))
except FileNotFoundError:
    last = {}                     # first run: no baseline yet, seeded on pass below
mono_ok = True
for name, prev in last.items():
    got = totals.get(name, 0)
    if got < prev:
        check(False, f"MONOTONIC violation: {name} {prev} -> {got} (goals cannot decrease)"); mono_ok = False
    elif got - prev > JUMP_CAP:
        check(False, f"per-run backstop: {name} {prev} -> {got} (+{got-prev} > {JUMP_CAP}, full-dup signature)"); mono_ok = False
if last and mono_ok:
    check(True, f"monotonic + per-run backstop vs last run ({len(last)} players, none dropped/jumped)")

# 4. VERDICT ------------------------------------------------------------------------------
print()
if FAILS:
    print(f"GATE: FAIL ({len(FAILS)} issue(s)) — HALT: do not commit or deploy. Last-good stays live.")
    sys.exit(1)
json.dump(totals, open("data/last_totals.json", "w", encoding="utf-8"), ensure_ascii=False, sort_keys=True, indent=0)
print("GATE: PASS — last_totals.json updated; build may proceed.")
sys.exit(0)
