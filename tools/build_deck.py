#!/usr/bin/env python3
"""Build docs/deck/deck.html (7 slides, self-contained) from data/facts.json.

Every number on a slide is formatted from facts.json here, so the deck cannot
drift from the snapshot. Screenshots are the real captures in docs/screenshots/,
inlined as data: URIs and cropped with CSS only. Standard library only.

    python3 tools/build_deck.py
"""
import base64
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
F = json.loads((ROOT / "data" / "facts.json").read_text())
SHOTS = ROOT / "docs" / "screenshots"
OUT = ROOT / "docs" / "deck" / "deck.html"

IMG_W = 1440  # screenshot width in px (desktop-*.png are 1440x900)


def n(x):
    return f"{x:,}"


# ---- numbers, all from facts.json ------------------------------------------
total = n(F["total_rows"])
modis = n(F["modis_rows"])
snpp = n(F["viirs_snpp_rows"])
n20 = n(F["noaa20_rows"])
n21 = n(F["noaa21_rows"])
raw_ratio = f'{F["raw_ratio_viirs_to_modis_detections"]}'
cell_ratio = f'{F["cell_ratio_viirs_to_modis"]}'
overlap = f'{F["modis_cells_also_seen_by_viirs_pct"]}'
focus = n(F["focus_cell_days"])
active = n(F["active_cell_days"])
top_name = F["top_province"]
top_cells = n(F["top_province_cell_days"])
aligned = F["aligned_days_total"]
pdays = F["province_days_total"]
assert F["viirs_snpp_rows"] == 0 and F["feeds"]["viirs_snpp"]["empty"]
assert F["modis_rows"] + F["noaa20_rows"] + F["noaa21_rows"] == F["total_rows"]

TEAM = "Can See Or Not"
MEMBER = "Lee Guan Feng"
CHALLENGE = "Harmonization of MODIS and VIIRS Hot Spots"
APP = "leeguanfeng.com/hazewatch"

FIRMS = "NASA FIRMS MODIS C6.1&nbsp;+&nbsp;VIIRS C2 NRT active fire"


def shot(name, x, y, w, h, width):
    """Real screenshot, cropped to (x,y,w,h) source px and shown `width` px wide."""
    s = width / w
    b64 = base64.b64encode((SHOTS / name).read_bytes()).decode()
    return (
        f'<div class="crop" style="width:{width}px;height:{round(h * s)}px">'
        f'<img alt="" style="width:{round(IMG_W * s)}px;left:{-round(x * s)}px;'
        f'top:{-round(y * s)}px" src="data:image/png;base64,{b64}"></div>'
    )


def cap(text):
    return f'<p class="cap">{text}</p>'


slides = []

# 1 — title -------------------------------------------------------------------
slides.append(f"""
<section class="slide s1">
  <div class="col">
    <p class="kicker">NASA Space Apps Challenge 2026<br>Singapore Local Event</p>
    <h1>HazeWatch</h1>
    <h2>Whose fires become Singapore's smoke?</h2>
    <p class="stat"><b>{total}</b></p>
    <p class="body">NASA fire detections. One week. Four files.</p>
    <p class="team">Team <b>“{TEAM}”</b> · {MEMBER}<br>{CHALLENGE}<br>Award target: Best Use of Data</p>
  </div>
  <figure>{shot("desktop-map-raw.png", 236, 306, 1010, 528, 580)}
    {cap(f"Live app, map view · {FIRMS} · Basemap NASA GIBS")}</figure>
</section>""")

# 2 — problem -----------------------------------------------------------------
slides.append(f"""
<section class="slide s2">
  <div class="col">
    <h2>Two sensors, two rulers</h2>
    <p class="stat"><b>{raw_ratio}×</b></p>
    <p class="body">more VIIRS than MODIS detections, same fires.</p>
    <ul class="feeds">
      <li>MODIS <b>{modis}</b></li>
      <li class="bad">S-NPP <b>{snpp}</b> · empty</li>
      <li>NOAA-20 <b>{n20}</b></li>
      <li>NOAA-21 <b>{n21}</b></li>
    </ul>
  </div>
  <figure>{shot("desktop-data-limits.png", 188, 395, 1064, 315, 700)}
    {cap("Live app, Data &amp; limits · NASA FIRMS MODIS C6.1 and VIIRS S-NPP / NOAA-20 / NOAA-21 C2 NRT feeds")}</figure>
</section>""")

# 3 — what it does ------------------------------------------------------------
slides.append(f"""
<section class="slide s3">
  <div class="top">
    <h2>One schema. One scale. One grid.</h2>
    <p class="stat"><b>{raw_ratio}× → {cell_ratio}×</b></p>
    <p class="body">Count burning cells, not dots. Only <b>{overlap}%</b> of MODIS cells are also seen by VIIRS.</p>
  </div>
  <div class="pair">
    <figure>{shot("desktop-map-raw.png", 236, 306, 1010, 528, 560)}
      {cap(f"Raw detections · {FIRMS}")}</figure>
    <figure>{shot("desktop-map-cells.png", 236, 306, 1010, 528, 560)}
      {cap(f"Harmonised 0.1° cells · {FIRMS}")}</figure>
  </div>
</section>""")

# 4 — burning calendar --------------------------------------------------------
slides.append(f"""
<section class="slide s4">
  <div class="col">
    <h2>Six provinces, one week</h2>
    <p class="stat"><b>{top_cells}</b></p>
    <p class="body">burning cell-days in {top_name}, the most active. Six provinces: <b>{focus}</b> of <b>{active}</b>.</p>
  </div>
  <figure>{shot("desktop-calendar.png", 184, 315, 1072, 437, 690)}
    {cap(f"Live app, burning calendar · {FIRMS}, harmonised to 0.1° cell-days")}</figure>
</section>""")

# 5 — wind windows ------------------------------------------------------------
slides.append(f"""
<section class="slide s5">
  <div class="col">
    <h2>When do fire and wind line up?</h2>
    <p class="stat"><b>{aligned} of {pdays}</b></p>
    <p class="body">province-days: fire burning, wind within 60° of Singapore.</p>
  </div>
  <figure>{shot("desktop-wind.png", 188, 298, 1064, 517, 690)}
    {cap("Live app, wind windows (South Sumatra) · NASA FIRMS MODIS&nbsp;+&nbsp;VIIRS<br>NASA POWER WD10M, WS10M, PRECTOTCORR · † Open-Meteo")}</figure>
</section>""")

# 6 — real vs missing ---------------------------------------------------------
slides.append(f"""
<section class="slide s6">
  <h2>Real vs missing</h2>
  <div class="two">
    <div class="real">
      <h3>Real</h3>
      <p class="body"><b>{total}</b> NASA detections, one week, rebuilt by one command.</p>
    </div>
    <div class="missing">
      <h3>Missing</h3>
      <ul class="body">
        <li>7-day window only</li>
        <li>No archive</li>
        <li>S-NPP feed empty</li>
        <li>Heuristic, not a forecast</li>
      </ul>
    </div>
  </div>
  <figure>{shot("desktop-data-limits.png", 188, 256, 1064, 116, 1152)}
    {cap("Live app, Data &amp; limits · NASA FIRMS VIIRS S-NPP C2 NRT (0 rows), NASA POWER, FIRMS archive (not loaded)")}</figure>
</section>""")

# 7 — close -------------------------------------------------------------------
slides.append(f"""
<section class="slide s7">
  <p class="kicker">4 files → 1 calendar</p>
  <h1>Can See Or Not?</h1>
  <p class="body">Yes. Next time the sky goes grey, where it starts is one page away.</p>
  <p class="link">{APP}</p>
  <p class="team">Team <b>“{TEAM}”</b> · {MEMBER}<br>Singapore Local Event · {CHALLENGE} · Best Use of Data</p>
  <p class="cap">Data: NASA FIRMS (MODIS, VIIRS), NASA GIBS, NASA POWER</p>
</section>""")

CSS = """
:root{--bg:#f6f3ec;--ink:#1b1b1b;--mute:#5b564c;--fire:#c4400f;--teal:#0f6b6b;--amber:#fdf0d5;--line:#d9d2c3}
@page{size:1280px 720px;margin:0}
*{box-sizing:border-box;margin:0;padding:0}
html,body{background:#888}
body{font-family:-apple-system,BlinkMacSystemFont,"Helvetica Neue",Helvetica,Arial,sans-serif;color:var(--ink);
  -webkit-print-color-adjust:exact;print-color-adjust:exact}
.slide{width:1280px;height:720px;overflow:hidden;background:var(--bg);position:relative;
  padding:56px 64px;display:flex;align-items:center;gap:40px;margin:0 auto 24px;
  break-after:page;page-break-after:always}
.slide:last-child{break-after:auto;page-break-after:auto;margin-bottom:0}
.col{flex:0 0 440px;display:flex;flex-direction:column;gap:20px}
figure{flex:0 0 auto;width:min-content;display:flex;flex-direction:column;gap:10px}
.crop{position:relative;overflow:hidden;border:2px solid var(--line);border-radius:8px;background:#fff}
.crop img{position:absolute;display:block;max-width:none}
h1{font-size:112px;line-height:1;letter-spacing:-2px}
h2{font-size:48px;line-height:1.1;letter-spacing:-.5px}
h3{font-size:36px;line-height:1.1}
.stat{font-size:96px;line-height:1;color:var(--fire);font-weight:800;letter-spacing:-2px}
.body,.body li{font-size:32px;line-height:1.25}
h1,h2,h3,.body,.kicker,.team,.cap{text-wrap:balance}
.kicker{font-size:22px;letter-spacing:1.5px;text-transform:uppercase;color:var(--mute)}
.team{font-size:22px;line-height:1.4;color:var(--mute)}
.team b{color:var(--ink)}
.cap{font-size:16px;line-height:1.3;color:var(--mute)}
.feeds{list-style:none;font-size:32px;line-height:1.35;border-top:2px solid var(--line);padding-top:12px}
.feeds b{font-variant-numeric:tabular-nums}
.feeds .bad{color:var(--fire)}
/* 1 */
.s1 .col{flex-basis:500px;gap:18px}
.s1 h1{font-size:96px}
.s1 h2{font-size:40px}
.s1 .stat{font-size:88px}
/* 3 */
.s3{flex-direction:column;align-items:stretch;justify-content:center;gap:24px}
.s3 .top{display:grid;grid-template-columns:auto auto;grid-template-areas:"h s" "b b";column-gap:40px;row-gap:6px;align-items:baseline}
.s3 .top h2{grid-area:h;font-size:44px}
.s3 .top .stat{grid-area:s;font-size:72px;justify-self:end}
.s3 .top .body{grid-area:b}
.s3 .pair{display:flex;gap:32px;justify-content:center}
/* 4, 5 */
.s2 .col,.s4 .col,.s5 .col{flex-basis:400px}
/* 6 */
.s6{flex-direction:column;align-items:stretch;justify-content:center;gap:24px}
.s6 .two{display:grid;grid-template-columns:1fr 1fr;gap:32px}
.s6 .two>div{padding:18px 26px;border-radius:10px;border-left:8px solid}
.s6 .real{background:#e3f0ee;border-color:var(--teal)}
.s6 .real h3{color:var(--teal)}
.s6 .missing{background:var(--amber);border-color:var(--fire)}
.s6 .missing h3{color:var(--fire)}
.s6 .missing ul{list-style:none}
.s6 figure{align-items:center}
/* 7 */
.s7{flex-direction:column;justify-content:center;align-items:flex-start;gap:22px;padding-left:96px}
.s7 h1{font-size:150px;color:var(--fire);letter-spacing:-3px}
.s7 .body{font-size:40px;max-width:900px}
.s7 .link{font-size:40px;font-weight:700;color:var(--teal)}
.s7 .team{margin-top:14px}
@media screen{.slide{box-shadow:0 2px 12px rgba(0,0,0,.35)}body{padding:24px 0}}
@media print{html,body{background:var(--bg)}body{padding:0}.slide{margin:0;box-shadow:none}}
"""

html = (
    '<!doctype html>\n<html lang="en"><head><meta charset="utf-8">'
    "<title>HazeWatch deck</title>"
    '<meta name="viewport" content="width=1280">'
    f"<style>{CSS}</style></head><body>"
    + "".join(slides)
    + "</body></html>\n"
)

# ---- guard rails ------------------------------------------------------------
assert len(slides) == 7
assert "<script" not in html and "http" not in re.sub(r"data:image/png;base64,[A-Za-z0-9+/=]+", "", html)
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(html)

# visible body copy per slide: headline + stat + .body text, excluding captions/team/kicker
for i, s in enumerate(slides, 1):
    keep = re.findall(r'<(?:h[12]|p class="(?:stat|body)"|ul class="(?:body|feeds)"|li)[^>]*>(.*?)</(?:h[12]|p|ul|li)>', s, re.S)
    text = re.sub(r"<[^>]+>", " ", " ".join(keep))
    print(f"slide {i}: {len(text.split())} words (headline+stat+body)")
print("wrote", OUT)
