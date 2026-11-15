#!/usr/bin/env python3
"""Write SUBMISSION.md: copy-paste-ready project-page fields with exact character counts.

Numbers are formatted from data/facts.json. Field text is plain ASCII so the
count is the same in any form. A count is len() of the text exactly as it
sits between the fences (no trailing newline).

    python3 tools/build_submission.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
F = json.loads((ROOT / "data" / "facts.json").read_text())


def n(x):
    return f"{x:,}"


total, modis = n(F["total_rows"]), n(F["modis_rows"])
n20, n21 = n(F["noaa20_rows"]), n(F["noaa21_rows"])
raw, cell = F["raw_ratio_viirs_to_modis_detections"], F["cell_ratio_viirs_to_modis"]
overlap = F["modis_cells_also_seen_by_viirs_pct"]
focus, active = n(F["focus_cell_days"]), n(F["active_cell_days"])
top, top_n = F["top_province"], n(F["top_province_cell_days"])
al, pd = F["aligned_days_total"], F["province_days_total"]
assert F["viirs_snpp_rows"] == 0

APP = "https://lgf2111.github.io/hazewatch/"
REPO = "https://github.com/lgf2111/hazewatch"
FIRMS = "https://firms.modaps.eosdis.nasa.gov/data/active_fire"

fields = []  # (title, limit, kind, text)


def field(title, limit, text, words=None):
    fields.append((title, limit, text, words))


field("Project name", 60, "HazeWatch")

field(
    "High-level summary (~120 words)",
    1000,
    f"HazeWatch is a burning calendar for the provinces whose fires can become Singapore's smoke. "
    f"It puts NASA FIRMS MODIS and VIIRS hot spots on one schema, one confidence scale and one 0.1 degree grid, "
    f"counts burning cells per province per day, and marks the days when fire and wind direction line up towards Singapore. "
    f"On a real 7-day snapshot ({total} detections in four files) it narrows the VIIRS-to-MODIS gap from {raw}x to {cell}x "
    f"and finds {focus} burning cell-days in six Sumatra and Kalimantan provinces, {top} the most active with {top_n}. "
    f"It also reports that the VIIRS S-NPP file came back empty. It is a heuristic, not a forecast, and has no archive yet.",
    words=(105, 125),
)

field("Demo link", 200, APP)
field("Final project link", 200, REPO)

field(
    "Detailed description",
    4000,
    f"""THE QUESTION
When the haze comes, Singapore asks one thing: where is it coming from? NASA already publishes the answer as tens of thousands of fire dots a week. HazeWatch makes it readable for one city: which provinces, on which days, in which wind windows.

THE PROBLEM
MODIS (Terra, Aqua) detects fires at 1 km with a 0-100 percent confidence. VIIRS (S-NPP, NOAA-20, NOAA-21) detects at 375 m with low / nominal / high confidence. The same fire gives different counts and different kinds of confidence, so raw numbers cannot be added or compared. On our snapshot VIIRS reports {raw} detections for every MODIS detection, and one of the four public files, VIIRS S-NPP, returned zero rows.

WHAT IT DOES
1. Fetches the four FIRMS 7-day regional files for South-East Asia and keeps them unmodified.
2. Maps both sensors to one schema.
3. Converts MODIS confidence to low / nominal / high (low is excluded by default).
4. Counts burning 0.1 degree cells (about 11 km) per day, whichever sensor sees them, and tags each cell-day MODIS-only, VIIRS-only or both.
5. Aggregates per day for Riau, Jambi, South Sumatra, West, Central and South Kalimantan.
6. Adds wind direction and dry days, and marks a province-day "aligned" when fire is burning and the wind is within 60 degrees of the line to Singapore.

WHAT THE DATA SHOWS (fetched 15 Nov 2026, 15:41 SGT)
- {total} detections in four files: MODIS {modis}, VIIRS S-NPP 0 (empty), NOAA-20 {n20}, NOAA-21 {n21}.
- Counting cells instead of dots narrows the VIIRS-to-MODIS ratio from {raw}x to {cell}x. It does not close it: only {overlap} percent of MODIS-seen cells were also seen by VIIRS.
- {focus} of the {active} burning cell-days in South-East Asia fall in the six provinces; {top} is the most active with {top_n}.
- On {al} of {pd} province-days, fire and wind lined up towards Singapore.

WHAT IS REAL AND WHAT IS NOT
Real: one week of NASA data, the harmonisation, the province-by-day calendar, the map, and the wind and dry-day ingredients. Every number is in data/facts.json and one command rebuilds it.
Not built: a multi-year archive and 12-month calendar, and a check of the wind index against Singapore's PSI record.
Limits: 7-day window only, no archive, the S-NPP feed was empty (we draw no conclusion about the sensor), and the wind index is a heuristic, not a forecast. Thresholds are chosen, not fitted. Surface wind is not transport wind, cloud hides fires, and some hot spots are not vegetation fires.

WHY IT MATTERS
MODIS has the long record and VIIRS the sharp one. Comparing this season with past ones means joining them without the sharper sensor looking like more fire. Next: load the FIRMS archive, track MODIS-VIIRS agreement by province over a season, and test the index against recorded haze days.

TEAM AND TOOLS
Team "Can See Or Not", solo: Lee Guan Feng. Singapore Local Event, challenge "Harmonization of MODIS and VIIRS Hot Spots", award target Best Use of Data. HTML, CSS and vanilla JavaScript with Leaflet, plus one standard-library Python script. Claude (Anthropic, via Claude Code) helped write the code and text; all data shown comes from the sources listed, none is AI-generated.""",
)

field(
    "NASA data used",
    1500,
    f"""1. MODIS Collection 6.1 NRT active fire (MCD14DL), Terra and Aqua, 1 km: {FIRMS}/modis-c6.1/csv/MODIS_C6_1_SouthEast_Asia_7d.csv ({modis} rows)
2. VIIRS S-NPP Collection 2 NRT active fire (VNP14IMGTDL), 375 m: {FIRMS}/suomi-npp-viirs-c2/csv/SUOMI_VIIRS_C2_SouthEast_Asia_7d.csv (0 rows, header only)
3. VIIRS NOAA-20 Collection 2 NRT active fire (VJ114IMGTDL), 375 m: {FIRMS}/noaa-20-viirs-c2/csv/J1_VIIRS_C2_SouthEast_Asia_7d.csv ({n20} rows)
4. VIIRS NOAA-21 Collection 2 NRT active fire (VJ214IMGTDL), 375 m: {FIRMS}/noaa-21-viirs-c2/csv/J2_VIIRS_C2_SouthEast_Asia_7d.csv ({n21} rows)
5. NASA GIBS imagery (WMTS), layer BlueMarble_ShadedRelief_Bathymetry: https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/
6. NASA POWER daily meteorology (WD10M, WS10M, PRECTOTCORR): https://power.larc.nasa.gov/api/temporal/daily/point
Fetched 15 Nov 2026 without an API key. FIRMS archive downloads (https://firms.modaps.eosdis.nasa.gov/download/) are planned, not used.""",
)

field(
    "Partner data and references",
    2000,
    """Other data
- Natural Earth admin-1 boundaries (public domain): https://www.naturalearthdata.com/
- Open-Meteo, wind and rain for 13-15 Nov 2026 only, where NASA POWER had no values yet: https://open-meteo.com/
- Leaflet 1.9.4 (map library): https://leafletjs.com/

References
1. NASA FIRMS, Fire Information for Resource Management System: https://firms.modaps.eosdis.nasa.gov/
2. NASA FIRMS FAQ (attributes, confidence, sensor differences): https://www.earthdata.nasa.gov/data/tools/firms/faq
3. Giglio, L., Schroeder, W., Justice, C. O. (2016). The collection 6 MODIS active fire detection algorithm and fire products. Remote Sensing of Environment, 178, 31-41. https://doi.org/10.1016/j.rse.2016.02.054
4. Schroeder, W., Oliva, P., Giglio, L., Csiszar, I. A. (2014). The new VIIRS 375 m active fire detection data product: algorithm description and initial assessment. Remote Sensing of Environment, 143, 85-96. https://doi.org/10.1016/j.rse.2013.12.008
5. NASA GIBS: https://www.earthdata.nasa.gov/engage/open-data-services-software/earthdata-developer-portal/gibs-api
6. NASA POWER: https://power.larc.nasa.gov/""",
)

blurb = (
    "HazeWatch turns NASA FIRMS MODIS and VIIRS hot spots into one burning calendar for the six Sumatra and "
    "Kalimantan provinces that matter to Singapore. Both sensors share one grid and confidence scale, and days "
    "when fire and wind line up are flagged. Built on a real 7-day NASA snapshot; the multi-year archive is concept only. Team Can See Or Not, Singapore."
)
field("Gallery blurb (60 words)", 450, blurb, words=(58, 62))

# ---- checks -----------------------------------------------------------------
rows = []
for title, limit, text, words in fields:
    assert text.isascii(), title
    assert len(text) <= limit, (title, len(text), limit)
    wc = len(text.split())
    if words:
        assert words[0] <= wc <= words[1], (title, wc, words)
    rows.append((title, len(text), limit, wc))

out = [
    "# HazeWatch: Space Apps project page, copy-paste ready",
    "",
    "Team **Can See Or Not** · Lee Guan Feng · Singapore Local Event · *Harmonization of MODIS and VIIRS Hot Spots* · award target **Best Use of Data**.",
    "",
    "Generated by `python3 tools/build_submission.py` from `data/facts.json` (snapshot fetched 2026-11-15 15:41 SGT); regenerate rather than editing numbers by hand.",
    "Each field below is plain ASCII text between the fences. The count is the exact number of characters between the fences.",
    "**The project form's own limits are not in this repo.** The limits shown are working caps I set; if the real form is stricter, trim before pasting.",
    "",
    "| Field | Characters | Limit | Words |",
    "|---|---:|---:|---:|",
]
for title, c, limit, wc in rows:
    out.append(f"| {title} | {c:,} | {limit:,} | {wc} |")
out.append("")
for (title, limit, text, _), (_, c, _, wc) in zip(fields, rows):
    out += [f"## {title}", f"*{c:,} characters · limit {limit:,} · {wc} words*", "", "```text", text, "```", ""]
out += [
    "## Deck",
    "",
    f"`docs/deck/HazeWatch-deck.pdf` (7 slides), source `docs/deck/deck.html`, built by `python3 tools/build_deck.py`. After the push it is at {REPO}/blob/main/docs/deck/HazeWatch-deck.pdf.",
    "",
]
(ROOT / "SUBMISSION.md").write_text("\n".join(out))
for title, c, limit, wc in rows:
    print(f"{title}: {c} chars / {limit} · {wc} words")
