/* HazeWatch — renders data/snapshot.json. No number is computed here that is not in the snapshot. */
(function () {
  "use strict";
  const $ = (id) => document.getElementById(id);
  const fmt = (n) => Number(n).toLocaleString("en-SG");
  const params = new URLSearchParams(location.search);
  const VIEWS = ["calendar", "map", "wind", "data"];
  const DOW = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
  const MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  const BINS = [[0, 0, "0"], [1, 4, "1–4"], [5, 14, "5–14"], [15, 29, "15–29"], [30, 59, "30–59"], [60, Infinity, "60+"]];
  const HEAT = ["#ece7db", "#fde2bd", "#f8b96e", "#ee8532", "#cf4d1a", "#8f2410"];
  const SENSOR_COL = ["#ffd23f", "#ff4d2e"];           // MODIS, VIIRS
  const CELL_COL = ["#ffd23f", "#ff4d2e", "#ffffff"];  // MODIS only, VIIRS only, both
  let S, GEO, map, mapLayer, mapMode = "points";
  let view = VIEWS.includes(params.get("view")) ? params.get("view") : "calendar";
  let prov = params.get("p");

  const dparts = (iso) => { const d = new Date(iso + "T00:00:00Z"); return { dow: DOW[d.getUTCDay()], day: d.getUTCDate(), mon: MON[d.getUTCMonth()] }; };
  const dlabel = (iso) => { const p = dparts(iso); return p.day + " " + p.mon; };
  const bin = (n) => BINS.findIndex((b) => n >= b[0] && n <= b[1]);
  const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

  Promise.all([
    fetch("data/snapshot.json").then((r) => r.json()),
    fetch("data/provinces.geojson").then((r) => r.json()),
  ]).then(([s, g]) => { S = s; GEO = g; init(); }).catch((e) => {
    $("stamp").textContent = "Could not load data/snapshot.json: " + e.message;
  });

  function init() {
    if (!S.provinces.some((p) => p.id === prov)) {
      prov = S.provinces.slice().sort((a, b) => b.total_cells - a.total_cells)[0].id;
    }
    renderHeader();
    renderCalendar();
    renderWind();
    renderData();
    document.querySelectorAll(".tabs a").forEach((a) => a.addEventListener("click", (e) => {
      e.preventDefault(); show(a.dataset.view, true);
    }));
    $("cal-sensor").addEventListener("change", renderCalendar);
    show(view, false);
  }

  function show(v, push) {
    view = v;
    VIEWS.forEach((x) => { $("view-" + x).hidden = x !== v; });
    document.querySelectorAll(".tabs a").forEach((a) => a.classList.toggle("on", a.dataset.view === v));
    if (push) history.pushState(null, "", "?view=" + v + (v === "wind" ? "&p=" + prov : ""));
    if (v === "map") renderMap();
  }

  /* ---------- header ---------- */
  function renderHeader() {
    const m = S.meta;
    $("stamp").innerHTML = "NASA FIRMS 7-day active-fire files · fetched <b>" + esc(m.fetched_sgt) + "</b> · acquisitions <b>" +
      dlabel(m.window_start) + " – " + dlabel(m.window_end) + " " + m.window_end.slice(0, 4) + "</b> (UTC+7 dates)";
    $("chips").innerHTML = S.feeds.map((f) =>
      '<li class="' + (f.rows ? "" : "empty") + '">' + esc(f.label.replace(" (Terra + Aqua)", "").replace(/ C2$/, "")) + " · <b>" + fmt(f.rows) + "<span class='r'> rows</span></b>" + (f.rows ? "" : " · empty") + "</li>").join("");
    const empty = S.feeds.filter((f) => !f.rows).map((f) => f.label);
    $("limits-bar").innerHTML = "<b>Prototype.</b> 7-day snapshot only, no archive" +
      (empty.length ? " · " + esc(empty.join(", ")) + " feed returned 0 rows" : "") +
      " · wind alignment is an unvalidated heuristic, not a haze forecast.";
  }

  /* ---------- calendar ---------- */
  function cellCount(d, mode) {
    return mode === "modis" ? d.modis_only + d.both : mode === "viirs" ? d.viirs_only + d.both : d.cells;
  }

  function renderCalendar() {
    const mode = $("cal-sensor").value, dates = S.meta.dates;
    const last = dates.length - 1;
    let html = "<thead><tr><th class='name'></th>" + dates.map((d, i) => {
      const p = dparts(d);
      return "<th class='" + (i === 0 || i === last ? "partial" : "") + "'>" + p.dow + "<b>" + p.day + "</b></th>";
    }).join("") + "</tr></thead><tbody>";
    let group = "", focus = 0;
    S.provinces.forEach((p) => {
      if (p.group !== group) { group = p.group; html += "<tr class='group'><th colspan='" + (dates.length + 1) + "'>" + esc(group) + "</th></tr>"; }
      const total = p.daily.reduce((a, d) => a + cellCount(d, mode), 0);
      focus += total;
      html += "<tr><th class='name' data-p='" + p.id + "'>" + esc(p.name) + "<small>" + fmt(total) + " cell-days</small></th>" +
        p.daily.map((d) => {
          const n = cellCount(d, mode);
          const w = d.weather_source === null ? "<i class='w nw' title='no wind data'></i>" : d.aligned ? "<i class='w al' title='wind towards Singapore'></i>" : "";
          return "<td><div class='c b" + bin(n) + "' title='" + esc(p.name) + ", " + dlabel(d.date) + ": " + n + " burning cells'>" + n + w + "</div></td>";
        }).join("") + "</tr>";
    });
    const elseTotal = S.elsewhere.reduce((a, d) => a + cellCount(d, mode), 0);
    html += "<tr class='group'><th colspan='" + (dates.length + 1) + "'>Not in the six provinces</th></tr>" +
      "<tr class='else'><th class='name'>Rest of SE Asia<small>" + fmt(elseTotal) + " cell-days</small></th>" +
      S.elsewhere.map((d) => "<td><div class='c'>" + fmt(cellCount(d, mode)) + "</div></td>").join("") + "</tr></tbody>";
    $("cal").innerHTML = html;
    $("cal").querySelectorAll("th.name[data-p]").forEach((th) => th.addEventListener("click", () => { prov = th.dataset.p; renderWind(); show("wind", true); }));

    const top = S.provinces.slice().sort((a, b) => b.total_cells - a.total_cells)[0];
    $("cal-lede").innerHTML = "<b>" + fmt(S.cells_focus.cells) + "</b> burning cell-days in six provinces, out of <b>" + fmt(S.cells_total.cells) +
      "</b> across South-East Asia. Most active: <b>" + esc(top.name) + ", " + fmt(top.total_cells) + "</b>. Each square is one province-day; the number is 0.1° grid cells with a nominal- or high-confidence hot spot.";
    $("cal-legend").innerHTML = BINS.map((b, i) => "<span><i style='background:" + HEAT[i] + "'></i>" + b[2] + "</span>").join("") +
      "<span><i class='bar'></i>fire + wind within 60° of Singapore (heuristic)</span>";
    const sensorNote = mode === "all" ? "" : " Showing cells seen by " + (mode === "modis" ? "MODIS" : "VIIRS") + " only: " + fmt(focus) + " cell-days in the six provinces.";
    $("cal-note").textContent = "* First and last columns are partial days: the 7-day files cover 7 × 24 h in UTC, which touches " + dates.length +
      " local dates. Hot spots are thermal anomalies; some are not vegetation fires. Cloud can hide fires, so 0 can mean “not observed”." + sensorNote + " Tap a province for its wind window.";
  }

  /* ---------- wind windows ---------- */
  function arrow(deg, strong) {
    return "<svg width='22' height='22' viewBox='-11 -11 22 22' aria-hidden='true'><g transform='rotate(" + deg + ")'>" +
      "<path d='M0 8V-6M0 -8l-4.5 6h9z' stroke='" + (strong ? "#0f6b74" : "#6a645b") + "' fill='" + (strong ? "#0f6b74" : "#6a645b") + "' stroke-width='1.8' stroke-linecap='round'/></g></svg>";
  }

  function renderWind() {
    const p = S.provinces.find((x) => x.id === prov);
    $("wind-provs").innerHTML = S.provinces.map((x) => "<button type='button' data-p='" + x.id + "' class='" + (x.id === prov ? "on" : "") + "'>" + esc(x.name) + "</button>").join("");
    $("wind-provs").querySelectorAll("button").forEach((b) => b.addEventListener("click", () => {
      prov = b.dataset.p; renderWind(); history.replaceState(null, "", "?view=wind&p=" + prov);
    }));
    $("wind-lede").innerHTML = "<b>" + S.aligned_days_total + " of " + S.province_days_total + "</b> province-days had fire burning and surface wind blowing within 60° of the line to Singapore. " +
      "<b>" + esc(p.name) + ": " + p.aligned_days + " of " + p.daily.length + "</b> days.";
    $("wind-geo").innerHTML = esc(p.name) + " centroid is <b>" + fmt(p.dist_km) + " km</b> from Singapore; Singapore lies at bearing <b>" + p.bearing_deg + "°</b> " +
      "<span style='display:inline-block;vertical-align:middle'>" + arrow(p.bearing_deg, true) + "</span>";
    const head = "<thead><tr><th class='rl'></th>" + p.daily.map((d) => { const x = dparts(d.date); return "<th>" + x.dow + "<b>" + x.day + "</b></th>"; }).join("") + "</tr></thead>";
    const row = (label, sub, fn) => "<tr><th class='rl'>" + label + "<small>" + sub + "</small></th>" + p.daily.map(fn).join("") + "</tr>";
    const na = "<td class='na'>–<small>no data</small></td>";
    $("wind").innerHTML = head + "<tbody>" +
      row("Fire", "burning cells", (d) => "<td class='" + (d.aligned ? "al" : "") + "'><span class='fire'>" + d.cells + "</span><small>" + d.modis + " M<br>" + d.viirs + " V</small></td>") +
      row("Wind", "blowing towards · alignment 0–1", (d) => d.weather_source === null ? na :
        "<td class='" + (d.aligned ? "al" : "") + "'>" + arrow(d.wind_toward_deg, d.wind_alignment >= S.params.aligned_min_alignment) + d.wind_alignment.toFixed(2) +
        "<small>" + d.wind_ms + " m/s" + (d.weather_source === "Open-Meteo" ? "†" : "") + "</small></td>") +
      row("Dry spell", "days under " + S.params.dry_day_mm + " mm · rain that day", (d) => d.weather_source === null ? na :
        "<td class='" + (d.aligned ? "al" : "") + "'>" + d.dry_days + "<small>" + d.precip_mm + " mm</small></td>") +
      row("Index", "fire × wind × dry factor", (d) => d.weather_source === null ? na :
        "<td class='" + (d.aligned ? "al" : "") + "'>" + d.index.toFixed(1) + (d.aligned ? "<small><span class='badge'>aligned</span></small>" : "<small>&nbsp;</small>") + "</td>") +
      "</tbody>";
    const om = p.daily.filter((d) => d.weather_source === "Open-Meteo").map((d) => dlabel(d.date));
    $("wind-note").textContent = "Fire: NASA FIRMS; M = MODIS detections, V = VIIRS detections (nominal + high). Wind and rain at the province centroid: NASA POWER (WD10M, WS10M, PRECTOTCORR)." +
      (om.length ? " † NASA POWER had no values yet for " + om.join(", ") + "; those days use Open-Meteo, which reports daily maximum wind speed and dominant direction, so they are not strictly comparable." : "");
  }

  /* ---------- map ---------- */
  function renderMap() {
    if (!map) {
      const b = S.meta.map_bbox;
      map = L.map("map", { preferCanvas: true, zoomSnap: 0.25, minZoom: 4, maxZoom: 8, maxBounds: [[b[0] - 16, b[2] - 12], [b[1] + 16, b[3] + 12]] });
      map.fitBounds([[-5.2, 99.0], [4.2, 118.6]]);
      L.tileLayer("https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/BlueMarble_ShadedRelief_Bathymetry/default/GoogleMapsCompatible_Level8/{z}/{y}/{x}.jpeg",
        { maxNativeZoom: 8, attribution: "Imagery: NASA GIBS · Fire: NASA FIRMS · Boundaries: Natural Earth" }).addTo(map);
      L.geoJSON(GEO, { style: { color: "#ffffff", weight: 1.4, fillColor: "#ffffff", fillOpacity: 0.07 }, interactive: false }).addTo(map);
      S.provinces.forEach((p) => {
        L.tooltip({ permanent: true, direction: "center", className: "prov-label" }).setLatLng(p.centroid)
          .setContent(esc(p.name) + " · " + fmt(p.total_cells)).addTo(map);
      });
      L.circleMarker(S.meta.singapore, { radius: 6, color: "#111", weight: 2, fillColor: "#fff", fillOpacity: 1 }).addTo(map)
        .bindTooltip("Singapore", { permanent: true, direction: "top", className: "sg-label", offset: [0, -6] });
      $("map-day").innerHTML = "<option value='-1'>All " + S.meta.dates.length + " dates</option>" + S.meta.dates.map((d, i) => "<option value='" + i + "'>" + dlabel(d) + "</option>").join("");
      $("map-day").addEventListener("change", drawMapLayer);
      $("map-mode").querySelectorAll("button").forEach((btn) => btn.addEventListener("click", () => {
        mapMode = btn.dataset.mode;
        $("map-mode").querySelectorAll("button").forEach((x) => x.classList.toggle("on", x === btn));
        drawMapLayer();
      }));
      if (params.get("mode") === "cells") { mapMode = "cells"; $("map-mode").querySelectorAll("button").forEach((x) => x.classList.toggle("on", x.dataset.mode === "cells")); }
    }
    setTimeout(() => map.invalidateSize(), 0);
    drawMapLayer();
  }

  function drawMapLayer() {
    const day = +$("map-day").value, c = S.params.cell_deg;
    if (mapLayer) map.removeLayer(mapLayer);
    mapLayer = L.layerGroup();
    const renderer = L.canvas({ padding: 0.3 });
    let n = 0, counts = [0, 0, 0];
    if (mapMode === "points") {
      // MODIS drawn last so its fewer, larger footprints stay visible over VIIRS
      [1, 0].forEach((sensor) => S.points.forEach((p) => {
        if (p[3] !== sensor || (day >= 0 && p[2] !== day)) return;
        n++; counts[sensor]++;
        L.circleMarker([p[0], p[1]], { renderer, radius: sensor === 0 ? 3.2 : 1.8, stroke: sensor === 0, color: "#3a2a00", weight: 0.6, fillColor: SENSOR_COL[sensor], fillOpacity: 0.9, interactive: false }).addTo(mapLayer);
      }));
      $("map-legend").innerHTML = "<span><i class='dot' style='background:" + SENSOR_COL[0] + "'></i>MODIS 1 km · " + fmt(counts[0]) + "</span>" +
        "<span><i class='dot' style='background:" + SENSOR_COL[1] + "'></i>VIIRS 375 m · " + fmt(counts[1]) + "</span><span>detections in this map window</span>";
    } else {
      S.cells.forEach((p) => {
        if (day >= 0 && p[2] !== day) return;
        n++; counts[p[3]]++;
        L.rectangle([[p[0], p[1]], [p[0] + c, p[1] + c]], { renderer, stroke: false, fillColor: CELL_COL[p[3]], fillOpacity: 0.85, interactive: false }).addTo(mapLayer);
      });
      $("map-legend").innerHTML = ["MODIS only", "VIIRS only", "both sensors"].map((t, i) =>
        "<span><i style='background:" + CELL_COL[i] + ";border:1px solid rgba(0,0,0,.35)'></i>" + t + " · " + fmt(counts[i]) + "</span>").join("") + "<span>cell-days in this map window</span>";
    }
    mapLayer.addTo(map);
    const when = day < 0 ? dlabel(S.meta.window_start) + " – " + dlabel(S.meta.window_end) : dlabel(S.meta.dates[day]);
    $("map-lede").innerHTML = mapMode === "points"
      ? "<b>" + fmt(n) + "</b> MODIS and VIIRS detections around Singapore, " + when + ". The same fire is more dots on the finer sensor."
      : "<b>" + fmt(n) + "</b> burning 0.1° cell-days around Singapore, " + when + ". One cell counts once per day, whichever sensor saw it.";
  }

  /* ---------- data & limits ---------- */
  function renderData() {
    const h = S.harmonisation, t = S.cells_total, empty = S.feeds.filter((f) => !f.rows);
    const om = Array.from(new Set(S.provinces.flatMap((p) => p.daily.filter((d) => d.weather_source === "Open-Meteo").map((d) => d.date)))).sort();
    $("missing").innerHTML =
      empty.map((f) => "<div><b>" + esc(f.label) + ": 0 rows</b>The file returned HTTP " + f.http_status + " with " + f.bytes + " bytes — a header and no detections. We do not know why and draw no conclusion about the sensor. VIIRS data here comes from NOAA-20 and NOAA-21 only.</div>").join("") +
      (om.length ? "<div><b>NASA POWER: " + om.length + " recent dates missing</b>No wind or rain yet for " + om.map(dlabel).join(", ") + " (normal processing lag). Those days are filled from Open-Meteo and marked †.</div>" : "") +
      "<div><b>Archive: not loaded</b>Only this 7-day window is real. No monthly calendar, no year-on-year comparison, no seasonal conclusion can be drawn from it.</div>";

    $("feeds").innerHTML = "<thead><tr><th>Dataset</th><th class='num'>Rows</th><th class='num'>In six provinces</th><th class='num'>Median FRP</th><th class='num'>Total FRP</th></tr></thead><tbody>" +
      S.feeds.map((f) => { const st = S.feed_stats[f.id]; return "<tr class='" + (f.rows ? "" : "empty") + "'><td>" + esc(f.dataset) + "<small>" + esc(f.url) + "</small><small>HTTP " + f.http_status + " · " + fmt(f.bytes) + " bytes · " + esc(f.fetched_utc) + "</small></td>" +
        "<td class='num'>" + fmt(f.rows) + "</td><td class='num'>" + fmt(st.rows_in_focus_provinces) + "</td><td class='num'>" + (st.frp_median_mw === null ? "–" : st.frp_median_mw + " MW") + "</td><td class='num'>" + (f.rows ? fmt(Math.round(st.frp_total_mw)) + " MW" : "–") + "</td></tr>"; }).join("") + "</tbody>";

    $("tiles").innerHTML =
      "<div><b>" + h.raw_ratio_viirs_to_modis_detections + "×</b><span>VIIRS detections per MODIS detection, raw (nominal + high)</span></div>" +
      "<div><b>" + h.cell_ratio_viirs_to_modis + "×</b><span>VIIRS burning cells per MODIS burning cell, on the shared 0.1° grid</span></div>" +
      "<div><b>" + h.modis_cells_also_seen_by_viirs_pct + "%</b><span>of MODIS burning cell-days also seen by VIIRS the same day</span></div>";
    $("harm-note").textContent = "Counting cells instead of dots narrows the gap between the sensors but does not close it: two VIIRS satellites at 375 m detect smaller fires that MODIS at 1 km misses, and overpass times differ. So every cell-day keeps its provenance, and the calendar can be switched to either sensor alone.";
    const parts = [["MODIS only", t.modis_only, CELL_COL[0]], ["VIIRS only", t.viirs_only, CELL_COL[1]], ["Both", t.both, "#1d1b18"]];
    $("prov-bar").innerHTML = "<div class='bar'>" + parts.map((p) => "<i style='width:" + (100 * p[1] / t.cells) + "%;background:" + p[2] + "'></i>").join("") + "</div>" +
      "<div class='legend'>" + parts.map((p) => "<span><i style='background:" + p[2] + "'></i>" + p[0] + " · " + fmt(p[1]) + "</span>").join("") + "<span>of " + fmt(t.cells) + " cell-days, all SE Asia</span></div>";

    const c = S.confidence, br = S.params.modis_confidence_breaks;
    $("conf").innerHTML = "<thead><tr><th>Harmonised class</th><th>MODIS value</th><th class='num'>MODIS rows</th><th>VIIRS value</th><th class='num'>VIIRS rows</th><th>Used</th></tr></thead><tbody>" +
      ["low", "nominal", "high"].map((k) => "<tr><td>" + k + "</td><td>" + br[k] + " %</td><td class='num'>" + fmt(c.MODIS[k]) + "</td><td>" + k + "</td><td class='num'>" + fmt(c.VIIRS[k]) + "</td><td>" + (k === "low" ? "filtered out" : "yes") + "</td></tr>").join("") + "</tbody>";

    const schema = [["lat, lon", "latitude, longitude", "latitude, longitude"], ["t_utc", "acq_date + acq_time", "acq_date + acq_time"],
      ["platform", "satellite (Terra / Aqua)", "satellite (N / N20 / N21)"], ["bt_fire_k", "brightness", "bright_ti4"], ["bt_bg_k", "bright_t31", "bright_ti5"],
      ["frp_mw", "frp", "frp"], ["pixel_km", "scan × track (~1 km)", "scan × track (~375 m)"], ["conf_class", "confidence 0–100 → 3 classes", "confidence low / nominal / high"],
      ["cell, date", "0.1° cell · local date at UTC+7", "0.1° cell · local date at UTC+7"]];
    $("schema").innerHTML = "<thead><tr><th>Harmonised</th><th>MODIS C6.1</th><th>VIIRS C2</th></tr></thead><tbody>" +
      schema.map((r) => "<tr><td><code>" + r[0] + "</code></td><td>" + r[1] + "</td><td>" + r[2] + "</td></tr>").join("") + "</tbody>";

    $("limits").innerHTML = [
      "Seven days of data. Nothing here supports a seasonal or year-on-year claim.",
      "The alignment index is a heuristic with chosen thresholds (" + S.params.dry_day_mm + " mm, " + S.params.dry_day_cap + " days, 60°). It is not a forecast, not PSI, and not validated against air-quality records.",
      "Wind is 10 m surface wind at one point per province. Smoke travels on winds aloft along the whole path; distance is shown but not used in the index.",
      "Hot spots are thermal anomalies. Some are gas flares, industry or volcanoes rather than vegetation fires; we do not filter by type.",
      "Cloud and thick smoke hide fires from both sensors. A zero can mean “not observed”.",
      "MODIS and VIIRS confidence come from different algorithms. Shared labels are a working alignment, not proof of equal reliability.",
      "The 0.1° cell (about 11 km) is a design choice. A cell is assigned to the province holding most of its detections.",
      "Brightness temperatures are carried through but never compared across sensors.",
    ].map((x) => "<li>" + x + "</li>").join("");
  }
})();
