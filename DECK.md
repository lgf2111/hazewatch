# HazeWatch — the 7 slides

Award category: **Best Use of Data**. Seven slides including the title; do not add an eighth.

`docs/deck/deck.html` is built by `python3 tools/build_deck.py` from `data/facts.json` and the captures in `docs/screenshots/` (run `tools/screenshots.sh` against `python3 -m http.server 8765` first). Export: headless Chrome `--print-to-pdf` → `docs/deck/HazeWatch-deck.pdf`, exactly 7 pages. This file records the slide copy as built; the build script is the source of truth for every number.

Plain-English rules: say "camera" for sensor, "square" for grid cell, "day" for cell-day, "pointing at us" for wind alignment. Banned on slides (the build fails if one appears): schema, harmonise/harmonised/harmonisation, provenance, cell-day, FRP, nominal, confidence class, heuristic, index, normalise, alignment, thermal anomaly. Source names (MODIS, VIIRS, NASA FIRMS) appear in small captions and in the challenge name only.

Live app: https://hazewatch.leeguanfeng.com/ · Code and data: https://github.com/lgf2111/hazewatch

---

## 1 — Title

> NASA SPACE APPS CHALLENGE 2026 · SINGAPORE
> # HazeWatch
> ## Where does the smoke come from?
> **28,523** fires NASA's satellites saw around us in one week. We turned them into one page.
>
> Team "Can See Or Not" · Lee Guan Feng · Harmonization of MODIS and VIIRS Hot Spots

Image: map, squares mode, all days (`desktop-map-cells`). Caption: NASA FIRMS MODIS + VIIRS, 8–15 November 2026. [`total_rows`]

## 2 — The problem

> ## Two cameras. One fire. Two answers.
> **13.4×** more dots from the sharper camera — for the same fires. Count the dots and you are measuring cameras, not fires.

Image: raw dots, cropped tight on the East Kalimantan cluster (`desktop-map-raw`), with a camera colour key. [`raw_ratio_viirs_to_modis_detections`]

## 3 — What we built

> ## One fire. One square. One day.
> **9,647** squares on fire this week. A square counts once a day if either camera saw fire in it — so both cameras now answer in the same units.

Image: raw dots and squares side by side, same area. [`active_cell_days`]

## 4 — The answer

> ## This week, South Sumatra burned.
> **78** squares on fire there on Wednesday alone. Six provinces, eight days: South Sumatra first, then South Kalimantan, further east.

Image: the burning calendar (`desktop-calendar`) with the colour key (0, 1–4, 5–14, 15–29, 30–59, 60+; the app's own hex values) and the teal "wind pointing at us" bar. [`focus_provinces.south-sumatra.by_date`, `focus_provinces.*.cell_days`]

## 5 — The twist

> ## The nearest fires were not aimed at us.
> **0 of 8** days Riau pointed fire at Singapore — 8 burning squares, 251 km away. South Sumatra is 511 km away, had 275 squares, and pointed at us on 4 days.

Image: wind view for Riau, all eight days (`desktop-wind-riau`). [`focus_provinces.riau`, `focus_provinces.south-sumatra`]

## 6 — Honest

> ## One week. Not a forecast.
> **Real:** 28,523 NASA detections, 8–15 November, every number in one file you can check.
> **Missing:** The years of history behind it. And one of NASA's four files came back empty.
>
> Surface wind at one point per province is not the wind that carries smoke. Nothing here predicts tomorrow.

Image: the live page on a phone (`phone-wind`), small.

## 7 — Close

> 4 FILES IN · 1 CALENDAR OUT
> # So. Whose fire is it?
> Next time the sky goes grey, the answer is one page away.
>
> **hazewatch.leeguanfeng.com**
>
> Team "Can See Or Not" · Lee Guan Feng · Singapore Local Event · Harmonization of MODIS and VIIRS Hot Spots · Best Use of Data

---

## Pre-export checklist

- [ ] `python3 tools/build_deck.py` prints 7 slides and no banned-word error.
- [ ] Numbers match `data/facts.json` (the script reads them from it).
- [ ] PDF is exactly 7 pages; look at every page for overflow, clipped captions, orphan lines.
