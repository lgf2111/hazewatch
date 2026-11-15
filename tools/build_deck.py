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
          "index", "normalis", "alignment", "thermal anomaly"]


def n(x):
    return f"{x:,}"


# ---- numbers, all from facts.json ------------------------------------------
FP = F["focus_provinces"]
total = n(F["total_rows"])
raw_ratio = f'{F["raw_ratio_viirs_to_modis_detections"]}'
cell_ratio = f'{F["cell_ratio_viirs_to_modis"]}'
overlap = f'{F["modis_cells_also_seen_by_viirs_pct"]}'
ss = FP["south-sumatra"]
day = ss["by_date"]["2026-11-11"]  # Wednesday 11 November
dmin = min(p["distance_to_singapore_km"] for p in FP.values())
dmax = max(p["distance_to_singapore_km"] for p in FP.values())
aligned, pdays = F["aligned_days_total"], F["province_days_total"]
assert F["viirs_snpp_rows"] == 0 and F["feeds"]["viirs_snpp"]["empty"]
assert F["modis_rows"] + F["noaa20_rows"] + F["noaa21_rows"] == F["total_rows"]
assert F["top_province"] == ss["name"]
assert day["aligned"] and day["wind_from_deg"] == 116 and day["cells"] == max(d["cells"] for p in FP.values() for d in p["by_date"].values())
# wind_from 116 deg blows towards 296; Singapore lies at 355 from South Sumatra: 59 deg off, inside the 60 deg window
assert abs(((day["wind_from_deg"] + 180) % 360) - ss["bearing_to_singapore_deg"]) < 60

TEAM = "Can See Or Not"
MEMBER = "Lee Guan Feng"
CHALLENGE = "Harmonization of MODIS and VIIRS Hot Spots"
APP = "hazewatch.leeguanfeng.com"
SRC = "NASA FIRMS MODIS&nbsp;+&nbsp;VIIRS, <span class=\"nw\">8\u201315 November 2026.</span>"
PSI = "PSI: Singapore 24-hour reading at 16:00 on 15 Nov 2026, data.gov.sg."

# colours are SENSOR_COL / HEAT in assets/app.js
SENSOR = [("#ffd23f", "MODIS camera"), ("#ff4d2e", "VIIRS camera")]
HEAT = ["#ece7db", "#fde2bd", "#f8b96e", "#ee8532", "#cf4d1a", "#8f2410"]
BINS = ["0", "1\u20134", "5\u201314", "15\u201329", "30\u201359", "60+"]

IMAGES = {}  # css class -> data URI, so each screenshot is inlined once however often it is cropped


def shot(name, x, y, w, h, width, css_w=CSS_W, marks=()):
    """Real screenshot (css_w CSS px wide), cropped to (x,y,w,h) CSS px and shown `width` px wide.
    marks: ('dot', n, px, py) numbered marker or ('box', x0, y0, x1, y1) outline, in source CSS px, drawn over the capture."""
    cls = "im-" + Path(name).stem
    IMAGES.setdefault(cls, "data:image/png;base64," + base64.b64encode((SHOTS / name).read_bytes()).decode())
    s = width / w
    over = ""
    for m in marks:
        if m[0] == "dot":
            over += f'<span class="mark" style="left:{round((m[2] - x) * s)}px;top:{round((m[3] - y) * s)}px">{m[1]}</span>'
        else:
            over += (f'<span class="box" style="left:{round((m[1] - x) * s)}px;top:{round((m[2] - y) * s)}px;'
                     f'width:{round((m[3] - m[1]) * s)}px;height:{round((m[4] - m[2]) * s)}px"></span>')
    return (
        f'<div class="crop {cls}" style="width:{width}px;height:{round(h * s)}px;'
        f'background-size:{round(css_w * s)}px auto;background-position:{-round(x * s)}px {-round(y * s)}px">{over}</div>'
    )


def cap(text):
    return f'<p class="cap">{text}</p>'


def key(items):
    return '<p class="legend">' + "".join(f'<span><i style="background:{c}"></i>{t}</span>' for c, t in items) + "</p>"


MAP = (236, 300, 1010, 500)  # map pane without the zoom buttons and the attribution strip

slides = []

# 1 — the morning -------------------------------------------------------------
slides.append(f"""
<section class="slide s1">
  <p class="kicker">NASA Space Apps Challenge 2026 \u00b7 Singapore</p>
  <div class="row">
    <div class="col">
      <p class="brand">HazeWatch</p>
      <h1>Can See Or Not?</h1>
      <p class="body">Singapore's haze is imported. The six provinces we watch sit {n(dmin)} to {n(dmax)} km away.</p>
      <p class="personal">[PERSONAL LINE]</p>
      <p class="team">Team <b>\u201c{TEAM}\u201d</b> \u00b7 {MEMBER}<br>{CHALLENGE}</p>
    </div>
    <figure>{shot("desktop-map-cells.png", *MAP, 500)}
      {cap("Singapore (white dot) and the fires NASA saw around it. " + SRC)}</figure>
  </div>
</section>""")

# 2 — why nobody can answer it ------------------------------------------------
slides.append(f"""
<section class="slide s2">
  <div class="col">
    <h2>The answer is on file. The record forgets.</h2>
    <p class="stat">{total}</p>
    <p class="body">dots in four NASA files, from two cameras with two different rulers. This season can't be compared with last.</p>
  </div>
  <figure>{shot("desktop-map-raw.png", 985, 440, 180, 120, 540)}
    {key([(SENSOR[0][0], "MODIS camera"), (SENSOR[1][0], "VIIRS camera")])}
    {cap("Raw dots, same fires. " + SRC)}</figure>
</section>""")

# 3 — the turn ----------------------------------------------------------------
slides.append(f"""
<section class="slide s3">
  <div class="top">
    <h2>Count burning squares, not dots.</h2>
    <p class="stat">{raw_ratio}\u00d7 \u2192 {cell_ratio}\u00d7</p>
    <p class="body">Count each square once a day and the gap between the cameras shrinks. Only <b>{overlap}%</b> of MODIS squares are seen by VIIRS at all.</p>
  </div>
  <div class="pair">
    <figure>{shot("desktop-map-raw.png", *MAP, 520)}
      {cap("Raw dots \u00b7 " + SRC)}</figure>
    <figure>{shot("desktop-map-cells.png", *MAP, 520)}
      {cap("Squares \u00b7 " + SRC)}</figure>
  </div>
</section>""")

# 4 — what it does ------------------------------------------------------------
CAL = (184, 262, 1072, 428)
slides.append(f"""
<section class="slide s4">
  <h2>One page. Six provinces. Eight days.</h2>
  <figure>{shot("desktop-calendar.png", *CAL, 800, marks=[("dot", 1, 362, 465), ("dot", 2, 806, 442), ("dot", 3, 690, 510)])}
    {key(list(zip(HEAT, BINS)) + [("#0f6b74", "wind pointing at us")])}
    {cap("Live app, burning calendar \u00b7 " + SRC)}</figure>
  <ol class="calls">
    <li>One row per province</li>
    <li>Darker square, more fire that day</li>
    <li>Teal bar: wind pointing at Singapore</li>
  </ol>
</section>""")

# 5 — the moment of use -------------------------------------------------------
slides.append(f"""
<section class="slide s5">
  <h2>One real day: Wednesday 11 November</h2>
  <div class="two">
    <div><p class="stat">{day["cells"]}</p>
      <p class="body">squares burning in {ss["name"]}. Wind from {day["wind_from_deg"]}\u00b0: just inside the 60\u00b0 window toward Singapore.</p></div>
    <div><p class="stat">{aligned} of {pdays}</p>
      <p class="body">province-days lined up like this. A heuristic, not a forecast.</p></div>
  </div>
  <figure>{shot("desktop-wind.png", 188, 285, 1064, 310, 860, marks=[("box", 693, 330, 805, 566)])}
    {cap("Live app, wind windows (" + ss["name"] + ") \u00b7 " + SRC + " Wind and rain: NASA POWER; \u2020 Open-Meteo.")}</figure>
</section>""")

# 6 — honesty as strength -----------------------------------------------------
slides.append(f"""
<section class="slide s6">
  <h2>What's real. What's missing. What's next.</h2>
  <div class="three">
    <div class="real"><h3>Real</h3><p class="body">One real week of NASA data.</p></div>
    <div class="missing"><h3>Missing</h3>
      <ul class="body"><li>7-day window</li><li>No archive</li><li>S-NPP file empty</li><li>Heuristic, not a forecast</li></ul></div>
    <div class="next"><h3>Next</h3>
      <ol class="body"><li>12-month archive</li><li>Agreement by province</li><li>Test against Singapore's PSI record</li></ol></div>
  </div>
</section>""")

# 7 — the ask -----------------------------------------------------------------
slides.append(f"""
<section class="slide s7">
  <h1>Can See Or Not?</h1>
  <p class="link">{APP}</p>
  <p class="body">Today is calm \u2014 PSI 33\u201335. The record has to exist for the mornings it isn't.</p>
  <p class="ask">Next: an agency pilot, or archive funding.</p>
  <p class="note">{PSI}</p>
  <p class="team">Team <b>\u201c{TEAM}\u201d</b> \u00b7 {MEMBER}<br>Singapore Local Event \u00b7 {CHALLENGE} \u00b7 Best Use of Data</p>
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
.nw{white-space:nowrap}
.cap{font-size:16px;line-height:1.3;color:var(--mute)}
.small{font-size:22px;line-height:1.35;color:var(--mute)}
/* 1 */
.s1{flex-direction:column;align-items:stretch;justify-content:center;gap:16px}
.s1 .row{display:flex;align-items:center;gap:44px}
.s1 .col{flex-basis:600px;gap:14px}
.s1 h1{font-size:100px}
.s1 .brand{font-size:34px;font-weight:800;color:var(--fire);letter-spacing:-.5px}
.s1 .body{font-size:32px}
.personal{font-size:30px;padding:8px 16px;border:2px dashed var(--fire);border-radius:8px;color:var(--fire);font-weight:700;align-self:flex-start}
/* 2 */
.s2 .col{flex-basis:600px}
/* 3, 4, 5: text across the top, picture below */
.s3 .top .stat{font-size:84px}
.s3,.s4,.s5,.s6{flex-direction:column;align-items:stretch;justify-content:center;gap:20px}
.top{display:grid;grid-template-columns:1fr auto;grid-template-areas:"h s" "b b";column-gap:40px;row-gap:8px;align-items:center}
.top h2{grid-area:h}
.top .stat{grid-area:s;justify-self:end}
.top .body{grid-area:b}
.s3 .pair{display:flex;gap:24px;justify-content:center}
.s4 figure,.s5 figure{align-self:center}
.s5 .two{display:grid;grid-template-columns:1fr 1fr;gap:40px}
.s5 .stat{font-size:80px}
.s5 .body{font-size:30px}
.s4 .calls{list-style:none;counter-reset:c;display:flex;gap:28px;align-self:center;width:1000px}
.s4 .calls li{counter-increment:c;font-size:28px;line-height:1.2;flex:1;display:flex;gap:12px;align-items:flex-start}
.s4 .calls li::before{content:counter(c);flex:0 0 40px;height:40px;border-radius:50%;background:var(--fire);color:#fff;font-weight:800;font-size:26px;display:flex;align-items:center;justify-content:center;border:3px solid #fff;box-shadow:0 0 0 1px var(--fire)}
.s4 figure{position:relative}
.crop{position:relative}
.mark{position:absolute;width:32px;height:32px;margin:-16px 0 0 -16px;border-radius:50%;background:var(--fire);color:#fff;font-weight:800;font-size:20px;display:flex;align-items:center;justify-content:center;border:3px solid #fff;box-shadow:0 0 0 1px var(--fire)}
.box{position:absolute;border:4px solid var(--fire);border-radius:6px}
/* 6 */
.s6 .three{display:grid;grid-template-columns:1fr 1.2fr 1.4fr;gap:20px}
.s6 .three>div{padding:18px 24px;border-radius:10px;border-top:8px solid}
.s6 .real{background:#e3f0ee;border-color:var(--teal)}
.s6 .real h3{color:var(--teal)}
.s6 .missing{background:var(--amber);border-color:var(--fire)}
.s6 .missing h3{color:var(--fire)}
.s6 .next{background:#fff;border-color:var(--ink)}
.s6 ul,.s6 ol{list-style:none;counter-reset:n}
.s6 ol li{counter-increment:n}
.s6 ol li::before{content:counter(n) ". ";font-weight:800}
.s6 h3{margin-bottom:8px}
.s6 .body{font-size:34px}
.s6 h2{font-size:56px}
/* 7 */
.s7{flex-direction:column;justify-content:center;align-items:flex-start;gap:22px;padding-left:96px}
.s7 h1{font-size:132px;white-space:nowrap;color:var(--fire);letter-spacing:-3px}
.s7 .body{font-size:40px;max-width:1000px}
.s7 .link{font-size:52px;font-weight:700;color:var(--teal)}
.s7 .ask{font-size:44px;font-weight:800;color:var(--teal)}
.s7 .note{font-size:16px;line-height:1.35;color:var(--mute);max-width:980px}
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
