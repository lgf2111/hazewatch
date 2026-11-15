# HazeWatch — Space Apps project page

**Before pasting**
- Numbers come from `data/facts.json` (snapshot fetched 2026-11-15 15:41 SGT).
- Lines marked **[CHECK]** depend on what the build actually used or on an external fact to confirm; edit or delete them.
- Field names follow the usual Space Apps project form; match them to the 2026 form as it appears.

---

## Project name

HazeWatch

## Challenge

Harmonization of MODIS and VIIRS Hot Spots

## Short description (gallery card, 60 words)

HazeWatch turns NASA FIRMS active-fire detections from MODIS and VIIRS into one burning calendar for Sumatra and Kalimantan provinces near Singapore. It maps both sensors onto a shared grid and confidence scale, then flags days when fires, wind direction and dry spells line up towards the city. Built on a real 7-day snapshot; archive comparison is designed, not yet built.

## High-level summary

HazeWatch is a web prototype that answers a local question with global data: which provinces' fires, on which days, could send smoke towards Singapore?

It takes NASA FIRMS active-fire records from MODIS and VIIRS, converts them to one schema and one three-level confidence scale, and counts burning on a shared 0.1° grid so that VIIRS's finer pixels do not look like more fire than MODIS's coarser ones. Those counts are aggregated per day for six Indonesian provinces in Sumatra and Kalimantan and shown as a burning calendar. Beside each day, the app shows whether the wind was pointing towards Singapore and how long it had been dry.

The prototype is live at https://lgf2111.github.io/hazewatch/ and runs on a real 7-day snapshot fetched on 15 November 2026 at 15:41 SGT: 28,523 detections in four NASA files. MODIS held 1,961 rows, VIIRS NOAA-20 12,961 and VIIRS NOAA-21 13,601, while the VIIRS S-NPP file for the same region returned a header and no rows. The app reports that gap instead of hiding it, which is the practical case for harmonisation: a calendar that depends on one feed stops when that feed does.

What the harmonisation measurably does on this snapshot: raw, VIIRS reports 13.4 detections for every MODIS detection; counted as burning cells on the shared grid, the ratio falls to 8.2. It does not fall to 1, and we say so: 55.5 % of the cell-days MODIS saw were also seen by VIIRS, and VIIRS saw many that MODIS did not. The six provinces held 724 of the 9,647 burning cell-days in South-East Asia that week, 275 of them in South Sumatra.

The multi-year historical calendar and the haze-index validation are designed and described, not built.

## Problem statement

Singapore experiences transboundary haze from land and forest fires in neighbouring regions. Whether a fire affects the city depends on where it is, when it burns, and where the wind takes the smoke. Public fire maps show dots; they do not answer "which provinces, which days, which wind windows".

Answering it over time requires a consistent fire record, and there are two. MODIS (on Terra and Aqua) offers the longer record at 1 km with a 0–100 % confidence value. VIIRS (on Suomi NPP, NOAA-20 and NOAA-21) offers 375 m detections with low / nominal / high confidence. The same fire therefore produces different numbers of detections with different kinds of confidence depending on the sensor, so raw counts cannot be added, compared, or joined into one long calendar. Feeds can also be unavailable: at the time of our fetch, one VIIRS regional file was empty.

The challenge asks for a harmonised burning-activity calendar that supports early warning and historical comparison for an area of interest. Our area of interest is the set of provinces that matter to one city.

## Solution and how it works

1. **Fetch.** A script downloads the FIRMS 7-day regional CSVs for MODIS and each VIIRS platform, and records URL, size, row count and time. Empty files are kept and reported.
2. **Normalise.** Both schemas are mapped to common fields (position, UTC time, sensor, platform, fire radiative power, day/night, pixel size, confidence).
3. **Harmonise confidence.** MODIS percentages become low (< 30), nominal (30–79) or high (≥ 80) to match VIIRS's classes. Low is excluded by default.
4. **Harmonise space.** A 0.1° cell counts as burning on a day if any sensor has a nominal- or high-confidence detection in it. Each cell-day is tagged MODIS-only, VIIRS-only or both.
5. **Aggregate.** Burning cells are counted per province per day for Riau, Jambi, South Sumatra, and West, Central and South Kalimantan.
6. **Add context.** For each province and day: wind alignment towards Singapore (0–1) and consecutive dry days. A day is marked "aligned" when at least one cell is burning and the wind is within 60° of the bearing to Singapore.
7. **Show.** A map, the province-by-day burning calendar, a per-province detail panel, and a methods panel listing feed status and limits.

## Impact

Award category aimed at: **Best Use of Data**. The claim is that the space data is made usable, and checkable: every figure on the site and in the deck is in `data/facts.json`, the unmodified NASA files are in `data/raw/`, and one command rebuilds everything.

- **For residents and communicators:** one page that connects fires to a place people care about, by province and day, instead of a regional scatter of dots.
- **For analysts:** a counting unit (burning cells on a common grid, with sensor provenance) that lets MODIS and VIIRS records be combined without the higher-resolution sensor inflating totals. This is what a long historical calendar needs.
- **For resilience:** the tool keeps working, and says what it is missing, when one sensor's feed is empty.

What we do not claim: we have not measured any effect on decisions or health, and the alignment index has not been tested against air-quality records. The impact described is the intended use, supported by a working prototype on one week of data.

## Limitations and uncertainty

- Hot spots are thermal anomalies; some are gas flares, industry or volcanoes. We do not filter by type.
- Gridding narrows the MODIS/VIIRS gap (13.4× to 8.2×) but does not close it; combined counts are dominated by VIIRS.
- NASA POWER had no values for 13–15 November at fetch time; those three days use Open-Meteo, which defines daily wind differently.
- Seven days of data (8 local dates, the first and last partial). No seasonal or year-on-year conclusion can be drawn from it.
- The alignment index is a heuristic with chosen, unfitted thresholds. It is not a forecast and not an air-quality measure.
- Wind is taken near the surface at one point per province; smoke transport depends on winds aloft along the whole path.
- Cloud and smoke can hide fires from both sensors; zero detections can mean "not observed".
- MODIS and VIIRS confidence values come from different algorithms; mapping them to shared labels is a working alignment.
- We do not know why the VIIRS S-NPP file was empty at fetch time and draw no conclusion about the sensor from it.

## How NASA data is used

| Dataset | Exact source | Use |
|---|---|---|
| MODIS Collection 6.1 NRT active fire (MCD14DL), Terra and Aqua, 1 km | `https://firms.modaps.eosdis.nasa.gov/data/active_fire/modis-c6.1/csv/MODIS_C6_1_SouthEast_Asia_7d.csv` | 1,961 rows fetched 15 Nov 2026; the MODIS side of every count |
| VIIRS S-NPP Collection 2 NRT active fire (VNP14IMGTDL), 375 m | `https://firms.modaps.eosdis.nasa.gov/data/active_fire/suomi-npp-viirs-c2/csv/SUOMI_VIIRS_C2_SouthEast_Asia_7d.csv` | Fetched; returned header only (0 rows). Schema drives the VIIRS side of the harmonisation; the empty feed is shown in the app |
| VIIRS NOAA-20 Collection 2 NRT active fire (VJ114IMGTDL), 375 m | `https://firms.modaps.eosdis.nasa.gov/data/active_fire/noaa-20-viirs-c2/csv/J1_VIIRS_C2_SouthEast_Asia_7d.csv` | 12,961 rows; VIIRS side of every count |
| VIIRS NOAA-21 Collection 2 NRT active fire (VJ214IMGTDL), 375 m | `https://firms.modaps.eosdis.nasa.gov/data/active_fire/noaa-21-viirs-c2/csv/J2_VIIRS_C2_SouthEast_Asia_7d.csv` | 13,601 rows; VIIRS side of every count |
| NASA GIBS imagery via WMTS | `https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/` — layer `BlueMarble_ShadedRelief_Bathymetry` (tile matrix set `GoogleMapsCompatible_Level8`) | Basemap of the map view, loaded live |
| NASA POWER daily meteorology | `https://power.larc.nasa.gov/api/temporal/daily/point` — parameters `WD10M`, `WS10M`, `PRECTOTCORR` | Wind direction, wind speed and precipitation at each province centroid, 1–12 Nov 2026 (later dates not yet available at fetch time) |

All of the above were accessed without an API key.

Designed, not used in the prototype: the FIRMS archive (`https://firms.modaps.eosdis.nasa.gov/download/` and the FIRMS API at `https://firms.modaps.eosdis.nasa.gov/api/`) for the multi-year calendar. No archive data was loaded.

## Other data

- Natural Earth admin-1 boundaries (public domain), `https://www.naturalearthdata.com/` — outlines of the six provinces (`data/provinces.geojson`).
- Open-Meteo, `https://open-meteo.com/` — wind and rain for 13, 14 and 15 November 2026 only, where NASA POWER had no values yet. Marked † in the app.

## Tools and technologies

HTML, CSS, vanilla JavaScript; Leaflet 1.9.4 for the map; one Python 3 script (standard library only, `tools/build_snapshot.py`) that fetches, harmonises and writes static JSON; GitHub Pages hosting. No backend, no framework, no API key.

## Use of artificial intelligence

Anthropic's Claude (via Claude Code) was used to help plan the project, write the application code, and draft this text and the slides. All fire, imagery and weather data shown are fetched from the sources listed above; no data, statistics or images were generated by AI. **[CHECK]** adjust to the form's wording and to what was actually done.

## References

**[CHECK]** open each link once before submitting.

1. NASA FIRMS — Fire Information for Resource Management System. https://firms.modaps.eosdis.nasa.gov/
2. NASA FIRMS active fire data downloads (regional 24 h / 48 h / 7 d files). https://firms.modaps.eosdis.nasa.gov/active_fire/
3. NASA FIRMS FAQ (attribute definitions, confidence values, sensor differences). https://www.earthdata.nasa.gov/data/tools/firms/faq
4. Giglio, L., Schroeder, W., Justice, C. O. (2016). The collection 6 MODIS active fire detection algorithm and fire products. *Remote Sensing of Environment*, 178, 31–41. https://doi.org/10.1016/j.rse.2016.02.054
5. Schroeder, W., Oliva, P., Giglio, L., Csiszar, I. A. (2014). The New VIIRS 375 m active fire detection data product: Algorithm description and initial assessment. *Remote Sensing of Environment*, 143, 85–96. https://doi.org/10.1016/j.rse.2013.12.008
6. NASA GIBS — Global Imagery Browse Services. https://www.earthdata.nasa.gov/engage/open-data-services-software/earthdata-developer-portal/gibs-api
7. NASA POWER — Prediction Of Worldwide Energy Resources. https://power.larc.nasa.gov/
8. Natural Earth. https://www.naturalearthdata.com/
9. Leaflet. https://leafletjs.com/
10. **[CHECK]** One source for Singapore's transboundary haze and its source regions (for example the National Environment Agency's haze pages, https://www.nea.gov.sg/) — add the exact page you cite; the geography rationale leans on it.

## Links

- Live app: https://lgf2111.github.io/hazewatch/
- Project repository: https://github.com/lgf2111/hazewatch
- Demo (slides): **[CHECK]** URL once the deck is exported
