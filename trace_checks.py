#!/usr/bin/env python3
"""End-to-end traces for two methodology spot-checks:
  1) Messi's elite goals (esp. 2022 final vs France -> France 2021 Elo, top-quartile of 2022 field)
  2) Rummenigge & Baggio at 0% elite -> confirm real, not a boundary artifact just under the line
No recomputation of logic — same resolve()/board()/fields() the gate validated."""
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
# per-tournament: ranked field with elo, tier, and the elite cutoff (elo of the last elite team)
field_rank = {}    # yr -> {team: (rank, elo, tier)}
elite_cut = {}     # yr -> (n, last_elite_elo, first_non_elite_elo)
for yr in sorted(fields):
    b = board(yr - 1)
    fld = []
    for team in fields[yr]:
        cands = resolve(team, yr); code = next(c for c in cands if c in b)
        fld.append((team, code, b[code][1]))
    fld.sort(key=lambda x: -x[2])
    n = len(fld); fr = {}
    last_elite = first_non = None
    for i, (team, code, elo) in enumerate(fld):
        tier = TIERS[min(3, int((i / n) * 4))]
        fr[team] = (i + 1, elo, tier, code)
        if tier == "elite": last_elite = elo
        elif first_non is None: first_non = elo
    field_rank[yr] = fr
    elite_cut[yr] = (n, last_elite, first_non)

def trace(player):
    gp = g[g.scorer == player].sort_values("date")
    print(f"\n===== {player}: {len(gp)} WC goals =====")
    print(f"{'date':10s} {'opponent':16s} {'yr':>4} {'oppElo':>6} {'rank/field':>10} {'tier':>6} {'gap→elite_cut':>13}")
    ne = 0
    for _, r in gp.iterrows():
        rank, elo, tier, code = field_rank[r.yr][r.opponent]
        n, last_elite, first_non = elite_cut[r.yr]
        gap = "" if tier == "elite" else f"{elo - last_elite:+d}"  # negative = below elite line
        ne += tier == "elite"
        flag = "  <ELITE" if tier == "elite" else ""
        print(f"{r.date:10s} {r.opponent:16s} {r.yr:4d} {elo:6d} {rank:4d}/{n:<5d} {tier:>6} {gap:>13}{flag}")
    print(f"  -> elite goals: {ne}/{len(gp)} = {ne/len(gp)*100:.0f}%")

# ---- spot-check 1: Messi, with the 2022 final isolated ----
trace("Lionel Messi")
print("\n  2022-final cross-check (France's frozen rating & the 2022 elite line):")
n, lc, fn = elite_cut[2022]
fr2022 = field_rank[2022]
print(f"    2022 field size n={n}; elite = top quartile; last-elite Elo={lc}, first-non-elite Elo={fn}")
print(f"    France 2022 -> {fr2022['France']}  (rank, frozen-2021 Elo, tier, code)")
print(f"    Argentina 2022 -> {fr2022['Argentina']}")

# ---- spot-check 2: Rummenigge & Baggio at 0% elite ----
for p in ["Karl-Heinz Rummenigge", "Roberto Baggio"]:
    trace(p)
    gp = g[g.scorer == p]
    closest = None
    for _, r in gp.iterrows():
        rank, elo, tier, code = field_rank[r.yr][r.opponent]
        n, last_elite, first_non = elite_cut[r.yr]
        d = elo - last_elite
        if tier != "elite" and (closest is None or d > closest[0]):
            closest = (d, r.opponent, r.yr, elo, last_elite)
    if closest:
        d, opp, yr, elo, lc = closest
        print(f"  closest any goal came to the elite line: vs {opp} {yr} (Elo {elo}, line {lc}, {d:+d} below)")
