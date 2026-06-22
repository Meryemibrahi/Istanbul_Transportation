// ==================== API CONFIGURATION ====================
const API_BASE_URL = "http://127.0.0.1:8000";

// ==================== MAP INITIALIZATION ====================
let map;
let layers = { stops: null, results: null, paths: null, network: null };
let isDrawingArea = false;
let areaStartPoint = null;
let nearestStopMode = false;

let allStopsCache = [];
let allRoutesCache = [];
let metroStationsCache = [];
let metroRouteDetailsCache = [];
let metroNetworkRoutesCache = [];
let selectedBaseRouteData = null;
let tspSelectedStops = [];

const DEFAULT_CENTER = [41.01, 28.97];
const DEFAULT_ZOOM = 11;

// ==================== STARTUP ====================
document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".tab-btn").forEach((btn) => {
        btn.addEventListener("click", function () {
            switchTab(this.getAttribute("data-tab"));
        });
    });

    initMap();
    populateRouteDropdown();
    loadMetroStations();
});

// ==================== MAP ====================
function initMap() {
    map = L.map("map").setView(DEFAULT_CENTER, DEFAULT_ZOOM);

    L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 19,
        attribution: "&copy; OpenStreetMap contributors",
    }).addTo(map);

    map.on("click", onMapClick);

    map.on("mousemove", (e) => {
        const lat = e.latlng.lat.toFixed(4);
        const lon = e.latlng.lng.toFixed(4);
        document.getElementById("coordDisplay").textContent = `Lat: ${lat}, Lon: ${lon}`;
    });

    layers.stops = L.layerGroup().addTo(map);
    layers.results = L.layerGroup().addTo(map);
    layers.paths = L.layerGroup().addTo(map);
    layers.network = L.layerGroup().addTo(map);
    layers.metroRoutes = L.layerGroup().addTo(map);  // Persistent metro routes layer
}

function clearMap() {
    layers.stops.clearLayers();
    layers.results.clearLayers();
    layers.paths.clearLayers();
    layers.network.clearLayers();
    layers.metroRoutes.clearLayers();  // Also clear persistent metro routes
    clearAllInteractiveModes();
    setResult("Map cleared.");
}

function clearAllInteractiveModes() {
    nearestStopMode = false;
    isDrawingArea = false;
    areaStartPoint = null;
}

function onMapClick(e) {
    if (isDrawingArea) {
        if (!areaStartPoint) {
            areaStartPoint = e.latlng;
            setResult("Click the second corner to complete the window query.");
        } else {
            completeAreaSelection(e.latlng);
        }
        return;
    }

    if (nearestStopMode) {
        document.getElementById("nearLat").value = e.latlng.lat.toFixed(6);
        document.getElementById("nearLon").value = e.latlng.lng.toFixed(6);
        nearestStopMode = false;
        findNearestStops();
    }
}

// ==================== UTILITY ====================
function showSpinner(show = true) {
    const spinner = document.getElementById("loadingSpinner");
    if (spinner) spinner.style.display = show ? "flex" : "none";
}

function setResult(html) {
    const box = document.getElementById("resultBox");
    if (box) box.innerHTML = html;
}

function clearResults() {
    setResult("Ready");
}

function switchTab(tabName) {
    document.querySelectorAll(".tab-content").forEach((tab) => {
        tab.style.display = "none";
    });

    const activeTab = document.getElementById(`${tabName}-tab`);
    if (activeTab) activeTab.style.display = "block";

    document.querySelectorAll(".tab-btn").forEach((btn) => btn.classList.remove("active"));
    const activeBtn = document.querySelector(`[data-tab="${tabName}"]`);
    if (activeBtn) activeBtn.classList.add("active");
}

async function fetchJson(url) {
    const res = await fetch(url);
    if (!res.ok) {
        const txt = await res.text();
        throw new Error(txt || `Request failed: ${res.status}`);
    }
    return res.json();
}

function escapeHtml(str) {
    return String(str ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

// ==================== DATA LOADERS ====================
async function loadAllStopsForSearch() {
    if (allStopsCache.length > 0) return allStopsCache;
    allStopsCache = await fetchJson(`${API_BASE_URL}/explorer`);
    return allStopsCache;
}

async function loadStopById(stopId) {
    const cached = allStopsCache.find((s) => String(s.stop_id) === String(stopId));
    if (cached) return cached;
    return await fetchJson(`${API_BASE_URL}/explorer/${encodeURIComponent(stopId)}`);
}

async function loadAllRoutes() {
    if (allRoutesCache.length > 0) return allRoutesCache;
    allRoutesCache = await fetchJson(`${API_BASE_URL}/explorer/routes`);
    return allRoutesCache;
}

// ==================== EXPLORE ====================
async function searchStopsByName() {
    const query = document.getElementById("stopNameSearch")?.value?.trim().toLowerCase();
    if (!query) return setResult("Enter a stop name.");

    showSpinner(true);
    try {
        const stops = await loadAllStopsForSearch();
        const matches = stops
            .filter((stop) => stop.stop_name && stop.stop_name.toLowerCase().includes(query))
            .slice(0, 20);

        layers.results.clearLayers();

        if (!matches.length) {
            setResult("No matching stops found.");
            return;
        }

        let html = `<h4>Matching Stops</h4>`;

        matches.forEach((stop) => {
            L.circleMarker([stop.stop_lat, stop.stop_lon], {
                radius: 6,
                color: "#9b59b6",
                weight: 2,
                fillOpacity: 0.8,
            })
                .bindPopup(`<b>${escapeHtml(stop.stop_name)}</b><br>ID: ${escapeHtml(stop.stop_id)}`)
                .addTo(layers.results);

            html += `
                <div style="padding: 6px; border-bottom: 1px solid #ddd; cursor: pointer;"
                     onclick="zoomToStop('${String(stop.stop_id).replace(/'/g, "\\'")}', '${String(stop.stop_name).replace(/'/g, "\\'")}', ${stop.stop_lat}, ${stop.stop_lon})">
                    <b>${escapeHtml(stop.stop_name)}</b><br>
                    ID: ${escapeHtml(stop.stop_id)}
                </div>
            `;
        });

        setResult(html);
        const bounds = L.latLngBounds(matches.map((s) => [s.stop_lat, s.stop_lon]));
        if (bounds.isValid()) map.fitBounds(bounds);
    } catch (err) {
        setResult(`Error: ${err.message}`);
    } finally {
        showSpinner(false);
    }
}

function zoomToStop(stopId, stopName, lat, lon) {
    layers.results.clearLayers();

    L.circleMarker([lat, lon], {
        radius: 8,
        color: "#e74c3c",
        weight: 2,
        fillOpacity: 0.9,
    })
        .bindPopup(`<b>${escapeHtml(stopName)}</b><br>ID: ${escapeHtml(stopId)}`)
        .addTo(layers.results);

    map.setView([lat, lon], 15);
    setResult(`<b>${escapeHtml(stopName)}</b><br>ID: ${escapeHtml(stopId)}<br>Lat: ${lat}<br>Lon: ${lon}`);
}

async function populateRouteDropdown() {
    try {
        const routes = await loadAllRoutes();
        const select = document.getElementById("routeSelect");
        if (!select) return;

        select.innerHTML = `<option value="">Choose a route...</option>`;

        routes.forEach((route) => {
            const option = document.createElement("option");
            option.value = route.route_id;
            option.textContent = `${route.route_short_name || route.route_id} - ${route.route_long_name || "N/A"}`;
            select.appendChild(option);
        });
    } catch (err) {
        console.error("Failed to populate route dropdown:", err);
    }
}

function showSelectedRouteFromDropdown() {
    const routeId = document.getElementById("routeSelect")?.value;
    if (!routeId) return setResult("Please choose a route first.");
    showRouteWithStops(routeId);
}

async function showRouteWithStops(routeId = null) {
    const id = routeId || document.getElementById("routeId")?.value;
    if (!id) return setResult("Enter a route ID");

    showSpinner(true);
    try {
        const data = await fetchJson(`${API_BASE_URL}/explorer/route/${encodeURIComponent(id)}`);

        layers.results.clearLayers();

        const latlngs = data.stops.map((s) => [s.stop_lat, s.stop_lon]);

        L.polyline(latlngs, {
            color: "#e74c3c",
            weight: 3,
            opacity: 0.75,
        }).addTo(layers.results);

        data.stops.forEach((stop, i) => {
            L.circleMarker([stop.stop_lat, stop.stop_lon], {
                radius: 6,
                color: "#9b59b6",
                weight: 2,
                fillOpacity: 0.9,
            })
                .bindPopup(`${i + 1}. ${escapeHtml(stop.stop_name)}`)
                .addTo(layers.results);
        });

        let html = `<h4>Route: ${escapeHtml(data.route.route_short_name)}</h4>
            <b>Name:</b> ${escapeHtml(data.route.route_long_name || "N/A")}<br>
            <b>Stops:</b> ${data.stop_count}<br>
            <b>Trips:</b> ${data.route.trip_count}<br>
            <h5>Stops in Order:</h5>`;

        data.stops.forEach((stop, i) => {
            html += `<div style="padding: 4px 0; border-bottom: 1px solid #ddd;">
                ${i + 1}. <b>${escapeHtml(stop.stop_name)}</b> (${escapeHtml(stop.stop_id)})
            </div>`;
        });

        setResult(html);

        if (latlngs.length > 0) {
            const bounds = L.latLngBounds(latlngs);
            if (bounds.isValid()) map.fitBounds(bounds);
        }
    } catch (err) {
        setResult(`Error: ${err.message}`);
    } finally {
        showSpinner(false);
    }
}

async function displayFullNetwork() {
    showSpinner(true);
    try {
        const res = await fetch(`${API_BASE_URL}/explorer/network`);
        if (!res.ok) throw new Error('Network load failed');

        const network = await res.json();
        console.log("FULL NETWORK RESPONSE:", network);

        const routes = network.routes || network.routes_data || [];
        const stops = network.stops || network.stops_data || [];

        layers.network.clearLayers();

        let html = `<h4>Full Network Visualization</h4>
            <b>Stops:</b> ${stops.length}<br>
            <b>Routes:</b> ${routes.length}<br><hr>`;

        let routesDrawn = 0;
        routes.forEach(route => {
            if (!route.geojson) {
                console.warn('No geojson for route:', route.route_id);
                return;
            }

            try {
                const geom = JSON.parse(route.geojson);
                console.log("Route geojson:", route.route_id, geom);

                L.geoJSON(geom, {
                    style: function(feature) {
                        return {
                            color: '#e74c3c',
                            weight: 4,
                            opacity: 0.8,
                            lineCap: 'round',
                            lineJoin: 'round'
                        };
                    },
                    onEachFeature: function(feature, layer) {
                        layer.bindPopup(`
                            <b>${route.route_short_name || route.route_id}</b><br>
                            ${route.route_long_name || ''}
                        `);
                    }
                }).addTo(layers.network);
                
                routesDrawn++;

            } catch (e) {
                console.error('Invalid route geojson:', route.route_id, e);
            }
        });

        const mcg = L.markerClusterGroup();

        stops.forEach(stop => {
            const marker = L.circleMarker([stop.stop_lat, stop.stop_lon], {
                radius: 3,
                color: '#27ae60',
                weight: 1,
                fillOpacity: 0.6,
                opacity: 0.7
            }).bindPopup(`${stop.stop_name}<br>ID: ${stop.stop_id}`);

            mcg.addLayer(marker);
        });

        layers.network.addLayer(mcg);

        html += `<b>Routes drawn:</b> ${routesDrawn}<br>
                 <i>Red lines show route paths, green markers show stops with clustering.</i>`;
        setResult(html);

        // Fit map bounds to show entire network
        if (stops.length > 0) {
            const bounds = L.latLngBounds(stops.map(s => [s.stop_lat, s.stop_lon]));
            if (bounds.isValid()) {
                map.fitBounds(bounds, { padding: [50, 50] });
            }
        }

    } catch (err) {
        setResult(`Error: ${err.message}`);
    } finally {
        showSpinner(false);
    }
}

// ==================== SPATIAL TOOLS ====================
function enableNearestStopMode() {
    clearAllInteractiveModes();
    nearestStopMode = true;
    setResult("Click on the map to find nearest stops.");
}

async function findNearestStops() {
    const lat = document.getElementById("nearLat")?.value;
    const lon = document.getElementById("nearLon")?.value;
    const radius = document.getElementById("nearRadius")?.value || 500;
    const kInput = document.getElementById("nearLimit")?.value?.trim();
    const k = kInput ? parseInt(kInput, 10) : null;

    if (!lat || !lon) return setResult("Enter latitude and longitude");

    showSpinner(true);
    try {
        const stops = await fetchJson(
            `${API_BASE_URL}/spail-tools/nearest?lat=${encodeURIComponent(lat)}&lon=${encodeURIComponent(lon)}&radius=${encodeURIComponent(radius)}`
        );

        const limitedStops = k ? stops.slice(0, k) : stops;
        layers.results.clearLayers();

        L.circleMarker([parseFloat(lat), parseFloat(lon)], {
            radius: 5,
            color: "#f39c12",
            weight: 2,
            fillOpacity: 0.9,
        }).addTo(layers.results);

        L.circle([parseFloat(lat), parseFloat(lon)], {
            radius: parseFloat(radius),
            color: "#e74c3c",
            fill: false,
        }).addTo(layers.results);

        let html = `<h4>Nearest ${limitedStops.length} Stops</h4>`;

        limitedStops.forEach((stop, i) => {
            L.circleMarker([stop.stop_lat, stop.stop_lon], {
                radius: 8,
                color: "#9b59b6",
                weight: 2,
                fillOpacity: 0.75,
            })
                .bindPopup(`${escapeHtml(stop.stop_name)}<br>Distance: ${Math.round(Number(stop.distance_m || 0))}m`)
                .addTo(layers.results);

            html += `<div style="padding: 5px; border-bottom: 1px solid #ddd;">
                ${i + 1}. <b>${escapeHtml(stop.stop_name)}</b><br>
                Distance: ${Math.round(Number(stop.distance_m || 0))} m
            </div>`;
        });

        map.setView([parseFloat(lat), parseFloat(lon)], 13);
        setResult(html);
    } catch (err) {
        setResult(`Error: ${err.message}`);
    } finally {
        showSpinner(false);
    }
}

function enableAreaSelection() {
    clearAllInteractiveModes();
    isDrawingArea = true;
    areaStartPoint = null;
    setResult("Click on the map to choose the first corner of the area.");
}

async function completeAreaSelection(endPoint) {
    isDrawingArea = false;

    const minLat = Math.min(areaStartPoint.lat, endPoint.lat);
    const maxLat = Math.max(areaStartPoint.lat, endPoint.lat);
    const minLon = Math.min(areaStartPoint.lng, endPoint.lng);
    const maxLon = Math.max(areaStartPoint.lng, endPoint.lng);
    areaStartPoint = null;

    showSpinner(true);
    try {
        const stops = await fetchJson(
            `${API_BASE_URL}/spail-tools/inarea?min_lat=${minLat}&max_lat=${maxLat}&min_lon=${minLon}&max_lon=${maxLon}`
        );

        layers.results.clearLayers();

        L.rectangle(
            [
                [minLat, minLon],
                [maxLat, maxLon],
            ],
            { color: "#3498db", weight: 2, fill: false }
        ).addTo(layers.results);

        stops.forEach((stop) => {
            L.circleMarker([stop.stop_lat, stop.stop_lon], {
                radius: 5,
                color: "#9b59b6",
                weight: 1,
                fillOpacity: 0.7,
            })
                .bindPopup(escapeHtml(stop.stop_name))
                .addTo(layers.results);
        });

        setResult(`Found ${stops.length} stops in the selected area.`);
    } catch (err) {
        setResult(`Error: ${err.message}`);
    } finally {
        showSpinner(false);
    }
}

async function useCurrentMapWindow() {
    const bounds = map.getBounds();
    const minLat = bounds.getSouth();
    const maxLat = bounds.getNorth();
    const minLon = bounds.getWest();
    const maxLon = bounds.getEast();

    showSpinner(true);
    try {
        const stops = await fetchJson(
            `${API_BASE_URL}/spail-tools/inarea?min_lat=${minLat}&max_lat=${maxLat}&min_lon=${minLon}&max_lon=${maxLon}`
        );

        layers.results.clearLayers();

        L.rectangle(
            [
                [minLat, minLon],
                [maxLat, maxLon],
            ],
            { color: "#3498db", weight: 2, fill: false }
        ).addTo(layers.results);

        stops.forEach((stop) => {
            L.circleMarker([stop.stop_lat, stop.stop_lon], {
                radius: 5,
                color: "#9b59b6",
                weight: 1,
                fillOpacity: 0.7,
            })
                .bindPopup(escapeHtml(stop.stop_name))
                .addTo(layers.results);
        });

        setResult(`Found ${stops.length} stops in the current map window.`);
    } catch (err) {
        setResult(`Error: ${err.message}`);
    } finally {
        showSpinner(false);
    }
}

async function showBusiestStops() {
    const startHour = document.getElementById("busyStart")?.value || 6;
    const endHour = document.getElementById("busyEnd")?.value || 9;

    showSpinner(true);
    try {
        const data = await fetchJson(
            `${API_BASE_URL}/spail-tools/busy?start_time=${encodeURIComponent(startHour)}&end_time=${encodeURIComponent(endHour)}`
        );

        layers.results.clearLayers();

        let html = `<h4>Busiest Stops</h4>
            <b>Time range:</b> ${escapeHtml(startHour)}:00 - ${escapeHtml(endHour)}:00<br><hr>`;

        data.forEach((stop, i) => {
            L.circleMarker([stop.stop_lat, stop.stop_lon], {
                radius: Math.max(5, Math.min(12, Number(stop.total_visits || 0) / 10)),
                color: "#9b59b6",
                weight: 1,
                fillOpacity: 0.75,
            })
                .bindPopup(`${escapeHtml(stop.stop_name)}<br>Visits: ${stop.total_visits}`)
                .addTo(layers.results);

            html += `<div style="padding: 5px; background: #f39c12; color: white; border-radius: 3px; margin: 3px 0;">
                ${i + 1}. <b>${escapeHtml(stop.stop_name)}</b><br>
                Visits: ${stop.total_visits} | Routes: ${stop.unique_routes}
            </div>`;
        });

        setResult(html);

        if (data.length > 0) {
            const bounds = L.latLngBounds(data.map((s) => [s.stop_lat, s.stop_lon]));
            if (bounds.isValid()) map.fitBounds(bounds);
        }
    } catch (err) {
        setResult(`Error: ${err.message}`);
    } finally {
        showSpinner(false);
    }
}

// ==================== ROUTING ====================
async function displayAllMetroRoutes() {
    if (!metroRouteDetailsCache.length) {
        return setResult("Metro routes not loaded yet. Please wait...");
    }

    showSpinner(true);
    try {
        layers.metroRoutes.clearLayers();

        let routesDrawn = 0;

        metroRouteDetailsCache.forEach((routeData, idx) => {
            try {
                const stops = routeData.stops || [];
                if (stops.length < 2) return;

                // Draw line connecting stops
                const latlngs = stops.map(s => [s.stop_lat, s.stop_lon]);
                const color = '#808080';  // Grey for all routes

                L.polyline(latlngs, {
                    color: color,
                    weight: 3,
                    opacity: 0.7,
                    dashArray: '0'
                })
                    .bindPopup(`<b>${routeData.route.route_short_name}</b><br>${routeData.route.route_long_name || 'Metro Route'}`, { maxHeight: 100 })
                    .addTo(layers.metroRoutes);

                // Draw small markers at stops
                stops.forEach((stop, i) => {
                    L.circleMarker([stop.stop_lat, stop.stop_lon], {
                        radius: 3,
                        color: color,
                        weight: 1,
                        fillOpacity: 0.6,
                        opacity: 0.8
                    })
                        .bindPopup(`${stop.stop_name} (${stop.stop_id})`)
                        .addTo(layers.metroRoutes);
                });

                routesDrawn++;
            } catch (e) {
                console.error("Error drawing route:", routeData.route.route_id, e);
            }
        });

        // Fit map to bounds
        const allStops = [];
        metroRouteDetailsCache.forEach(rd => {
            (rd.stops || []).forEach(s => allStops.push([s.stop_lat, s.stop_lon]));
        });
        if (allStops.length > 0) {
            const bounds = L.latLngBounds(allStops);
            if (bounds.isValid()) map.fitBounds(bounds, { padding: [50, 50] });
        }

        setResult(`<h4>✓ All Metro Routes Displayed</h4>
            <b>${routesDrawn}</b> routes on map<br>
            Different colors for each route<br>
            <i>Routes persist until Clear Map is pressed</i>`);
    } catch (err) {
        setResult(`Error: ${err.message}`);
    } finally {
        showSpinner(false);
    }
}

async function loadMetroStations() {
    showSpinner(true);
    try {
        const routes = await loadAllRoutes();
        const metroRoutes = routes.filter(r =>
            String(r.route_short_name || '').toUpperCase().startsWith('M')
        );

        metroRouteDetailsCache = [];
        metroNetworkRoutesCache = [];

        // load full network once to get actual route geojson
        try {
            const network = await fetchJson(`${API_BASE_URL}/explorer/network`);
            metroNetworkRoutesCache = (network.routes || network.routes_data || []).filter(r =>
                String(r.route_short_name || '').toUpperCase().startsWith('M')
            );
        } catch (err) {
            console.warn("Could not load full network route shapes", err);
        }

        for (const route of metroRoutes) {
            try {
                const routeData = await fetchJson(`${API_BASE_URL}/explorer/route/${route.route_id}`);
                metroRouteDetailsCache.push(routeData);
            } catch (err) {
                console.warn("Skipping metro route:", route.route_id, err);
            }
        }

        const baseRouteSelect = document.getElementById("baseRouteSelect");
        if (baseRouteSelect) {
            baseRouteSelect.innerHTML = `<option value="">Choose a metro route...</option>`;

            metroRouteDetailsCache.forEach(routeData => {
                const opt = document.createElement("option");
                opt.value = routeData.route.route_id;
                opt.textContent = `${routeData.route.route_short_name || routeData.route.route_id} - ${routeData.route.route_long_name || "Metro Route"}`;
                baseRouteSelect.appendChild(opt);
            });
        }

        setResult(`Loaded ${metroRouteDetailsCache.length} metro routes.`);
    } catch (err) {
        setResult(`Error: ${err.message}`);
    } finally {
        showSpinner(false);
    }
}

async function showStaticRoute() {
    const startId = document.getElementById("metroStartSelect")?.value;
    const endId = document.getElementById("metroEndSelect")?.value;

    if (!selectedBaseRouteData) {
        return setResult("Choose a base metro route first.");
    }

    if (!startId || !endId) {
        return setResult("Choose start and end metro stations.");
    }

    layers.paths.clearLayers();

    const routeGeo = metroNetworkRoutesCache.find(r =>
        String(r.route_id) === String(selectedBaseRouteData.route.route_id)
    );

    if (routeGeo?.geojson) {
        try {
            const geom = JSON.parse(routeGeo.geojson);
            L.geoJSON(geom, {
                style: {
                    color: "#7f8c8d",
                    weight: 5,
                    opacity: 0.85
                }
            }).addTo(layers.paths);
        } catch (err) {
            console.warn("Failed to draw static route geojson", err);
        }
    }

    const stops = selectedBaseRouteData.stops || [];
    const startStop = stops.find(s => String(s.stop_id) === String(startId));
    const endStop = stops.find(s => String(s.stop_id) === String(endId));

    if (!startStop || !endStop) {
        return setResult("Selected stops are not on the chosen route.");
    }

    L.circleMarker([startStop.stop_lat, startStop.stop_lon], {
        radius: 8,
        color: "#27ae60",
        weight: 2,
        fillOpacity: 0.9
    }).bindPopup(`<b>START</b><br>${startStop.stop_name}`).addTo(layers.paths);

    L.circleMarker([endStop.stop_lat, endStop.stop_lon], {
        radius: 8,
        color: "#c0392b",
        weight: 2,
        fillOpacity: 0.9
    }).bindPopup(`<b>END</b><br>${endStop.stop_name}`).addTo(layers.paths);

    const bounds = L.latLngBounds([
        [startStop.stop_lat, startStop.stop_lon],
        [endStop.stop_lat, endStop.stop_lon]
    ]);
    if (bounds.isValid()) map.fitBounds(bounds.pad(0.5));

    setResult(`
        <h4>Static Metro Route</h4>
        <b>Route:</b> ${selectedBaseRouteData.route.route_short_name || selectedBaseRouteData.route.route_id}<br>
        <b>Start:</b> ${startStop.stop_name}<br>
        <b>End:</b> ${endStop.stop_name}<br>
        <i>The real route line is shown in gray, with start and end stations highlighted.</i>
    `);
}

function syncMetroDropdownsToPathInputs() {
    const start = document.getElementById("metroStartSelect")?.value || "";
    const end = document.getElementById("metroEndSelect")?.value || "";

    const rawStart = document.getElementById("pathStart");
    const rawEnd = document.getElementById("pathEnd");

    if (rawStart) rawStart.value = start;
    if (rawEnd) rawEnd.value = end;
}

function getPathInputValues() {
    const rawStart = document.getElementById("pathStart")?.value?.trim() || "";
    const rawEnd = document.getElementById("pathEnd")?.value?.trim() || "";
    return { start: rawStart, end: rawEnd };
}

async function enrichPathStopsWithCoordinates(stops) {
    await loadAllStopsForSearch();
    const lookup = new Map(allStopsCache.map((s) => [String(s.stop_id), s]));

    return stops.map((stop) => {
        const full = lookup.get(String(stop.stop_id));
        return {
            stop_id: stop.stop_id,
            stop_name: stop.stop_name,
            lat: full?.stop_lat ?? null,
            lon: full?.stop_lon ?? null,
            distance_from_start: Number(stop.agg_cost ?? stop.cost ?? 0),
        };
    }).filter((s) => s.lat !== null && s.lon !== null);
}

// Store current paths for comparison
let currentBasePath = null;
let currentComparePaths = [];

async function showBaseRoute() {
    const { start, end } = getPathInputValues();
    if (!start || !end) return setResult("Choose start and end stops.");

    showSpinner(true);
    try {
        const data = await fetchJson(
            `${API_BASE_URL}/routes/dijkstra?start_id=${encodeURIComponent(start)}&end_id=${encodeURIComponent(end)}`
        );

        const path = await enrichPathStopsWithCoordinates(data.stops || []);
        currentBasePath = {
            algorithm: "Base Route (Direct)",
            path,
            total_distance: path.length ? path[path.length - 1].distance_from_start : 0,
            hops: path.length,
        };

        // Clear all paths and draw base route
        currentComparePaths = [];
        layers.paths.clearLayers();
        drawBasePathOnly();
        
        setResult(`<h4>Base Route Selected</h4>
            Start: <b>${path[0].stop_name}</b><br>
            End: <b>${path[path.length-1].stop_name}</b><br>
            Distance: ${Math.round(currentBasePath.total_distance)}<br>
            Stops: ${currentBasePath.hops}<br>
            <hr>
            <p style="color: #666; font-size: 0.9em;">
                Now select <b>Dijkstra</b> or <b>A*</b> to compare algorithms on this route.
            </p>`);
    } catch (err) {
        setResult(`Error: ${err.message}`);
    } finally {
        showSpinner(false);
    }
}

function drawBasePathOnly() {
    if (!currentBasePath) return;

    const path = currentBasePath.path;
    const latlngs = path.map((p) => [p.lat, p.lon]);
    if (!latlngs.length) return;

    // Draw base route in light gray
    L.polyline(latlngs, {
        color: '#95a5a6',
        weight: 3,
        opacity: 0.6,
        dashArray: '5, 5',
    }).addTo(layers.paths);

    path.forEach((stop, i) => {
        L.circleMarker([stop.lat, stop.lon], {
            radius: 4,
            color: '#95a5a6',
            weight: 1,
            fillOpacity: 0.5,
        })
            .bindPopup(`${i + 1}. ${escapeHtml(stop.stop_name)}`)
            .addTo(layers.paths);
    });

    const bounds = L.latLngBounds(latlngs);
    if (bounds.isValid()) map.fitBounds(bounds, { padding: [50, 50] });
}

async function runDijkstra() {
    const { start, end } = getPathInputValues();
    if (!start || !end) return setResult("Choose start and end stops.");

    showSpinner(true);
    try {
        const data = await fetchJson(
            `${API_BASE_URL}/routes/dijkstra?start_id=${encodeURIComponent(start)}&end_id=${encodeURIComponent(end)}`
        );

        const path = await enrichPathStopsWithCoordinates(data.stops || []);
        const pathObj = {
            algorithm: "Dijkstra",
            path,
            total_distance: path.length ? path[path.length - 1].distance_from_start : 0,
            hops: path.length,
        };

        // If no base path exists, set this as base, otherwise overlay
        if (!currentBasePath) {
            currentBasePath = pathObj;
            currentComparePaths = [];
            layers.paths.clearLayers();
            drawBasePathOnly();
        } else {
            currentComparePaths = [pathObj];
            layers.paths.clearLayers();
            drawBasePathOnly();
            drawOverlayPath(pathObj, "#3498db");
        }

        displayComparisonInfo();
    } catch (err) {
        setResult(`Error: ${err.message}`);
    } finally {
        showSpinner(false);
    }
}

async function runAStar() {
    const { start, end } = getPathInputValues();
    if (!start || !end) return setResult("Choose start and end stops.");

    showSpinner(true);
    try {
        const data = await fetchJson(
            `${API_BASE_URL}/routes/astar?start_id=${encodeURIComponent(start)}&end_id=${encodeURIComponent(end)}`
        );

        const path = await enrichPathStopsWithCoordinates(data.stops || []);
        const pathObj = {
            algorithm: "A*",
            path,
            total_distance: path.length ? path[path.length - 1].distance_from_start : 0,
            hops: path.length,
        };

        // If no base path exists, set this as base, otherwise overlay
        if (!currentBasePath) {
            currentBasePath = pathObj;
            currentComparePaths = [];
            layers.paths.clearLayers();
            drawBasePathOnly();
        } else {
            currentComparePaths = [pathObj];
            layers.paths.clearLayers();
            drawBasePathOnly();
            drawOverlayPath(pathObj, "#e74c3c");
        }

        displayComparisonInfo();
    } catch (err) {
        setResult(`Error: ${err.message}`);
    } finally {
        showSpinner(false);
    }
}

function drawOverlayPath(pathObj, color) {
    const latlngs = pathObj.path.map((p) => [p.lat, p.lon]);
    if (!latlngs.length) return;

    // Draw overlay route in bold color
    L.polyline(latlngs, {
        color,
        weight: 5,
        opacity: 0.9,
    }).addTo(layers.paths);

    pathObj.path.forEach((stop, i) => {
        L.circleMarker([stop.lat, stop.lon], {
            radius: 6,
            color,
            weight: 2,
            fillOpacity: 0.8,
        })
            .bindPopup(`${pathObj.algorithm} - ${i + 1}. ${escapeHtml(stop.stop_name)}`)
            .addTo(layers.paths);
    });
}

function displayComparisonInfo() {
    if (!currentBasePath) return;

    let html = `<h4>Route Comparison</h4>
        <div style="padding: 8px; background: #f5f5f5; border-radius: 4px; margin-bottom: 8px;">
            <b style="color: #95a5a6;">━━ Base Route</b><br>
            Stops: ${currentBasePath.hops} | Distance: ${Math.round(currentBasePath.total_distance)}
        </div>`;

    currentComparePaths.forEach(algo => {
        const color = algo.algorithm === "Dijkstra" ? "#3498db" : "#e74c3c";
        const timeSaved = currentBasePath.total_distance - algo.total_distance;
        const improvement = timeSaved !== 0 ? ` (${timeSaved > 0 ? "-" : "+"}${Math.abs(timeSaved)})` : " (same)";
        
        html += `<div style="padding: 8px; background: #f5f5f5; border-radius: 4px; margin-bottom: 8px; border-left: 4px solid ${color};">
            <b style="color: ${color};">━━ ${algo.algorithm}</b><br>
            Stops: ${algo.hops} | Distance: ${Math.round(algo.total_distance)}${improvement}
        </div>`;
    });

    html += `<hr><h5>Base Route Stops:</h5>`;
    currentBasePath.path.forEach((stop, i) => {
        html += `<div style="padding: 3px; font-size: 0.85em; border-bottom: 1px solid #eee;">
            ${i + 1}. ${escapeHtml(stop.stop_name)}
        </div>`;
    });

    setResult(html);
}

function drawPath(pathObj, color) {
    layers.paths.clearLayers();

    const latlngs = pathObj.path.map((p) => [p.lat, p.lon]);
    if (!latlngs.length) {
        setResult("Path returned, but stop coordinates could not be resolved.");
        return;
    }

    L.polyline(latlngs, {
        color,
        weight: 4,
        opacity: 0.85,
    }).addTo(layers.paths);

    pathObj.path.forEach((stop, i) => {
        L.circleMarker([stop.lat, stop.lon], {
            radius: 5,
            color,
            weight: 2,
            fillOpacity: 0.85,
        })
            .bindPopup(`${i + 1}. ${escapeHtml(stop.stop_name)}`)
            .addTo(layers.paths);
    });

    const bounds = L.latLngBounds(latlngs);
    if (bounds.isValid()) map.fitBounds(bounds);

    displayPathInfo(pathObj);
}

function displayPathInfo(pathObj) {
    let html = `<h4>${escapeHtml(pathObj.algorithm)} Path</h4>
        Total Cost: ${Math.round(Number(pathObj.total_distance || 0))}<br>
        Hops: ${pathObj.hops}<br>
        <h5>Stops in Order:</h5>`;

    pathObj.path.forEach((stop, i) => {
        html += `<div style="padding: 5px; border-bottom: 1px solid #ddd;">
            ${i + 1}. <b>${escapeHtml(stop.stop_name)}</b><br>
            Cost from start: ${Math.round(Number(stop.distance_from_start || 0))}
        </div>`;
    });

    setResult(html);
}

async function runTSP() {
    const startId = document.getElementById("tspStartSelect")?.value;

    if (!startId) {
        return setResult("Choose a TSP start station.");
    }

    if (!tspSelectedStops.length) {
        return setResult("Add at least one stop for TSP.");
    }

    showSpinner(true);
    try {
        const query = new URLSearchParams();
        query.append("start_id", startId);
        tspSelectedStops.forEach(stop => query.append("stop_ids", stop.stop_id));

        const data = await fetchJson(`${API_BASE_URL}/routes/tsp?${query.toString()}`);

        let html = `<h4>TSP Optimized Order</h4>`;

        if (data.order && data.order.length) {
            html += `<h5>Visit Order:</h5>`;
            data.order.forEach((item, i) => {
                html += `<div style="padding: 4px; border-bottom: 1px solid #ddd;">
                    ${i + 1}. Node ${item.node}
                </div>`;
            });
        }

        setResult(html);
    } catch (err) {
        setResult(`Error: ${err.message}`);
    } finally {
        showSpinner(false);
    }
}

function addTspStop() {
    const select = document.getElementById("tspStopSelect");
    const stopId = select?.value;
    const stopName = select?.options[select.selectedIndex]?.textContent || "";

    if (!stopId) return;

    if (tspSelectedStops.some(s => String(s.stop_id) === String(stopId))) {
        return;
    }

    tspSelectedStops.push({
        stop_id: stopId,
        stop_name: stopName
    });

    renderTspSelectedStops();
}

function renderTspSelectedStops() {
    const box = document.getElementById("tspSelectedStops");
    if (!box) return;

    if (!tspSelectedStops.length) {
        box.innerHTML = "No TSP stops selected yet.";
        return;
    }

    box.innerHTML = tspSelectedStops.map((stop, i) => `
        <div style="padding:4px; border-bottom:1px solid #ddd;">
            ${i + 1}. ${stop.stop_name}
        </div>
    `).join("");
}

function clearTspStops() {
    tspSelectedStops = [];
    renderTspSelectedStops();
}

function onBaseRouteChange() {
    const routeId = document.getElementById("baseRouteSelect")?.value;
    const startSelect = document.getElementById("metroStartSelect");
    const endSelect = document.getElementById("metroEndSelect");
    const tspStartSelect = document.getElementById("tspStartSelect");
    const tspStopSelect = document.getElementById("tspStopSelect");

    selectedBaseRouteData = metroRouteDetailsCache.find(r => String(r.route.route_id) === String(routeId)) || null;

    const clearSelect = (sel, placeholder) => {
        if (!sel) return;
        sel.innerHTML = `<option value="">${placeholder}</option>`;
    };

    clearSelect(startSelect, "Choose start station...");
    clearSelect(endSelect, "Choose end station...");
    clearSelect(tspStartSelect, "Choose start station...");
    clearSelect(tspStopSelect, "Choose stop...");

    tspSelectedStops = [];
    renderTspSelectedStops();

    if (!selectedBaseRouteData) return;

    const stops = selectedBaseRouteData.stops || [];
    const seen = new Set();

    stops.forEach(stop => {
        const key = String(stop.stop_id);
        if (seen.has(key)) return;
        seen.add(key);

        const label = `${stop.stop_name} (${stop.stop_id})`;

        [startSelect, endSelect, tspStartSelect, tspStopSelect].forEach(sel => {
            if (!sel) return;
            const opt = document.createElement("option");
            opt.value = stop.stop_id;
            opt.textContent = label;
            sel.appendChild(opt);
        });
    });

    setResult(`Loaded ${(selectedBaseRouteData.stops || []).length} stops for selected metro route.`);
}

// ==================== ADVANCED ====================
async function getStopById() {
    const stopId = document.getElementById("stopId")?.value?.trim();
    if (!stopId) return setResult("Enter a stop ID");

    showSpinner(true);
    try {
        const stop = await fetchJson(`${API_BASE_URL}/explorer/${encodeURIComponent(stopId)}`);

        layers.results.clearLayers();
        L.circleMarker([stop.stop_lat, stop.stop_lon], {
            radius: 8,
            color: "#e74c3c",
            weight: 2,
            fillOpacity: 0.8,
        })
            .bindPopup(`<b>${escapeHtml(stop.stop_name)}</b><br>ID: ${escapeHtml(stop.stop_id)}`)
            .addTo(layers.results);

        map.setView([stop.stop_lat, stop.stop_lon], 14);
        setResult(`<b>${escapeHtml(stop.stop_name)}</b><br>ID: ${escapeHtml(stop.stop_id)}<br>Lat: ${stop.stop_lat}<br>Lon: ${stop.stop_lon}`);
    } catch (err) {
        setResult(`Error: ${err.message}`);
    } finally {
        showSpinner(false);
    }
}

async function getStopByCode() {
    const code = document.getElementById("stopCode")?.value?.trim();
    if (!code) return setResult("Enter a stop code");

    showSpinner(true);
    try {
        const stop = await fetchJson(`${API_BASE_URL}/advanced/${encodeURIComponent(code)}`);

        layers.results.clearLayers();
        L.circleMarker([stop.stop_lat, stop.stop_lon], {
            radius: 8,
            color: "#3498db",
            weight: 2,
            fillOpacity: 0.8,
        })
            .bindPopup(`<b>${escapeHtml(stop.stop_name)}</b><br>Code: ${escapeHtml(stop.stop_code)}`)
            .addTo(layers.results);

        map.setView([stop.stop_lat, stop.stop_lon], 14);
        setResult(`<b>${escapeHtml(stop.stop_name)}</b><br>Code: ${escapeHtml(stop.stop_code)}<br>ID: ${escapeHtml(stop.stop_id)}`);
    } catch (err) {
        setResult(`Error: ${err.message}`);
    } finally {
        showSpinner(false);
    }
}

async function loadAllStops() {
    showSpinner(true);
    try {
        const stops = await loadAllStopsForSearch();

        layers.stops.clearLayers();
        const mcg = L.markerClusterGroup();

        stops.forEach((stop) => {
            const marker = L.circleMarker([stop.stop_lat, stop.stop_lon], {
                radius: 4,
                color: "#27ae60",
                weight: 1,
                fillOpacity: 0.7,
            }).bindPopup(`${escapeHtml(stop.stop_name)}<br>ID: ${escapeHtml(stop.stop_id)}`);
            mcg.addLayer(marker);
        });

        layers.stops.addLayer(mcg);
        setResult(`Loaded all ${stops.length} stops.`);
    } catch (err) {
        setResult(`Error: ${err.message}`);
    } finally {
        showSpinner(false);
    }
}

async function loadTopRoutes() {
    const limit = document.getElementById("topRoutesLimit")?.value || 10;
    showSpinner(true);
    try {
        const data = await fetchJson(`${API_BASE_URL}/advanced/top-routes?limit=${encodeURIComponent(limit)}`);

        let html = `<h4>Top ${limit} Routes by Trips</h4>`;
        data.forEach((route) => {
            html += `<div style="padding: 8px; background: #ecf0f1; margin: 5px 0; border-radius: 4px; cursor: pointer;"
                onclick="showRouteWithStops('${String(route.route_id).replace(/'/g, "\\'")}')">
                <b>${escapeHtml(route.route_short_name)}</b> - ${escapeHtml(route.route_long_name || "N/A")}<br>
                <small>Trips: ${route.trip_count} | Stops: ${route.stop_count}</small>
            </div>`;
        });

        setResult(html);
    } catch (err) {
        setResult(`Error: ${err.message}`);
    } finally {
        showSpinner(false);
    }
}

// ==================== MOBILITY PLACEHOLDERS ====================
// The current backend in this project version does not expose mobility endpoints.
// These placeholders prevent frontend crashes and clearly inform the user.

function setMobilityTimePreset(value) {
    const input = document.getElementById("mobilityTime");
    if (input) input.value = value;
}

function loadMobilityTrajectories() {
    setResult("Mobility endpoints are not available in this backend version yet.");
}

function loadMobilityAtTime() {
    setResult("Mobility endpoints are not available in this backend version yet.");
}

function loadMobilityCurrentWindow() {
    setResult("Mobility endpoints are not available in this backend version yet.");
}

function loadMobilityWindow() {
    setResult("Mobility endpoints are not available in this backend version yet.");
}