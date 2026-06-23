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
    const date = document.getElementById("busyDate")?.value?.trim();
    const startTime = document.getElementById("busyStart")?.value?.trim() || "06:00";
    const endTime = document.getElementById("busyEnd")?.value?.trim() || "09:00";

    if (!date) {
        return setResult("Enter a date for busiest stops, for example 2023-05-02.");
    }

    showSpinner(true);
    try {
        const data = await fetchJson(
            `${API_BASE_URL}/spail-tools/busy?start_time=${encodeURIComponent(startTime)}&end_time=${encodeURIComponent(endTime)}&dateday=${encodeURIComponent(date)}`
        );

        layers.results.clearLayers();

        let html = `<h4>Busiest Stops</h4>
            <b>Date:</b> ${escapeHtml(date)}<br>
            <b>Time range:</b> ${escapeHtml(startTime)} - ${escapeHtml(endTime)}<br><hr>`;

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
async function devBusiestStops() {
    const date = document.getElementById("devBusyDate")?.value?.trim();
    const startTime = document.getElementById("devBusyStart")?.value?.trim() || "06:00";
    const endTime = document.getElementById("devBusyEnd")?.value?.trim() || "09:00";

    if (!date) {
        return setResult("Advanced Busiest Stops: enter dateday first.");
    }

    showSpinner(true);
    try {
        const data = await fetchJson(
            `${API_BASE_URL}/spail-tools/busy?start_time=${encodeURIComponent(startTime)}&end_time=${encodeURIComponent(endTime)}&dateday=${encodeURIComponent(date)}`
        );

        layers.results.clearLayers();

        let html = `<h4>Advanced: Busiest Stops</h4>
            <b>Date:</b> ${escapeHtml(date)}<br>
            <b>Time range:</b> ${escapeHtml(startTime)} - ${escapeHtml(endTime)}<br>
            <b>Returned:</b> ${data.length} stops<br><hr>`;

        data.forEach((stop, i) => {
            if (stop.stop_lat && stop.stop_lon) {
                L.circleMarker([stop.stop_lat, stop.stop_lon], {
                    radius: Math.max(5, Math.min(12, Number(stop.total_visits || 0) / 10)),
                    color: "#9b59b6",
                    weight: 1,
                    fillOpacity: 0.75,
                })
                    .bindPopup(`${escapeHtml(stop.stop_name)}<br>Visits: ${stop.total_visits}`)
                    .addTo(layers.results);
            }

            html += `<div style="padding: 5px; border-bottom: 1px solid #ddd;">
                ${i + 1}. <b>${escapeHtml(stop.stop_name || "Unknown stop")}</b><br>
                Visits: ${escapeHtml(stop.total_visits ?? "N/A")} | Routes: ${escapeHtml(stop.unique_routes ?? "N/A")}
            </div>`;
        });

        setResult(html);

        const points = data.filter((s) => s.stop_lat && s.stop_lon);
        if (points.length > 0) {
            const bounds = L.latLngBounds(points.map((s) => [s.stop_lat, s.stop_lon]));
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

// ==================== MOBILITYDB USER-FRIENDLY FRONTEND ====================
// Normal user flow:
// 1) Select a small map area
// 2) Find trips for one service date
// 3) Select a readable trip result
// 4) Animate movement or show position at time
// Heavy endpoint /all_vehicle_positions_at_time is intentionally kept for Advanced tab only.

let mobilityTripsCache = [];
let mobilitySelectedTrip = null;
let mobilityAnimationTimer = null;
let mobilityMovingMarker = null;
let mobilityCustomBounds = null;
let mobilityAreaPicking = false;
let mobilityAreaFirstCorner = null;
let mobilityRouteLabelCache = new Map();
const MOBILITY_VALID_DEMO_DATES = [
    "2023-05-02",
    "2023-05-03",
    "2023-05-01",
    "2023-04-20",
    "2023-04-21",
    "2023-04-24",
    "2023-04-19",
];
const MOBILITY_DEMO_CENTER = [41.01, 28.97];
const MOBILITY_DEMO_ZOOM = 13;

function initMobilityTools() {
    if (!map) return;
    map.on("click", handleMobilityAreaClick);
    map.on("moveend zoomend", refreshMobilityAreaHint);
    initMobilityDateControls();
    refreshMobilityAreaHint();
}

document.addEventListener("DOMContentLoaded", () => {
    setTimeout(initMobilityTools, 150);
});

function mobilityTimestamp(dateValue, timeValue) {
    if (!dateValue || !timeValue) return "";
    const cleanTime = timeValue.length === 5 ? `${timeValue}:00` : timeValue;
    return `${dateValue} ${cleanTime}+03`;
}

function initMobilityDateControls() {
    populateMobilityDateDropdown();

    const preset = document.getElementById("mobilityDatePreset");
    const dateInput = document.getElementById("mobilityDate");

    if (preset && !preset.value) preset.value = MOBILITY_VALID_DEMO_DATES[0];
    if (dateInput) {
        dateInput.value = preset?.value && preset.value !== "custom" ? preset.value : MOBILITY_VALID_DEMO_DATES[0];
    }

    updateMobilityDateHint();
    syncMobilityDateToAdvanced();
}

function populateMobilityDateDropdown() {
    const preset = document.getElementById("mobilityDatePreset");
    if (!preset) return;

    const current = preset.value || MOBILITY_VALID_DEMO_DATES[0];
    preset.innerHTML = "";

    MOBILITY_VALID_DEMO_DATES.forEach((date) => {
        const option = document.createElement("option");
        option.value = date;
        option.textContent = date;
        preset.appendChild(option);
    });

    const custom = document.createElement("option");
    custom.value = "custom";
    custom.textContent = "Custom date...";
    preset.appendChild(custom);

    preset.value = MOBILITY_VALID_DEMO_DATES.includes(current) ? current : MOBILITY_VALID_DEMO_DATES[0];
}

function onMobilityDatePresetChange() {
    const preset = document.getElementById("mobilityDatePreset");
    const dateInput = document.getElementById("mobilityDate");
    if (!preset || !dateInput) return;

    if (preset.value === "custom") {
        dateInput.disabled = false;
        dateInput.focus();
    } else {
        dateInput.disabled = false;
        dateInput.value = preset.value;
    }

    resetMobilityTripSelectionForNewDate();
    updateMobilityDateHint();
    syncMobilityDateToAdvanced();
}

function onMobilityDateInputChange() {
    const preset = document.getElementById("mobilityDatePreset");
    const dateInput = document.getElementById("mobilityDate");
    if (!dateInput) return;

    if (preset) {
        preset.value = MOBILITY_VALID_DEMO_DATES.includes(dateInput.value) ? dateInput.value : "custom";
    }

    resetMobilityTripSelectionForNewDate();
    updateMobilityDateHint();
    syncMobilityDateToAdvanced();
}

function updateMobilityDateHint() {
    const hint = document.getElementById("mobilityDateHint");
    const date = getMobilitySelectedDate();
    if (!hint) return;

    if (MOBILITY_VALID_DEMO_DATES.includes(date)) {
        hint.innerHTML = `Using valid MobilityDB date <b>${escapeHtml(date)}</b>. If no trips appear, choose a smaller area around Istanbul.`;
    } else {
        hint.innerHTML = `Custom date <b>${escapeHtml(date)}</b> is not in the known valid list. The trip dropdown may stay empty unless this date exists in <code>trips_mdb</code>.`;
    }
}

function resetMobilityTripSelectionForNewDate() {
    mobilityTripsCache = [];
    mobilitySelectedTrip = null;
    fillMobilityTripSelect();
    updateMobilitySelectedTripInfo();
}

function getMobilitySelectedDate() {
    const dateInput = document.getElementById("mobilityDate");
    return dateInput?.value || MOBILITY_VALID_DEMO_DATES[0];
}

function syncMobilityDateToAdvanced() {
    const date = getMobilitySelectedDate();
    const time = document.getElementById("mobilityPositionTime")?.value || "08:15";

    const devDate = document.getElementById("devMobilityDate");
    const devStart = document.getElementById("devMobilityStartTs");
    const devEnd = document.getElementById("devMobilityEndTs");
    const devPos = document.getElementById("devMobPositionTs");

    if (devDate) devDate.value = date;
    if (devStart) devStart.value = `${date} 08:00:00+03`;
    if (devEnd) devEnd.value = `${date} 08:30:00+03`;
    if (devPos) devPos.value = `${date} ${time}:00+03`;
}

function zoomToMobilityDemoArea() {
    if (!map) return;
    mobilityCustomBounds = null;
    mobilityAreaPicking = false;
    mobilityAreaFirstCorner = null;
    map.setView(MOBILITY_DEMO_CENTER, MOBILITY_DEMO_ZOOM);
    layers.results.clearLayers();
    setTimeout(() => {
        const bounds = map.getBounds();
        drawMobilitySearchArea(bounds);
        refreshMobilityAreaHint();
    }, 200);
    setResult(`
        <h4>Demo area selected</h4>
        The map moved to the Istanbul demo area. Now choose the valid demo date and press <b>Find Trips in Selected Area</b>.<br><br>
        <small>The green rectangle is the search box sent to the backend as min/max longitude and latitude.</small>
    `);
}

function mobilityTimeOnlyFromTimestamp(value) {
    const text = String(value || "");
    const match = text.match(/(\d{2}:\d{2})/);
    return match ? match[1] : "";
}

function stopMobilityAnimation() {
    if (mobilityAnimationTimer) {
        clearInterval(mobilityAnimationTimer);
        mobilityAnimationTimer = null;
    }
    if (mobilityMovingMarker && layers.results.hasLayer(mobilityMovingMarker)) {
        layers.results.removeLayer(mobilityMovingMarker);
    }
    mobilityMovingMarker = null;
}

function clearMobilityLayersOnly() {
    stopMobilityAnimation();
    layers.results.clearLayers();
}

function refreshMobilityAreaHint() {
    const hint = document.getElementById("mobilityAreaHint");
    if (!hint || !map) return;

    if (mobilityAreaPicking) {
        hint.innerHTML = mobilityAreaFirstCorner
            ? "Click the opposite corner of the rectangle. The area between the two clicks will be searched."
            : "Click the first corner of the rectangle on the map.";
        return;
    }

    const b = getMobilitySearchBounds();
    const lonWidth = Math.abs(b.getEast() - b.getWest());
    const latHeight = Math.abs(b.getNorth() - b.getSouth());
    const sizeWarning = mobilityAreaLooksTooLarge(b)
        ? `<br><span style="color:#c0392b;"><b>Area is large:</b> zoom in or draw a smaller rectangle for faster results.</span>`
        : `<br><span style="color:#16a085;"><b>Area size looks good</b> for demo search.</span>`;

    if (mobilityCustomBounds) {
        hint.innerHTML = `
            <b>Search area:</b> custom drawn rectangle<br>
            <small>Lon ${b.getWest().toFixed(4)} → ${b.getEast().toFixed(4)} | Lat ${b.getSouth().toFixed(4)} → ${b.getNorth().toFixed(4)}</small>
            ${sizeWarning}
        `;
    } else {
        hint.innerHTML = `
            <b>Search area:</b> current visible map window<br>
            <small>Zoom ${map.getZoom()} | Width ${lonWidth.toFixed(3)}° | Height ${latHeight.toFixed(3)}°</small>
            ${sizeWarning}
        `;
    }
}

function enableMobilityAreaSelection() {
    mobilityAreaPicking = true;
    mobilityAreaFirstCorner = null;
    mobilityCustomBounds = null;
    layers.results.clearLayers();
    setResult("Click two corners on the map to draw a small MobilityDB search area.");
    refreshMobilityAreaHint();
}

function useMobilityCurrentView() {
    mobilityAreaPicking = false;
    mobilityAreaFirstCorner = null;
    mobilityCustomBounds = null;
    layers.results.clearLayers();
    const bounds = map.getBounds();
    drawMobilitySearchArea(bounds);
    setResult("Mobility search area changed to the current visible map. Now press Find Trips in Selected Area.");
    refreshMobilityAreaHint();
}

function handleMobilityAreaClick(e) {
    if (!mobilityAreaPicking) return;

    if (!mobilityAreaFirstCorner) {
        mobilityAreaFirstCorner = e.latlng;
        setResult("First corner selected. Click the opposite corner.");
        refreshMobilityAreaHint();
        return;
    }

    const second = e.latlng;
    const south = Math.min(mobilityAreaFirstCorner.lat, second.lat);
    const north = Math.max(mobilityAreaFirstCorner.lat, second.lat);
    const west = Math.min(mobilityAreaFirstCorner.lng, second.lng);
    const east = Math.max(mobilityAreaFirstCorner.lng, second.lng);

    mobilityCustomBounds = L.latLngBounds([[south, west], [north, east]]);
    mobilityAreaPicking = false;
    mobilityAreaFirstCorner = null;

    layers.results.clearLayers();
    drawMobilitySearchArea(mobilityCustomBounds);
    map.fitBounds(mobilityCustomBounds, { padding: [30, 30] });

    setResult("Custom MobilityDB search area selected. Now press Find Trips in Selected Area.");
    refreshMobilityAreaHint();
}

function getMobilitySearchBounds() {
    return mobilityCustomBounds || map.getBounds();
}

function mobilityBoundsToParams(bounds) {
    return {
        min_lon: bounds.getWest(),
        min_lat: bounds.getSouth(),
        max_lon: bounds.getEast(),
        max_lat: bounds.getNorth(),
    };
}

function drawMobilitySearchArea(bounds) {
    L.rectangle(bounds, {
        color: "#16a085",
        weight: 2,
        fill: false,
    }).addTo(layers.results);
}

function mobilityAreaLooksTooLarge(bounds) {
    const lonWidth = Math.abs(bounds.getEast() - bounds.getWest());
    const latHeight = Math.abs(bounds.getNorth() - bounds.getSouth());
    return (lonWidth > 0.30 || latHeight > 0.20 || map.getZoom() < 11) && !mobilityCustomBounds;
}

async function getMobilityRouteLabel(routeId) {
    const key = String(routeId || "");
    if (!key) return "Unknown route";
    if (mobilityRouteLabelCache.has(key)) return mobilityRouteLabelCache.get(key);

    let label = `Route ${key}`;
    try {
        const routes = await loadAllRoutes();
        const route = routes.find(r => String(r.route_id) === key);
        if (route) {
            const shortName = route.route_short_name || route.route_id;
            const longName = route.route_long_name ? ` - ${route.route_long_name}` : "";
            label = `${shortName}${longName}`;
        }
    } catch (err) {
        // Labels are only for display. Mobility tools still work if route names cannot be loaded.
    }

    mobilityRouteLabelCache.set(key, label);
    return label;
}

async function enrichMobilityTripLabels(trips) {
    for (const trip of trips) {
        trip.route_label = await getMobilityRouteLabel(trip.route_id);
    }
    return trips;
}

function normalizeMobilityTrip(row) {
    return {
        trip_id: row.trip_id,
        route_id: row.route_id,
        service_id: row.service_id,
        date: row.date || getMobilitySelectedDate() || "",
        raw: row,
    };
}

function mergeMobilityTrips(rows) {
    const seen = new Map();
    rows.forEach(row => {
        const key = `${row.trip_id}|${row.date || ""}`;
        if (row.trip_id && !seen.has(key)) seen.set(key, row);
    });
    return [...seen.values()];
}

function getSelectedMobilityTrip() {
    if (mobilitySelectedTrip) return mobilitySelectedTrip;

    const select = document.getElementById("mobilityTripSelect");
    const selectedIndex = select?.value;
    if (selectedIndex === "" || selectedIndex === undefined) return null;

    return mobilityTripsCache[Number(selectedIndex)] || null;
}

function onMobilityTripSelectChange() {
    const select = document.getElementById("mobilityTripSelect");
    const selectedIndex = select?.value;
    mobilitySelectedTrip = selectedIndex === "" ? null : (mobilityTripsCache[Number(selectedIndex)] || null);
    updateMobilitySelectedTripInfo();
}

function selectMobilityTrip(index) {
    const select = document.getElementById("mobilityTripSelect");
    if (select) select.value = String(index);
    mobilitySelectedTrip = mobilityTripsCache[index] || null;
    updateMobilitySelectedTripInfo();
}

function updateMobilitySelectedTripInfo() {
    const box = document.getElementById("mobilitySelectedTripInfo");
    if (!box) return;

    const trip = getSelectedMobilityTrip();
    if (!trip) {
        box.innerHTML = "No trip selected yet.";
        return;
    }

    box.innerHTML = `
        <b>${escapeHtml(trip.route_label || `Route ${trip.route_id || ""}`)}</b><br>
        Selected result #${mobilityTripsCache.indexOf(trip) + 1}<br>
        <small>Trip ID is hidden from the normal user flow, but available in Advanced tab for testing.</small>
    `;
}

function fillMobilityTripSelect() {
    const select = document.getElementById("mobilityTripSelect");
    if (!select) return;

    select.innerHTML = `<option value="">Choose a found trip...</option>`;
    mobilityTripsCache.forEach((trip, index) => {
        const option = document.createElement("option");
        option.value = String(index);
        option.textContent = `${index + 1}. ${trip.route_label || `Route ${trip.route_id || ""}`}`;
        select.appendChild(option);
    });
}

function renderMobilityTripResults(date, bounds) {
    fillMobilityTripSelect();

    let html = `
        <h4>MobilityDB Trips Found</h4>
        <b>Date:</b> ${escapeHtml(date)}<br>
        <b>Search area:</b> ${mobilityCustomBounds ? "custom drawn rectangle" : "current map view"}<br>
        <b>Results:</b> ${mobilityTripsCache.length}<br>
        <small>Select one result, then animate it or check its position at a time.</small>
        <hr>
    `;

    if (!mobilityTripsCache.length) {
        html += "No trips found. Try a different date or a slightly larger nearby area.";
        setResult(html);
        updateMobilitySelectedTripInfo();
        return;
    }

    mobilityTripsCache.slice(0, 80).forEach((trip, index) => {
        html += `
            <div style="padding: 8px; border-bottom: 1px solid #ddd; cursor: pointer; border-left: 4px solid #16a085; margin-bottom: 4px;"
                 onclick="selectMobilityTrip(${index})">
                <b>${index + 1}. ${escapeHtml(trip.route_label || `Route ${trip.route_id || ""}`)}</b><br>
                <small>Click to select this trip for animation.</small>
            </div>
        `;
    });

    setResult(html);
}

function buildMobilityUserError(errors) {
    const joined = errors.filter(Boolean).join("\n");

    if (joined.includes("trips_mdb") || joined.includes("does not exist")) {
        return "MobilityDB table trips_mdb is missing. Run the MobilityDB transformation first.";
    }
    if (joined.includes("tuple index out of range") || joined.includes("IndexError")) {
        return "The MobilityDB SQL function has a parameter mismatch. Replace RQuery_MobilityDB.py with the fixed version.";
    }
    if (joined.includes("500")) {
        return "The backend returned an internal error. Check the FastAPI terminal for the exact SQL error.";
    }

    return joined || "MobilityDB request failed.";
}

// FUNCTION 1: Find trips in selected area. This avoids the heavy all-vehicles-at-time endpoint.
async function findMobilityTripsInArea() {
    const date = getMobilitySelectedDate();
    if (!date) return setResult("Choose a service date first.");

    const bounds = getMobilitySearchBounds();
    if (mobilityAreaLooksTooLarge(bounds)) {
        drawMobilitySearchArea(bounds);
        return setResult(`
            <h4>Search area is too large for a fast demo</h4>
            Zoom in closer or press <b>Draw Area on Map</b> and select a small rectangle.<br><br>
            This prevents slow searches over millions of MobilityDB trajectories.
        `);
    }

    const area = mobilityBoundsToParams(bounds);
    const url = `${API_BASE_URL}/mobilitydb/trips_in_area?` + new URLSearchParams({
        min_lon: area.min_lon,
        min_lat: area.min_lat,
        max_lon: area.max_lon,
        max_lat: area.max_lat,
        date,
    });

    showSpinner(true);
    clearMobilityLayersOnly();
    drawMobilitySearchArea(bounds);

    try {
        const data = await fetchJson(url);
        const rows = Array.isArray(data) ? data : [data];
        const trips = mergeMobilityTrips(rows.map(normalizeMobilityTrip)).slice(0, 100);

        mobilityTripsCache = await enrichMobilityTripLabels(trips);
        mobilitySelectedTrip = mobilityTripsCache[0] || null;

        if (mobilityTripsCache.length && document.getElementById("mobilityTripSelect")) {
            fillMobilityTripSelect();
            document.getElementById("mobilityTripSelect").value = "0";
        }

        renderMobilityTripResults(date, bounds);
        updateMobilitySelectedTripInfo();

        if (mobilityTripsCache.length) {
            setResult(document.getElementById("resultBox").innerHTML + `
                <hr><b>Recommended next step:</b> press <b>Show / Animate Trip</b>.
            `);
        }
    } catch (err) {
        setResult(`
            <h4>Could not find MobilityDB trips</h4>
            ${escapeHtml(buildMobilityUserError([err.message]))}<br><br>
            <b>Try this:</b><br>
            1. Use the demo date <b>${escapeHtml(date)}</b><br>
            2. Press <b>Go to Demo Area</b><br>
            3. Press <b>Find Trips in Selected Area</b> again<br>
            4. If still empty, draw a slightly larger rectangle.
        `);
    } finally {
        showSpinner(false);
    }
}

function extractLatLonFromMobilityRow(row) {
    if (!row) return null;

    if (row.lat !== undefined && row.lon !== undefined && row.lat !== null && row.lon !== null) {
        const lat = Number(row.lat);
        const lon = Number(row.lon);
        if (!Number.isNaN(lat) && !Number.isNaN(lon)) return { lat, lon };
    }

    const geojson = row.geojson || row.position?.geojson || row.position;
    if (geojson && typeof geojson === "object") {
        const coords = geojson.coordinates || geojson.geometry?.coordinates;
        if (Array.isArray(coords) && coords.length >= 2) {
            const lon = Number(coords[0]);
            const lat = Number(coords[1]);
            if (!Number.isNaN(lat) && !Number.isNaN(lon)) return { lat, lon };
        }
    }

    const text = typeof geojson === "string" ? geojson : JSON.stringify(row.position || row || "");
    const pointMatch = text.match(/POINT\s*\(?\s*([+-]?\d+(?:\.\d+)?)\s+([+-]?\d+(?:\.\d+)?)/i);
    if (pointMatch) {
        const lon = Number(pointMatch[1]);
        const lat = Number(pointMatch[2]);
        if (!Number.isNaN(lat) && !Number.isNaN(lon)) return { lat, lon };
    }

    return null;
}

function getPositionsFromAnimatedResponse(data, selectedDate) {
    const rows = Array.isArray(data) ? data : [data];
    const chosen = rows.find(item => selectedDate && String(item.date) === String(selectedDate)) || rows[0];
    return {
        row: chosen,
        positions: (chosen?.positions || [])
            .map(p => ({ lat: Number(p.lat), lon: Number(p.lon), time: p.time }))
            .filter(p => !Number.isNaN(p.lat) && !Number.isNaN(p.lon)),
    };
}

function decimatePositions(positions, maxPoints = 900) {
    if (positions.length <= maxPoints) return positions;
    const step = Math.ceil(positions.length / maxPoints);
    return positions.filter((_, index) => index % step === 0 || index === positions.length - 1);
}

function drawMobilityTrajectory(positions, routeLabel) {
    const displayPositions = decimatePositions(positions, 900);
    const latlngs = displayPositions.map(p => [p.lat, p.lon]);
    if (!latlngs.length) return null;

    const line = L.polyline(latlngs, {
        color: "#8e44ad",
        weight: 4,
        opacity: 0.85,
    }).addTo(layers.results);

    L.circleMarker(latlngs[0], {
        radius: 7,
        color: "#27ae60",
        weight: 2,
        fillOpacity: 0.9,
    }).bindPopup(`<b>Start</b><br>${escapeHtml(routeLabel)}<br>${escapeHtml(displayPositions[0].time || "")}`).addTo(layers.results);

    L.circleMarker(latlngs[latlngs.length - 1], {
        radius: 7,
        color: "#c0392b",
        weight: 2,
        fillOpacity: 0.9,
    }).bindPopup(`<b>End</b><br>${escapeHtml(routeLabel)}<br>${escapeHtml(displayPositions[displayPositions.length - 1].time || "")}`).addTo(layers.results);

    return { line, latlngs, displayPositions };
}

function animateMobilityMarker(latlngs) {
    if (!latlngs.length) return;

    mobilityMovingMarker = L.marker(latlngs[0]).addTo(layers.results);
    let i = 0;
    const step = Math.max(1, Math.floor(latlngs.length / 120));

    mobilityAnimationTimer = setInterval(() => {
        if (i >= latlngs.length) {
            clearInterval(mobilityAnimationTimer);
            mobilityAnimationTimer = null;
            return;
        }
        mobilityMovingMarker.setLatLng(latlngs[i]);
        i += step;
    }, 100);
}

// FUNCTION 2: Animate selected trip.
async function showSelectedMobilityTrajectory() {
    const trip = getSelectedMobilityTrip();
    if (!trip) return setResult("Find trips first, then choose one from the dropdown or result list.");

    showSpinner(true);
    clearMobilityLayersOnly();

    try {
        const data = await fetchJson(`${API_BASE_URL}/mobilitydb/animated_vehicle_positions?trip_id=${encodeURIComponent(trip.trip_id)}`);
        const { row, positions } = getPositionsFromAnimatedResponse(data, trip.date || getMobilitySelectedDate());

        if (!positions.length) {
            return setResult("The selected trip was found, but the backend did not return movement points for animation.");
        }

        const routeLabel = trip.route_label || await getMobilityRouteLabel(row?.route_id || trip.route_id);
        const drawn = drawMobilityTrajectory(positions, routeLabel);
        if (!drawn) return setResult("Movement points were returned, but no valid map coordinates were found.");

        animateMobilityMarker(drawn.latlngs);

        const bounds = drawn.line.getBounds();
        if (bounds.isValid()) map.fitBounds(bounds, { padding: [35, 35] });

        const firstTime = mobilityTimeOnlyFromTimestamp(positions[0]?.time);
        if (firstTime && document.getElementById("mobilityPositionTime")) {
            document.getElementById("mobilityPositionTime").value = firstTime;
        }

        setResult(`
            <h4>Trip Movement Animation</h4>
            <b>Route:</b> ${escapeHtml(routeLabel)}<br>
            <b>Original movement points:</b> ${positions.length}<br>
            <b>Displayed map points:</b> ${drawn.displayPositions.length}<br>
            <b>Start:</b> ${escapeHtml(positions[0]?.time || "")}<br>
            <b>End:</b> ${escapeHtml(positions[positions.length - 1]?.time || "")}<br>
            <small>Purple line = trip trajectory, green = start, red = end, moving marker = animation.</small>
        `);
    } catch (err) {
        setResult(`<h4>Could not animate movement</h4>${escapeHtml(buildMobilityUserError([err.message]))}`);
    } finally {
        showSpinner(false);
    }
}

function findNearestAnimatedPosition(positions, targetTime) {
    const target = String(targetTime || "").match(/(\d{2}):(\d{2})/);
    if (!target || !positions.length) return positions[0] || null;
    const targetMinutes = Number(target[1]) * 60 + Number(target[2]);

    let best = null;
    let bestDiff = Infinity;
    positions.forEach(p => {
        const match = String(p.time || "").match(/(\d{2}):(\d{2})/);
        if (!match) return;
        const minutes = Number(match[1]) * 60 + Number(match[2]);
        const diff = Math.abs(minutes - targetMinutes);
        if (diff < bestDiff) {
            bestDiff = diff;
            best = p;
        }
    });
    return best || positions[0] || null;
}

// FUNCTION 3: Position of selected trip at chosen time.
async function showMobilityPositionAtTime() {
    const trip = getSelectedMobilityTrip();
    if (!trip) return setResult("Find trips first, then choose one from the dropdown or result list.");

    const date = trip.date || getMobilitySelectedDate();
    const time = document.getElementById("mobilityPositionTime")?.value;
    const timestamp = mobilityTimestamp(date, time);
    if (!timestamp) return setResult("Choose a time first.");

    showSpinner(true);
    stopMobilityAnimation();

    try {
        let point = null;
        let exact = true;
        let returnedTime = "";
        let routeLabel = trip.route_label || await getMobilityRouteLabel(trip.route_id);

        try {
            const data = await fetchJson(`${API_BASE_URL}/mobilitydb/vehicle_position_at_time?trip_id=${encodeURIComponent(trip.trip_id)}&timestamp=${encodeURIComponent(timestamp)}`);
            const rows = Array.isArray(data) ? data : [data];
            const row = rows.find(item => extractLatLonFromMobilityRow(item)) || rows[0];
            point = extractLatLonFromMobilityRow(row);
            if (row?.route_id) routeLabel = await getMobilityRouteLabel(row.route_id);
        } catch (err) {
            console.warn("Exact MobilityDB position endpoint failed. Using animation fallback.", err);
        }

        if (!point) {
            exact = false;
            const data = await fetchJson(`${API_BASE_URL}/mobilitydb/animated_vehicle_positions?trip_id=${encodeURIComponent(trip.trip_id)}`);
            const { positions } = getPositionsFromAnimatedResponse(data, date);
            const nearest = findNearestAnimatedPosition(positions, time);
            if (nearest) {
                point = { lat: Number(nearest.lat), lon: Number(nearest.lon) };
                returnedTime = nearest.time || "";
            }
        }

        if (!point || Number.isNaN(point.lat) || Number.isNaN(point.lon)) {
            return setResult("No valid vehicle position was found at this time. Try a time inside the trip movement period.");
        }

        L.circleMarker([point.lat, point.lon], {
            radius: 10,
            color: "#e67e22",
            weight: 3,
            fillOpacity: 0.95,
        }).bindPopup(`
            <b>${exact ? "Vehicle position" : "Nearest available position"}</b><br>
            ${escapeHtml(routeLabel)}<br>
            ${escapeHtml(time)}
        `).addTo(layers.results);

        map.setView([point.lat, point.lon], Math.max(map.getZoom(), 14));

        setResult(`
            <h4>${exact ? "Vehicle Position at Time" : "Nearest Vehicle Position"}</h4>
            <b>Route:</b> ${escapeHtml(routeLabel)}<br>
            <b>Requested time:</b> ${escapeHtml(time)}<br>
            ${returnedTime ? `<b>Nearest returned time:</b> ${escapeHtml(returnedTime)}<br>` : ""}
            <b>Latitude:</b> ${Number(point.lat).toFixed(6)}<br>
            <b>Longitude:</b> ${Number(point.lon).toFixed(6)}<br>
            <small>${exact ? "Orange marker shows the valueAtTimestamp result." : "Exact endpoint did not return coordinates, so the closest trip point was used."}</small>
        `);
    } catch (err) {
        setResult(`<h4>Could not show position</h4>${escapeHtml(buildMobilityUserError([err.message]))}`);
    } finally {
        showSpinner(false);
    }
}

function loadMobilityCurrentWindow() { return findMobilityTripsInArea(); }
function loadMobilityTrajectories() { return showSelectedMobilityTrajectory(); }
function loadMobilityAtTime() { return showMobilityPositionAtTime(); }
function loadMobilityWindow() { return findMobilityTripsInArea(); }
