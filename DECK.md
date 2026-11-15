# HazeWatch — the 7 slides

Award category: **Best Use of Data**. Seven slides including the title; do not add an eighth.

`docs/deck/deck.html` is built by `/opt/homebrew/bin/python3 tools/build_deck.py` from `data/facts.json` and the captures in `docs/screenshots/` (run `tools/screenshots.sh` against `python3 -m http.server 8765` first). Export: headless Chrome `--print-to-pdf --no-pdf-header-footer` → `docs/deck/HazeWatch-deck.pdf`, exactly 7 pages. This file records the copy as built; the build script is the source of truth for every number.

The build needs **Python 3.12 or newer** (the f-strings reuse double quotes inside expressions); macOS's `/usr/bin/python3` is 3.9 and fails on it. Homebrew's `python3` is fine.

Live app: https://hazewatch.leeguanfeng.com/ · Code and data: https://github.com/lgf2111/hazewatch

## Why it reads the way it does (report → pitch)

The first deck was a report: it opened on the data model and reached a person, a day and a decision only in the middle. The deck now runs as a story, with the evidence kept as proof: the question (1), why the obvious answer doesn't exist (2), the one move that fixes it (3), what the product shows (4), one real day it matters (5), what's real, missing and next (6), and an ask (7). Same numbers, same screenshots, different order and language.

Language rules: say **camera** for a satellite instrument, **square** for a grid cell, **day** for a cell-day, **rough guide** for the wind heuristic. Banned on slides (the build fails if one appears): schema, harmonise/harmonised/harmonisation, provenance, cell-day, FRP, nominal, confidence class, heuristic, index, normalise, alignment, thermal anomaly. Sensor names (MODIS, VIIRS) appear only in small captions and the challenge line.

---

## 1 — The question

> NASA SPACE APPS CHALLENGE 2026 · SINGAPORE
> **HazeWatch**
> # Where does the smoke come from?
> I live here. When the sky goes grey, nobody can tell you where it came from — though the six provinces that matter sit 251 to 1,371 km away.
>
> Team "Can See Or Not" · Lee Guan Feng · Harmonization of MODIS and VIIRS Hot Spots

Image: squares map with Singapore marked (`desktop-map-cells`). Numbers: nearest and farthest `focus_provinces.*.distance_to_singapore_km`. The first-person line is the entrant's own and is true of the presenter; no haze memory, date or PSI record is invented.

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

Image: the burning calendar (`desktop-calendar`) with the app's own colour key. [`top_province_cell_days`, `focus_provinces.riau.cell_days`]

## 5 — The moment of use

> ## One real day: Wednesday 11 November
> **78** squares burning in South Sumatra. That day the wind was blowing our way — within 60° of the line to us.
> **20 of 48** province-days lined up like this. A rough guide, not a forecast.

Image: wind view for South Sumatra with 11 Nov outlined (`desktop-wind`). [`focus_provinces.south-sumatra.by_date.2026-11-11`, `aligned_days_total`, `province_days_total`]. Wind direction is where it blows *from*: 116° blows toward 296°, 59° off Singapore's bearing of 355°, so the day only just counts — hence "within 60° of the line", not "at Singapore".

## 6 — What's real. What's missing. What's next.

> **Real** One week of real NASA data. Every number here is in one file you can check.
> **Missing** One week only, no years behind it · One of NASA's four files came back empty · A rough guide, not a forecast
> **Next** 1. Load the years of history 2. Compare camera by camera, province by province 3. Test it against Singapore's PSI record

## 7 — The ask

> # Can See Or Not?
> **hazewatch.leeguanfeng.com**
> Today is calm — PSI 33–35. The record has to exist for the mornings it isn't.
> **Next: an agency pilot, or archive funding.**
>
> Small: PSI is Singapore's 24-hour reading at 16:00 on 15 Nov 2026 (data.gov.sg, keyless `/v1/environment/psi`; checked live when the deck was built: central 35, east 35, north 33, south 34, west 34). Used only as contrast.
> Team "Can See Or Not" · Lee Guan Feng · Singapore Local Event · Harmonization of MODIS and VIIRS Hot Spots · Best Use of Data

---

## Pre-export checklist

- [ ] `/opt/homebrew/bin/python3 tools/build_deck.py` prints 7 slides and no banned-word error.
- [ ] No placeholder text anywhere in the deck or the PDF (the build has one personal line, written out, not a token).
- [ ] PDF is exactly 7 pages; look at every page for overflow (the build prints word counts, not heights).
- [ ] Every number on a slide still matches `data/facts.json`.
