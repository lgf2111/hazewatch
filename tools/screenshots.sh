#!/bin/sh
# Take the deck screenshots from a running copy of the site.
# Usage: tools/screenshots.sh [base-url]   (default: http://localhost:8765, i.e. `python3 -m http.server 8765` in the repo root)
BASE="${1:-http://localhost:8765}"
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
OUT="$(cd "$(dirname "$0")/.." && pwd)/docs/screenshots"
mkdir -p "$OUT"

desktop() { # name query
  "$CHROME" --headless=new --hide-scrollbars --virtual-time-budget=15000 \
    --window-size=1440,900 --screenshot="$OUT/$1.png" "$BASE/?$2" >/dev/null 2>&1
}
phone() { # name query  -> 390x844 CSS px at 2x
  "$CHROME" --headless=new --hide-scrollbars --virtual-time-budget=15000 --force-device-scale-factor=2 \
    --window-size=500,844 --screenshot="$OUT/$1.png" "$BASE/tools/phone-frame.html?$2" >/dev/null 2>&1
  sips -c 1688 780 "$OUT/$1.png" >/dev/null
}

desktop desktop-calendar      "view=calendar"
desktop desktop-map-raw       "view=map"
desktop desktop-map-cells     "view=map&mode=cells"
desktop desktop-wind          "view=wind&p=south-sumatra"
desktop desktop-data-limits   "view=data"
phone   phone-calendar        "view=calendar"
phone   phone-map             "view=map&mode=cells"
phone   phone-wind            "view=wind&p=south-sumatra"
phone   phone-data-limits     "view=data"
ls -l "$OUT"
