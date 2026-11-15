#!/usr/bin/env python3
"""One-off: cut the six focus provinces out of Natural Earth admin-1.

Usage:
  curl -LO https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_10m_admin_1_states_provinces.geojson
  python3 tools/extract_provinces.py ne_10m_admin_1_states_provinces.geojson

Writes data/provinces.geojson (committed; the snapshot build reads it).
"""
import json
import pathlib
import sys

FOCUS = {
    "ID-RI": ("riau", "Riau", "Sumatra"),
    "ID-JA": ("jambi", "Jambi", "Sumatra"),
    "ID-SS": ("south-sumatra", "South Sumatra", "Sumatra"),
    "ID-KB": ("west-kalimantan", "West Kalimantan", "Kalimantan"),
    "ID-KT": ("central-kalimantan", "Central Kalimantan", "Kalimantan"),
    "ID-KS": ("south-kalimantan", "South Kalimantan", "Kalimantan"),
}


def rounded(coords):
    if isinstance(coords[0], (int, float)):
        return [round(coords[0], 3), round(coords[1], 3)]
    return [rounded(c) for c in coords]


def main():
    src = json.load(open(sys.argv[1]))
    feats = {}
    for f in src["features"]:
        code = f["properties"].get("iso_3166_2")
        if code in FOCUS:
            pid, name, group = FOCUS[code]
            feats[code] = {
                "type": "Feature",
                "properties": {"id": pid, "name": name, "group": group, "iso_3166_2": code},
                "geometry": {"type": f["geometry"]["type"], "coordinates": rounded(f["geometry"]["coordinates"])},
            }
    missing = set(FOCUS) - set(feats)
    if missing:
        sys.exit(f"missing provinces: {missing}")
    out = pathlib.Path(__file__).resolve().parent.parent / "data" / "provinces.geojson"
    out.write_text(json.dumps({
        "type": "FeatureCollection",
        "source": "Natural Earth 10m admin-1 states and provinces (public domain), coordinates rounded to 3 dp",
        "features": [feats[c] for c in FOCUS],
    }, separators=(",", ":")))
    print(f"wrote {out} ({out.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
