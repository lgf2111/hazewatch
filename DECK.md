# HazeWatch — the 7 slides

Award category: **Best Use of Data**. Seven slides including the title; do not add an eighth.

Every number below is in `data/facts.json` (key given in brackets) from the snapshot fetched 2026-11-15 15:41 SGT. If the snapshot is refreshed, re-run `tools/screenshots.sh` and update the numbers from the file, never from memory.

Screenshots are real captures of the live app, in `docs/screenshots/`. Each shows the fetch time, the dataset name and the feed row counts in its header.

Live app: https://hazewatch.leeguanfeng.com/ · Code and data: https://github.com/lgf2111/hazewatch

---

## Slide 1 — Title

**Anchor number:** `28,523` — NASA fire detections in one week, from four files [`total_rows`].

**On the slide**

> # HazeWatch
> ### Whose fires become Singapore's smoke?
>
> **28,523** NASA fire detections over South-East Asia, 8–15 November 2026, turned into one calendar for the six provinces that matter to one city.
>
> hazewatch.leeguanfeng.com
>
> NASA Space Apps Challenge 2026 · Singapore · Harmonization of MODIS and VIIRS Hot Spots

**Screenshot:** `docs/screenshots/desktop-map-raw.png`

**Notes:** I live here. When the haze comes, everyone asks where it is coming from. NASA already publishes the answer as tens of thousands of dots a week; this makes it readable.

---

## Slide 2 — The problem

**Anchor number:** `0` — rows in the VIIRS S-NPP file when we fetched it [`viirs_snpp_rows`].

**On the slide**

> ## Two sensors, two rulers — and one feed was silent
>
> | | MODIS (Terra, Aqua) | VIIRS (S-NPP, NOAA-20, NOAA-21) |
> |---|---|---|
> | Pixel | 1 km | 375 m |
> | Confidence | 0–100 % | low / nominal / high |
> | Rows, same region, same week | **1,961** | S-NPP **0** · NOAA-20 **12,961** · NOAA-21 **13,601** |
>
> Same fires, same week: one sensor family reports 13 times as many detections as the other, and one of the four public files came back empty.
>
> Add the dots up and you are measuring the satellites, not the fires.

**Screenshot:** `docs/screenshots/desktop-data-limits.png` (feed table with the highlighted empty row).

**Notes:** The zero is what the public file returned (HTTP 200, 112 bytes, header only). We do not know why and draw no conclusion about the sensor. Numbers: [`modis_rows`, `noaa20_rows`, `noaa21_rows`, `raw_ratio_viirs_to_modis_detections` = 13.4].

---

## Slide 3 — What we built

**Anchor number:** `13.4× → 8.2×` — the VIIRS-to-MODIS gap, raw versus harmonised [`raw_ratio_viirs_to_modis_detections`, `cell_ratio_viirs_to_modis`].

**On the slide**

> ## One schema, one confidence scale, one grid
>
> 1. **Normalise** both sensors' records into one schema.
> 2. **Align confidence**: MODIS 0–100 % becomes low / nominal / high, like VIIRS. Low is dropped (2,194 of 28,523 rows).
> 3. **Count cells, not dots**: a 0.1° cell (about 11 km) is burning on a day if either sensor sees a fire in it.
> 4. **Keep the provenance**: every cell-day is tagged MODIS-only, VIIRS-only, or both.
>
> Result: **9,647** burning cell-days. The sensor gap narrows from **13.4×** to **8.2×**. It does not close, so the app never hides which sensor saw what.

**Screenshot:** `docs/screenshots/desktop-map-cells.png` beside a crop of `desktop-map-raw.png` (same area, dots versus cells).

**Notes:** 55.5 % of MODIS burning cell-days were also seen by VIIRS the same day [`modis_cells_also_seen_by_viirs_pct`]; provenance split is 499 MODIS-only, 8,526 VIIRS-only, 622 both [`cell_days_provenance_all`]. The cell size is a design choice. Equal confidence labels are a working alignment between two algorithms.

---

## Slide 4 — The burning calendar

**Anchor number:** `275` — burning cell-days in South Sumatra, the most active of the six [`top_province_cell_days`].

**On the slide**

> ## Six provinces, one week
>
> **South Sumatra: 275 burning cell-days**, peaking at 78 on Wednesday 11 November.
>
> Rows are the Sumatra and Kalimantan provinces most often named in Singapore's haze. Each square is one day; the number is how many grid cells were burning.
>
> The six together: **724** of the **9,647** cell-days across South-East Asia. Riau, the closest to Singapore, had 8.

**Screenshot:** `docs/screenshots/desktop-calendar.png` (phone version: `phone-calendar.png`).

**Notes:** Eight date columns because a 7 × 24 h UTC window touches eight local dates; the first and last are partial. Hot spots are thermal anomalies, and some are not vegetation fires. One week is a strip, not a season. [`focus_cell_days`, `active_cell_days`, `focus_provinces.*.cell_days`]

---

## Slide 5 — Wind windows

**Anchor number:** `20 of 48` — province-days when fire and wind lined up towards Singapore [`aligned_days_total`, `province_days_total`].

**On the slide**

> ## When do the ingredients line up?
>
> On **20 of 48** province-days, fire was burning *and* the surface wind blew within 60° of the line to Singapore.
>
> For each province and day the app shows three ingredients, not a verdict:
> - **Fire**: burning cells
> - **Wind**: how directly it points at Singapore (0 to 1)
> - **Dry spell**: consecutive days under 1 mm of rain
>
> This is a heuristic. It is not a haze forecast, it ignores distance (South Sumatra is 511 km away, South Kalimantan 1,371 km), and it has not been checked against air-quality readings.

**Screenshot:** `docs/screenshots/desktop-wind.png` (South Sumatra, 4 aligned days of 8; phone version: `phone-wind.png`).

**Notes:** Wind and rain are NASA POWER for 8–12 November; POWER had no values yet for 13–15 November, so those three days use Open-Meteo and are marked † in the app. It rained on most days, which is why the dry-spell row is mostly zero.

---

## Slide 6 — What is real, what is not

**Anchor number:** `1` — weeks of data behind every number in this deck.

**On the slide**

> ## Honest boundaries
>
> **Working and public: one week of real NASA data**
> - 4 FIRMS files, fetched 15 Nov 2026 15:41 SGT, kept unmodified in the repo
> - Schema, confidence and grid harmonisation for MODIS and VIIRS
> - Province-by-day calendar, map, wind and dry-day ingredients
> - Every number traceable in `data/facts.json`; one command rebuilds it
>
> **Concept: designed, not built**
> - Multi-year archive and the 12-month calendar
> - Checking the wind index against Singapore's PSI record
>
> **Limits:** one feed empty · cloud hides fires · surface wind is not transport wind · thresholds chosen, not fitted · nothing here is a prediction.

**Screenshot:** `docs/screenshots/phone-data-limits.png` (the three "what is missing" cards).

**Notes:** This slide is the validity score. Do not soften it.

---

## Slide 7 — Why it matters, what comes next

**Anchor number:** `4 files → 1 calendar`.

**On the slide**

> ## 4 files → 1 calendar
>
> **Who it is for:** people in Singapore who want to know where smoke may come from, and the journalists, agencies and researchers who explain it.
>
> **Why harmonise:** MODIS has the long record, VIIRS the sharp one. Comparing this season with past ones means joining them without the sharper sensor looking like more fire.
>
> **Next:**
> 1. Load the FIRMS archive for a true month-by-month, year-by-year calendar
> 2. Track MODIS–VIIRS agreement province by province over a full season
> 3. Test the alignment index against recorded haze days
>
> Open it now: **hazewatch.leeguanfeng.com** · Data: NASA FIRMS, GIBS, POWER.

**Screenshot:** `docs/screenshots/phone-calendar.png`, small, as "it works on your phone".

**Notes:** Close on the personal angle: next time the sky goes grey here, the answer to "where is it coming from" is one page away.

---

## Pre-export checklist

- [ ] Numbers still match `data/facts.json` (re-check if the snapshot was refreshed).
- [ ] Seven slides, no more.
- [ ] The word "forecast" appears only in sentences that say the tool is not one.
- [ ] Slide 7's "long record / sharp record" wording stays qualitative unless start years are checked against FIRMS documentation.
