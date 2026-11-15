/* HazeWatch — renders data/snapshot.json. No number is computed here that is not in the snapshot. */
(function () {
  "use strict";
  const $ = (id) => document.getElementById(id);
  const fmt = (n) => Number(n).toLocaleString("en-SG");
  const params = new URLSearchParams(location.search);
  const VIEWS = ["calendar", "map", "wind", "data"];
  const DOW = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
  const MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  const MONTH = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
  const BINS = [[0, 0, "0"], [1, 4, "1–4"], [5, 14, "5–14"], [15, 29, "15–29"], [30, 59, "30–59"], [60, Infinity, "60+"]];
  const HEAT = ["#ece7db", "#fde2bd", "#f8b96e", "#ee8532", "#cf4d1a", "#8f2410"];
  const SENSOR_COL = ["#ffd23f", "#ff4d2e"];           // MODIS, VIIRS
  const CELL_COL = ["#ffd23f", "#ff4d2e", "#ffffff"];  // MODIS only, VIIRS only, both
  let S, GEO, map, mapLayer, mapMode = params.get("mode") === "points" ? "points" : "cells";
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
    const m = S.meta, d0 = new Date(m.window_start + "T00:00:00Z"), d1 = new Date(m.window_end + "T00:00:00Z");
    const sgt = m.fetched_sgt.match(/^(\d{4})-(\d{2})-(\d{2}) (\d{2}:\d{2}) SGT$/);
    const fetched = sgt ? (+sgt[3]) + " " + MON[+sgt[2] - 1] + " " + sgt[1] + ", " + sgt[4] + " SGT" : m.fetched_sgt;
    $("stamp").innerHTML = "NASA satellites · " + d0.getUTCDate() + "–" + d1.getUTCDate() + " " + MONTH[d1.getUTCMonth()] + " " + d1.getUTCFullYear() +
      " · fetched <b>" + esc(fetched) + "</b>";
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
      html += "<tr><th class='name' data-p='" + p.id + "'>" + esc(p.name) + "<small>" + fmt(total) + " squares</small></th>" +
        p.daily.map((d) => {
          const n = cellCount(d, mode);
          const w = d.weather_source === null ? "<i class='w nw' title='no wind data'></i>" : d.aligned ? "<i class='w al' title='wind towards Singapore'></i>" : "";
          return "<td><div class='c b" + bin(n) + "' title='" + esc(p.name) + ", " + dlabel(d.date) + ": " + n + " burning squares'>" + n + w + "</div></td>";
        }).join("") + "</tr>";
    });
    html += "</tbody>";
    $("cal").innerHTML = html;
    $("cal").querySelectorAll("th.name[data-p]").forEach((th) => th.addEventListener("click", () => { prov = th.dataset.p; renderWind(); show("wind", true); }));

    const top = S.provinces.slice().sort((a, b) => b.total_cells - a.total_cells)[0];
    $("cal-lede").innerHTML = "<b>" + fmt(top.total_cells) + " burning squares in " + esc(top.name) + " this week</b> — more than any other province. " +
      "Each column is a day; each square on fire counts once.";
    $("cal-legend").innerHTML = "<span>Burning squares a day</span>" + BINS.map((b, i) => "<span><i style='background:" + HEAT[i] + "'></i>" + b[2] + "</span>").join("") +
      "<span><i class='bar'></i>wind pointing at Singapore</span>";
    $("cal-else").textContent = "The other " + fmt(S.elsewhere.reduce((a, d) => a + d.cells, 0)) + " squares NASA saw this week were outside these six provinces.";
    const sensorNote = mode === "all" ? "" : " Showing squares seen by " + (mode === "modis" ? "MODIS" : "VIIRS") + " only: " + fmt(focus) + " in the six provinces.";
    $("cal-note").textContent = "* First and last days are partial: the files cover 7 × 24 hours of satellite passes, which touch " + dates.length +
      " dates. Cloud can hide fires, so 0 can mean “not seen”." + sensorNote + " Tap a province for its wind window.";
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
    const near = S.provinces.find((x) => x.id === "riau"), far = S.provinces.find((x) => x.id === "south-sumatra");
    $("wind-lede").innerHTML = "<b>The nearest fires were not the ones aimed at us.</b> " + esc(near.name) + " is " + fmt(near.dist_km) + " km away and had " +
      near.total_cells + " burning squares, " + (near.aligned_days === 0 ? "none on a day the wind pointed at Singapore" : "on " + near.aligned_days + " of " + near.daily.length + " days with the wind pointing at Singapore") + ". " +
      esc(far.name) + " is " + fmt(far.dist_km) + " km away, had " + far.total_cells + ", and pointed at us on <b>" + far.aligned_days + " of " + far.daily.length + " days</b>.";
    $("wind-geo").innerHTML = esc(p.name) + " is <b>" + fmt(p.dist_km) + " km</b> from Singapore; Singapore lies at bearing <b>" + p.bearing_deg + "°</b> " +
      "<span style='display:inline-block;vertical-align:middle'>" + arrow(p.bearing_deg, true) + "</span>";
    const head = "<thead><tr><th class='rl'></th>" + p.daily.map((d) => { const x = dparts(d.date); return "<th>" + x.dow + "<b>" + x.day + "</b></th>"; }).join("") + "</tr></thead>";
    const row = (label, sub, fn) => "<tr><th class='rl'>" + label + "<small>" + sub + "</small></th>" + p.daily.map(fn).join("") + "</tr>";
    const na = "<td class='na'>–<small>no data</small></td>";
    $("wind").innerHTML = head + "<tbody>" +
      row("Fire", "burning squares", (d) => "<td class='" + (d.aligned ? "al" : "") + "'><span class='fire'>" + d.cells + "</span></td>") +
      row("Wind", "blowing towards · 0–1 how directly at us", (d) => d.weather_source === null ? na :
        "<td class='" + (d.aligned ? "al" : "") + "'>" + arrow(d.wind_toward_deg, d.wind_alignment >= S.params.aligned_min_alignment) + d.wind_alignment.toFixed(2) +
        "<small>" + d.wind_ms + " m/s" + (d.weather_source === "Open-Meteo" ? "†" : "") + "</small></td>") +
      row("Dry spell", "days in a row under " + S.params.dry_day_mm + " mm of rain", (d) => d.weather_source === null ? na :
        "<td class='" + (d.aligned ? "al" : "") + "'>" + d.dry_days + "<small>" + d.precip_mm + " mm</small></td>") +
      "</tbody>";
    const om = p.daily.filter((d) => d.weather_source === "Open-Meteo").map((d) => dlabel(d.date));
    $("wind-note").textContent = om.length ? "† NASA POWER had no wind or rain yet for " + om.join(", ") + "; those days come from Open-Meteo, so they are not strictly comparable. Shaded days are the ones that count." : "Shaded days are the ones that count.";
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
          .setContent(esc(p.name)).addTo(map);
      });
      L.circleMarker(S.meta.singapore, { radius: 6, color: "#111", weight: 2, fillColor: "#fff", fillOpacity: 1 }).addTo(map)
        .bindTooltip("Singapore", { permanent: true, direction: "top", className: "sg-label", offset: [0, -6] });
      $("map-day").innerHTML = "<option value='-1'>All days</option>" + S.meta.dates.map((d, i) => "<option value='" + i + "'>" + dlabel(d) + "</option>").join("");
      $("map-day").addEventListener("change", drawMapLayer);
      $("map-mode").querySelectorAll("button").forEach((btn) => btn.addEventListener("click", () => {
        mapMode = btn.dataset.mode;
        $("map-mode").querySelectorAll("button").forEach((x) => x.classList.toggle("on", x === btn));
        drawMapLayer();
      }));
      $("map-mode").querySelectorAll("button").forEach((x) => x.classList.toggle("on", x.dataset.mode === mapMode));
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
      $("map-legend").innerHTML = "<span><i class='dot' style='background:" + SENSOR_COL[0] + "'></i>MODIS (1 km)</span>" +
        "<span><i class='dot' style='background:" + SENSOR_COL[1] + "'></i>VIIRS (375 m)</span>";
    } else {
      S.cells.forEach((p) => {
        if (day >= 0 && p[2] !== day) return;
        n++; counts[p[3]]++;
        L.rectangle([[p[0], p[1]], [p[0] + c, p[1] + c]], { renderer, stroke: false, fillColor: CELL_COL[p[3]], fillOpacity: 0.85, interactive: false }).addTo(mapLayer);
      });
      $("map-legend").innerHTML = ["MODIS only", "VIIRS only", "both"].map((t, i) =>
        "<span><i style='background:" + CELL_COL[i] + ";border:1px solid rgba(0,0,0,.35)'></i>" + t + "</span>").join("");
    }
    mapLayer.addTo(map);
    const when = day < 0 ? dlabel(S.meta.window_start) + " – " + dlabel(S.meta.window_end) : dlabel(S.meta.dates[day]);
    $("map-lede").innerHTML = mapMode === "points"
      ? "The same fires as raw dots. The sharper camera, VIIRS, draws <b>" + S.harmonisation.raw_ratio_viirs_to_modis_detections + "×</b> as many dots as MODIS, " + when + "."
      : day < 0
        ? "<b>" + fmt(S.cells_total.cells) + " squares NASA saw fire in</b> across South-East Asia, " + when + ". One square counts once a day, whichever camera saw it."
        : "Squares NASA saw fire in on " + when + ". One square counts once a day, whichever camera saw it.";
  }

  /* ---------- about the data: the proof that both instruments share one scale and one layout ---------- */
  function renderData() {
    const h = S.harmonisation;
    $("feeds").innerHTML = "<thead><tr><th>File</th><th class='num'>Rows</th><th class='num'>In the six provinces</th></tr></thead><tbody>" +
      S.feeds.map((f) => { const st = S.feed_stats[f.id]; return "<tr class='" + (f.rows ? "" : "empty") + "'><td>" + esc(f.dataset) + "<small>" + esc(f.url) + "</small><small>HTTP " + f.http_status + " · " + fmt(f.bytes) + " bytes · fetched " + esc(f.fetched_utc) + "</small></td>" +
        "<td class='num'>" + (f.rows ? fmt(f.rows) : "0 · empty") + "</td><td class='num'>" + fmt(st.rows_in_focus_provinces) + "</td></tr>"; }).join("") + "</tbody>";

    const c = S.confidence, br = S.params.modis_confidence_breaks;
    $("conf").innerHTML = "<thead><tr><th>Shared grade</th><th>MODIS value</th><th class='num'>MODIS rows</th><th>VIIRS value</th><th class='num'>VIIRS rows</th><th>Used</th></tr></thead><tbody>" +
      ["low", "nominal", "high"].map((k) => "<tr><td>" + k + "</td><td>" + br[k] + " %</td><td class='num'>" + fmt(c.MODIS[k]) + "</td><td>" + k + "</td><td class='num'>" + fmt(c.VIIRS[k]) + "</td><td>" + (k === "low" ? "left out" : "yes") + "</td></tr>").join("") + "</tbody>";

    const schema = [["latitude, longitude", "latitude, longitude", "latitude, longitude"], ["time (UTC)", "acq_date + acq_time", "acq_date + acq_time"],
      ["satellite", "satellite (Terra / Aqua)", "satellite (S-NPP / NOAA-20 / NOAA-21)"], ["fire temperature", "brightness", "bright_ti4"], ["background temperature", "bright_t31", "bright_ti5"],
      ["fire power", "frp", "frp"], ["pixel size", "scan × track (~1 km)", "scan × track (~375 m)"], ["grade", "confidence 0–100 → 3 grades", "confidence low / nominal / high"],
      ["square and day", "0.1° square · local date at UTC+7", "0.1° square · local date at UTC+7"]];
    $("schema").innerHTML = "<thead><tr><th>Shared column</th><th>MODIS C6.1 file</th><th>VIIRS C2 files</th></tr></thead><tbody>" +
      schema.map((r) => "<tr><td>" + r[0] + "</td><td>" + r[1] + "</td><td>" + r[2] + "</td></tr>").join("") + "</tbody>";

    $("tiles").innerHTML =
      "<div><b>" + h.raw_ratio_viirs_to_modis_detections + "×</b><span>VIIRS dots for every MODIS dot, raw</span></div>" +
      "<div><b>" + h.cell_ratio_viirs_to_modis + "×</b><span>VIIRS squares for every MODIS square, on the shared grid</span></div>" +
      "<div><b>" + h.modis_cells_also_seen_by_viirs_pct + "%</b><span>of MODIS's burning squares also seen by VIIRS the same day</span></div>";
  }
})();
