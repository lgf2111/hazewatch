#!/usr/bin/env python3
"""Fetch NASA FIRMS hot spots + weather, harmonise, and write the frozen snapshot.

Usage:
  python3 tools/build_snapshot.py            # fetch everything, rebuild data/
  python3 tools/build_snapshot.py --offline  # rebuild from data/raw + data/manifest.json

Outputs (all under data/):
  raw/*.csv        FIRMS files, unmodified
  raw/weather.json NASA POWER / Open-Meteo responses, unmodified
  manifest.json    URL, HTTP status, bytes, rows, fetch time per file
  snapshot.json    what the page renders
  facts.json       every number the deck and project page quote

Standard library only. Network goes through curl.
"""
import csv
import datetime as dt
import json
import math
import pathlib
import statistics
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
RAW = DATA / "raw"

FIRMS = "https://firms.modaps.eosdis.nasa.gov/data/active_fire"
FEEDS = [
    {"id": "modis", "sensor": "MODIS", "label": "MODIS C6.1 (Terra + Aqua)",
     "dataset": "MODIS Collection 6.1 NRT active fire (MCD14DL), 1 km",
     "file": "MODIS_C6_1_SouthEast_Asia_7d.csv",
     "url": f"{FIRMS}/modis-c6.1/csv/MODIS_C6_1_SouthEast_Asia_7d.csv"},
    {"id": "viirs_snpp", "sensor": "VIIRS", "label": "VIIRS S-NPP C2",
     "dataset": "VIIRS S-NPP Collection 2 NRT active fire (VNP14IMGTDL), 375 m",
     "file": "SUOMI_VIIRS_C2_SouthEast_Asia_7d.csv",
     "url": f"{FIRMS}/suomi-npp-viirs-c2/csv/SUOMI_VIIRS_C2_SouthEast_Asia_7d.csv"},
    {"id": "viirs_noaa20", "sensor": "VIIRS", "label": "VIIRS NOAA-20 C2",
     "dataset": "VIIRS NOAA-20 Collection 2 NRT active fire (VJ114IMGTDL), 375 m",
     "file": "J1_VIIRS_C2_SouthEast_Asia_7d.csv",
     "url": f"{FIRMS}/noaa-20-viirs-c2/csv/J1_VIIRS_C2_SouthEast_Asia_7d.csv"},
    {"id": "viirs_noaa21", "sensor": "VIIRS", "label": "VIIRS NOAA-21 C2",
     "dataset": "VIIRS NOAA-21 Collection 2 NRT active fire (VJ214IMGTDL), 375 m",
     "file": "J2_VIIRS_C2_SouthEast_Asia_7d.csv",
     "url": f"{FIRMS}/noaa-21-viirs-c2/csv/J2_VIIRS_C2_SouthEast_Asia_7d.csv"},
]
PLATFORM = {"T": "Terra", "A": "Aqua", "Terra": "Terra", "Aqua": "Aqua",
            "N": "S-NPP", "N20": "NOAA-20", "N21": "NOAA-21"}

SG = (1.3521, 103.8198)          # Singapore
CELL = 0.1                        # degrees; a design choice, not a tuned value
LOCAL_OFFSET_H = 7                # calendar day = local date at UTC+7 (WIB)
DRY_MM = 1.0                      # a day under this much rain counts as dry
DRY_CAP = 5                       # dry spell is capped at this many days
ALIGN_MIN = 0.5                   # W >= 0.5  <=>  wind within 60 deg of bearing
WEATHER_LOOKBACK = 7              # days before the window, for the dry-day count
MAP_BBOX = (-8.0, 9.0, 94.0, 121.0)  # lat0, lat1, lon0, lon1 of points shipped to the map

POWER_URL = ("https://power.larc.nasa.gov/api/temporal/daily/point"
             "?parameters=WD10M,WS10M,PRECTOTCORR&community=RE"
             "&longitude={lon}&latitude={lat}&start={start}&end={end}&format=JSON")
OPENMETEO_URL = ("https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
                 "&daily=wind_direction_10m_dominant,wind_speed_10m_max,precipitation_sum"
                 "&start_date={start}&end_date={end}&timezone=Asia%2FJakarta&wind_speed_unit=ms")


def now_utc():
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0)


def curl(url, dest=None):
    """Return (http_status, bytes). Body goes to dest, or is returned when dest is None."""
    cmd = ["curl", "-sL", "--max-time", "120", "-w", "\n%{http_code}", url]
    if dest:
        cmd = ["curl", "-sL", "--max-time", "120", "-o", str(dest), "-w", "%{http_code}", url]
        out = subprocess.run(cmd, capture_output=True, text=True).stdout
        return int(out or 0), dest.stat().st_size if dest.exists() else 0
    out = subprocess.run(cmd, capture_output=True, text=True).stdout
    body, _, status = out.rpartition("\n")
    return int(status or 0), body


# ---------- geometry ----------

def rings_of(geom):
    polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    return [ring for poly in polys for ring in poly]


def in_rings(lon, lat, rings):
    inside = False
    for ring in rings:
        j = len(ring) - 1
        for i in range(len(ring)):
            xi, yi = ring[i]
            xj, yj = ring[j]
            if (yi > lat) != (yj > lat) and lon < (xj - xi) * (lat - yi) / (yj - yi) + xi:
                inside = not inside
            j = i
    return inside


def ring_area_centroid(ring):
    a = cx = cy = 0.0
    for i in range(len(ring) - 1):
        x0, y0 = ring[i]
        x1, y1 = ring[i + 1]
        f = x0 * y1 - x1 * y0
        a += f
        cx += (x0 + x1) * f
        cy += (y0 + y1) * f
    a /= 2
    return abs(a), (cx / (6 * a), cy / (6 * a)) if a else ring[0]


def haversine_km(lat1, lon1, lat2, lon2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    h = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2
    return 6371.0 * 2 * math.asin(math.sqrt(h))


def bearing_deg(lat1, lon1, lat2, lon2):
    p1, p2, dl = math.radians(lat1), math.radians(lat2), math.radians(lon2 - lon1)
    y = math.sin(dl) * math.cos(p2)
    x = math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dl)
    return (math.degrees(math.atan2(y, x)) + 360) % 360


def load_provinces():
    out = []
    for f in json.load(open(DATA / "provinces.geojson"))["features"]:
        rings = rings_of(f["geometry"])
        # centroid of the largest ring: a crude stand-in for a large province
        _, (clon, clat) = max((ring_area_centroid(r) for r in rings), key=lambda t: t[0])
        xs = [p[0] for r in rings for p in r]
        ys = [p[1] for r in rings for p in r]
        out.append({
            **f["properties"], "rings": rings,
            "bbox": (min(xs), min(ys), max(xs), max(ys)),
            "centroid": [round(clat, 3), round(clon, 3)],
            "dist_km": round(haversine_km(clat, clon, *SG)),
            "bearing_deg": round(bearing_deg(clat, clon, *SG)),
        })
    return out


def province_of(lat, lon, provinces):
    for p in provinces:
        x0, y0, x1, y1 = p["bbox"]
        if x0 <= lon <= x1 and y0 <= lat <= y1 and in_rings(lon, lat, p["rings"]):
            return p["id"]
    return None


# ---------- FIRMS ----------

def conf_class(sensor, raw):
    if sensor == "MODIS":
        v = int(raw)
        return "low" if v < 30 else "nominal" if v < 80 else "high"
    return {"l": "low", "n": "nominal", "h": "high"}[raw.strip().lower()[0]]


def fetch_feeds(offline):
    manifest = json.load(open(DATA / "manifest.json")) if offline else {"feeds": {}}
    for feed in FEEDS:
        dest = RAW / feed["file"]
        if not offline:
            status, size = curl(feed["url"], dest)
            manifest["feeds"][feed["id"]] = {"http_status": status, "bytes": size,
                                             "fetched_utc": now_utc().isoformat()}
            if status != 200:
                sys.exit(f"{feed['url']} -> HTTP {status}")
        feed.update({k: manifest["feeds"][feed["id"]][k] for k in ("http_status", "bytes", "fetched_utc")})
    return manifest


def normalise(feed, provinces):
    """One harmonised record per CSV row."""
    rows = []
    with open(RAW / feed["file"], newline="") as fh:
        for r in csv.DictReader(fh):
            lat, lon = float(r["latitude"]), float(r["longitude"])
            t = dt.datetime.strptime(r["acq_date"] + r["acq_time"].zfill(4), "%Y-%m-%d%H%M")
            modis = feed["sensor"] == "MODIS"
            rows.append({
                "lat": lat, "lon": lon,
                "t_utc": t.isoformat() + "Z",
                "utc_date": r["acq_date"],
                "date": (t + dt.timedelta(hours=LOCAL_OFFSET_H)).date().isoformat(),
                "sensor": feed["sensor"], "feed": feed["id"],
                "platform": PLATFORM.get(r["satellite"], r["satellite"]),
                "bt_fire_k": float(r["brightness" if modis else "bright_ti4"]),
                "bt_bg_k": float(r["bright_t31" if modis else "bright_ti5"]),
                "frp_mw": float(r["frp"]),
                "daynight": r["daynight"],
                "pixel_km": [float(r["scan"]), float(r["track"])],
                "conf_raw": r["confidence"],
                "conf_class": conf_class(feed["sensor"], r["confidence"]),
                "cell": (math.floor(lat / CELL), math.floor(lon / CELL)),
                "province": province_of(lat, lon, provinces),
            })
    return rows


# ---------- weather ----------

def fetch_weather(provinces, dates, offline):
    path = RAW / "weather.json"
    if offline:
        return json.load(open(path))
    start = dt.date.fromisoformat(dates[0]) - dt.timedelta(days=WEATHER_LOOKBACK)
    end = dt.date.fromisoformat(dates[-1])
    raw = {"fetched_utc": now_utc().isoformat(), "start": start.isoformat(), "end": end.isoformat(), "provinces": {}}
    for p in provinces:
        lat, lon = p["centroid"]
        purl = POWER_URL.format(lat=lat, lon=lon, start=start.strftime("%Y%m%d"), end=end.strftime("%Y%m%d"))
        ourl = OPENMETEO_URL.format(lat=lat, lon=lon, start=start.isoformat(), end=end.isoformat())
        ps, pbody = curl(purl)
        os_, obody = curl(ourl)
        raw["provinces"][p["id"]] = {
            "power": {"url": purl, "http_status": ps, "body": json.loads(pbody) if ps == 200 else None},
            "open_meteo": {"url": ourl, "http_status": os_, "body": json.loads(obody) if os_ == 200 else None},
        }
    path.write_text(json.dumps(raw, separators=(",", ":")))
    return raw


def daily_weather(raw_p):
    """date -> {wind_from_deg, wind_ms, precip_mm, source}. NASA POWER first; Open-Meteo only fills its gaps."""
    out = {}
    power = raw_p["power"]["body"]
    if power:
        par = power["properties"]["parameter"]
        fill = power["header"]["fill_value"]
        for key, wd in par["WD10M"].items():
            ws, pr = par["WS10M"][key], par["PRECTOTCORR"][key]
            if fill in (wd, ws, pr):
                continue
            out[f"{key[:4]}-{key[4:6]}-{key[6:]}"] = {
                "wind_from_deg": wd, "wind_ms": ws, "precip_mm": pr, "source": "NASA POWER"}
    om = raw_p["open_meteo"]["body"]
    if om:
        d = om["daily"]
        for i, day in enumerate(d["time"]):
            vals = (d["wind_direction_10m_dominant"][i], d["wind_speed_10m_max"][i], d["precipitation_sum"][i])
            if day in out or None in vals:
                continue
            out[day] = {"wind_from_deg": vals[0], "wind_ms": vals[1], "precip_mm": vals[2], "source": "Open-Meteo"}
    return out


def dry_days(weather, date):
    """Consecutive days up to and including `date` under DRY_MM of rain, capped. None if that day is unknown."""
    if date not in weather:
        return None
    n, d = 0, dt.date.fromisoformat(date)
    while n < DRY_CAP and d.isoformat() in weather and weather[d.isoformat()]["precip_mm"] < DRY_MM:
        n += 1
        d -= dt.timedelta(days=1)
    return n


# ---------- build ----------

def main():
    offline = "--offline" in sys.argv
    RAW.mkdir(parents=True, exist_ok=True)
    provinces = load_provinces()
    manifest = fetch_feeds(offline)

    rows = []
    for feed in FEEDS:
        feed_rows = normalise(feed, provinces)
        feed["rows"] = len(feed_rows)
        manifest["feeds"][feed["id"]].update(rows=len(feed_rows), url=feed["url"], path=f"data/raw/{feed['file']}")
        rows += feed_rows
    if not rows:
        sys.exit("no detections in any feed")

    dates = sorted({r["date"] for r in rows})
    weather_raw = fetch_weather(provinces, dates, offline)
    manifest["weather"] = {
        "fetched_utc": weather_raw["fetched_utc"],
        "file": "data/raw/weather.json",
        "requests": {pid: {src: {"url": v[src]["url"], "http_status": v[src]["http_status"]}
                           for src in ("power", "open_meteo")}
                     for pid, v in weather_raw["provinces"].items()},
    }
    (DATA / "manifest.json").write_text(json.dumps(manifest, indent=1))

    kept = [r for r in rows if r["conf_class"] != "low"]   # default filter: nominal + high

    # active fire cells: (date, cell) -> set of sensors, and the province that owns most of its detections
    cell_sensors, cell_prov = {}, {}
    for r in kept:
        key = (r["date"], r["cell"])
        cell_sensors.setdefault(key, set()).add(r["sensor"])
        cell_prov.setdefault(key, {}).setdefault(r["province"], 0)
        cell_prov[key][r["province"]] += 1
    cell_owner = {k: max(v.items(), key=lambda kv: kv[1])[0] for k, v in cell_prov.items()}

    def provenance(sensors):
        return "both" if len(sensors) == 2 else "modis_only" if "MODIS" in sensors else "viirs_only"

    def cell_summary(keys):
        c = {"cells": 0, "modis_only": 0, "viirs_only": 0, "both": 0}
        for k in keys:
            c["cells"] += 1
            c[provenance(cell_sensors[k])] += 1
        return c

    def det_summary(rs):
        return {
            "detections": len(rs),
            "modis": sum(r["sensor"] == "MODIS" for r in rs),
            "viirs": sum(r["sensor"] == "VIIRS" for r in rs),
            "frp_mw": round(sum(r["frp_mw"] for r in rs), 1),
        }

    prov_out, aligned_total, weather_sources = [], 0, set()
    for p in provinces:
        weather = daily_weather(weather_raw["provinces"][p["id"]])
        daily = []
        for d in dates:
            keys = [k for k, owner in cell_owner.items() if owner == p["id"] and k[0] == d]
            rs = [r for r in kept if r["province"] == p["id"] and r["date"] == d]
            day = {"date": d, **cell_summary(keys), **det_summary(rs),
                   "low_filtered": sum(r["province"] == p["id"] and r["date"] == d and r["conf_class"] == "low" for r in rows)}
            w = weather.get(d)
            if w:
                toward = (w["wind_from_deg"] + 180) % 360
                theta = abs((toward - p["bearing_deg"] + 180) % 360 - 180)
                align = max(0.0, math.cos(math.radians(theta)))
                dd = dry_days(weather, d)
                index = day["cells"] * align * (0.5 + 0.5 * dd / DRY_CAP)
                aligned = day["cells"] >= 1 and align >= ALIGN_MIN
                weather_sources.add(w["source"])
                day.update(wind_from_deg=round(w["wind_from_deg"]), wind_toward_deg=round(toward),
                           wind_ms=round(w["wind_ms"], 1), precip_mm=round(w["precip_mm"], 1),
                           weather_source=w["source"], wind_alignment=round(align, 2), dry_days=dd,
                           index=round(index, 2), aligned=aligned)
                aligned_total += aligned
            else:
                day.update(weather_source=None, wind_alignment=None, dry_days=None, index=None, aligned=None)
            daily.append(day)
        prov_out.append({k: p[k] for k in ("id", "name", "group", "centroid", "dist_km", "bearing_deg")} | {
            "daily": daily,
            "total_cells": sum(x["cells"] for x in daily),
            "total_detections": sum(x["detections"] for x in daily),
            "aligned_days": sum(bool(x["aligned"]) for x in daily),
        })

    focus_ids = {p["id"] for p in provinces}
    elsewhere = [{"date": d, **cell_summary([k for k, o in cell_owner.items() if o is None and k[0] == d])} for d in dates]
    all_cells = cell_summary(cell_sensors)
    focus_cells = cell_summary([k for k, o in cell_owner.items() if o in focus_ids])

    lat0, lat1, lon0, lon1 = MAP_BBOX
    in_box = lambda lat, lon: lat0 <= lat <= lat1 and lon0 <= lon <= lon1
    points = [[round(r["lat"], 3), round(r["lon"], 3), dates.index(r["date"]),
               0 if r["sensor"] == "MODIS" else 1, 1 if r["conf_class"] == "high" else 0]
              for r in kept if in_box(r["lat"], r["lon"])]
    cells = [[round(c[0] * CELL, 1), round(c[1] * CELL, 1), dates.index(d),
              ["modis_only", "viirs_only", "both"].index(provenance(s))]
             for (d, c), s in cell_sensors.items() if in_box(c[0] * CELL, c[1] * CELL)]

    fetched = max(dt.datetime.fromisoformat(manifest["feeds"][f["id"]]["fetched_utc"]) for f in FEEDS)
    fetched_sgt = (fetched + dt.timedelta(hours=8)).strftime("%Y-%m-%d %H:%M SGT")
    conf = {s: {c: sum(r["sensor"] == s and r["conf_class"] == c for r in rows) for c in ("low", "nominal", "high")}
            for s in ("MODIS", "VIIRS")}
    feeds_out = [{k: f[k] for k in ("id", "sensor", "label", "dataset", "url", "http_status", "bytes", "rows", "fetched_utc")}
                 for f in FEEDS]
    params = {"cell_deg": CELL, "local_day_utc_offset_h": LOCAL_OFFSET_H, "dry_day_mm": DRY_MM,
              "dry_day_cap": DRY_CAP, "aligned_min_alignment": ALIGN_MIN,
              "modis_confidence_breaks": {"low": "0-29", "nominal": "30-79", "high": "80-100"},
              "default_filter": "nominal + high"}

    snapshot = {
        "meta": {"fetched_utc": fetched.isoformat(), "fetched_sgt": fetched_sgt, "dates": dates,
                 "window_start": dates[0], "window_end": dates[-1], "singapore": SG, "map_bbox": MAP_BBOX,
                 "weather_fetched_utc": weather_raw["fetched_utc"], "weather_sources": sorted(weather_sources)},
        "params": params, "feeds": feeds_out, "confidence": conf,
        "cells_total": all_cells, "cells_focus": focus_cells,
        "provinces": prov_out, "elsewhere": elsewhere,
        "aligned_days_total": aligned_total, "province_days_total": len(provinces) * len(dates),
        "points": points, "cells": cells,
    }
    snapshot["harmonisation"] = {}
    # ---------- facts.json: every number the deck may quote ----------
    def frp_stats(rs):
        v = [r["frp_mw"] for r in rs]
        return {"rows": len(v), "frp_total_mw": round(sum(v), 1),
                "frp_median_mw": round(statistics.median(v), 2) if v else None,
                "frp_max_mw": max(v) if v else None}

    by_feed = {}
    for f in FEEDS:
        rs = [r for r in rows if r["feed"] == f["id"]]
        by_feed[f["id"]] = {
            "dataset": f["dataset"], "url": f["url"], "file": f"data/raw/{f['file']}",
            "http_status": f["http_status"], "bytes": f["bytes"], "fetched_utc": f["fetched_utc"],
            "empty": not rs, **frp_stats(rs),
            "rows_by_acq_date_utc": {d: sum(r["utc_date"] == d for r in rs) for d in sorted({r["utc_date"] for r in rs})},
            "rows_by_platform": {pl: sum(r["platform"] == pl for r in rs) for pl in sorted({r["platform"] for r in rs})},
            "rows_by_confidence": {c: sum(r["conf_class"] == c for r in rs) for c in ("low", "nominal", "high")},
            "rows_in_focus_provinces": sum(r["province"] in focus_ids for r in rs),
            "lat_range": [min(r["lat"] for r in rs), max(r["lat"] for r in rs)] if rs else None,
            "lon_range": [min(r["lon"] for r in rs), max(r["lon"] for r in rs)] if rs else None,
        }

    top = max(prov_out, key=lambda p: p["total_cells"])
    quiet = min(prov_out, key=lambda p: p["aligned_days"])
    power_days = sorted({x["date"] for p in prov_out for x in p["daily"] if x["weather_source"] == "NASA POWER"})
    om_days = sorted({x["date"] for p in prov_out for x in p["daily"] if x["weather_source"] == "Open-Meteo"})
    focus_rows = [r for r in rows if r["province"] in focus_ids]
    facts = {
        "generated_utc": now_utc().isoformat(),
        "fetch_time_utc": fetched.isoformat(), "fetch_time_sgt": fetched_sgt,
        "window_start": dates[0], "window_end": dates[-1], "calendar_dates_utc7": dates,
        "note_window": "FIRMS '7d' files span 7 x 24 h of UTC acquisitions; binned to local dates at UTC+7 "
                       "this can touch more than 7 calendar dates, and the first and last are partial days.",
        "parameters": params,
        "feeds": by_feed,
        "modis_rows": by_feed["modis"]["rows"], "viirs_snpp_rows": by_feed["viirs_snpp"]["rows"],
        "noaa20_rows": by_feed["viirs_noaa20"]["rows"], "noaa21_rows": by_feed["viirs_noaa21"]["rows"],
        "total_rows": len(rows), "all_sensors": frp_stats(rows),
        "rows_low": sum(r["conf_class"] == "low" for r in rows),
        "rows_nominal": sum(r["conf_class"] == "nominal" for r in rows),
        "rows_high": sum(r["conf_class"] == "high" for r in rows),
        "rows_by_sensor_and_confidence": conf,
        "active_cell_days": all_cells["cells"], "cell_days_provenance_all": all_cells,
        "focus_cell_days": focus_cells["cells"], "cell_days_provenance_focus": focus_cells,
        "elsewhere_cell_days": sum(e["cells"] for e in elsewhere),
        "raw_ratio_viirs_to_modis_detections": round(
            (conf["VIIRS"]["nominal"] + conf["VIIRS"]["high"]) / max(1, conf["MODIS"]["nominal"] + conf["MODIS"]["high"]), 1),
        "cell_ratio_viirs_to_modis": round(
            (all_cells["viirs_only"] + all_cells["both"]) / max(1, all_cells["modis_only"] + all_cells["both"]), 1),
        "modis_cells_also_seen_by_viirs_pct": round(
            100 * all_cells["both"] / max(1, all_cells["modis_only"] + all_cells["both"]), 1),
        "cells_seen_by_modis": all_cells["modis_only"] + all_cells["both"],
        "cells_seen_by_viirs": all_cells["viirs_only"] + all_cells["both"],
        "focus_provinces": {p["id"]: {
            "name": p["name"], "group": p["group"], "centroid_lat_lon": p["centroid"],
            "distance_to_singapore_km": p["dist_km"], "bearing_to_singapore_deg": p["bearing_deg"],
            "cell_days": p["total_cells"], "detections_nominal_high": p["total_detections"],
            "aligned_days": p["aligned_days"],
            "frp_total_mw": round(sum(x["frp_mw"] for x in p["daily"]), 1),
            "by_date": {x["date"]: {k: x[k] for k in ("cells", "modis_only", "viirs_only", "both", "detections",
                                                       "modis", "viirs", "frp_mw", "wind_from_deg", "wind_alignment",
                                                       "precip_mm", "dry_days", "index", "aligned", "weather_source")
                                    if k in x} for x in p["daily"]},
        } for p in prov_out},
        "focus_rows_all_confidence": frp_stats(focus_rows),
        "top_province": top["name"], "top_province_cell_days": top["total_cells"],
        "aligned_days_total": aligned_total, "province_days_total": len(provinces) * len(dates),
        "province_days_with_weather": sum(x["weather_source"] is not None for p in prov_out for x in p["daily"]),
        "example_province": quiet["name"],
        "example_days_away": sum(x["wind_alignment"] == 0 for x in quiet["daily"]),
        "weather_source": " + ".join(sorted(weather_sources)),
        "weather": {"fetched_utc": weather_raw["fetched_utc"], "nasa_power_dates": power_days,
                    "open_meteo_gap_fill_dates": om_days,
                    "requests": manifest["weather"]["requests"]},
        "step0_checks": {
            "viirs_snpp_feed_empty": by_feed["viirs_snpp"]["empty"],
            "viirs_noaa20_feed_populated": not by_feed["viirs_noaa20"]["empty"],
            "viirs_noaa21_feed_populated": not by_feed["viirs_noaa21"]["empty"],
            "nasa_power_returns_wd10m_ws10m_prectotcorr": bool(power_days),
            "nasa_power_latest_date": power_days[-1] if power_days else None,
            "nasa_power_missing_dates_in_window": [d for d in dates if d not in power_days],
            "open_meteo_fallback_used": bool(om_days),
            "province_polygons": "Natural Earth 10m admin-1, 6 provinces (data/provinces.geojson)",
        },
    }
    (DATA / "facts.json").write_text(json.dumps(facts, indent=1))
    snapshot["harmonisation"] = {k: facts[k] for k in (
        "raw_ratio_viirs_to_modis_detections", "cell_ratio_viirs_to_modis", "modis_cells_also_seen_by_viirs_pct",
        "rows_low", "rows_nominal", "rows_high", "total_rows")}
    snapshot["feed_stats"] = {k: {x: v[x] for x in ("frp_total_mw", "frp_median_mw", "rows_in_focus_provinces")}
                              for k, v in by_feed.items()}
    (DATA / "snapshot.json").write_text(json.dumps(snapshot, separators=(",", ":")))

    print(f"fetched {fetched_sgt} | dates {dates[0]}..{dates[-1]} ({len(dates)})")
    for f in FEEDS:
        print(f"  {f['label']:28s} {f['rows']:6d} rows")
    print(f"  cell-days: all {all_cells} | focus {focus_cells}")
    for p in prov_out:
        print(f"  {p['name']:20s} cells {[x['cells'] for x in p['daily']]} aligned {p['aligned_days']} "
              f"dist {p['dist_km']} km bearing {p['bearing_deg']}")
    print(f"  aligned province-days {aligned_total}/{len(provinces) * len(dates)} | weather {sorted(weather_sources)}")
    print(f"  map points {len(points)}, cells {len(cells)}, snapshot {(DATA / 'snapshot.json').stat().st_size} bytes")


if __name__ == "__main__":
    main()
