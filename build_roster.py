#!/usr/bin/env python3
"""Data layer v1: WC goals -> per-player totals -> top-20 roster -> goal-count gate.
Stops short of any Elo work (blocked on owner eyeball)."""
import pandas as pd

results = pd.read_csv("data/results.csv")
goals = pd.read_csv("data/goalscorers.csv")

# 1. WC matches only
wc = results[results["tournament"] == "FIFA World Cup"].copy()
print(f"WC matches in results.csv: {len(wc)}  (date range {wc.date.min()}..{wc.date.max()})")

# inner-join goals -> WC matches on (date, home_team, away_team)
key = ["date", "home_team", "away_team"]
wc_keys = wc[key].drop_duplicates()
g = goals.merge(wc_keys, on=key, how="inner")
print(f"goal rows joined to WC matches: {len(g)}")

# drop own goals
g["own_goal"] = g["own_goal"].astype(str).str.lower().isin(["true", "1"])
own = int(g["own_goal"].sum())
g = g[~g["own_goal"]].copy()
print(f"own goals dropped: {own}  | scoring rows remaining: {len(g)}")

# penalties = YES (locked) -> no filtering on penalty

# 2/3. per-player totals by EXACT scorer name (no substring)
totals = g.groupby("scorer").size().sort_values(ascending=False)

# trap inspection
print("\n=== substring trap inspection (exact-name resolution) ===")
for needle in ["Müller", "Ronaldo"]:
    hits = totals[totals.index.str.contains(needle, na=False)]
    print(f"  '{needle}' substring -> {hits.sum()} goals across {len(hits)} exact names:")
    for nm, c in hits.items():
        print(f"      {c:3d}  {repr(nm)}")

# A (owner ruling): the bare "Müller" (2 goals) is an unresolved orphan, NOT Gerd (who is already
# complete at 14). Out of scope, harmless (well below the roster cut). Not chased.

# 4. Roster rule (owner ruling, supersedes fixed-20 + tiebreaker in brief §1.2):
#    roster = ALL players with >= 9 WC goals. The cut sits at the natural gap ABOVE the 8-goal block,
#    so no boundary splits a tie and no appearances/tiebreaker dataset is needed. Recomputes cleanly
#    each run; stays provisional (a current-8 player can reach 9 before the 2026-07-19 lock).
THRESHOLD = 9
roster = totals[totals >= THRESHOLD].reset_index()
roster.columns = ["player", "goals"]
roster = roster.sort_values(["goals", "player"], ascending=[False, True]).reset_index(drop=True)

# verify the cut sits at a real gap (no one at THRESHOLD-1 would tie into the roster)
just_below = int((totals == THRESHOLD - 1).sum())
top = roster

# 5. goal-count gate vs known published totals
known = {
    "Just Fontaine": 13, "Sándor Kocsis": 11, "Pelé": 12, "Miroslav Klose": 16,
    "Lionel Messi": 18, "Jürgen Klinsmann": 11, "Gary Lineker": 10, "Gabriel Batistuta": 10,
    "Gerd Müller": 14, "Ronaldo": 15, "Cristiano Ronaldo": 8,
}
print("\n=== GOAL-COUNT GATE (computed vs known published) ===")
tdict = totals.to_dict()
fails = 0
for nm, exp in sorted(known.items(), key=lambda x: -x[1]):
    got = tdict.get(nm, None)
    if got is None:
        # try to surface a near-name so a spelling mismatch is visible
        cand = [n for n in tdict if nm.split()[-1] in n]
        status = "NOT FOUND  candidates=" + str(cand[:4])
        fails += 1
    elif got == exp:
        status = "ok"
    else:
        status = f"*** MISMATCH (got {got}, expected {exp})"
        fails += 1
    print(f"  {exp:3d} expected | {str(got):>4} computed | {status:40s} {nm}")
print(f"\nGATE: {'PASS' if fails == 0 else f'FAIL ({fails} issue(s))'}")

# roster preview (>= 9 goals)
print(f"\n=== ROSTER: ALL PLAYERS WITH >= {THRESHOLD} WC GOALS  ({len(roster)} players) ===")
print(f"(cut sits at the gap above the 8-goal block; players sitting at {THRESHOLD-1}g just below cut: {just_below})")
for i, r in top.iterrows():
    print(f"  {i+1:2d}.  {int(r.goals):2d}g  {r.player}")
