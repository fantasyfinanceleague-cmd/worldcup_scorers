# World Cup Scorers — by Opponent Strength

A single-file interactive site that compares the all-time top World Cup goalscorers not by *how many*
goals they scored, but by **how strong the teams were that they scored against**.

🔗 **Live:** _(Vercel URL — add after first deploy)_

---

## What it measures

For each top scorer, the site shows the strength of the opponents they actually scored against. It
describes **which opponents a player happened to face** — which is shaped by the tournament draw and
the knockout structure as much as by the player. The page presents that honestly: two lenses side by
side, and no claim that any era was "weaker" or that any player "made it count." The restraint is the
point — the numbers sit next to each other and let you judge.

## Methodology

- **Opponent strength = World Football Elo** ([eloratings.net](https://eloratings.net)) — a chess-style
  team rating that adjusts for result, goal margin, match importance and home advantage. Studies have
  found Elo-based ratings predict match outcomes better than the old FIFA ranking (Lasek et al., 2013);
  FIFA itself adopted an Elo-based method in 2018.
- **Frozen pre-tournament.** Each opponent's Elo is taken as of **Dec 31 of the year *before* the
  tournament**, so the tournament's own results can't contaminate the rating used to judge it. Applied
  uniformly to every edition, 1930–2026.
- **Percentile-of-field tiers.** Each tournament's qualified field is ranked by that frozen Elo; the
  top quarter is **elite**, then strong, mid, weak. Tiers are relative to *that* tournament's field, so
  a 16-team 1958 edition and a 48-team 2026 edition compare fairly (era-fair) — while absolute Elo is
  shown alongside as the era-revealing lens.
- **The honest caveat.** A tier distribution reflects the draw and the knockout structure as much as
  anything about the player — it measures *who they faced, not agency*. Quartile cuts are also
  boundary-sensitive: a goal against a team sitting on a tier line is flagged (`*`) rather than counted
  as settled, so a near-tie never reads as a clean fact.
- **Era-correct nations.** West Germany, East Germany, the USSR, Czechoslovakia, Yugoslavia, Serbia &
  Montenegro and Zaire are kept as separate historical entities — never bridged into modern successors.

## Data sources

- **Goals & matches:** [martj42/international_results](https://github.com/martj42/international_results)
- **Opponent strength:** [eloratings.net](https://eloratings.net) — World Football Elo, frozen year-end boards (1929–2025) committed under `data/elo/`.

## How it stays current

A daily GitHub Actions job re-pulls the source match data, runs **every verification gate**, rebuilds
the single `index.html`, and — only if all gates pass — commits and deploys. If any check fails (a
schema change, an unmapped opponent, an implausible goal jump, or a newly-qualifying player without a
staged photo + blurb), the build **halts** and the last-good site stays live. Unattended isn't
unchecked. The gate distinguishes **retired** players (totals are settled → exact-match) from **active**
players (totals may only rise, never drop or jump implausibly), so a live tournament goal never
false-halts the build.

## Reproduce locally

```bash
pip install pandas pillow
python3 build_breakdown.py   # join WC goals → frozen Elo → percentile tiers → data/player_breakdown.json
python3 build_ui.py          # render the self-contained index.html
python3 gate.py              # run the full verification suite
```

The analysis/validation scripts print the working: `build_roster.py` (roster + goal-count gate),
`build_map.py` (era-correct name→Elo-code map + full-field completeness gate), `boundary_scan.py` /
`boundary_scan2.py` (tier-boundary fragility, e.g. the Salenko per-match ceiling and the
Belgium/Colombia tie), and `trace_checks.py` (per-goal elite-attribution traces).

## Player photo credits

All player photos are from Wikimedia Commons under the licenses below, downscaled and cropped for
display (derivatives), with share-alike preserved where the license requires it.

| Player | Photo | License | Credit |
|---|---|---|---|
| Lionel Messi | Argentina · 2022 | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) | Hossein Zohrevand ([Commons](https://commons.wikimedia.org/wiki/File:Lionel-Messi-Argentina-2022-FIFA-World-Cup.jpg)) |
| Kylian Mbappé | France · 2026 | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) | Bryan Berlin ([Commons](https://commons.wikimedia.org/wiki/File:Kylian_Mbappe_France_v_Senegal_16_June_2026-391_(cropped).jpg)) |
| Miroslav Klose | Germany · 2012 | [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/) | Andrzej Otrębski ([Commons](https://commons.wikimedia.org/wiki/File:Gdansk_PGE_Arena_GER-GRE_Euro_2012_24_Klose.jpg)) |
| Ronaldo | Brazil · 2002 | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) | Milly barzellai ([Commons](https://commons.wikimedia.org/wiki/File:Ronaldo_2002_cropped.jpg)) |
| Gerd Müller | West Germany · 1974 | [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/) | Nationaal Archief / Anefo ([Commons](https://commons.wikimedia.org/wiki/File:Gerd_M%C3%BCller_1974.jpg)) |
| Just Fontaine | France (Reims) · 1960 | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) | André Cros ([Commons](https://commons.wikimedia.org/wiki/File:17.1.60._Foot._Simon_(TFC)_et_Just_Fontaine_(Reims)_(1960)_-_53Fi6501_(Fontaine).jpg)) |
| Pelé | Brazil · 1962 | [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/) | Anefo / Nationaal Archief ([Commons](https://commons.wikimedia.org/wiki/File:Pele_(voetballer)_(kop),_Bestanddeelnr_918-6208.jpg)) |
| Jürgen Klinsmann | Germany · 1989 | [CC BY-SA 3.0 de](https://creativecommons.org/licenses/by-sa/3.0/de/deed.en) | Bundesarchiv, Klaus Oberst ([Commons](https://commons.wikimedia.org/wiki/File:Bundesarchiv_Bild_183-1989-0419-044,_Uefa-Cup,_Dynamo_Dresden_-_VFB_Stuttgart_1-1.jpg)) |
| Sándor Kocsis | Hungary · 1950s | [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/) | Fortepan / Faragó György ([Commons](https://commons.wikimedia.org/wiki/File:Kocsis_S%C3%A1ndor_Fortepan_261526.jpg)) |
| Harry Kane | England · 2018 | [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/) | Кирилл Венедиктов (Kirill Venediktov) ([Commons](https://commons.wikimedia.org/wiki/File:Harry_Kane_in_Russia.jpg)) |
| Grzegorz Lato | Poland · 1974 | [CC BY-SA 3.0 de](https://creativecommons.org/licenses/by-sa/3.0/de/deed.en) | Bundesarchiv ([Commons](https://commons.wikimedia.org/wiki/File:Bundesarchiv_Bild_183-N0615-0029,_Fu%C3%9Fball-WM,_VR_Polen_-_Argentinien_3-2_(Lato_cropped).jpg)) |
| Cristiano Ronaldo | Portugal · 2025 | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) | YantsImages ([Commons](https://commons.wikimedia.org/wiki/File:Portugal_national_football_team_0866_(Cristiano_Ronaldo).jpg)) |

## Attribution & licenses

- **Match/goal data:** [martj42/international_results](https://github.com/martj42/international_results) (CC BY 4.0).
- **Elo ratings:** © [eloratings.net](https://eloratings.net).
- **Player photos:** Wikimedia Commons, per the table above (CC BY / CC BY-SA / CC0).
- **Code:** [MIT](LICENSE) — and MIT covers the **code only** (build scripts, workflow, site
  HTML/CSS/JS). It does **not** relicense the bundled data or photos: the match data stays CC BY 4.0,
  the Elo data stays © eloratings.net, and every player photo keeps its own CC BY / CC BY-SA / CC0
  license per the credit table above. Reusing a photo means following *its* license, not MIT.
