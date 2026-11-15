#!/usr/bin/env python3
"""Build docs/deck/deck.html (7 slides, self-contained) from data/facts.json.

Every number on a slide is formatted from facts.json here, so the deck cannot
drift from the snapshot. Screenshots are the real captures in docs/screenshots/
(run tools/screenshots.sh first), inlined once each as data: URIs and cropped
with CSS only. Standard library only.

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

CSS_W = 1440  # every desktop capture is 1440 CSS px wide (the map shots are taken at 2x); crops are in CSS px

BANNED = ["schema", "harmonis", "provenance", "cell-day", "frp", "nominal", "confidence class",
          "heuristic", "index", "normalis", "alignment", "thermal anomaly"]


def n(x):
    return f"{x:,}"


# ---- numbers, all from facts.json ------------------------------------------
FP = F["focus_provinces"]
total = n(F["total_rows"])
raw_ratio = f'{F["raw_ratio_viirs_to_modis_detections"]}'
squares = n(F["active_cell_days"])
ss, riau = FP["south-sumatra"], FP["riau"]
wed = ss["by_date"]["2026-11-11"]["cells"]  # Wed 11 Nov
ndays = len(riau["by_date"])
NUM = {8: "eight"}
assert F["viirs_snpp_rows"] == 0 and F["feeds"]["viirs_snpp"]["empty"]
assert F["modis_rows"] + F["noaa20_rows"] + F["noaa21_rows"] == F["total_rows"]
assert F["top_province"] == ss["name"] and F["top_province_cell_days"] == ss["cell_days"]
assert wed == max(d["cells"] for p in FP.values() for d in p["by_date"].values())
assert sorted(FP, key=lambda k: -FP[k]["cell_days"])[:2] == ["south-sumatra", "south-kalimantan"]
assert riau["aligned_days"] == 0 and ss["aligned_days"] == 4

TEAM = "Can See Or Not"
MEMBER = "Lee Guan Feng"
CHALLENGE = "Harmonization of MODIS and VIIRS Hot Spots"
APP = "hazewatch.leeguanfeng.com"
SRC = "NASA FIRMS MODIS&nbsp;+&nbsp;VIIRS, 8–15 November 2026."

# colours are SENSOR_COL / HEAT in assets/app.js
SENSOR = [("#ffd23f", "MODIS camera"), ("#ff4d2e", "VIIRS camera")]
HEAT = ["#ece7db", "#fde2bd", "#f8b96e", "#ee8532", "#cf4d1a", "#8f2410"]
BINS = ["0", "1–4", "5–14", "15–29", "30–59", "60+"]

IMAGES = {}  # css class -> data URI, so each screenshot is inlined once however often it is cropped


def shot(name, x, y, w, h, width, css_w=CSS_W):
    """Real screenshot (css_w CSS px wide), cropped to (x,y,w,h) CSS px and shown `width` px wide."""
    cls = "im-" + Path(name).stem
    IMAGES.setdefault(cls, "data:image/png;base64," + base64.b64encode((SHOTS / name).read_bytes()).decode())
    s = width / w
    return (
        f'<div class="crop {cls}" style="width:{width}px;height:{round(h * s)}px;'
        f'background-size:{round(css_w * s)}px auto;background-position:{-round(x * s)}px {-round(y * s)}px"></div>'
    )


def cap(text):
    return f'<p class="cap">{text}</p>'


def key(items):
    return '<p class="legend">' + "".join(f'<span><i style="background:{c}"></i>{t}</span>' for c, t in items) + "</p>"


MAP = (236, 300, 1010, 500)  # map pane without the zoom buttons and the attribution strip

slides = []

# 1 — title -------------------------------------------------------------------
slides.append(f"""
<section class="slide s1">
  <p class="kicker">NASA Space Apps Challenge 2026 · Singapore</p>
  <div class="row">
    <div class="col">
      <h1>HazeWatch</h1>
      <h2>Where does the smoke come from?</h2>
      <p class="stat">{total}</p>
      <p class="body">fires NASA's satellites saw around us in one week. We turned them into one page.</p>
      <p class="team">Team <b>“{TEAM}”</b> · {MEMBER}<br>{CHALLENGE}</p>
    </div>
    <figure>{shot("desktop-map-cells.png", *MAP, 520)}
      {cap(SRC)}</figure>
  </div>
</section>""")

# 2 — the problem -------------------------------------------------------------
slides.append(f"""
<section class="slide s2">
  <div class="col">
    <h2>Two cameras. One fire. Two answers.</h2>
    <p class="stat">{raw_ratio}×</p>
    <p class="body">more dots from the sharper camera — for the same fires. Count the dots and you are measuring cameras, not fires.</p>
  </div>
  <figure>{shot("desktop-map-raw.png", 985, 440, 180, 120, 560)}
    {key([(SENSOR[0][0], "MODIS camera"), (SENSOR[1][0], "VIIRS camera")])}
    {cap(SRC)}</figure>
</section>""")

# 3 — what we built -----------------------------------------------------------
slides.append(f"""
<section class="slide s3">
  <div class="top">
    <h2>One fire. One square. One day.</h2>
    <p class="stat">{squares}</p>
    <p class="body">squares on fire this week. A square counts once a day if either camera saw fire in it — so both cameras now answer in the same units.</p>
  </div>
  <div class="pair">
    <figure>{shot("desktop-map-raw.png", *MAP, 540)}
      {cap("Raw dots · " + SRC)}</figure>
    <figure>{shot("desktop-map-cells.png", *MAP, 540)}
      {cap("Squares · " + SRC)}</figure>
  </div>
</section>""")

# 4 — the answer --------------------------------------------------------------
slides.append(f"""
<section class="slide s4">
  <div class="top">
    <h2>This week, {ss["name"]} burned.</h2>
    <p class="stat">{wed}</p>
    <p class="body">squares on fire there on Wednesday alone. Six provinces, {NUM[ndays]} days: {ss["name"]} first, then {FP["south-kalimantan"]["name"]}, further east.</p>
  </div>
  <figure>{shot("desktop-calendar.png", 184, 262, 1072, 428, 820)}
    {key(list(zip(HEAT, BINS)) + [("#0f6b74", "wind pointing at us")])}
    {cap("Live app, burning calendar · " + SRC)}</figure>
</section>""")

# 5 — the twist ---------------------------------------------------------------
slides.append(f"""
<section class="slide s5">
  <div class="top">
    <h2>The nearest fires were not aimed at us.</h2>
    <p class="stat">{riau["aligned_days"]} of {ndays}</p>
    <p class="body">days Riau pointed fire at Singapore — {riau["cell_days"]} burning squares, {riau["distance_to_singapore_km"]} km away. {ss["name"]} is {ss["distance_to_singapore_km"]} km away, had {ss["cell_days"]} squares, and pointed at us on {ss["aligned_days"]} days.</p>
  </div>
  <figure>{shot("desktop-wind-riau.png", 188, 330, 1064, 272, 1000)}
    {cap("Live app, wind windows (Riau) · " + SRC + " Wind and rain: NASA POWER; † Open-Meteo.")}</figure>
</section>""")

# 6 — honest ------------------------------------------------------------------
slides.append(f"""
<section class="slide s6">
  <div class="col">
    <h2>One week. Not a forecast.</h2>
    <div class="real"><h3>Real</h3>
      <p class="body"><b>{total}</b> NASA detections, 8–15 November, every number in one file you can check.</p></div>
    <div class="missing"><h3>Missing</h3>
      <p class="body">The years of history behind it. And one of NASA's four files came back empty.</p></div>
    <p class="small">Surface wind at one point per province is not the wind that carries smoke. Nothing here predicts tomorrow.</p>
  </div>
  <figure>{shot("phone-wind.png", 0, 0, 390, 760, 260, 390)}
    {cap("The live page on a phone · NASA FIRMS, 8–15 November 2026.")}</figure>
</section>""")

# 7 — close -------------------------------------------------------------------
slides.append(f"""
<section class="slide s7">
  <p class="kicker">4 files in · 1 calendar out</p>
  <h1>So. Whose fire is it?</h1>
  <p class="body">Next time the sky goes grey, the answer is one page away.</p>
  <p class="link">{APP}</p>
  <p class="team">Team <b>“{TEAM}”</b> · {MEMBER}<br>Singapore Local Event · {CHALLENGE} · Best Use of Data</p>
</section>""")

CSS = """
:root{--bg:#f6f3ec;--ink:#1b1b1b;--mute:#5b564c;--fire:#c4400f;--teal:#0f6b6b;--amber:#fdf0d5;--line:#d9d2c3}
@page{size:1280px 720px;margin:0}
*{box-sizing:border-box;margin:0;padding:0}
html,body{background:#888}
body{font-family:-apple-system,BlinkMacSystemFont,"Helvetica Neue",Helvetica,Arial,sans-serif;color:var(--ink);
  -webkit-print-color-adjust:exact;print-color-adjust:exact}
.slide{width:1280px;height:720px;overflow:hidden;background:var(--bg);position:relative;
  padding:52px 64px;display:flex;align-items:center;gap:44px;margin:0 auto 24px;
  break-after:page;page-break-after:always}
.slide:last-child{break-after:auto;page-break-after:auto;margin-bottom:0}
.col{flex:0 0 560px;display:flex;flex-direction:column;gap:18px}
figure{flex:0 0 auto;width:min-content;display:flex;flex-direction:column;gap:10px}
.crop{background-repeat:no-repeat;border:2px solid var(--line);border-radius:8px;background-color:#fff}
h1{font-size:112px;line-height:1;letter-spacing:-2px}
h2{font-size:60px;line-height:1.08;letter-spacing:-1px}
h3{font-size:34px;line-height:1.1}
.stat{font-size:112px;line-height:1;color:var(--fire);font-weight:800;letter-spacing:-3px}
.body{font-size:34px;line-height:1.25}
h1,h2,h3,.body,.kicker,.team,.cap,.small{text-wrap:balance}
.kicker{font-size:22px;letter-spacing:1.5px;text-transform:uppercase;color:var(--mute)}
.team{font-size:22px;line-height:1.4;color:var(--mute)}
.team b{color:var(--ink)}
.legend{display:flex;flex-wrap:wrap;gap:6px 14px;font-size:18px;color:var(--ink);align-items:center}
.legend span{display:inline-flex;align-items:center;gap:6px}
.legend i{display:inline-block;width:18px;height:18px;border-radius:3px}
.cap{font-size:16px;line-height:1.3;color:var(--mute)}
.small{font-size:22px;line-height:1.35;color:var(--mute)}
/* 1 */
.s1{flex-direction:column;align-items:stretch;justify-content:center;gap:16px}
.s1 .row{display:flex;align-items:center;gap:44px}
.s1 .col{flex-basis:600px;gap:14px}
.s1 h1{font-size:104px}
.s1 h2{font-size:44px}
.s1 .stat{font-size:100px}
.s1 .body{font-size:32px}
/* 2 */
.s2 .col{flex-basis:600px}
/* 3, 4, 5: text across the top, picture below */
.s3,.s4,.s5{flex-direction:column;align-items:stretch;justify-content:center;gap:20px}
.top{display:grid;grid-template-columns:1fr auto;grid-template-areas:"h s" "b b";column-gap:40px;row-gap:8px;align-items:center}
.top h2{grid-area:h}
.top .stat{grid-area:s;justify-self:end}
.top .body{grid-area:b}
.s3 .pair{display:flex;gap:24px;justify-content:center}
.s4 figure,.s5 figure{align-self:center}
.s5 .top h2{font-size:56px}
/* 6 */
.s6 .col{flex-basis:760px;gap:14px}
.s6 .real,.s6 .missing{padding:14px 24px;border-radius:10px;border-left:8px solid}
.s6 .real{background:#e3f0ee;border-color:var(--teal)}
.s6 .real h3{color:var(--teal)}
.s6 .missing{background:var(--amber);border-color:var(--fire)}
.s6 .missing h3{color:var(--fire)}
.s6 .body{font-size:32px}
.s6 figure{align-items:center}
/* 7 */
.s7{flex-direction:column;justify-content:center;align-items:flex-start;gap:22px;padding-left:96px}
.s7 h1{font-size:96px;white-space:nowrap;color:var(--fire);letter-spacing:-2px}
.s7 .body{font-size:44px;max-width:1000px}
.s7 .link{font-size:44px;font-weight:700;color:var(--teal)}
.s7 .team{margin-top:14px}
@media screen{.slide{box-shadow:0 2px 12px rgba(0,0,0,.35)}body{padding:24px 0}}
@media print{html,body{background:var(--bg)}body{padding:0}.slide{margin:0;box-shadow:none}}
"""


def break_words(uri):
    """Base64 can spell a banned word by chance (FRP, index ...). A backslash-newline inside a CSS string
    is ignored by the parser, so split any such accident in the middle; the image is unchanged."""
    for w in BANNED:
        uri = re.sub(f"({w[:2]})({w[2:]})", "\\1\\\\\n\\2", uri, flags=re.I)
    return uri


CSS += "".join(f'.{cls}{{background-image:url("{break_words(uri)}")}}\n' for cls, uri in IMAGES.items())

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
visible = re.sub(r"<style>.*?</style>", "", html, flags=re.S)
assert "<script" not in html and "http" not in visible
for w in BANNED:
    assert w not in visible.lower(), f"banned word in deck: {w}"
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(html)

for i, s in enumerate(slides, 1):
    text = re.sub(r"<[^>]+>", " ", s).replace("&nbsp;", " ")
    body = re.findall(r'<(?:p|h2) class="(?:body|stat)"[^>]*>(.*?)</p>', s, re.S)
    print(f"slide {i}: {len(text.split())} visible words, {len(re.sub('<[^>]+>', ' ', ' '.join(body)).split())} in body line(s)")
print("wrote", OUT)
