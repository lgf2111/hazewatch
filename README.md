# HazeWatch

**Where does the smoke come from?** A burning calendar built from NASA FIRMS MODIS and VIIRS hot spots for six Sumatra and Kalimantan provinces, with the days when fire and wind lined up towards Singapore.

Live: https://hazewatch.leeguanfeng.com/ · NASA Space Apps Challenge 2026, Singapore · Challenge: *Harmonization of MODIS and VIIRS Hot Spots*

## What it does

1. Fetches the four keyless FIRMS 7-day South-East Asia files (MODIS C6.1, VIIRS S-NPP, NOAA-20, NOAA-21).
2. Maps both schemas to one, and MODIS 0 to 100 confidence to VIIRS's low / nominal / high.
3. Counts **burning cells** on a shared 0.1° grid per local day, tagged MODIS-only, VIIRS-only or both.
4. Aggregates per province per day, and adds wind alignment towards Singapore and dry days (NASA POWER, gaps filled by Open-Meteo).
5. Looks back at **September 2015** with the FIRMS archive (MODIS and VIIRS S-NPP, 1 to 30 September): burning cells per day across the six provinces, set against the closure of Singapore's schools on 25 September 2015. The result and its caveats are in `data/archive-2015.json` and on slide 5 of the deck.

## Limits (also shown in the app)

- The live app shows a 7-day snapshot. The archive pull covers one month (September 2015) and one event; there is no multi-year series, no 12-month calendar, and no seasonal or year-on-year claim.
- The VIIRS S-NPP file returned 0 rows on 15 November 2026 because Suomi NPP stopped delivering new data at 13:00 UTC on 2 November 2026 ([NASA Earthdata alert](https://www.earthdata.nasa.gov/data/alerts-outages/suomi-npp-observations-cease-november-2-2026)). It is shown as empty, not filled. NOAA-20 and NOAA-21 carry on.
- The wind rule (fire burning and wind within 60° of the line to Singapore) is a rough guide with chosen thresholds, not a haze forecast, and it has not been tested against Singapore's PSI record beyond the one 2015 event. In 2015, fires peaked on 22 September, three days before the closure, but 8 September burned almost as much with no closure, so fire counts alone do not explain PSI.

## Check the numbers

- `data/facts.json`: every number about the live snapshot that the site, deck and project page quote.
- `data/archive-2015.json`: the September 2015 daily counts, the parameters used and the row counts fetched.
- `data/raw/`: the NASA files exactly as downloaded; `data/manifest.json`: URL, HTTP status, bytes, rows and fetch time for each.
- `data/archive-raw/`: the cached archive CSVs; `data/snapshot.json`: what the page renders.

## Requirements

- **Python 3.12 or newer** for `tools/build_deck.py` and `tools/build_submission.py`. macOS's `/usr/bin/python3` is 3.9 and fails; use Homebrew's (`/opt/homebrew/bin/python3`).
- `curl` and the standard library for the live snapshot; no packages.
- A **`FIRMS_MAP_KEY`** in the environment for the archive pull only (a free key from https://firms.modaps.eosdis.nasa.gov/api/map_key/). Never put it in a file or a command history; the scripts read it from the environment and never print it.

## Refresh the data

```sh
python3 tools/build_snapshot.py            # live snapshot: re-fetch from NASA (no key) and rebuild data/
python3 tools/build_snapshot.py --offline  # rebuild from data/raw without the network

export FIRMS_MAP_KEY=...                   # set in your shell, never committed
/opt/homebrew/bin/python3 tools/fetch_archive.py             # September 2015 archive pull -> data/archive-2015.json
/opt/homebrew/bin/python3 tools/fetch_archive.py --offline   # re-derive from data/archive-raw without the network
```

Commit `data/` and push; GitHub Pages serves the new snapshot.

## Run locally and retake screenshots

```sh
python3 -m http.server 8765      # then open http://localhost:8765
tools/screenshots.sh             # writes docs/screenshots/*.png (headless Chrome, macOS)
```

## Layout

`index.html`, `assets/`: the static site. `tools/`: snapshot, archive, deck, submission and screenshot scripts. `data/`: snapshot and archive. `docs/screenshots/`, `docs/deck/`: deck images and the deck. `PLAN.md`, `DECK.md`, `SUBMISSION.md`: spec, slides, project-page text.

## Credits

Fire data: NASA FIRMS. Imagery: NASA GIBS. Weather: NASA POWER, Open-Meteo. Boundaries: Natural Earth. Map library: Leaflet. Not affiliated with or endorsed by NASA.
