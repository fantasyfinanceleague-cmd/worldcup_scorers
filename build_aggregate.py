#!/usr/bin/env python3
"""Join each WC goal -> opponent's frozen (end-of-prior-year) Elo + that tournament's percentile tier,
then aggregate per roster player (career). Prints the aggregate for owner review. No UI, no deploy.

Reuses the gate-clean (name,year)->code resolution from build_map.py."""
import pandas as pd
from build_map import resolve, board, fields, wc

# ---------- 1. WC goals: inner-join goalscorers to WC matches, drop own goals ----------
goals = pd.read_csv("data/goalscorers.csv")
key = ["date", "home_team", "away_team"]
g = goals.merge(wc[key].drop_duplicates(), on=key, how="inner").copy()
g["own_goal"] = g["own_goal"].astype(str).str.lower().isin(["true", "1"])
g = g[~g["own_goal"]].copy()                      # penalties RETAINED (locked: a goal is a goal)
g["yr"] = g["date"].str[:4].astype(int)

# opponent per goal = the side that is NOT the scorer's team
g["opponent"] = g.apply(lambda r: r.away_team if r.team == r.home_team else r.home_team, axis=1)

# ---------- 2. tournament tiering: rank the full field by frozen Elo -> percentile -> quartile tier ----------
TIERS = ["elite", "strong", "mid", "weak"]        # top quartile = elite
def code_to_elo(name, yr, b):
    cands = resolve(name, yr)
    code = next((c for c in cands if c in b), None)
    return code, (b[code][1] if code else None)

tier_of = {}      # (yr, opponent_name) -> (tier, elo, code)
for yr in sorted(fields):
    b = board(yr - 1)
    fld = []
    for team in fields[yr]:
        code, elo = code_to_elo(team, yr, b)
        assert elo is not None, f"GATE VIOLATION {yr} {team}"   # must never fire (gate passed)
        fld.append((team, code, elo))
    fld.sort(key=lambda x: -x[2])                  # strongest first
    n = len(fld)
    for i, (team, code, elo) in enumerate(fld):
        pct = i / n                                # 0 = strongest
        tier = TIERS[min(3, int(pct * 4))]
        tier_of[(yr, team)] = (tier, elo, code)

# ---------- 3. attach tier + opponent Elo to every goal ----------
g["tier"] = g.apply(lambda r: tier_of[(r.yr, r.opponent)][0], axis=1)
g["opp_elo"] = g.apply(lambda r: tier_of[(r.yr, r.opponent)][1], axis=1)

# ---------- 4. roster = players with >= 9 WC goals (cut at the natural gap) ----------
ROSTER_MIN = 9
totals = g.groupby("scorer").size()
roster = sorted(totals[totals >= ROSTER_MIN].index, key=lambda s: (-totals[s], s))

# ---------- 5. per-player career aggregate ----------
print(f"WC goals (own-goals dropped, penalties kept): {len(g)} | roster (>= {ROSTER_MIN}g): {len(roster)} players\n")
hdr = f"{'player':22s} {'G':>3} {'elite%':>6} {'avgElo':>6} {'T':>2}  {'elite':>5} {'strong':>6} {'mid':>4} {'weak':>4}"
print(hdr); print("-" * len(hdr))
agg_rows = []
for p in roster:
    gp = g[g.scorer == p]
    G = len(gp)
    tc = gp["tier"].value_counts().to_dict()
    e, s, m, w = (tc.get(t, 0) for t in TIERS)
    elite_share = e / G
    avg_elo = gp["opp_elo"].mean()
    ntourn = gp["yr"].nunique()
    agg_rows.append((p, G, elite_share, avg_elo, ntourn, e, s, m, w))
    print(f"{p:22s} {G:3d} {elite_share*100:5.0f}% {avg_elo:6.0f} {ntourn:2d}  {e:5d} {s:6d} {m:4d} {w:4d}")

# sanity: tier counts sum to goal total for every player
bad = [(p, G, e+s+m+w) for (p, G, _, _, _, e, s, m, w) in agg_rows if e+s+m+w != G]
print("\nTIER-SUM CHECK:", "PASS (tiers sum to goals for all players)" if not bad else f"FAIL {bad}")
