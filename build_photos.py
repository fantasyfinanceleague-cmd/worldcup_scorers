#!/usr/bin/env python3
"""Process the 11 walkthrough photos -> tight 4:5 display-res crops -> base64 -> data/photos.json,
with author/license/source metadata for the footer credits. Re-run to regenerate."""
import base64, io, json
from PIL import Image, ImageOps

CC = {
    "by4":  ("CC BY 4.0",      "https://creativecommons.org/licenses/by/4.0/"),
    "bysa4":("CC BY-SA 4.0",   "https://creativecommons.org/licenses/by-sa/4.0/"),
    "bysa3":("CC BY-SA 3.0",   "https://creativecommons.org/licenses/by-sa/3.0/"),
    "bysa3de":("CC BY-SA 3.0 de","https://creativecommons.org/licenses/by-sa/3.0/de/deed.en"),
    "cc0":  ("CC0 1.0",        "https://creativecommons.org/publicdomain/zero/1.0/"),
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
