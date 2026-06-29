#!/usr/bin/env python3
"""CORRECT boundary scan (supersedes boundary_scan.py, which only checked each player's single
highest-Elo goal vs the elite line). Here: for EVERY goal of every roster player, the signed Elo gap
to the nearest tier boundary, with the elite line called out specifically (it drives the displayed
elite%). A boundary 'line' is the Elo midpoint between the two teams straddling a quartile cut.
Reports the tightest cases across the whole dataset so any |gap| within ~3 Elo is surfaced."""
import pandas as pd
from build_map import resolve, board, fields, wc

goals = pd.read_csv("data/goalscorers.csv")
key = ["date", "home_team", "away_team"]
g = goals.merge(wc[key].drop_duplicates(), on=key, how="inner").copy()
g["own_goal"] = g["own_goal"].astype(str).str.lower().isin(["true", "1"])
g = g[~g["own_goal"]].copy()
g["yr"] = g["date"].str[:4].astype(int)
g["opponent"] = g.apply(lambda r: r.away_team if r.team == r.home_team else r.home_team, axis=1)

TIERS = ["elite", "strong", "mid", "weak"]
# per tournament: opponent -> (elo, tier); plus the three boundary-line Elos (midpoints at tier cuts)
opp_info, lines = {}, {}
for yr in sorted(fields):
    b = board(yr - 1)
    fld = [(t, b[next(c for c in resolve(t, yr) if c in b)][1]) for t in fields[yr]]
    fld.sort(key=lambda x: -x[1]); n = len(fld)
    tiers = [TIERS[min(3, int((i / n) * 4))] for i in range(n)]
    # boundary line = midpoint between adjacent teams where the tier label changes
    bl = {}                       # ('elite','strong') -> midpoint elo, etc.
    for i in range(1, n):
        if tiers[i] != tiers[i - 1]:
            bl[(tiers[i - 1], tiers[i])] = (fld[i - 1][1] + fld[i][1]) / 2
    lines[yr] = bl
    for i, (t, elo) in enumerate(fld):
        opp_info[(yr, t)] = (elo, tiers[i])

ROSTER_MIN = 9
totals = g.groupby("scorer").size()
roster = sorted(totals[totals >= ROSTER_MIN].index, key=lambda s: (-totals[s], s))

elite_key = ("elite", "strong")
rows = []     # one row per player: tightest-to-elite-line goal + tightest-to-any-boundary goal
for p in roster:
    gp = g[g.scorer == p]
    best_elite = best_any = None
    for _, r in gp.iterrows():
        elo, tier = opp_info[(r.yr, r.opponent)]
        bl = lines[r.yr]
        # gap to elite line (signed: + above line = elite side, - below = non-elite side)
        if elite_key in bl:
            ge = elo - bl[elite_key]
            if best_elite is None or abs(ge) < abs(best_elite[0]):
                best_elite = (ge, r.opponent, r.yr, elo, tier)
        # gap to nearest of ALL boundaries
        ga = min(((elo - v, k) for k, v in bl.items()), key=lambda x: abs(x[0]))
        if best_any is None or abs(ga[0]) < abs(best_any[0]):
            best_any = (ga[0], ga[1], r.opponent, r.yr, elo, tier)
    rows.append((p, best_elite, best_any))

print("=== TIGHTEST TO THE ELITE LINE (drives elite%) — every goal considered, per player ===")
ranked = sorted([r for r in rows if r[1]], key=lambda r: abs(r[1][0]))
print(f"{'gap':>6}  {'player':22s} {'opponent':16s} {'yr':>4} {'oppElo':>6} {'tier':>6}")
print("-" * 70)
for p, be, _ in ranked[:8]:
    gap, opp, yr, elo, tier = be
    print(f"{gap:+6.1f}  {p:22s} {opp:16s} {yr:4d} {elo:6d} {tier:>6}")

print("\n=== TIGHTEST TO ANY TIER BOUNDARY — every goal considered, per player ===")
ranked_any = sorted(rows, key=lambda r: abs(r[2][0]))
print(f"{'gap':>6}  {'player':22s} {'opponent':16s} {'yr':>4} {'oppElo':>6} {'boundary':>16}")
print("-" * 80)
for p, _, ba in ranked_any[:8]:
    gap, bk, opp, yr, elo, tier = ba
    print(f"{gap:+6.1f}  {p:22s} {opp:16s} {yr:4d} {elo:6d} {bk[0]+'/'+bk[1]:>16}")

ge_min = min(abs(r[1][0]) for r in rows if r[1])
ga_min = min(abs(r[2][0]) for r in rows)
print(f"\nDATASET MINIMUM gap to elite line: {ge_min:.1f} Elo")
print(f"DATASET MINIMUM gap to ANY boundary: {ga_min:.1f} Elo")
print(f"Any goal within 3 Elo of the ELITE line: "
      f"{[r[0] for r in rows if r[1] and abs(r[1][0]) <= 3] or 'NONE'}")
print(f"Any goal within 3 Elo of ANY boundary: "
      f"{[(r[0], round(r[2][0],1)) for r in rows if abs(r[2][0]) <= 3] or 'NONE'}")
