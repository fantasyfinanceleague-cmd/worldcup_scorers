#!/usr/bin/env python3
"""Process the 11 walkthrough photos -> tight 4:5 display-res crops -> base64 -> data/photos.json,
with author/license/source metadata for the footer credits. Re-run to regenerate."""
import base64, io, json
from PIL import Image, ImageOps

CC = {
    "by4":  ("CC BY 4.0",      "https://creativecommons.org/licenses/by/4.0/"),
    "by3br":("CC BY 3.0 BR",   "https://creativecommons.org/licenses/by/3.0/br/deed.en"),
    "bysa4":("CC BY-SA 4.0",   "https://creativecommons.org/licenses/by-sa/4.0/"),
    "bysa3":("CC BY-SA 3.0",   "https://creativecommons.org/licenses/by-sa/3.0/"),
    "bysa3de":("CC BY-SA 3.0 de","https://creativecommons.org/licenses/by-sa/3.0/de/deed.en"),
    "bysa3nl":("CC BY-SA 3.0 NL","https://creativecommons.org/licenses/by-sa/3.0/nl/deed.en"),
    "cc0":  ("CC0 1.0",        "https://creativecommons.org/publicdomain/zero/1.0/"),
    # Personal, non-commercial page — for the older press photos the owner accepts a stated source +
    # author as sufficient attribution (see footer credits) rather than FIFA-archive licence chasing.
    "pd":   ("Public domain",  "https://en.wikipedia.org/wiki/Public_domain"),
}
# player -> raw file, vertical centering (0=top), pre-crop box (fractions) or None, metadata
P = {
  "Lionel Messi":     ("messi.jpg",    0.10, None, "Hossein Zohrevand", "by4",
                       "Argentina · 2022", "https://commons.wikimedia.org/wiki/File:Lionel-Messi-Argentina-2022-FIFA-World-Cup.jpg"),
  "Kylian Mbappé":    ("mbappe.jpg",   0.28, None, "Bryan Berlin", "bysa4",
                       "France · 2026", "https://commons.wikimedia.org/wiki/File:Kylian_Mbappe_France_v_Senegal_16_June_2026-391_(cropped).jpg"),
  "Miroslav Klose":   ("klose.jpg",    0.18, None, "Andrzej Otrębski", "bysa3",
                       "Germany · 2012", "https://commons.wikimedia.org/wiki/File:Gdansk_PGE_Arena_GER-GRE_Euro_2012_24_Klose.jpg"),
  "Ronaldo":          ("ronaldo.jpg",  0.22, None, "Milly barzellai", "bysa4",
                       "Brazil · 2002", "https://commons.wikimedia.org/wiki/File:Ronaldo_2002_cropped.jpg"),
  "Gerd Müller":      ("muller.jpg",   0.30, None, "Nationaal Archief / Anefo", "bysa3",
                       "West Germany · 1974", "https://commons.wikimedia.org/wiki/File:Gerd_M%C3%BCller_1974.jpg"),
  "Just Fontaine":    ("fontaine.jpg", 0.05, None, "André Cros", "bysa4",
                       "France (Reims) · 1960", "https://commons.wikimedia.org/wiki/File:17.1.60._Foot._Simon_(TFC)_et_Just_Fontaine_(Reims)_(1960)_-_53Fi6501_(Fontaine).jpg"),
  "Pelé":             ("pele.jpg",     0.18, (0.16,0.10,0.86,0.97), "Anefo / Nationaal Archief", "cc0",
                       "Brazil · 1962", "https://commons.wikimedia.org/wiki/File:Pele_(voetballer)_(kop),_Bestanddeelnr_918-6208.jpg"),
  "Jürgen Klinsmann": ("klinsmann.jpg",0.12, None, "Bundesarchiv, Klaus Oberst", "bysa3de",
                       "Germany (Stuttgart) · 1989", "https://commons.wikimedia.org/wiki/File:Bundesarchiv_Bild_183-1989-0419-044,_Uefa-Cup,_Dynamo_Dresden_-_VFB_Stuttgart_1-1.jpg"),
  "Sándor Kocsis":    ("kocsis.jpg",   0.28, None, "Fortepan / Faragó György", "bysa3",
                       "Hungary · 1950s", "https://commons.wikimedia.org/wiki/File:Kocsis_S%C3%A1ndor_Fortepan_261526.jpg"),
  "Harry Kane":       ("kane.jpg",     0.22, None, "Кирилл Венедиктов (Kirill Venediktov)", "bysa3",
                       "England · 2018", "https://commons.wikimedia.org/wiki/File:Harry_Kane_in_Russia.jpg"),
  "Grzegorz Lato":    ("lato.jpg",     0.12, None, "Bundesarchiv", "bysa3de",
                       "Poland · 1974", "https://commons.wikimedia.org/wiki/File:Bundesarchiv_Bild_183-N0615-0029,_Fu%C3%9Fball-WM,_VR_Polen_-_Argentinien_3-2_(Lato_cropped).jpg"),
  "Cristiano Ronaldo":("cristiano.jpg",0.22, None, "YantsImages", "bysa4",
                       "Portugal · 2025", "https://commons.wikimedia.org/wiki/File:Portugal_national_football_team_0866_(Cristiano_Ronaldo).jpg"),
  # --- 2026 additions: the remaining 9+ goal scorers (arena bubbles + comparison cards) ---
  "Helmut Rahn":      ("rahn.jpg",     0.08, None, "Jack de Nijs / Anefo", "cc0",
                       "West Germany · 1962", "https://commons.wikimedia.org/wiki/File:Helmut_Rahn.jpg"),
  "Gary Lineker":     ("lineker.jpg",  0.06, None, "Rob Bogaerts / Anefo", "cc0",
                       "England · 1988", "https://commons.wikimedia.org/wiki/File:Lineker_Nederland_1-3,_Bestanddeelnr_934-2662_(cropped).jpg"),
  "Thomas Müller":    ("thomas_muller.jpg",0.10, None, "Werner100359", "bysa4",
                       "Germany · 2022", "https://commons.wikimedia.org/wiki/File:Thomas_M%C3%BCller_2022_(cropped).jpg"),
  "Ademir de Menezes":("ademir.jpg",   0.08, None, "O Cruzeiro (press photo)", "pd",
                       "Brazil · 1950", "https://commons.wikimedia.org/wiki/File:Ademir_de_Menezes_(1950).jpg"),
  "Eusébio":          ("eusebio.jpg",  0.10, None, "Harry Pot / Anefo", "bysa3nl",
                       "Portugal · 1963", "https://commons.wikimedia.org/wiki/File:Eusebio_(1963_version2).jpg"),
  "Vavá":             ("vava.jpg",     0.06, None, "Arquivo Nacional / Correio da Manhã", "pd",
                       "Brazil · 1962", "https://commons.wikimedia.org/wiki/File:Vav%C3%A1,_Fundo_Correio_da_Manh%C3%A3.tif"),
  "Jairzinho":        ("jairzinho.jpg",0.10, None, "Rob Mieremet / Anefo", "bysa3nl",
                       "Brazil · 1974", "https://commons.wikimedia.org/wiki/File:Jairzinho_1974.jpg"),
  "Paolo Rossi":      ("rossi.jpg",    0.14, None, "El Gráfico", "pd",
                       "Italy · 1982", "https://commons.wikimedia.org/wiki/File:Paolo_Rossi_at_the_1982_FIFA_World_Cup.jpg"),
  "Christian Vieri":  ("vieri.jpg",    0.08, None, "Roberto Vicario", "bysa3",
                       "Italy · 2007", "https://commons.wikimedia.org/wiki/File:Christian_Vieri_(cropped).jpg"),
  "Karl-Heinz Rummenigge":("rummenigge.jpg",0.35, (0.27,0.085,0.69,0.45), "Marcel Antonisse / Anefo", "cc0",
                       "West Germany · 1982", "https://commons.wikimedia.org/wiki/File:FC_Bayern_Munchen_tegen_Aston_Villa_0-1_Europa_Cup_I_Rummennige_in_aktie,_Bestanddeelnr_932-1815.jpg"),
  "Roberto Baggio":   ("baggio.jpg",   0.10, None, "Unknown (Italia '90)", "pd",
                       "Italy · 1990", "https://commons.wikimedia.org/wiki/File:Roberto_Baggio_-_Italia_%2790.jpg"),
  "David Villa":      ("villa.jpg",    0.10, None, "Tânia Rêgo / Agência Brasil", "by3br",
                       "Spain · 2013", "https://commons.wikimedia.org/wiki/File:Spain-Tahiti,_Confederations_Cup_2013_(02)_(Villa_crop).jpg"),
  "Uwe Seeler":       ("seeler.jpg",   0.08, None, "Joop van Bilsen / Anefo", "cc0",
                       "West Germany · 1966", "https://commons.wikimedia.org/wiki/File:Uwe_Seeler_1966_(cropped).jpg"),
  "Neymar":           ("neymar.jpg",   0.10, None, "Bryan Berlin / WikiPortraits", "bysa4",
                       "Brazil · 2026", "https://commons.wikimedia.org/wiki/File:Neymar_Junior_Brazil_V_Morocco_13_June_2026-40.jpg"),
  # Cubillas 1978 — a clean playing-era portrait in the Peru kit (PD-Peru-anonymous, unknown author).
  # It was in his Wikipedia infobox all along; the earlier sweep saw this class of file but rejected it
  # on strict provenance (news-site scrape) — acceptable under the owner's cite-source standard.
  "Teófilo Cubillas": ("cubillas.jpg", 0.05, None, "Unknown author (PD-Peru-anonymous)", "pd",
                       "Peru · 1978", "https://commons.wikimedia.org/wiki/File:Te%C3%B3filo_Cubillas_1978.jpg"),
}
TARGET = (300, 375)   # 4:5 display resolution

out = {}
total = 0
for name, (fn, vcenter, precrop, author, lic, era, src) in P.items():
    img = Image.open(f"data/photos_raw/{fn}").convert("RGB")
    if precrop:
        w, h = img.size
        img = img.crop((int(precrop[0]*w), int(precrop[1]*h), int(precrop[2]*w), int(precrop[3]*h)))
    img = ImageOps.fit(img, TARGET, method=Image.LANCZOS, centering=(0.5, vcenter))
    buf = io.BytesIO(); img.save(buf, "JPEG", quality=78, optimize=True)
    b = buf.getvalue(); total += len(b)
    lic_short, lic_url = CC[lic]
    out[name] = {
        "b64": "data:image/jpeg;base64," + base64.b64encode(b).decode(),
        "author": author, "license": lic_short, "license_url": lic_url,
        "source": src, "era": era, "bytes": len(b),
    }
    print(f"  {name:20s} {len(b)//1024:3d} KB  {lic_short}")

json.dump(out, open("data/photos.json", "w"), ensure_ascii=False)
print(f"\n{len(out)} photos · {total//1024} KB raw JPEG · ~{int(total*1.34)//1024} KB as base64 · wrote data/photos.json")
