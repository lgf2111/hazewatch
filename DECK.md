# HazeWatch — the 7 slides

Award category: **Best Use of Data**. Seven slides including the title; do not add an eighth.

`docs/deck/deck.html` is built by `/opt/homebrew/bin/python3 tools/build_deck.py` from `data/facts.json`, `data/archive-2015.json` and the captures in `docs/screenshots/` (run `tools/screenshots.sh` against `python3 -m http.server 8765` first). Export: headless Chrome `--print-to-pdf --no-pdf-header-footer` → `docs/deck/HazeWatch-deck.pdf`, exactly 7 pages. This file records the copy as built; the build script reads every number from those two files and asserts the ones it quotes.

The build needs **Python 3.12 or newer** (the f-strings reuse double quotes inside expressions); macOS's `/usr/bin/python3` is 3.9 and fails on it. Homebrew's `python3` is fine.

Live app: https://hazewatch.leeguanfeng.com/ · Code and data: https://github.com/lgf2111/hazewatch

## Why it reads the way it does (report → pitch → backtest)

The first deck was a report: it opened on the data model and reached a person, a day and a decision only in the middle. The second ran as a story but still opened on a claim. This one opens on a day the presenter lived — 25 September 2015, the first time air pollution had closed Singapore's schools — and asks the question the project answers: what if something had seen it coming? The evidence then does the proving: the problem (2), the one move that fixes it (3), the product (4), and a **look back at that very September** (5) that reads the NASA archive the way the app reads this week. It is told straight: fires peaked three days before the closure and collapsed on the morning itself, which fits smoke arriving after fires; but 8 September burned almost as much and no school closed, so fire counts alone do not explain smoke. Slide 6 keeps the limits and adds why one of NASA's four files is empty (the satellite ended). Slide 7 ends on an ask.

Language rules: say **camera** for a satellite instrument, **square** for a grid cell, **day** for a cell-day, **rough guide** for the wind heuristic. Banned on slides (the build fails if one appears): schema, harmonise/harmonised/harmonisation, provenance, cell-day, FRP, nominal, confidence class, heuristic, index, normalise, alignment, thermal anomaly. Sensor names (MODIS, VIIRS) appear only in small captions and the challenge line.

---

## 1 — The morning

> NASA SPACE APPS CHALLENGE 2026 · SINGAPORE
> # 25 September 2015
> I was in Primary 5. I woke up early for school and my parents told me I didn't have to go. It was the first time air pollution had ever closed Singapore's schools.
> **What if something had seen it coming?** (in the fire colour)
>
> Team "Can See Or Not" · Lee Guan Feng · Harmonization of MODIS and VIIRS Hot Spots

Facts (all in `data/archive-2015.json`, `events.closure_2015`, supplied as verified): Friday 25 September 2015; all primary and secondary schools, MOE kindergartens and special education schools closed; JCs, polytechnics and universities stayed open; 24-hour PSI peaked at 322 at 08:00 (hazardous from 04:00); 3-hour PSI 341 at 05:00; about 3,300 pupils turned up anyway, under 1%. Never write "first time in history": the first school closure of any kind was SARS in 2003, so the slide says "the first time air pollution had ever closed Singapore's schools". Only the date is typeset from the data file; the first-person line is the presenter's.

## 2 — Why nobody can answer it

> ## NASA already sees the fires. You still can't tell what they mean.
> **28,523** detections in one week, from two cameras that count differently. Add them up and you are counting cameras, not fires.

Image: raw dots, tight crop, MODIS / VIIRS colour key (`desktop-map-raw`). [`total_rows`]

## 3 — The turn

> ## One fire. One square. One day.
> **9,647** squares on fire this week. A square counts once a day if either camera saw fire in it, so both cameras answer the same question — and the gap between them falls from 13.4× to 8.2×.

Image: raw dots and squares side by side, same area. [`active_cell_days`, `raw_ratio_viirs_to_modis_detections`, `cell_ratio_viirs_to_modis`]. The 55.5% MODIS/VIIRS overlap [`modis_cells_also_seen_by_viirs_pct`] stays in this file, not on the slide.

## 4 — What it shows

> ## One page. Six provinces. Eight days.
> **275** squares in South Sumatra. **8**, in Riau — the closest province.
> How to read it: one row per province, with the week's total. Darker square, more fire that day. Teal bar, the wind pointing at Singapore.

Image: the burning calendar (`desktop-calendar`) with the app's own colour key. [`top_province_cell_days`, `focus_provinces.riau.cell_days`]. The old "one real day: 11 Nov, 78 squares, wind from 116° — just inside the 60° window (116° is where wind comes *from*; it blows toward 296°, 59° off Singapore's 355°)" and "20 of 48 province-days" no longer have a slide; the 2015 look back replaced them.

## 5 — The look back

> ## The fires peaked three days before the schools closed.
> *Bar chart, one bar per day, 5–30 September 2015, burning squares across the six provinces.* Marked: **22 Sep · 1,590 · fires peak**; **8 Sep · 1,545 · no closure**; **25 Sep · 562 · schools closed · PSI 322**.
> A build-up of fires, then smoke. But 8 Sep burned almost as much and no school closed: fire counts alone don't explain smoke.
> Small: Burning squares a day across the six provinces, 5–30 September 2015. NASA FIRMS archive, MODIS + VIIRS. A look back at one event, not a prediction.

Numbers: `data/archive-2015.json` (`six_province_total`; 23 Sep 1,269, 24 Sep 1,017 are the days still high after the peak). The build asserts peak = 22 Sep (1,590), closure day = 562, second-highest = 8 Sep (1,545), peak to closure = 3 days. The chart is SVG drawn from the JSON, not a screenshot.

Honest reading, as the slide carries it: a build-up in the three days before the closure, consistent with smoke arriving after the fires and **not** with fires on the day; and 8 September shows fire alone does not explain PSI. Chart covers 5–30 September: the backtest supplied no figures for 1–4 September, so none are drawn.

Provenance of the file: `data/archive-2015.json` was seeded from the backtest supplied with the brief (FIRMS area API, `MODIS_SP` + `VIIRS_SNPP_SP`, box 95,-6,119,4, 5-day chunks, UTC+7 local days, low-grade detections dropped, 0.1° squares counted once a day, provinces from `tools/build_snapshot.py`). It was **not re-fetched here** (no `FIRMS_MAP_KEY`), so only the six-province total and South Sumatra are in it. `FIRMS_MAP_KEY=… /opt/homebrew/bin/python3 tools/fetch_archive.py` rebuilds the full per-province file from the API; `--offline` re-derives it from cached CSVs in `data/archive-raw/`. The key is read from the environment only.

## 6 — What's real. What's missing. What's next.

> **Real** One week of real NASA data, and one September from the archive. Every number is in a file you can check.
> **Missing** Years of history: one week live, one month of 2015 · One of NASA's four files is empty because the satellite ended — Suomi NPP stopped on 2 November 2026 · A rough guide, not a forecast
> **Next** 1. Load the years of history 2. Compare camera by camera, province by province 3. Test it against Singapore's PSI record
> Small: NASA points users of Suomi NPP data to NOAA-20 and NOAA-21: a different satellite, a different record. Source: NASA Earthdata alert, 13:00 UTC, 2 November 2026.

The brief's line ended "and nothing replaces it". NASA's own notices name NOAA-20 and NOAA-21 as the replacements (the app already uses both), so the slide says the record changes satellite instead. Alert: https://www.earthdata.nasa.gov/data/alerts-outages/suomi-npp-observations-cease-november-2-2026 · FIRMS note: https://www.earthdata.nasa.gov/news/blog/transitioning-from-suomi-npp-viirs-omps-what-firms-users-need-know

## 7 — The ask

> # Can See Or Not?
> **hazewatch.leeguanfeng.com**
> Today is calm — PSI 33–35. The record has to exist for the mornings it isn't.
> **Next: an agency pilot, or archive funding.**
>
> Small: PSI is Singapore's 24-hour reading at 16:00 on 15 Nov 2026 (data.gov.sg, keyless `/v1/environment/psi`; checked live: central 35, east 35, north 33, south 34, west 34). Used only as contrast. Numbers in `data/archive-2015.json`, `events.psi_today`.
> Team "Can See Or Not" · Lee Guan Feng · Singapore Local Event · Harmonization of MODIS and VIIRS Hot Spots · Best Use of Data

---

## Pre-export checklist

- [ ] `/opt/homebrew/bin/python3 tools/build_deck.py` prints 7 slides and no banned-word error.
- [ ] No placeholder text anywhere in the deck or the PDF.
- [ ] PDF is exactly 7 pages; look at every page for overflow (the build prints word counts, not heights).
- [ ] Every number on a slide still matches `data/facts.json` or `data/archive-2015.json`.
