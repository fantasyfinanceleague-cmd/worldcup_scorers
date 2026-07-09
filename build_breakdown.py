#!/usr/bin/env python3
"""Per-player PER-TOURNAMENT breakdown (the structure the hero tier-distribution visual needs).
Prints for review and writes a JSON data artifact. No UI, no deploy."""
import pandas as pd, json
from build_map import resolve, board, fields, wc

goals = pd.read_csv("data/goalscorers.csv")
key = ["date", "home_team", "away_team"]
g = goals.merge(wc[key].drop_duplicates(), on=key, how="inner").copy()
g["own_goal"] = g["own_goal"].astype(str).str.lower().isin(["true", "1"])
g = g[~g["own_goal"]].copy()
g["yr"] = g["date"].str[:4].astype(int)
g["opponent"] = g.apply(lambda r: r.away_team if r.team == r.home_team else r.home_team, axis=1)

TIERS = ["elite", "strong", "mid", "weak"]
FLAG_THRESHOLD = 3.5          # Elo proximity to the elite line that triggers a per-card boundary flag
tier_of = {}
eline = {}                    # yr -> (midpoint Elo of elite/strong cut, (last_elite,elo), (first_strong,elo))
for yr in sorted(fields):
    b = board(yr - 1)
    fld = [(t, next(c for c in resolve(t, yr) if c in b)) for t in fields[yr]]
    fld = [(t, c, b[c][1]) for t, c in fld]
    fld.sort(key=lambda x: -x[2]); n = len(fld)
    tiers = [TIERS[min(3, int((i / n) * 4))] for i in range(n)]
    for i, (t, c, elo) in enumerate(fld):
        tier_of[(yr, t)] = (tiers[i], elo)
    cut = next(i for i in range(1, n) if tiers[i] == "strong")   # first strong index
    eline[yr] = ((fld[cut - 1][2] + fld[cut][2]) / 2, (fld[cut - 1][0], fld[cut - 1][2]),
                 (fld[cut][0], fld[cut][2]))

g["tier"] = g.apply(lambda r: tier_of[(r.yr, r.opponent)][0], axis=1)
g["opp_elo"] = g.apply(lambda r: tier_of[(r.yr, r.opponent)][1], axis=1)

# Era-correct opponent code — the SAME (name, year) -> code resolution the Elo join uses, so that
# grouping a player's goals by opponent never merges eras that share a martj42 label: "Germany" is
# West Germany (<=1990, WG) vs reunified Germany (>=1994, DE); "Russia" is the USSR (SU) vs modern
# Russia (RU); "Serbia" splits Yugoslavia / Serbia & Montenegro / Serbia. Grouping by NAME would fuse
# these; grouping by code keeps them distinct.
_boards = {yr: board(yr - 1) for yr in fields}
def _opp_code(name, yr):
    return next((c for c in resolve(name, yr) if c in _boards[yr]), "NAME:" + name)  # gate guarantees a hit
g["opp_code"] = g.apply(lambda r: _opp_code(r.opponent, r.yr), axis=1)

ROSTER_MIN = 9
totals = g.groupby("scorer").size()
roster = sorted(totals[totals >= ROSTER_MIN].index, key=lambda s: (-totals[s], s))

data = {}
for p in roster:
    gp = g[g.scorer == p]
    per_t = []
    for yr in sorted(gp.yr.unique()):
        gt = gp[gp.yr == yr]
        tc = gt.tier.value_counts().to_dict()
        # per-tier opponent detail, so each UI bar cell can name exactly who it represents
        by_tier = {}
        for t in TIERS:
            sub = gt[gt.tier == t]
            if len(sub):
                opp_counts = sub.groupby("opponent").size().sort_values(ascending=False)
                by_tier[t] = {
                    "goals": int(len(sub)),
                    "opponents": [{"name": o, "goals": int(c), "elo": int(sub[sub.opponent == o].opp_elo.iloc[0])}
                                  for o, c in opp_counts.items()],
                }
        per_t.append({
            "year": int(yr), "goals": int(len(gt)),
            "elite": int(tc.get("elite", 0)), "strong": int(tc.get("strong", 0)),
            "mid": int(tc.get("mid", 0)), "weak": int(tc.get("weak", 0)),
            "avg_opp_elo": round(float(gt.opp_elo.mean()), 1),
            "opponents": sorted(gt.opponent.unique().tolist()),
            "by_tier": by_tier,
        })
    tc = gp.tier.value_counts().to_dict()
    # boundary flag: find the player's goal nearest the elite line; flag if within FLAG_THRESHOLD.
    # The marker is honest about the discrete fragile input, NOT a range over the whole metric.
    nearest = None
    for _, r in gp.iterrows():
        line, last_elite, first_strong = eline[r.yr]
        gap = r.opp_elo - line                     # +inside elite, -outside
        if nearest is None or abs(gap) < abs(nearest["gap"]):
            inside = (r.tier == "elite")
            tie = abs(last_elite[1] - first_strong[1]) < 0.5   # exact Elo tie straddling the cut
            if tie and r.opponent in (last_elite[0], first_strong[0]):
                other = first_strong[0] if r.opponent == last_elite[0] else last_elite[0]
                note = (f"vs {r.opponent} ({r.yr}) sits on the elite boundary — tied {other} at "
                        f"{r.opp_elo} Elo, placed on the {'elite' if inside else 'strong'} side by "
                        f"sort order. A tie-break, not a rating gap, decides this goal's tier.")
            else:
                side = "just inside the elite cut" if inside else "just outside the elite cut"
                note = (f"vs {r.opponent} ({r.yr}) sits {side} ({gap:+.1f} Elo). Small rating "
                        f"changes could flip this goal's tier.")
            nearest = {"opponent": r.opponent, "year": int(r.yr), "gap": round(float(gap), 1),
                       "inside_elite": bool(inside), "note": note}
    flag = nearest if nearest and abs(nearest["gap"]) <= FLAG_THRESHOLD else None
    # Most-punished opponent(s): all of a player's WC goals grouped by ERA-CORRECT opponent code and
    # summed (a 3-in-one-match haul and 1+1+1 across three matches both count as 3). A tie is a tie —
    # list EVERY opponent at the maximum, no tie-break (picking a winner by Elo would invent an answer
    # the data doesn't give). Degenerate case: if the max goals against any single opponent is 1, there
    # is no most-punished opponent (the player never scored twice against anyone) — record None so the
    # UI renders "—" rather than every opponent they ever scored against. e.g. Messi -> Algeria + Nigeria
    # (3 each); Cristiano -> Spain (3, unique); Ronaldo -> five sides at 2; Uwe Seeler (all singletons) -> None.
    mp = {}
    for _, r in gp.iterrows():
        a = mp.setdefault(r.opp_code, {"opponent": r.opponent, "goals": 0})
        a["goals"] += 1
        a["opponent"] = r.opponent            # display name, stable within a code
    maxg = max((a["goals"] for a in mp.values()), default=0)
    most_punished = ({"goals": int(maxg),
                      "opponents": sorted(a["opponent"] for a in mp.values() if a["goals"] == maxg)}
                     if maxg > 1 else None)
    data[p] = {
        "goals": int(len(gp)), "tournaments": int(gp.yr.nunique()),
        "career_tiers": {t: int(tc.get(t, 0)) for t in TIERS},
        "elite_share": round(float(tc.get("elite", 0) / len(gp)), 3),
        "avg_opp_elo": round(float(gp.opp_elo.mean()), 1),
        "per_tournament": per_t,
        "boundary_flag": flag,
        "most_punished": most_punished,
        # distinct WC matches this player scored a (non-own) goal in. A hard floor on appearances —
        # you cannot score in a match you did not play — used by build_ui.py's appearances guard.
        "scoring_matches": int(gp[["date", "home_team", "away_team"]].drop_duplicates().shape[0]),
    }

with open("data/player_breakdown.json", "w") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

# ---- compact print for review ----
print(f"per-tournament breakdown written: data/player_breakdown.json ({len(roster)} players)\n")
for p in roster:
    d = data[p]
    ct = d["career_tiers"]
    print(f"{p}  —  {d['goals']}g over {d['tournaments']} WC(s)  |  career E/S/M/W = "
          f"{ct['elite']}/{ct['strong']}/{ct['mid']}/{ct['weak']}  avgElo {d['avg_opp_elo']:.0f}")
    for t in d["per_tournament"]:
        print(f"     {t['year']}: {t['goals']}g  E/S/M/W={t['elite']}/{t['strong']}/{t['mid']}/{t['weak']}"
              f"  avgElo {t['avg_opp_elo']:.0f}  vs {', '.join(t['opponents'])}")
