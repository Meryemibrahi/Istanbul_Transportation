"""
Advanced pathfinding algorithms: Dijkstra and A* for GTFS transit networks
Also includes network analysis features
"""
from typing import List, Dict, Tuple, Optional
from database_Creation import execute_query
import heapq
import math

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two coordinates in meters"""
    R = 6371000  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = math.sin(delta_phi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c


def get_stop_coords(stop_id: str) -> Tuple[float, float]:
    """Get latitude and longitude of a stop"""
    query = "SELECT stop_lat, stop_lon FROM stops WHERE stop_id = %s"
    result = execute_query(query, (stop_id,))
    if result:
        return result[0]['stop_lat'], result[0]['stop_lon']
    return None, None


# ============================================================================
# DIJKSTRA SHORTEST PATH
# ============================================================================

def dijkstra_shortest_path(start_stop_id: str, end_stop_id: str) -> Dict:
    """
    Find shortest path between two stops using Dijkstra's algorithm
    Uses transfer distance between stops as cost
    """
    start_lat, start_lon = get_stop_coords(start_stop_id)
    end_lat, end_lon = get_stop_coords(end_stop_id)
    
    if start_lat is None or end_lat is None:
        return {"error": "Invalid stop IDs"}
    
    # Get all stops for building the graph
    query = "SELECT stop_id, stop_lat, stop_lon FROM stops"
    all_stops = execute_query(query)
    
    # Build distance map (stops within 500m are connected)
    stops_map = {s['stop_id']: (s['stop_lat'], s['stop_lon']) for s in all_stops}
    
    # Dijkstra algorithm
    dist = {s['stop_id']: float('inf') for s in all_stops}
    dist[start_stop_id] = 0
    prev = {}
    visited = set()
    pq = [(0, start_stop_id)]
    
    while pq:
        current_dist, current = heapq.heappop(pq)
        
        if current in visited:
            continue
        visited.add(current)
        
        if current == end_stop_id:
            break
        
        if current_dist > dist[current]:
            continue
        
        # Find neighbors (stops within 500m)
        curr_lat, curr_lon = stops_map[current]
        for neighbor_id, (n_lat, n_lon) in stops_map.items():
            if neighbor_id not in visited:
                edge_cost = haversine_distance(curr_lat, curr_lon, n_lat, n_lon)
                if edge_cost <= 500:  # Only connect nearby stops
                    new_dist = dist[current] + edge_cost
                    if new_dist < dist[neighbor_id]:
                        dist[neighbor_id] = new_dist
                        prev[neighbor_id] = current
                        heapq.heappush(pq, (new_dist, neighbor_id))
    
    # Reconstruct path
    path = []
    current = end_stop_id
    total_cost = dist[end_stop_id]
    
    if total_cost == float('inf'):
        return {"error": "No path found", "start": start_stop_id, "end": end_stop_id}
    
    while current in prev:
        path.append(current)
        current = prev[current]
    path.append(start_stop_id)
    path.reverse()
    
    # Get stop details for the path
    path_details = []
    for i, stop_id in enumerate(path):
        stop_query = "SELECT stop_id, stop_name, stop_lat, stop_lon FROM stops WHERE stop_id = %s"
        stop_data = execute_query(stop_query, (stop_id,))
        if stop_data:
            path_details.append({
                "order": i + 1,
                "stop_id": stop_data[0]['stop_id'],
                "stop_name": stop_data[0]['stop_name'],
                "lat": stop_data[0]['stop_lat'],
                "lon": stop_data[0]['stop_lon'],
                "distance_from_start": dist[stop_id]
            })
    
    return {
        "algorithm": "Dijkstra",
        "start": start_stop_id,
        "end": end_stop_id,
        "total_distance": total_cost,
        "hops": len(path) - 1,
        "path": path_details
    }


# ============================================================================
# A* SHORTEST PATH
# ============================================================================

def a_star_shortest_path(start_stop_id: str, end_stop_id: str) -> Dict:
    """
    Find shortest path using A* algorithm
    Uses haversine heuristic to guide search
    """
    start_lat, start_lon = get_stop_coords(start_stop_id)
    end_lat, end_lon = get_stop_coords(end_stop_id)
    
    if start_lat is None or end_lat is None:
        return {"error": "Invalid stop IDs"}
    
    # Get all stops
    query = "SELECT stop_id, stop_lat, stop_lon FROM stops"
    all_stops = execute_query(query)
    stops_map = {s['stop_id']: (s['stop_lat'], s['stop_lon']) for s in all_stops}
    
    # A* algorithm
    g_score = {s['stop_id']: float('inf') for s in all_stops}
    g_score[start_stop_id] = 0
    f_score = {s['stop_id']: float('inf') for s in all_stops}
    f_score[start_stop_id] = haversine_distance(start_lat, start_lon, end_lat, end_lon)
    
    prev = {}
    visited = set()
    open_set = [(f_score[start_stop_id], start_stop_id)]
    
    while open_set:
        _, current = heapq.heappop(open_set)
        
        if current in visited:
            continue
        visited.add(current)
        
        if current == end_stop_id:
            break
        
        curr_lat, curr_lon = stops_map[current]
        
        # Find neighbors within 500m
        for neighbor_id, (n_lat, n_lon) in stops_map.items():
            if neighbor_id not in visited:
                edge_cost = haversine_distance(curr_lat, curr_lon, n_lat, n_lon)
                if edge_cost <= 500:
                    tentative_g = g_score[current] + edge_cost
                    if tentative_g < g_score[neighbor_id]:
                        prev[neighbor_id] = current
                        g_score[neighbor_id] = tentative_g
                        h_score = haversine_distance(n_lat, n_lon, end_lat, end_lon)
                        f_score[neighbor_id] = tentative_g + h_score
                        heapq.heappush(open_set, (f_score[neighbor_id], neighbor_id))
    
    # Reconstruct path
    path = []
    current = end_stop_id
    total_cost = g_score[end_stop_id]
    
    if total_cost == float('inf'):
        return {"error": "No path found", "start": start_stop_id, "end": end_stop_id}
    
    while current in prev:
        path.append(current)
        current = prev[current]
    path.append(start_stop_id)
    path.reverse()
    
    # Get stop details
    path_details = []
    for i, stop_id in enumerate(path):
        stop_query = "SELECT stop_id, stop_name, stop_lat, stop_lon FROM stops WHERE stop_id = %s"
        stop_data = execute_query(stop_query, (stop_id,))
        if stop_data:
            path_details.append({
                "order": i + 1,
                "stop_id": stop_data[0]['stop_id'],
                "stop_name": stop_data[0]['stop_name'],
                "lat": stop_data[0]['stop_lat'],
                "lon": stop_data[0]['stop_lon'],
                "distance_from_start": g_score[stop_id]
            })
    
    return {
        "algorithm": "A*",
        "start": start_stop_id,
        "end": end_stop_id,
        "total_distance": total_cost,
        "hops": len(path) - 1,
        "path": path_details
    }


# ============================================================================
# NETWORK ANALYSIS
# ============================================================================

def get_top_routes_by_trip_count(limit: int = 10) -> List[Dict]:
    """Get routes with most trips"""
    query = """
        SELECT 
            r.route_id,
            r.route_short_name,
            r.route_long_name,
            r.route_type,
            r.route_color,
            COUNT(DISTINCT t.trip_id) AS trip_count,
            COUNT(DISTINCT st.stop_id) AS stop_count
        FROM routes r
        LEFT JOIN trips t ON r.route_id = t.route_id
        LEFT JOIN stop_times st ON t.trip_id = st.trip_id
        GROUP BY r.route_id, r.route_short_name, r.route_long_name, r.route_type, r.route_color
        ORDER BY trip_count DESC
        LIMIT %s
    """
    return execute_query(query, (limit,))


def get_busiest_stops_by_time(start_hour: int = 0, end_hour: int = 23) -> List[Dict]:
    """
    Get busiest stops during a specific time range
    Based on number of arrivals/departures during that time
    """
    query = """
        SELECT 
            s.stop_id,
            s.stop_name,
            s.stop_lat,
            s.stop_lon,
            COUNT(DISTINCT st.trip_id) as total_visits,
            COUNT(DISTINCT t.route_id) as unique_routes
        FROM stops s
        LEFT JOIN stop_times st ON s.stop_id = st.stop_id
        LEFT JOIN trips t ON st.trip_id = t.trip_id
        WHERE EXTRACT(HOUR FROM st.arrival_time::TIME) >= %s
          AND EXTRACT(HOUR FROM st.arrival_time::TIME) < %s
        GROUP BY s.stop_id, s.stop_name, s.stop_lat, s.stop_lon
        ORDER BY total_visits DESC
        LIMIT 50
    """
    return execute_query(query, (start_hour, end_hour))


def get_full_network() -> Dict:
    """Get all stops and routes for network visualization"""
    stops_query = "SELECT stop_id, stop_name, stop_lat, stop_lon FROM stops ORDER BY stop_id"
    routes_query = """
        SELECT 
            r.route_id,
            r.route_short_name,
            r.route_long_name,
            r.route_type,
            r.route_color
        FROM routes r
    """
    
    stops = execute_query(stops_query)
    routes = execute_query(routes_query)
    
    return {
        "stops": stops,
        "routes": routes,
        "stop_count": len(stops),
        "route_count": len(routes)
    }


def get_route_with_stops(route_id: str) -> Dict:
    """Get a specific route and all its stops in order"""
    route_query = """
        SELECT 
            r.route_id,
            r.route_short_name,
            r.route_long_name,
            r.route_type,
            r.route_color,
            COUNT(DISTINCT t.trip_id) as trip_count
        FROM routes r
        LEFT JOIN trips t ON r.route_id = t.route_id
        WHERE r.route_id = %s
        GROUP BY r.route_id, r.route_short_name, r.route_long_name, r.route_type, r.route_color
    """
    
    route_data = execute_query(route_query, (route_id,))
    if not route_data:
        return {"error": f"Route {route_id} not found"}
    
    # Get stops for this route (ordered by sequence)
    stops_query = """
        SELECT
            s.stop_id,
            s.stop_name,
            s.stop_lat,
            s.stop_lon,
            st.stop_sequence as sequence
        FROM routes r
        JOIN trips t ON r.route_id = t.route_id
        JOIN stop_times st ON t.trip_id = st.trip_id
        JOIN stops s ON st.stop_id = s.stop_id
        WHERE r.route_id = %s
        AND t.trip_id = (SELECT trip_id FROM trips WHERE route_id = %s LIMIT 1)
        ORDER BY st.stop_sequence ASC
    """
    
    stops = execute_query(stops_query, (route_id, route_id))
    
    return {
        "route": route_data[0],
        "stops": stops,
        "stop_count": len(stops)
    }
