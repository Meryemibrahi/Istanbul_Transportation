// ==================== API CONFIGURATION ====================
const API_BASE_URL = 'http://127.0.0.1:8000';

// ==================== MAP INITIALIZATION ====================
let map;
let layers = { stops: null, results: null, paths: null, network: null };
let currentPathLayers = [];
let isDrawingArea = false, areaStartPoint = null;
const DEFAULT_CENTER = [41.01, 28.97], DEFAULT_ZOOM = 11;

function initMap() {
    map = L.map('map').setView(DEFAULT_CENTER, DEFAULT_ZOOM);
    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '&copy; OpenStreetMap contributors'
    }).addTo(map);
    
    map.on('click', onMapClick);
    map.on('mousemove', e => {
        const lat = e.latlng.lat.toFixed(4), lon = e.latlng.lng.toFixed(4);
        document.getElementById('coordDisplay').textContent = `Lat: ${lat}, Lon: ${lon}`;
    });
    
    layers.stops = L.layerGroup().addTo(map);
    layers.results = L.layerGroup().addTo(map);
    layers.paths = L.layerGroup().addTo(map);
    layers.network = L.layerGroup().addTo(map);
}

// ==================== UTILITY FUNCTIONS ====================
function showSpinner(show = true) {
    document.getElementById('loadingSpinner').style.display = show ? 'flex' : 'none';
}

function setResult(html) {
    document.getElementById('resultBox').innerHTML = html;
}

function clearResults() {
    document.getElementById('resultBox').innerHTML = 'Ready';
}

function onMapClick(e) {
    if (isDrawingArea) {
        if (!areaStartPoint) {
            areaStartPoint = e.latlng;
            setResult('Click to complete area selection...');
        } else {
            completeAreaSelection(e.latlng);
        }
    }
}

// ==================== TAB NAVIGATION ====================
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const tabName = this.getAttribute('data-tab');
            switchTab(tabName);
        });
    });
    initMap();
});

function switchTab(tabName) {
    document.querySelectorAll('.tab-content').forEach(tab => tab.style.display = 'none');
    document.getElementById(tabName + '-tab').style.display = 'block';
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
}

// ==================== STOPS FUNCTIONS ====================
async function getStopById() {
    const stopId = document.getElementById('stopId').value;
    if (!stopId) return setResult('Enter a stop ID');
    
    showSpinner(true);
    try {
        const res = await fetch(`${API_BASE_URL}/stops/${stopId}`);
        if (!res.ok) throw new Error('Stop not found');
        const stop = await res.json();
        
        layers.results.clearLayers();
        const marker = L.circleMarker([stop.stop_lat, stop.stop_lon], {
            radius: 8, color: '#e74c3c', weight: 2, opacity: 1, fillOpacity: 0.8
        }).bindPopup(`<b>${stop.stop_name}</b><br>ID: ${stop.stop_id}`).addTo(layers.results);
        
        map.setView([stop.stop_lat, stop.stop_lon], 14);
        setResult(`<b>${stop.stop_name}</b><br>ID: ${stop.stop_id}<br>Lat: ${stop.stop_lat}<br>Lon: ${stop.stop_lon}`);
    } catch (err) {
        setResult(`Error: ${err.message}`);
    } finally {
        showSpinner(false);
    }
}

async function getStopByCode() {
    const code = document.getElementById('stopCode').value;
    if (!code) return setResult('Enter a stop code');
    
    showSpinner(true);
    try {
        const res = await fetch(`${API_BASE_URL}/stops/by-code/${code}`);
        if (!res.ok) throw new Error('Stop code not found');
        const stops = await res.json();
        
        layers.results.clearLayers();
        let html = `<h4>Found ${stops.length} stop(s)</h4>`;
        
        stops.forEach(stop => {
            const marker = L.circleMarker([stop.stop_lat, stop.stop_lon], {
                radius: 6, color: '#3498db', weight: 2, fillOpacity: 0.7
            }).bindPopup(`${stop.stop_name}<br>Code: ${stop.stop_code}`).addTo(layers.results);
            
            html += `<div style="padding: 5px; border-bottom: 1px solid #ddd;">
                <b>${stop.stop_name}</b><br>
                Code: ${stop.stop_code} | ID: ${stop.stop_id}
            </div>`;
        });
        
        setResult(html);
        if (stops.length > 0) map.setView([stops[0].stop_lat, stops[0].stop_lon], 13);
    } catch (err) {
        setResult(`Error: ${err.message}`);
    } finally {
        showSpinner(false);
    }
}

async function loadAllStops() {
    showSpinner(true);
    try {
        const res = await fetch(`${API_BASE_URL}/stops`);
        if (!res.ok) throw new Error('Failed to load stops');
        const stops = await res.json();
        
        layers.stops.clearLayers();
        let mcg = L.markerClusterGroup();
        
        stops.slice(0, 100).forEach(stop => {
            const marker = L.circleMarker([stop.stop_lat, stop.stop_lon], {
                radius: 4, color: '#27ae60', weight: 1, fillOpacity: 0.7
            }).bindPopup(`${stop.stop_name}<br>ID: ${stop.stop_id}`);
            mcg.addLayer(marker);
        });
        
        layers.stops.addLayer(mcg);
        setResult(`Loaded ${Math.min(stops.length, 100)} of ${stops.length} stops`);
    } catch (err) {
        setResult(`Error: ${err.message}`);
    } finally {
        showSpinner(false);
    }
}

async function findNearestStops() {
    const lat = document.getElementById('nearLat').value;
    const lon = document.getElementById('nearLon').value;
    const radius = document.getElementById('nearRadius').value || 500;
    
    if (!lat || !lon) return setResult('Enter latitude and longitude');
    
    showSpinner(true);
    try {
        const res = await fetch(`${API_BASE_URL}/stops/nearest?lat=${lat}&lon=${lon}&radius=${radius}`);
        if (!res.ok) throw new Error('No stops found');
        const stops = await res.json();
        
        layers.results.clearLayers();
        
        // Center point
        L.circleMarker([lat, lon], {
            radius: 5, color: '#f39c12', weight: 2, fillOpacity: 0.9
        }).addTo(layers.results);
        
        // Radius circle
        L.circle([lat, lon], { radius: radius, color: '#95a5a6', fill: false }).addTo(layers.results);
        
        // Stops
        let html = `<h4>Found ${stops.length} stops</h4>`;
        stops.forEach((stop, i) => {
            const marker = L.circleMarker([stop.stop_lat, stop.stop_lon], {
                radius: 5, color: '#e74c3c', weight: 1, fillOpacity: 0.7
            }).bindPopup(`${stop.stop_name}<br>Distance: ${Math.round(stop.distance_m)}m`).addTo(layers.results);
            
            html += `<div style="padding: 5px; border-bottom: 1px solid #ddd;">
                ${i+1}. <b>${stop.stop_name}</b><br>Distance: ${Math.round(stop.distance_m)}m
            </div>`;
        });
        
        map.setView([lat, lon], 13);
        setResult(html);
    } catch (err) {
        setResult(`Error: ${err.message}`);
    } finally {
        showSpinner(false);
    }
}

function enableAreaSelection() {
    isDrawingArea = true;
    areaStartPoint = null;
    setResult('Click on map to start area selection...');
}

async function completeAreaSelection(endPoint) {
    isDrawingArea = false;
    const minLat = Math.min(areaStartPoint.lat, endPoint.lat);
    const maxLat = Math.max(areaStartPoint.lat, endPoint.lat);
    const minLon = Math.min(areaStartPoint.lng, endPoint.lng);
    const maxLon = Math.max(areaStartPoint.lng, endPoint.lng);
    
    showSpinner(true);
    try {
        const res = await fetch(`${API_BASE_URL}/stops/inarea?min_lat=${minLat}&max_lat=${maxLat}&min_lon=${minLon}&max_lon=${maxLon}`);
        if (!res.ok) throw new Error('No stops found');
        const stops = await res.json();
        
        layers.results.clearLayers();
        L.rectangle([[minLat, minLon], [maxLat, maxLon]], {
            color: '#3498db', weight: 2, fill: false
        }).addTo(layers.results);
        
        stops.forEach(stop => {
            L.circleMarker([stop.stop_lat, stop.stop_lon], {
                radius: 5, color: '#9b59b6', weight: 1, fillOpacity: 0.7
            }).bindPopup(stop.stop_name).addTo(layers.results);
        });
        
        setResult(`Found ${stops.length} stops in area`);
    } catch (err) {
        setResult(`Error: ${err.message}`);
    } finally {
        showSpinner(false);
    }
}

// ==================== ROUTES FUNCTIONS ====================
async function loadTopRoutes() {
    const limit = document.getElementById('topRoutesLimit').value || 10;
    showSpinner(true);
    try {
        const res = await fetch(`${API_BASE_URL}/analysis/top-routes?limit=${limit}`);
        if (!res.ok) throw new Error('Failed to load routes');
        const data = await res.json();
        
        let html = `<h4>Top ${limit} Routes by Trips</h4>`;
        data.top_routes.forEach(route => {
            html += `<div style="padding: 8px; background: #ecf0f1; margin: 5px 0; border-radius: 4px; cursor: pointer;" onclick="showRouteWithStops('${route.route_id}')">
                <b>${route.route_short_name}</b> - ${route.route_long_name || 'N/A'}<br>
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

async function showRouteWithStops(routeId = null) {
    const id = routeId || document.getElementById('routeId').value;
    if (!id) return setResult('Enter a route ID');
    
    showSpinner(true);
    try {
        const res = await fetch(`${API_BASE_URL}/analysis/route/${id}`);
        if (!res.ok) throw new Error('Route not found');
        const data = await res.json();
        
        layers.results.clearLayers();
        
        // Draw route path
        const latlngs = data.stops.map(s => [s.stop_lat, s.stop_lon]);
        L.polyline(latlngs, { color: '#e74c3c', weight: 3, opacity: 0.7 }).addTo(layers.results);
        
        // Add stop markers with numbers
        data.stops.forEach((stop, i) => {
            const marker = L.circleMarker([stop.stop_lat, stop.stop_lon], {
                radius: 6, color: '#27ae60', weight: 2, fillOpacity: 0.9
            }).bindPopup(`${i+1}. ${stop.stop_name}`).addTo(layers.results);
            
            L.divIcon({
                html: `<div style="background: #27ae60; color: white; border-radius: 50%; width: 20px; height: 20px; display: flex; align-items: center; justify-content: center; font-weight: bold;">${i+1}</div>`
            });
        });
        
        let html = `<h4>Route: ${data.route.route_short_name}</h4>
            <b>Name:</b> ${data.route.route_long_name || 'N/A'}<br>
            <b>Stops:</b> ${data.stop_count}<br>
            <b>Trips:</b> ${data.route.trip_count}<br>
            <h5>Stops in Order:</h5>`;
        
        data.stops.forEach((stop, i) => {
            html += `<div style="padding: 4px 0; border-bottom: 1px solid #ddd;">
                ${i+1}. <b>${stop.stop_name}</b> (${stop.stop_id})
            </div>`;
        });
        
        setResult(html);
        if (data.stops.length > 0) {
            const bounds = L.latLngBounds(latlngs);
            map.fitBounds(bounds);
        }
    } catch (err) {
        setResult(`Error: ${err.message}`);
    } finally {
        showSpinner(false);
    }
}

// ==================== PATHFINDING FUNCTIONS ====================
async function runDijkstra() {
    const start = document.getElementById('pathStart').value;
    const end = document.getElementById('pathEnd').value;
    if (!start || !end) return setResult('Enter start and end stops');
    
    showSpinner(true);
    try {
        const res = await fetch(`${API_BASE_URL}/analysis/dijkstra?start=${start}&end=${end}`);
        if (!res.ok) throw new Error('Path not found');
        const path = await res.json();
        
        drawPath(path, 'Dijkstra', '#3498db');
        displayPathInfo(path);
    } catch (err) {
        setResult(`Error: ${err.message}`);
    } finally {
        showSpinner(false);
    }
}

async function runAStar() {
    const start = document.getElementById('pathStart').value;
    const end = document.getElementById('pathEnd').value;
    if (!start || !end) return setResult('Enter start and end stops');
    
    showSpinner(true);
    try {
        const res = await fetch(`${API_BASE_URL}/analysis/astar?start=${start}&end=${end}`);
        if (!res.ok) throw new Error('Path not found');
        const path = await res.json();
        
        drawPath(path, 'A*', '#e74c3c');
        displayPathInfo(path);
    } catch (err) {
        setResult(`Error: ${err.message}`);
    } finally {
        showSpinner(false);
    }
}

async function comparePaths() {
    const start = document.getElementById('pathStart').value;
    const end = document.getElementById('pathEnd').value;
    if (!start || !end) return setResult('Enter start and end stops');
    
    showSpinner(true);
    try {
        const res = await fetch(`${API_BASE_URL}/analysis/compare-paths?start=${start}&end=${end}`);
        if (!res.ok) throw new Error('Comparison failed');
        const data = await res.json();
        
        layers.paths.clearLayers();
        
        // Draw both paths
        const dijkstraLatlngs = data.dijkstra.path.map(p => [p.lat, p.lon]);
        const astarLatlngs = data.astar.path.map(p => [p.lat, p.lon]);
        
        L.polyline(dijkstraLatlngs, { color: '#3498db', weight: 3, opacity: 0.6, dashArray: '5,5' }).addTo(layers.paths);
        L.polyline(astarLatlngs, { color: '#e74c3c', weight: 3, opacity: 0.6 }).addTo(layers.paths);
        
        // Add markers
        dijkstraLatlngs.forEach((p, i) => {
            L.circleMarker(p, { radius: 4, color: '#3498db', weight: 1 }).addTo(layers.paths);
        });
        astarLatlngs.forEach((p, i) => {
            L.circleMarker(p, { radius: 4, color: '#e74c3c', weight: 1 }).addTo(layers.paths);
        });
        
        const comparison = data.comparison;
        let html = `<h4>Algorithm Comparison</h4>
            <div style="background: #ecf0f1; padding: 10px; border-radius: 4px; margin-bottom: 10px;">
            <b>Dijkstra:</b> ${Math.round(comparison.dijkstra_distance)}m, ${comparison.dijkstra_hops} hops<br>
            <b>A*:</b> ${Math.round(comparison.astar_distance)}m, ${comparison.astar_hops} hops<br>
            <b>Same Path:</b> ${comparison.same_path ? 'Yes' : 'No'}
            </div>
            
            <h5>Dijkstra Path:</h5>`;
        data.dijkstra.path.forEach(p => {
            html += `<div style="padding: 3px; font-size: 0.9em;"><b>${p.stop_name}</b> (${Math.round(p.distance_from_start)}m)</div>`;
        });
        
        html += `<hr><h5>A* Path:</h5>`;
        data.astar.path.forEach(p => {
            html += `<div style="padding: 3px; font-size: 0.9em;"><b>${p.stop_name}</b> (${Math.round(p.distance_from_start)}m)</div>`;
        });
        
        setResult(html);
        const bounds = L.latLngBounds(dijkstraLatlngs.concat(astarLatlngs));
        map.fitBounds(bounds);
    } catch (err) {
        setResult(`Error: ${err.message}`);
    } finally {
        showSpinner(false);
    }
}

function drawPath(path, algorithm, color) {
    layers.paths.clearLayers();
    const latlngs = path.path.map(p => [p.lat, p.lon]);
    
    L.polyline(latlngs, { color: color, weight: 3, opacity: 0.8 }).addTo(layers.paths);
    
    path.path.forEach((stop, i) => {
        const marker = L.circleMarker([stop.lat, stop.lon], {
            radius: 5, color: color, weight: 2, fillOpacity: 0.8
        }).bindPopup(`${i+1}. ${stop.stop_name}`).addTo(layers.paths);
    });
    
    const bounds = L.latLngBounds(latlngs);
    map.fitBounds(bounds);
}

function displayPathInfo(path) {
    let html = `<h4>${path.algorithm} Path</h4>
        Total Distance: ${Math.round(path.total_distance)}m<br>
        Hops: ${path.hops}<br>
        <h5>Route:</h5>`;
    
    path.path.forEach((stop, i) => {
        html += `<div style="padding: 5px; border-bottom: 1px solid #ddd;">
            ${i+1}. <b>${stop.stop_name}</b><br>
            Distance from start: ${Math.round(stop.distance_from_start)}m
        </div>`;
    });
    
    setResult(html);
}

// ==================== NETWORK FUNCTIONS ====================
async function displayFullNetwork() {
    showSpinner(true);
    try {
        const res = await fetch(`${API_BASE_URL}/analysis/network`);
        if (!res.ok) throw new Error('Network load failed');
        const network = await res.json();
        
        layers.network.clearLayers();
        let html = `<h4>Full Network Visualization</h4>
            <b>Stops:</b> ${network.stop_count}<br>
            <b>Routes:</b> ${network.route_count}<br><hr>`;
        
        // Sample stops (first 200 to avoid lag)
        network.stops.slice(0, 200).forEach(stop => {
            L.circleMarker([stop.stop_lat, stop.stop_lon], {
                radius: 3, color: '#27ae60', weight: 1, fillOpacity: 0.6, opacity: 0.6
            }).bindPopup(stop.stop_name).addTo(layers.network);
        });
        
        html += `<i>Displaying ${Math.min(network.stop_count, 200)} of ${network.stop_count} stops</i>`;
        setResult(html);
    } catch (err) {
        setResult(`Error: ${err.message}`);
    } finally {
        showSpinner(false);
    }
}

// ==================== ANALYSIS FUNCTIONS ====================
async function showBusiestStops() {
    const startHour = document.getElementById('busyStart').value || 6;
    const endHour = document.getElementById('busyEnd').value || 9;
    
    showSpinner(true);
    try {
        const res = await fetch(`${API_BASE_URL}/analysis/busiest-stops?start_hour=${startHour}&end_hour=${endHour}`);
        if (!res.ok) throw new Error('Analysis failed');
        const data = await res.json();
        
        layers.results.clearLayers();
        
        let html = `<h4>Busiest Stops: ${data.time_range}</h4>`;
        
        data.busiest_stops.forEach((stop, i) => {
            const marker = L.circleMarker([stop.stop_lat, stop.stop_lon], {
                radius: Math.max(5, Math.min(12, stop.total_visits / 10)),
                color: '#e74c3c', weight: 1, fillOpacity: 0.7
            }).bindPopup(`${stop.stop_name}<br>Visits: ${stop.total_visits}`).addTo(layers.results);
            
            html += `<div style="padding: 5px; background: #f39c12; color: white; border-radius: 3px; margin: 3px 0;">
                ${i+1}. <b>${stop.stop_name}</b><br>
                Visits: ${stop.total_visits} | Routes: ${stop.unique_routes}
            </div>`;
        });
        
        setResult(html);
        if (data.busiest_stops.length > 0) {
            const bounds = L.latLngBounds(data.busiest_stops.map(s => [s.stop_lat, s.stop_lon]));
            map.fitBounds(bounds);
        }
    } catch (err) {
        setResult(`Error: ${err.message}`);
    } finally {
        showSpinner(false);
    }
}

window.addEventListener('DOMContentLoaded', initMap);
