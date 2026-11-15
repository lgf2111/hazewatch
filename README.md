# HazeWatch

**Whose fires become Singapore's smoke?** A burning calendar built from NASA FIRMS MODIS and VIIRS hot spots for six Sumatra and Kalimantan provinces, with the days when fire and wind lined up towards Singapore.

Live: https://hazewatch.leeguanfeng.com/ · NASA Space Apps Challenge 2026, Singapore · Challenge: *Harmonization of MODIS and VIIRS Hot Spots*

## What it does

1. Fetches the four keyless FIRMS 7-day South-East Asia files (MODIS C6.1, VIIRS S-NPP, NOAA-20, NOAA-21).
2. Maps both schemas to one, and MODIS 0–100 confidence to VIIRS's low / nominal / high.
3. Counts **burning cells** on a shared 0.1° grid per local day, tagged MODIS-only, VIIRS-only or both.
4. Aggregates per province per day, and adds wind alignment towards Singapore and dry days (NASA POWER, gaps filled by Open-Meteo).

## Limits (also shown in the app)

- 7-day snapshot only. No archive, no seasonal or year-on-year claim.
- The VIIRS S-NPP file returned 0 rows at fetch time. It is shown as empty, not filled.
- The wind-alignment index is an unvalidated heuristic, not a haze forecast.

## Check the numbers

- `data/facts.json` — every number the site, deck and project page quote.
- `data/raw/` — the NASA files exactly as downloaded; `data/manifest.json` — URL, HTTP status, bytes, rows and fetch time for each.
- `data/snapshot.json` — what the page renders.

## Refresh the snapshot

Python 3 and curl, no packages, no API key:

```sh
python3 tools/build_snapshot.py            # re-fetch from NASA and rebuild data/
python3 tools/build_snapshot.py --offline  # rebuild from data/raw without the network
```

Commit `data/` and push; GitHub Pages serves the new snapshot.

## Run locally and retake screenshots

```sh
python3 -m http.server 8765      # then open http://localhost:8765
tools/screenshots.sh             # writes docs/screenshots/*.png (headless Chrome, macOS)
```

## Layout

`index.html`, `assets/` — the static site · `tools/` — pipeline and screenshot scripts · `data/` — snapshot · `docs/screenshots/` — deck images · `PLAN.md`, `DECK.md`, `SUBMISSION.md` — spec, slides, project-page text.

## Credits

Fire data: NASA FIRMS. Imagery: NASA GIBS. Weather: NASA POWER, Open-Meteo. Boundaries: Natural Earth. Map library: Leaflet. Not affiliated with or endorsed by NASA.
