#!/usr/bin/env python3
"""Canonical (team-name, tournament-year) -> era-correct Elo code map + §4 level-2 full-field gate.
Stops before computing any Elo aggregate. Prints orphans + a resolution table with frozen ranks so
San-Marino-style wrong-but-valid resolutions surface (implausible rank within field)."""
import pandas as pd, os

# ---- load WC fields (the §3.7 denominator: distinct teams in each tournament's WC matches) ----
r = pd.read_csv("data/results.csv")
wc = r[r.tournament == "FIFA World Cup"].copy()
wc["yr"] = wc.date.str[:4].astype(int)
fields = {}
for yr, grp in wc.groupby("yr"):
    fields[yr] = sorted(pd.unique(grp[["home_team", "away_team"]].values.ravel()))

# ---- base name -> eloratings code (ISO-2 upper, with verified eloratings exceptions) ----
BASE = {
    "Algeria":"DZ","Angola":"AO","Argentina":"AR","Australia":"AU","Austria":"AT","Belgium":"BE",
    "Bolivia":"BO","Bosnia and Herzegovina":"BA","Brazil":"BR","Bulgaria":"BG","Cameroon":"CM",
    "Canada":"CA","Cape Verde":"CV","Chile":"CL","China":"CN","Colombia":"CO","Costa Rica":"CR",
    "Croatia":"HR","Cuba":"CU","Curaçao":"CW","Czech Republic":"CZ","Czechoslovakia":"CS",
    "Denmark":"DK","Ecuador":"EC","Egypt":"EG","El Salvador":"SV","England":"EN","France":"FR",
    "German DR":"DD","Ghana":"GH","Greece":"GR","Haiti":"HT","Honduras":"HN","Hungary":"HU",
    "Iceland":"IS","Indonesia":"ID","Iran":"IR","Iraq":"IQ","Israel":"IL","Italy":"IT",
    "Ivory Coast":"CI","Jamaica":"JM","Japan":"JP","Jordan":"JO","Kuwait":"KW","Mexico":"MX",
    "Morocco":"MA","Netherlands":"NL","New Zealand":"NZ","Nigeria":"NG","North Korea":"KP",
    "Northern Ireland":"EI","Norway":"NO","Panama":"PA","Paraguay":"PY","Peru":"PE","Poland":"PL",
    "Portugal":"PT","Qatar":"QA","Republic of Ireland":"IE","Romania":"RO","Saudi Arabia":"SA",
    "Scotland":"SQ","Senegal":"SN","Slovakia":"SK","Slovenia":"SI","South Africa":"ZA",
    "South Korea":"KR","Spain":"ES","Sweden":"SE","Switzerland":"CH","Togo":"TG",
    "Trinidad and Tobago":"TT","Tunisia":"TN","Turkey":"TR","Ukraine":"UA",
    "United Arab Emirates":"AE","United States":"US","Uruguay":"UY","Uzbekistan":"UZ","Wales":"WA",
    "Yugoslavia":"YU",
}

# ---- year-keyed era resolution: martj42 reuses one name across political successions; the Elo data
# keeps eras separate. Returns a PRIORITY LIST of era-candidate codes; the gate picks the one present
# in the freeze board. Board-awareness guards against eloratings' inconsistent labels (e.g. it codes
# the USSR as RU in 1962/1965/1966 but SU elsewhere — same lineage, never coexisting). ----
def resolve(name, yr):
    if name == "Germany":
        if 1949 <= yr <= 1990: return ["WG"]   # West Germany (goal data labels "Germany")
        return ["DE"]                            # pre-war (<=1938) & reunified (>=1994)
    if name == "Russia":
        return ["SU", "RU"] if yr <= 1991 else ["RU", "SU"]   # USSR<->Russia, label varies by year
    if name == "Serbia":
        if yr <= 2002: return ["YU"]           # FR Yugoslavia (1998)
        if yr <= 2006: return ["RM"]           # Serbia & Montenegro (2003-2006)
        return ["RS"]                           # modern Serbia (2010+)
    if name == "DR Congo":
        return ["ZR"] if yr == 1974 else ["CD"]  # Zaire (1974) vs modern DR Congo
    if name == "Indonesia":
        return ["DI"] if yr == 1938 else ["ID"]  # Dutch East Indies (1938) vs modern Indonesia
    c = BASE.get(name)
    return [c] if c else None

# ---- load prior-year boards: code -> (rank, elo); field-size for percentile context ----
def board(year):
    path = f"data/elo/{year}.tsv"
    d = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            c = line.rstrip("\n").split("\t")
            if len(c) >= 4 and c[2]:
                d[c[2]] = (int(c[1]), int(c[3]))
    return d

# ---- run the gate over EVERY field participant (not just roster opponents) ----
def field_gate():
    """Resolve every (team, tournament) field slot to an in-era Elo code.
    Returns (orphans, rows). orphans = [(yr, team, reason)]; empty = PASS. Importable by gate.py."""
    orphans, rows = [], []
    for yr in sorted(fields):
        b = board(yr - 1)                       # end-of-prior-year freeze
        nfield = len(fields[yr])
        for team in fields[yr]:
            cands = resolve(team, yr)
            if cands is None:
                orphans.append((yr, team, "NO-CODE (name not in map)")); continue
            code = next((c for c in cands if c in b), None)
            if code is None:
                orphans.append((yr, team, f"none of {cands} in {yr-1} board")); continue
            rank, elo = b[code]
            rows.append((yr, team, code, rank, elo, nfield))
    return orphans, rows

if __name__ == "__main__":
    orphans, rows = field_gate()
    print(f"WC tournaments: {len(fields)} | total (team,tournament) field slots: {sum(len(v) for v in fields.values())}")
    print(f"\n=== §4 LEVEL-2 FULL-FIELD GATE ===")
    if orphans:
        print(f"*** {len(orphans)} ORPHAN(S) — build must HALT (no silent drop): ***")
        for yr, team, why in orphans:
            print(f"   {yr}  {team:26s} {why}")
    else:
        print("ZERO ORPHANS — every field participant in every tournament resolves to exactly one in-era code.")
    # plausibility scan: a WC qualifier ranked in the bottom of its own *world* board is suspect.
    df = pd.DataFrame(rows, columns=["yr","team","code","rank","elo","nfield"])
    print("\n=== PLAUSIBILITY FLAGS (qualifier with surprisingly weak frozen rank — eyeball for mis-resolution) ===")
    sus = df[df["rank"] > 80].sort_values(["yr","rank"])
    if len(sus) == 0:
        print("  none above rank-80 threshold")
    else:
        for _, x in sus.iterrows():
            print(f"   {x.yr}  {x.team:26s} {x.code}  world-rank {x['rank']:3d}  elo {x.elo}")
