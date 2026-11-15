# HazeWatch — build plan

NASA Space Apps Challenge 2026 · Singapore · solo · challenge: *Harmonization of MODIS and VIIRS Hot Spots*
Written 2026-11-15. Submission closes 23:59 SGT tonight. Deliverable is a 7-slide deck; the app exists to produce honest screenshots.

## 1. Product one-liner

**HazeWatch is a burning calendar for the provinces whose fires can become Singapore's smoke: it puts MODIS and VIIRS hot spots on one grid and one confidence scale, counts burning per province per day, and marks the days when fire, wind direction and dry weather line up towards the city.**

The question it answers is not "where are fires?" but "which provinces, on which days, in which wind windows, matter for Singapore?"

## 2. Rules that override everything else

1. Nothing on screen is invented. Every number comes from a file we fetched, with its fetch time shown.
2. A missing dataset is shown as missing. The empty VIIRS feed gets its own visible state; it is never filled, interpolated or mocked.
3. The haze-risk output is called a heuristic everywhere it appears, and is never expressed as PSI, AQI or a forecast.
4. Every number on a slide must be readable off a screenshot or `data/facts.json` (section 5.7).

## 3. Verified vs. unverified inputs

| Input | Status | Used for |
|---|---|---|
| FIRMS `MODIS_C6_1_SouthEast_Asia_7d.csv` (keyless) | **Verified today**: ~150 KB of real rows | All fire data in the prototype |
| FIRMS `SUOMI_VIIRS_C2_SouthEast_Asia_7d.csv` (keyless) | **Verified today**: header only, zero rows | The "feed empty" state; evidence for the problem |
| NASA GIBS WMTS (keyless) | **Verified reachable** | Basemap / imagery |
| FIRMS NOAA-20 / NOAA-21 VIIRS 7d CSVs (`J1_VIIRS_C2_…`, `J2_VIIRS_C2_…`) | Not checked | If populated, they are the VIIRS side of the harmonisation. Check in step 0 |
| Where the MODIS rows are (how many fall in our provinces) | Not checked | Decides the story on slides 4–5. Check in step 0 |
| NASA POWER daily API (`WD10M`, `WS10M`, `PRECTOTCORR`, keyless) | Not checked; data normally lags a few days | Wind and dry days. Check in step 0 |
| Open-Meteo (keyless, non-NASA) | Not checked | Wind/rain fallback if POWER is missing recent days |
| Natural Earth admin-1 polygons (public domain) | Not checked | Province boundaries |
| FIRMS yearly per-country archive CSVs | Not checked | Stretch only: the monthly calendar |

Exact URLs are in SUBMISSION.md. Any "not checked" item that fails takes its fallback from section 9; none of them blocks the core.

## 4. Screens and states

One static page, four views, plus a persistent header. No login, no routing, no backend.

**Header (always visible)**
- Snapshot stamp: "Data fetched 2026-11-15 HH:MM SGT · window: [first date] – [last date]".
- Feed status chips, one per sensor file: `MODIS C6.1 — N rows` / `VIIRS S-NPP C2 — 0 rows (feed empty)` / NOAA-20, NOAA-21 likewise.
- Persistent label: "Prototype · 7-day snapshot · haze index is an unvalidated heuristic".

**View A — Map**
- GIBS basemap, the focus-province outlines, Singapore marker, hot spots as points coloured by harmonised confidence class and shaped by sensor.
- Toggle: raw detections ↔ 0.1° harmonised cells. Day scrubber over the 7 days.
- States: loading · loaded · day with no detections ("No detections on this day") · imagery tile missing (falls back to static Blue Marble layer).

**View B — Burning calendar** (the centrepiece; slide 4)
- Grid: rows = focus provinces, columns = the 7 days, cell colour = active fire cells that day, number printed in the cell. Row totals at right.
- A thin strip under each row shows the wind-alignment flag per day (the "wind window").
- Month tab: 12-month × province grid fed by the archive. Without the stretch goal it renders the empty frame with the text "Archive not loaded in this prototype — see Methods". No placeholder colours.
- States: populated · province with zero fires all week (row shown, cells read 0, not hidden) · wind unavailable for a day (strip cell hatched, labelled "no wind data").

**View C — Province detail** (slide 5)
- Opened by clicking a calendar row. Shows distance and bearing to Singapore (computed from centroid), then four aligned daily rows: fire cells, wind direction arrow with alignment value, consecutive dry days, heuristic product.
- "Aligned day" badge where the rule in section 7 is met.
- States: populated · no fires (ingredients still shown, product 0) · weather missing.

**View D — Sensors & Methods** (slides 2, 3, 6)
- Side-by-side schema table (MODIS vs VIIRS fields → harmonised field).
- Confidence mapping table and how many rows fell in each class.
- Sensor-agreement breakdown of cell-days: MODIS-only / VIIRS-only / both. When no VIIRS file has rows, this reads "VIIRS feeds empty in this snapshot — agreement cannot be computed", not 100 % MODIS.
- Plain-language limits list (section 8) and data credits.

## 5. Data pipeline

A fetch script run once at build time writes a frozen snapshot into `data/`; the page reads only local files. This avoids browser CORS uncertainty, makes screenshots reproducible, and lets the header state exactly when the data was taken.

### 5.1 Fetch
- Download the four FIRMS 7-day CSVs (MODIS, VIIRS S-NPP, NOAA-20, NOAA-21) unmodified into `data/raw/`, recording URL, HTTP status, byte size, row count and fetch time in `data/manifest.json`.
- A header-only file is recorded as `rows: 0`, kept, and surfaced in the UI.
- Download daily wind direction, wind speed and precipitation for each province centroid for the window plus 7 days before it (needed for the dry-day count).

### 5.2 Normalise schemas

| Harmonised field | MODIS C6.1 | VIIRS C2 |
|---|---|---|
| `lat`, `lon` | `latitude`, `longitude` | same |
| `t_utc` | `acq_date` + `acq_time` (UTC) | same |
| `sensor` | `MODIS` | `VIIRS` |
| `platform` | `satellite` (Terra / Aqua) | `satellite` (S-NPP / NOAA-20 / NOAA-21) |
| `bt_fire_k` | `brightness` (band 21/22) | `bright_ti4` (band I4) |
| `bt_bg_k` | `bright_t31` | `bright_ti5` |
| `frp_mw` | `frp` | `frp` |
| `daynight` | `daynight` | `daynight` |
| `pixel_km` | `scan` × `track` (nominal 1 km) | `scan` × `track` (nominal 375 m) |
| `conf_raw` | `confidence` (0–100) | `confidence` (low / nominal / high, or l / n / h) |
| `conf_class` | derived, 5.3 | derived, 5.3 |

Brightness temperatures are carried through but never compared across sensors: they come from different bands and pixel sizes.

### 5.3 Confidence harmonisation
- VIIRS: native three classes, used as-is.
- MODIS: 0–29 → low, 30–79 → nominal, 80–100 → high. These are the class breaks FIRMS documents for MODIS; confirm against the FIRMS FAQ before the Methods text is frozen.
- Default filter: nominal + high. A toggle shows low. The Methods view reports how many rows the filter removed.
- Caveat stated in the UI: the two confidence schemes are produced by different algorithms; equal labels are a working alignment, not proof of equal reliability.

### 5.4 Spatial and temporal harmonisation
- Raw counts are not comparable: one fire fills more 375 m VIIRS pixels than 1 km MODIS pixels. So the counting unit is the **active fire cell**: a 0.1° × 0.1° cell (about 11 km at the equator) that has at least one nominal-or-high detection from any sensor on a given day.
- Each cell-day keeps its provenance: MODIS-only, VIIRS-only, or both.
- Day = local date at UTC+7 (western Indonesia time), so an afternoon pass and the following night pass land on the same calendar day.
- The cell size is a design choice, not a tuned value. It is stated as such.

### 5.5 Per-province daily counts
- Point-in-polygon each cell centre against the focus provinces → `data/province_daily.json`: province, date, active cells, cells by provenance, summed FRP, detections by class.
- Rows outside all focus provinces are counted once as "elsewhere in SE Asia" so the header total reconciles with the calendar total.

### 5.6 Calendar
- 7-day view straight from `province_daily.json`.
- Month view from `province_monthly.json` only if the archive stretch goal (section 9) lands.

### 5.7 `facts.json`
The pipeline writes every number the deck quotes (row counts per feed, rows per class, cells per province, top province, aligned-day counts, window dates) into `data/facts.json`. Slides are filled from this file and nowhere else.

## 6. Geography decision

**Aggregate to six Indonesian provinces, in two groups, and report everything else as "elsewhere".**

| Group | Provinces | Why it matters for Singapore |
|---|---|---|
| Sumatra, across the Malacca Strait | Riau, Jambi, South Sumatra | The nearest large peat and plantation landscapes to Singapore; west to south of the city, so southwesterly and southerly winds carry smoke towards it |
| Kalimantan (Borneo) | West, Central and South Kalimantan | Further away to the east and south-east; relevant when south-easterly winds persist |

Reasoning:
- Province is the unit at which burning is governed and reported, so a per-province calendar is something an agency or journalist can act on.
- Both groups are the regions conventionally named in transboundary-haze reporting for Singapore. That is background knowledge from the literature (cite in SUBMISSION.md references), not something our 7-day snapshot proves.
- Six rows fit one legible calendar on a slide.
- Distance and bearing to Singapore are computed in the app from province centroids and shown, not quoted from memory.

Not included, and said so: Peninsular Malaysia, Sarawak, and mainland South-East Asia. They appear only in the "elsewhere" total.

Boundaries: Natural Earth admin-1, filtered to the six provinces and simplified. A centroid is a crude stand-in for a large province; noted in Methods.

## 7. Haze-risk heuristic

Stated plainly: **this is an alignment heuristic with untuned parameters. It has not been validated against any air-quality record.** It says "the ingredients for smoke heading towards Singapore were present", never "haze will occur".

For province *p* on day *d*:

- **A** = active fire cells (section 5.4).
- **W** = wind alignment = max(0, cos θ), where θ is the angle between the direction the wind is blowing *towards* (reported direction + 180°) and the bearing from the province centroid to Singapore. 1 = straight at Singapore, 0 = crosswind or away.
- **D** = consecutive days up to *d* with precipitation under 1 mm, capped at 5, divided by 5.
- **Index** = A × W × (0.5 + 0.5 × D).
- **Aligned day** = A ≥ 1 and W ≥ 0.5 (wind within 60° of the bearing).

Presentation rules:
- The three ingredients are always shown beside the product, so a judge can see why a day scored.
- No red/amber/green alarm bands and no relative scaling to the week's maximum: in a quiet week that would paint one stray fire as "high".
- Distance is displayed but deliberately left out of the product, to avoid adding another untuned parameter.

Known weaknesses, listed in the Methods view:
- Surface wind (10 m) at one point per province is not the wind that transports smoke; real transport depends on winds aloft along the whole path.
- No plume rise, dispersion, rain washout en route, or fire intensity (FRP is recorded but unused in the index).
- Cloud hides fires from both sensors, so a zero can mean "not observed".
- Thresholds (1 mm, 5 days, 60°) are choices, not fitted values.

Concept-only validation path: compare aligned days against Singapore's published PSI history over several haze seasons using the archive.

## 8. Prototype vs. concept

| Prototype — real, on screen, from fetched data | Concept — designed, shown as empty states or diagrams, labelled |
|---|---|
| 7-day MODIS hot spots for SE Asia | Multi-year archive and the 12-month calendar (unless the stretch lands) |
| Schema normalisation and confidence mapping for both sensors; VIIRS path exercised by whichever VIIRS files have rows, else shown as empty | MODIS↔VIIRS agreement statistics over a full season |
| 0.1° active-cell counting, per-province daily calendar | Year-over-year "is this month unusual?" comparison |
| Wind-alignment and dry-day ingredients for the same 7 days | Validation of the index against PSI |
| Feed-status reporting, including the empty feed | Scheduled refresh and alerts |

The deck uses these two words consistently. Any slide element that is concept carries the word "concept" on the slide.

## 9. Build order, risks, cuts

**Time budget (8 h total):** build 2 h of agent time → verification and screenshots 1 h → deck 2 h → project page 1 h → 2 h buffer. Target submitting about 90 minutes before the deadline.

**Build order**
0. *Checks (15 min, before any UI):* count MODIS rows inside each focus province; fetch the NOAA-20/21 files and record row counts; confirm POWER returns wind direction and rain for the window; confirm the province polygons load. Write results to the manifest.
1. Fetch + normalise + confidence classes + `facts.json`.
2. Cell gridding, province join, 7-day calendar (View B).
3. Map (View A).
4. Wind/rain ingredients and province detail (View C).
5. Sensors & Methods (View D).
6. Stretch, 20-minute timebox: one or more archive years → monthly calendar.

**Risks**

| Risk | Likelihood | Response |
|---|---|---|
| Mid-November is outside the usual dry season: few or no fires in the six provinces, winds not towards Singapore | High | Step 0 measures it first. If quiet, the story becomes "a quiet week, and the tool shows why": zeros shown, ingredients shown, slides 4–5 use the alternate wording in DECK.md. The archive stretch moves up to step 3 |
| All VIIRS feeds are empty | Medium | Harmonisation is demonstrated on schema and method; agreement panel shows its empty state; slide 3 says so |
| FIRMS SE Asia region file does not cover part of Kalimantan | Low | Step 0 checks the lat/lon extent of the rows; report the extent in Methods |
| POWER lags past the most recent days or lacks a parameter | Medium | Use Open-Meteo for the gap, labelled as non-NASA; or show "no wind data" for those days |
| Province polygons unavailable or too heavy | Low | Hand-drawn bounding boxes, labelled "approximate regions" on every view |
| Archive files need a login or are too large for the timebox | Medium | Month view stays as the labelled empty state |
| GIBS daily imagery mostly cloud | High | Use it only as backdrop; default to the static Blue Marble layer |
| Build overruns 2 h | Medium | Cut list below |

**Cut order if time runs out** (first cut first)
1. Archive / monthly calendar → empty state.
2. Raw-vs-cell toggle and day scrubber on the map → static map of all 7 days.
3. Dry-day term → index becomes A × W, Methods text updated to match.
4. Map view entirely → calendar, province detail and Methods are enough for all seven slides (slide 1 then uses the calendar).
5. Never cut: feed-status header, the empty-VIIRS state, the heuristic label, `facts.json`.

## 10. Stack (for the build turn)

Static HTML/CSS/vanilla JS, Leaflet for the map, GIBS WMTS tiles, one small fetch-and-aggregate script producing JSON in `data/`. No framework, no build step, no server, opened from disk or any static host.
