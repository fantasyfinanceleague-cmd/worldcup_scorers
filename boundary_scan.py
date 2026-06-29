#!/usr/bin/env python3
"""Boundary-fragility scan: for each of the 26 roster players, find their single highest-Elo goal and
measure how far it sits from that tournament's elite (top-quartile) line. Report the tightest gaps so
any near-coin-flip (e.g. -2/-3 under the line) is identified BEFORE the UI renders it.
Negative gap = highest-Elo goal fell just BELOW the elite line (the misleading-0% risk)."""
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
opp_meta = {}     # (yr, team) -> (rank, elo, tier, nfield)
elite_line = {}   # yr -> elo of last elite team (the boundary)
for yr in sorted(fields):
    b = board(yr - 1)
    fld = [(t, next(c for c in resolve(t, yr) if c in b)) for t in fields[yr]]
    fld = [(t, b[c][1]) for t, c in fld]
    fld.sort(key=lambda x: -x[1]); n = len(fld); last_elite = None
    for i, (t, elo) in enumerate(fld):
        tier = TIERS[min(3, int((i / n) * 4))]
        opp_meta[(yr, t)] = (i + 1, elo, tier, n)
        if tier == "elite":
            last_elite = elo
    elite_line[yr] = last_elite

ROSTER_MIN = 9
totals = g.groupby("scorer").size()
roster = sorted(totals[totals >= ROSTER_MIN].index, key=lambda s: (-totals[s], s))

scan = []
for p in roster:
    gp = g[g.scorer == p]
    # the player's single highest-Elo goal
    best = max((opp_meta[(r.yr, r.opponent)] + (r.opponent, r.yr) for _, r in gp.iterrows()),
               key=lambda x: x[1])
    rank, elo, tier, n, opp, yr = best
    gap = elo - elite_line[yr]          # signed: negative = below the elite line
    scan.append((gap, p, opp, yr, elo, rank, n, tier))

scan.sort(key=lambda x: x[0])           # most-negative (tightest below) first
print("Highest-Elo goal vs that tournament's elite line — sorted tightest-below first")
print(f"{'gap':>5}  {'player':22s} {'best opp':16s} {'yr':>4} {'oppElo':>6} {'rank/field':>10} {'tier':>6}")
print("-" * 78)
for gap, p, opp, yr, elo, rank, n, tier in scan:
    mark = "  <-- below elite line (fragile 0/low elite%)" if gap < 0 else ""
    print(f"{gap:+5d}  {p:22s} {opp:16s} {yr:4d} {elo:6d} {rank:4d}/{n:<5d} {tier:>6}{mark}")

below = [s for s in scan if s[0] < 0]
print(f"\nPlayers whose BEST goal fell below the elite line: {len(below)}")
if below:
    tightest = below[-1]  # closest to zero among the below-line set
    print(f"Tightest near-miss (closest to the line from below): {tightest[1]} vs {tightest[2]} {tightest[3]}, {tightest[0]:+d} Elo")
    print("Any within -3 (coin-flip):", [f'{s[1]} ({s[0]:+d})' for s in below if s[0] >= -3] or "none")
