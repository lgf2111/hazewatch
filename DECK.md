# HazeWatch — the 7 slides

Award category: **Best Use of Data**. Seven slides including the title; do not add an eighth.

`docs/deck/deck.html` is built by `python3 tools/build_deck.py` from `data/facts.json` and the captures in `docs/screenshots/` (run `tools/screenshots.sh` against `python3 -m http.server 8765` first). Export: headless Chrome `--print-to-pdf --no-pdf-header-footer` → `docs/deck/HazeWatch-deck.pdf`, exactly 7 pages. This file records the copy as built; the build script is the source of truth for every number.

Live app: https://hazewatch.leeguanfeng.com/ · Code and data: https://github.com/lgf2111/hazewatch

## Why the order changed (report → pitch)

The first deck was a report: it opened on the data model (two sensors, two rulers, one schema) and only reached a person, a day and a decision in the middle. A judge had no reason to care about harmonisation before knowing what it is for, and a report can only earn Validity and Relevance. The deck now runs as a story with evidence as proof: the question (slide 1), why nobody can answer it (2), the one move that fixes it (3), what the product does (4), one real day it matters (5), what is real, missing and next (6), and an ask (7). Every number and every screenshot is the same as before; only the order, the framing and the ending changed.

Plain-English rules: "instrument" (or just MODIS / VIIRS) for sensor, never "camera" (MODIS flies on Terra and Aqua; VIIRS on S-NPP, NOAA-20, NOAA-21); "square" for grid cell, "day" for cell-day. Banned on slides (the build fails if one appears): schema, harmonise/harmonised/harmonisation, provenance, cell-day, FRP, nominal, confidence class, index, normalise, alignment, thermal anomaly. "Heuristic" is allowed, on purpose, on slides 5 and 6. Source names appear in small captions and the challenge name.

---

## 1 — The morning

> NASA SPACE APPS CHALLENGE 2026 · SINGAPORE
> **HazeWatch**
> # Can See Or Not?
> Singapore's haze is imported. The six provinces we watch sit 251 to 1,371 km away.
> **[PERSONAL LINE]**  ← placeholder for the entrant's own words; replace before submitting
>
> Team "Can See Or Not" · Lee Guan Feng · Harmonization of MODIS and VIIRS Hot Spots

Image: squares map with Singapore marked (`desktop-map-cells`). Numbers: nearest and farthest `focus_provinces.*.distance_to_singapore_km`. No haze memory, date or PSI record is invented.

## 2 — Why nobody can answer it

> ## The answer is on file. The record forgets.
> **28,523** dots in four NASA files, from two instruments with two different rulers. This season can't be compared with last.

Image: raw dots, tight crop, MODIS / VIIRS colour key (`desktop-map-raw`). [`total_rows`]

## 3 — The turn

> ## Count burning squares, not dots.
> **13.4× → 8.2×** Count each square once a day and the gap between the instruments shrinks. Only 55.5% of MODIS squares are seen by VIIRS at all.

Image: raw dots and squares side by side, same area. [`raw_ratio_viirs_to_modis_detections`, `cell_ratio_viirs_to_modis`, `modis_cells_also_seen_by_viirs_pct`]

## 4 — What it does

> ## One page. Six provinces. Eight days.
> ① One row per province ② Darker square, more fire that day ③ Teal bar: wind pointing at Singapore

Image: the burning calendar (`desktop-calendar`) with three numbered markers drawn over the real capture and the app's own colour key.

## 5 — The moment of use

> ## One real day: Wednesday 11 November
> **78** squares burning in South Sumatra. Wind from 116°: just inside the 60° window toward Singapore.
> **20 of 48** province-days lined up like this. A heuristic, not a forecast.

Image: wind view for South Sumatra with 11 Nov outlined (`desktop-wind`). [`focus_provinces.south-sumatra.by_date.2026-11-11`, `aligned_days_total`, `province_days_total`]. Wind direction is where it blows *from*; 116° blows toward 296°, 59° away from Singapore's bearing of 355°, so the day only just counts. The slide says "just inside" for that reason.

## 6 — What's real. What's missing. What's next.

> **Real** One real week of NASA data.
> **Missing** 7-day window · No archive · S-NPP file empty · Heuristic, not a forecast
> **Next** 1. 12-month archive 2. Agreement by province 3. Test against Singapore's PSI record

## 7 — The ask

> # Can See Or Not?
> **hazewatch.leeguanfeng.com**
> Today is calm — PSI 33–35. The record has to exist for the mornings it isn't.
> **Next: an agency pilot, or archive funding.**
>
> Small: PSI is Singapore's 24-hour reading at 16:00 on 15 Nov 2026 (data.gov.sg, keyless `/v1/environment/psi`; checked live when the deck was built). Used only as contrast.
> Team "Can See Or Not" · Lee Guan Feng · Singapore Local Event · Harmonization of MODIS and VIIRS Hot Spots · Best Use of Data

---

## Pre-export checklist

- [ ] `python3 tools/build_deck.py` prints 7 slides and no banned-word error.
- [ ] `[PERSONAL LINE]` appears once in the deck (slide 1) until the entrant replaces it.
- [ ] PDF is exactly 7 pages; look at every page for overflow, clipped captions, orphan lines.
