#!/usr/bin/env python3
"""Build docs/deck/deck.html (7 slides, self-contained) from data/facts.json and data/archive-2015.json.

Every number on a slide is formatted from those two files here (and asserted), so the deck cannot
drift from the data. Screenshots are the real captures in docs/screenshots/
(run tools/screenshots.sh first), inlined once each as data: URIs and cropped
with CSS only. Standard library only.

    python3 tools/build_deck.py
"""
import base64
import datetime as dt
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
F = json.loads((ROOT / "data" / "facts.json").read_text())
A = json.loads((ROOT / "data" / "archive-2015.json").read_text())
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
cell_ratio = f'{F["cell_ratio_viirs_to_modis"]}'
overlap = f'{F["modis_cells_also_seen_by_viirs_pct"]}'  # quoted in DECK.md notes, not on a slide
ss = FP["south-sumatra"]
active_cells = n(F["active_cell_days"])
top_cells = n(F["top_province_cell_days"])
riau_cells = n(F["focus_provinces"]["riau"]["cell_days"])
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

# ---- the September 2015 look back (data/archive-2015.json) ------------------
EV = A["events"]
CL = EV["closure_2015"]
closure = dt.date.fromisoformat(CL["date"])
TOT = A["six_province_total"]
peak = max(TOT, key=TOT.get)
peak_d = dt.date.fromisoformat(peak)
second = sorted(TOT, key=TOT.get)[-2]
lead_days = (closure - peak_d).days
WORD = {3: "three"}
assert A["dates"] == sorted(TOT) and set(A["provinces"]["south-sumatra"]) == set(TOT)
assert closure.strftime("%A") == CL["weekday"] == "Friday"
assert (peak, TOT[peak]) == ("2015-09-22", 1590) and TOT[CL["date"]] == 562 and (second, TOT[second]) == ("2015-09-08", 1545)
assert lead_days in WORD and TOT["2015-09-23"] == 1269 and TOT["2015-09-24"] == 1017  # still high, then the collapse
assert CL["psi_24h_peak"] == 322
npp = dt.datetime.fromisoformat(EV["suomi_npp_cessation"]["utc"].replace("Z", "+00:00"))
psi_now = EV["psi_today"]
long_date = lambda d: f"{d.day} {d:%B} {d.year}"

TEAM = "Can See Or Not"
MEMBER = "Lee Guan Feng"
CHALLENGE = "Harmonization of MODIS and VIIRS Hot Spots"
APP = "hazewatch.leeguanfeng.com"
SRC = "NASA FIRMS MODIS&nbsp;+&nbsp;VIIRS, <span class=\"nw\">8\u201315 November 2026.</span>"
PSI = f"PSI: Singapore 24-hour reading at {psi_now['time']} on {long_date(dt.date.fromisoformat(psi_now['date']))}, data.gov.sg."

# colours are SENSOR_COL / HEAT in assets/app.js
SENSOR = [("#ffd23f", "MODIS"), ("#ff4d2e", "VIIRS")]
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


def chart():
    """One bar per day of the look back, drawn from archive-2015.json. Peak and closure day are marked."""
    W, H, L, B, T = 1152, 318, 50, 30, 8
    dates = A["dates"]
    top = 1800
    bw = (W - L) / len(dates)
    y = lambda v: T + (H - T - B) * (1 - v / top)
    out = [f'<svg class="chart" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Burning squares per day, six provinces, September 2015">']
    for g in (0, 500, 1000, 1500):
        out.append(f'<line x1="{L}" x2="{W}" y1="{y(g):.1f}" y2="{y(g):.1f}" stroke="#d9d2c3" stroke-width="1"/>'
                   f'<text x="{L - 8}" y="{y(g) + 6:.1f}" text-anchor="end" font-size="17" fill="#5b564c">{n(g)}</text>')
    for i, d in enumerate(dates):
        v, x = TOT[d], L + i * bw
        colour = "#8f2410" if d == peak else "#0f6b74" if d == CL["date"] else "#f4b476"
        out.append(f'<rect x="{x + 3:.1f}" y="{y(v):.1f}" width="{bw - 6:.1f}" height="{y(0) - y(v):.1f}" rx="2" fill="{colour}"/>')
        out.append(f'<text x="{x + bw / 2:.1f}" y="{H - 8}" text-anchor="middle" font-size="16" fill="{"#1b1b1b" if d in (peak, CL["date"]) else "#5b564c"}" font-weight="{700 if d in (peak, CL["date"]) else 400}">{int(d[-2:])}</text>')
    cx = lambda d: L + dates.index(d) * bw + bw / 2
    def tag(d, lines, colour, anchor="middle", dx=0, ly=None):
        x0, yb = cx(d), y(TOT[d])
        ty = ly if ly is not None else yb - 10 - 22 * (len(lines) - 1)
        for k, t in enumerate(lines):
            out.append(f'<text x="{x0 + dx:.1f}" y="{ty + 22 * k:.1f}" text-anchor="{anchor}" font-size="20" font-weight="800" fill="{colour}">{t}</text>')
        return ty + 22 * (len(lines) - 1)
    d_short = lambda d: f"{int(d[-2:])} Sep"
    tag(peak, [f"{d_short(peak)} \u00b7 {n(TOT[peak])} \u00b7 fires peak"], "#8f2410", "middle", -30)
    tag(second, [f"{d_short(second)} \u00b7 {n(TOT[second])} \u00b7 no closure"], "#5b564c", "start", -22)
    ly = y(1500)
    last = tag(CL["date"], [f"{d_short(CL['date'])} \u00b7 {n(TOT[CL['date']])}", f"schools closed \u00b7 PSI {CL['psi_24h_peak']}"], "#0f6b74", "start", -14, ly)
    out.append(f'<line x1="{cx(CL["date"]):.1f}" x2="{cx(CL["date"]):.1f}" y1="{last + 8:.1f}" y2="{y(TOT[CL["date"]]) - 4:.1f}" stroke="#0f6b74" stroke-width="3"/>')
    out.append("</svg>")
    return "".join(out)


MAP = (236, 300, 1010, 500)  # map pane without the zoom buttons and the attribution strip

slides = []

# 1 — the morning -------------------------------------------------------------
slides.append(f"""
<section class="slide s1">
  <p class="kicker">NASA Space Apps Challenge 2026 \u00b7 Singapore</p>
  <h1>{long_date(closure)}</h1>
  <p class="body">I was in Primary 5. I woke up early for school and my parents told me I didn't have to go. It was the first time air pollution had ever closed Singapore's schools.</p>
  <p class="turn">What if something had seen it coming?</p>
  <p class="team">Team <b>\u201c{TEAM}\u201d</b> \u00b7 {MEMBER}<br>{CHALLENGE}</p>
</section>""")

# 2 — why nobody can answer it ------------------------------------------------
slides.append(f"""
<section class="slide s2">
  <div class="col">
    <h2>NASA already sees the fires. You still can't tell what they mean.</h2>
    <p class="stat">{total}</p>
    <p class="body">detections in one week, from two cameras that count differently. Add them up and you are counting cameras, not fires.</p>
  </div>
  <figure>{shot("desktop-map-raw.png", 985, 440, 180, 120, 540)}
    {key(SENSOR)}
    {cap("Raw dots, same fires. " + SRC)}</figure>
</section>""")

# 3 — the turn ----------------------------------------------------------------
slides.append(f"""
<section class="slide s3">
  <div class="top">
    <h2>One fire. One square. One day.</h2>
    <p class="stat">{active_cells}</p>
    <p class="body">squares on fire this week. A square counts once a day if either camera saw fire in it, so both cameras answer the same question &mdash; and the gap between them falls from {raw_ratio}&times; to {cell_ratio}&times;.</p>
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
  <p class="body">{top_cells} squares in South Sumatra. {riau_cells}, in Riau &mdash; the closest province.</p>
  <figure>{shot("desktop-calendar.png", *CAL, 800)}
    {key(list(zip(HEAT, BINS)) + [("#0f6b74", "wind pointing at us")])}
    {cap("Live app, burning calendar \u00b7 " + SRC)}</figure>
  <p class="small"><b>How to read it:</b> one row per province, with the week's total. Darker square, more fire that day. Teal bar, the wind pointing at Singapore.</p>
</section>""")

# 5 — the look back ----------------------------------------------------------
d0, d1 = dt.date.fromisoformat(A["dates"][0]), dt.date.fromisoformat(A["dates"][-1])
slides.append(f"""
<section class="slide s5">
  <h2>The fires peaked {WORD[lead_days]} days before the schools closed.</h2>
  {chart()}
  <p class="body">A build-up of fires, then smoke. But {int(second[-2:])} Sep burned almost as much and no school closed: fire counts alone don't explain smoke.</p>
  <p class="cap">Burning squares a day across the six provinces, {d0.day}\u2013{d1.day} {d1:%B %Y}. NASA FIRMS archive, MODIS + VIIRS. A look back at one event, not a prediction.</p>
</section>""")

# 6 — honesty as strength -----------------------------------------------------
slides.append(f"""
<section class="slide s6">
  <h2>What's real. What's missing. What's next.</h2>
  <div class="three">
    <div class="real"><h3>Real</h3><p class="body">One week of real NASA data, and one September from the archive. Every number is in a file you can check.</p></div>
    <div class="missing"><h3>Missing</h3>
      <ul class="body"><li>Years of history: one week live, one month of 2015</li><li>One of NASA's four files is empty because the satellite ended &mdash; Suomi NPP stopped on {long_date(npp.date())}</li><li>A rough guide, not a forecast</li></ul></div>
    <div class="next"><h3>Next</h3>
      <ol class="body"><li>Load the years of history</li><li>Compare camera by camera, province by province</li><li>Test it against Singapore's PSI record</li></ol></div>
  </div>
  <p class="small">NASA points users of Suomi NPP data to NOAA-20 and NOAA-21: a different satellite, a different record. Source: NASA Earthdata alert, {npp:%H:%M} UTC, {long_date(npp.date())}.</p>
</section>""")

# 7 — the ask -----------------------------------------------------------------
slides.append(f"""
<section class="slide s7">
  <h1>Can See Or Not?</h1>
  <p class="link">{APP}</p>
  <p class="body">Today is calm \u2014 PSI {psi_now["low"]}\u2013{psi_now["high"]}. The record has to exist for the mornings it isn't.</p>
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
.s1{flex-direction:column;align-items:flex-start;justify-content:center;gap:20px;padding-left:96px;padding-right:96px}
.s1 h1{font-size:112px;letter-spacing:-3px;white-space:nowrap}
.s1 .body{font-size:38px;line-height:1.25;max-width:1060px}
.turn{font-size:54px;font-weight:800;color:var(--fire);line-height:1.1;letter-spacing:-1px}
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
.s4 figure{align-self:center}
.s5{gap:12px}
.s5 h2{font-size:52px}
.s5 .body{font-size:30px}
.s5 .chart{display:block;align-self:center}
.s4 figure{position:relative}
.crop{position:relative}
.box{position:absolute;border:4px solid var(--fire);border-radius:6px}
/* 6 */
.s6 .three{display:grid;grid-template-columns:1fr 1.5fr 1.2fr;gap:20px}
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
.s6 li{margin-bottom:10px}
.s6 li:last-child{margin-bottom:0}
.s6 .body{font-size:30px}
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
