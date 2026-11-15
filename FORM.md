# Space Apps project form: paste-ready

Deadline 23:59 tonight. Fill top to bottom, press **Save Progress** after each block, then
**Submit for Judging** once. Only that final click is judged.

## 1. Project Name

```text
HazeWatch
```

## 2. Summary (form allows 1,500 characters, suggests 50 to 200 words)

```text
HazeWatch is a burning calendar for the provinces whose fires can become Singapore's smoke. It puts NASA FIRMS MODIS and VIIRS hot spots on one set of columns, one confidence scale and a 0.1 degree grid, counts burning cells per province per day, and marks the days when fire and wind line up towards Singapore. Live, it reads a real 7-day snapshot (28,523 detections) and narrows the VIIRS-to-MODIS gap from 13.4x to 8.2x. A September 2015 archive look back shows fires peaking on 22 September at 1,579 cells, three days before Singapore closed its schools, and 8 September almost as high (1,520) with no closure, so fire counts alone do not explain smoke. It is a rough guide, not a forecast.
```

## 3. Project Demonstration (7-slide deck, public, no login)

```text
https://github.com/lgf2111/hazewatch/blob/main/docs/deck/HazeWatch-deck.pdf
```

## 4. Project link

```text
https://hazewatch.leeguanfeng.com/
```

## 5. Project Details

Paste the whole block. It is plain text; the editor's headings are optional.

```text
THE QUESTION
When the haze comes, Singapore asks one thing: where is it coming from? NASA already publishes the answer as tens of thousands of fire dots a week. HazeWatch makes it readable for one city: which provinces, on which days, in which wind windows.

THE PROBLEM
MODIS (Terra, Aqua) detects fires at 1 km with a 0 to 100 percent confidence. VIIRS (S-NPP, NOAA-20, NOAA-21) detects at 375 m with low / nominal / high confidence. The same fire gives different counts and different kinds of confidence, so raw numbers cannot be added or compared. On our live snapshot VIIRS reports 13.4 detections for every MODIS detection.

WHAT IT DOES
1. Fetches the four FIRMS 7-day regional files for South-East Asia and keeps them unmodified.
2. Maps both sensors to one set of columns, and MODIS confidence to low / nominal / high (low is excluded by default).
3. Counts burning 0.1 degree cells per day, whichever sensor sees them, and tags each cell MODIS-only, VIIRS-only or both.
4. Aggregates per day for Riau, Jambi, South Sumatra, West, Central and South Kalimantan.
5. Adds wind direction and dry days, and marks a province-day as lined up when fire is burning and the wind is within 60 degrees of the line to Singapore.

WHAT THE LIVE DATA SHOWS (fetched 15 November 2026, 15:41 SGT)
- 28,523 detections in four files: MODIS 1,961, VIIRS S-NPP 0 (empty, see below), NOAA-20 12,961, NOAA-21 13,601.
- Counting cells instead of dots narrows the VIIRS-to-MODIS ratio from 13.4x to 8.2x. It does not close it: only 55.5 percent of MODIS-seen cells were also seen by VIIRS.
- 724 of the 9,647 burning cell-days in South-East Asia fall in the six provinces; South Sumatra is the most active with 275.
- On 20 of 48 province-days, fire and wind lined up towards Singapore.

THE 2015 TEST
We pulled 1 to 30 September 2015 from the FIRMS archive (MODIS and VIIRS S-NPP) and counted burning cells per day across the six provinces the same way. On 25 September 2015 Singapore closed its primary and secondary schools, the first time air pollution had closed them; the 24-hour PSI peaked at 322. Fires peaked on 22 September at 1,579 cells, stayed high on 23 and 24 September (1,243 and 1,004) and fell to 555 on the day of the closure. That build-up fits smoke arriving after the fires. But 8 September had 1,520 cells and no closure, so fire counts alone do not explain PSI. One event, one month: a look back, not a test.

WHAT IS REAL AND WHAT IS NOT
Real: one week of live NASA data, one month of archive, the harmonisation, the province-by-day calendar, the map, and the wind and dry-day ingredients. Every number is in data/facts.json or data/archive-2015.json; tools/build_snapshot.py and tools/fetch_archive.py rebuild them.
Not built: a multi-year series and 12-month calendar, and a test of the wind rule against Singapore's PSI record over many events.
Limits: the live app shows 7 days; the archive covers one month and one event; the wind rule is a rough guide, not a forecast. Thresholds are chosen, not fitted. Surface wind is not transport wind, cloud hides fires, and some hot spots are not vegetation fires.
The empty S-NPP file is not a glitch: Suomi NPP stopped delivering new data at 13:00 UTC on 2 November 2026 (NASA Earthdata alert). NOAA-20 and NOAA-21 carry on.

WHY IT MATTERS
MODIS has the long record and VIIRS the sharp one, and now one VIIRS satellite has ended. Joining them without VIIRS looking like more fire is the whole problem. Next: a multi-year series, MODIS-VIIRS agreement by province over a season, and the wind rule tested against recorded haze days.

TEAM AND TOOLS
Team "Can See Or Not", solo: Lee Guan Feng. Singapore Local Event, challenge "Harmonization of MODIS and VIIRS Hot Spots", award target Best Use of Data. HTML, CSS and vanilla JavaScript with Leaflet, plus standard-library Python scripts. Claude (Anthropic, via Claude Code) helped write the code and text; all data shown comes from the sources listed, none is AI-generated. No image is AI-generated: every visual is a screenshot of the running app or a chart drawn from the data files.
```

## 6. Use of Super Intelligence

Tick these five, and only these five:

- Coding, Debugging, or Troubleshooting
- Ideation or Brainstorming
- Research or Information Gathering
- Data Analysis and Interpretation
- Writing, Editing, or Translation

Leave clear: Building SI/ML Into the Project (the app has no model), Visual Design or Image
Creation (nothing was generated; every visual is a screenshot or an SVG chart), Other
Project-Related SI Use, and None.

If there is a free-text box, paste:

```text
Claude (Anthropic, via Claude Code) assisted with: code, debugging and layout (HTML, CSS, JavaScript); the written copy for the site, the deck and this form; research into the September 2015 event and into comparable public services; and the archive analysis behind the September 2015 chart. No image, video or audio was generated. Every visual is a screenshot of the running app or a chart drawn from data files. All data comes from the NASA and partner sources listed.
```

## 7. NASA Data (one row each: Link Text, then Link Url)

| Link Text | Link Url |
|---|---|
| NASA FIRMS MODIS C6.1 7-day active fire | https://firms.modaps.eosdis.nasa.gov/data/active_fire/modis-c6.1/csv/MODIS_C6_1_SouthEast_Asia_7d.csv |
| NASA FIRMS VIIRS S-NPP C2 7-day active fire | https://firms.modaps.eosdis.nasa.gov/data/active_fire/suomi-npp-viirs-c2/csv/SUOMI_VIIRS_C2_SouthEast_Asia_7d.csv |
| NASA FIRMS VIIRS NOAA-20 C2 7-day active fire | https://firms.modaps.eosdis.nasa.gov/data/active_fire/noaa-20-viirs-c2/csv/J1_VIIRS_C2_SouthEast_Asia_7d.csv |
| NASA FIRMS VIIRS NOAA-21 C2 7-day active fire | https://firms.modaps.eosdis.nasa.gov/data/active_fire/noaa-21-viirs-c2/csv/J2_VIIRS_C2_SouthEast_Asia_7d.csv |
| NASA FIRMS area API, archive pull September 2015 | https://firms.modaps.eosdis.nasa.gov/api/area/ |
| NASA GIBS imagery, Blue Marble Shaded Relief | https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/ |
| NASA POWER daily meteorology | https://power.larc.nasa.gov/docs/services/api/temporal/daily/ |
| NASA Earthdata alert, Suomi NPP data delivery ends | https://www.earthdata.nasa.gov/data/alerts-outages/suomi-npp-observations-cease-november-2-2026 |

## 8. Space Agency Partner and Other Data

| Link Text | Link Url |
|---|---|
| Natural Earth admin-1 boundaries | https://www.naturalearthdata.com/ |
| Open-Meteo, wind and rain where NASA POWER lagged | https://open-meteo.com/ |
| Leaflet 1.9.4 | https://leafletjs.com/ |
| Giglio et al. 2016, MODIS Collection 6 active fire algorithm | https://doi.org/10.1016/j.rse.2016.02.054 |
| Schroeder et al. 2014, VIIRS 375 m active fire product | https://doi.org/10.1016/j.rse.2013.12.008 |
| Singapore NEA, PSI reading of 25 September 2015 | https://www.nea.gov.sg/ |

## 9. Before the final click

- Save Progress after every block, then check the summary counter reads under 1,500.
- Open the demo link in a private window: it must load without login and show 7 pages.
- Open the project link in the same window: the September 2015 tab must draw its chart.
- Tick the SI options for code and text only.
- Press Submit for Judging once. Submission is final.
