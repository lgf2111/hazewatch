#!/usr/bin/env python3
"""Pull September 2015 from the FIRMS archive and count burning squares per province per day.

Usage:
  FIRMS_MAP_KEY=... python3 tools/fetch_archive.py     # fetch 5-day chunks, cache the CSVs, write data/archive-2015.json
  python3 tools/fetch_archive.py --offline             # re-derive the JSON from the cached CSVs in data/archive-raw/

The key comes from the environment only. It is never written to a file, never printed and never
part of any cached CSV or output. Standard library only.

What is counted is the same as the live snapshot (tools/build_snapshot.py): low-confidence detections are
dropped, a 0.1 degree square counts once per local day (UTC+7) whichever instrument saw it, and a square belongs
to the province holding most of its detections (build_snapshot.load_provinces / province_of).

Output keeps the "events" block of the existing data/archive-2015.json: those are supplied facts (the 2015 school
closure, the Suomi NPP end date, the PSI reading used as contrast), not something this script fetches.
"""
import csv
import datetime as dt
import json
import math
import os
import pathlib
import sys
import time
import urllib.error
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import build_snapshot as bs  # noqa: E402

DATA = bs.DATA
RAW = DATA / "archive-raw"
OUT = DATA / "archive-2015.json"

AREA = (95.0, -6.0, 119.0, 4.0)          # west, south, east, north
SOURCES = ["MODIS_SP", "VIIRS_SNPP_SP"]  # standard-processing archive: Terra/Aqua MODIS, Suomi NPP VIIRS
SENSOR = {"MODIS_SP": "MODIS", "VIIRS_SNPP_SP": "VIIRS"}
START, END = dt.date(2015, 9, 1), dt.date(2015, 9, 30)
CHUNK_DAYS = 5
API = "https://firms.modaps.eosdis.nasa.gov/api/area/csv"


def chunk_starts():
    d = START
    while d <= END:
        yield d
        d += dt.timedelta(days=CHUNK_DAYS)


def cache_path(source, start):
    return RAW / f"{source}_{start.isoformat()}.csv"


def fetch(key):
    RAW.mkdir(parents=True, exist_ok=True)
    area = ",".join(f"{v:g}" for v in AREA)
    for source in SOURCES:
        for start in chunk_starts():
            url = f"{API}/{key}/{source}/{area}/{CHUNK_DAYS}/{start.isoformat()}"
            try:
                with urllib.request.urlopen(url, timeout=120) as r:
                    body = r.read().decode("utf-8", "replace")
            except urllib.error.URLError as e:
                sys.exit(f"{source} {start}: request failed ({getattr(e, 'code', e.reason)})")  # never print the URL
            if not body.startswith("latitude"):
                sys.exit(f"{source} {start}: FIRMS did not return CSV: {body[:120].strip()!r}")
            cache_path(source, start).write_text(body)
            print(f"  {source} {start}: {max(body.count(chr(10)) - 1, 0)} rows", flush=True)
            time.sleep(1)


def derive(raw_dir=RAW):
    provinces = bs.load_provinces()
    rows_by_source, owners, sensors = {}, {}, {}
    for source in SOURCES:
        n = 0
        for start in chunk_starts():
            path = pathlib.Path(raw_dir) / f"{source}_{start.isoformat()}.csv"
            if not path.exists():
                sys.exit(f"missing {path}; run with FIRMS_MAP_KEY set to fetch it")
            with open(path, newline="") as fh:
                for r in csv.DictReader(fh):
                    n += 1
                    if bs.conf_class(SENSOR[source], r["confidence"]) == "low":
                        continue
                    lat, lon = float(r["latitude"]), float(r["longitude"])
                    t = dt.datetime.strptime(r["acq_date"] + r["acq_time"].zfill(4), "%Y-%m-%d%H%M")
                    day = (t + dt.timedelta(hours=bs.LOCAL_OFFSET_H)).date()
                    if not START <= day <= END:
                        continue
                    key = (day.isoformat(), (math.floor(lat / bs.CELL), math.floor(lon / bs.CELL)))
                    sensors.setdefault(key, set()).add(SENSOR[source])
                    p = bs.province_of(lat, lon, provinces)
                    owners.setdefault(key, {}).setdefault(p, 0)
                    owners[key][p] += 1
        rows_by_source[source] = n

    per_province, total = {}, {}
    for (day, _), votes in owners.items():
        owner = max(votes.items(), key=lambda kv: kv[1])[0]
        if owner is None:
            continue
        per_province.setdefault(owner, {}).setdefault(day, 0)
        per_province[owner][day] += 1
        total[day] = total.get(day, 0) + 1
    dates = sorted(total)
    return {
        "provinces": {p: {d: v.get(d, 0) for d in dates} for p, v in sorted(per_province.items())},
        "six_province_total": {d: total[d] for d in dates},
        "dates": dates,
        "rows_fetched": rows_by_source,
    }


def main():
    offline = "--offline" in sys.argv
    if not offline:
        key = os.environ.get("FIRMS_MAP_KEY", "").strip()
        if not key:
            sys.exit("FIRMS_MAP_KEY is not set. Get a free key at https://firms.modaps.eosdis.nasa.gov/api/map_key/ "
                     "and export it; or run with --offline against data/archive-raw/.")
        fetch(key)
    prior = json.loads(OUT.read_text()) if OUT.exists() else {}
    if "events" not in prior:
        sys.exit(f"{OUT} must exist with its 'events' block before this script can rewrite it")
    result = derive()
    doc = {
        "source": "FIRMS area API, rederived by tools/fetch_archive.py",
        "params": {
            "area_west_south_east_north": list(AREA), "sources": SOURCES, "chunk_days": CHUNK_DAYS,
            "window": [START.isoformat(), END.isoformat()], "local_day_utc_offset_h": bs.LOCAL_OFFSET_H,
            "cell_deg": bs.CELL, "low_confidence": "dropped", "squares_counted": "once per local day, either instrument",
            "province_rule": "build_snapshot.province_of; a square belongs to the province with most of its detections",
        },
        "rows_fetched": result["rows_fetched"],
        "dates": result["dates"],
        "six_province_total": result["six_province_total"],
        "provinces": result["provinces"],
        "events": prior["events"],
    }
    OUT.write_text(json.dumps(doc, indent=1))
    print(f"wrote {OUT}: {len(result['dates'])} days, rows {result['rows_fetched']}")


if __name__ == "__main__":
    main()
