from typing import Optional, List, Dict, Any
from database_Creation import execute_query, update_insert_delete_query


def get_all_routes() -> List[Dict[str, Any]]:
    query = """
        SELECT route_id, agency_id, route_short_name, route_long_name, 
               route_desc, route_type, route_url, route_color, route_text_color
        FROM routes
        ORDER BY route_short_name
    """
    return execute_query(query)


def get_route_by_id(route_id: str) -> Dict[str, Any]:
    query = """
        SELECT route_id, agency_id, route_short_name, route_long_name, 
               route_desc, route_type, route_url, route_color, route_text_color
        FROM routes
        WHERE route_id = %s
    """
    results = execute_query(query, (route_id,))
    return results[0] if results else {}


def get_routes_by_agency(agency_id: str) -> List[Dict[str, Any]]:
    query = """
        SELECT route_id, agency_id, route_short_name, route_long_name, 
               route_desc, route_type, route_url, route_color, route_text_color
        FROM routes
        WHERE agency_id = %s
        ORDER BY route_short_name
    """
    return execute_query(query, (agency_id,))

# ============================================================================
# STOPS TABLE QUERIES
# ============================================================================

def get_all_stops() -> List[Dict[str, Any]]:
    """Retrieve all stops"""
    query = """
        SELECT stop_id, stop_code, stop_name, stop_desc, stop_lat, stop_lon,
               zone_id, stop_url, location_type, parent_station, 
               stop_timezone, wheelchair_boarding
        FROM stops
        ORDER BY stop_name
    """
    return execute_query(query)


def get_stop_by_id(stop_id: str) -> Dict[str, Any]:
    """Retrieve a specific stop by ID"""
    query = """
        SELECT stop_id, stop_code, stop_name, stop_desc, stop_lat, stop_lon,
               zone_id, stop_url, location_type, parent_station, 
               stop_timezone, wheelchair_boarding
        FROM stops
        WHERE stop_id = %s
    """
    results = execute_query(query, (stop_id,))
    return results[0] if results else {}


def get_stops_near(lat: float, lon: float, radius: int = 500) -> List[Dict[str, Any]]:
    """
    Retrieve stops within a specified radius (in meters) using PostGIS
    
    Args:
        lat: Latitude
        lon: Longitude
        radius: Search radius in meters (default 500)
    """
    query = """
        SELECT stop_id, stop_code, stop_name, stop_desc, stop_lat, stop_lon,
               zone_id, stop_url, location_type, parent_station, 
               stop_timezone, wheelchair_boarding,
               ST_Distance(geom, ST_GeomFromText(%s, 4326))::numeric as distance_m
        FROM stops
        WHERE ST_DWithin(geom, ST_GeomFromText(%s, 4326), %s)
        ORDER BY distance_m ASC
    """
    point_wkt = f"POINT({lon} {lat})"
    return execute_query(query, (point_wkt, point_wkt, radius))


def get_stops_by_zone(zone_id: str) -> List[Dict[str, Any]]:
    """Retrieve all stops in a specific zone"""
    query = """
        SELECT stop_id, stop_code, stop_name, stop_desc, stop_lat, stop_lon,
               zone_id, stop_url, location_type, parent_station, 
               stop_timezone, wheelchair_boarding
        FROM stops
        WHERE zone_id = %s
        ORDER BY stop_name
    """
    return execute_query(query, (zone_id,))


def get_stops_by_area(min_lat: float, max_lat: float, min_lon: float, max_lon: float) -> List[Dict[str, Any]]:
    """Retrieve all stops within a bounding box area"""
    query = """
        SELECT stop_id, stop_code, stop_name, stop_desc, stop_lat, stop_lon,
               zone_id, stop_url, location_type, parent_station, 
               stop_timezone, wheelchair_boarding
        FROM stops
        WHERE stop_lat >= %s AND stop_lat <= %s
          AND stop_lon >= %s AND stop_lon <= %s
        ORDER BY stop_name
    """
    return execute_query(query, (min_lat, max_lat, min_lon, max_lon))

# ============================================================================
# SHAPES TABLE QUERIES
# ============================================================================

def get_shape_by_id(shape_id: str) -> List[Dict[str, Any]]:
    """Retrieve all points for a specific shape"""
    query = """
        SELECT shape_id, shape_pt_lat, shape_pt_lon, shape_pt_sequence, shape_dist_traveled
        FROM shapes
        WHERE shape_id = %s
        ORDER BY shape_pt_sequence ASC
    """
    return execute_query(query, (shape_id,))


def get_shapes_for_route(route_id: str) -> List[Dict[str, Any]]:
    """Retrieve all unique shapes used by trips on a specific route"""
    query = """
        SELECT DISTINCT t.shape_id
        FROM trips t
        WHERE t.route_id = %s AND t.shape_id IS NOT NULL
    """
    results = execute_query(query, (route_id,))
    # Get all shape points for each shape
    all_shapes = []
    for row in results:
        shape_id = row.get('shape_id')
        shape_points = get_shape_by_id(shape_id)
        all_shapes.append({
            'shape_id': shape_id,
            'points': shape_points
        })
    return all_shapes


# ============================================================================
# REAL-TIME VEHICLES QUERIES
# ============================================================================

def get_all_realtime_vehicles() -> List[Dict[str, Any]]:
    """Retrieve current position of all vehicles"""
    query = """
        SELECT vehicle_id, route_id, latitude, longitude, heading, speed, timestamp
        FROM realtime_vehicles
        ORDER BY timestamp DESC
        LIMIT 1000
    """
    return execute_query(query)


def get_realtime_vehicle_by_id(vehicle_id: str) -> Dict[str, Any]:
    """Retrieve current position of a specific vehicle"""
    query = """
        SELECT vehicle_id, route_id, latitude, longitude, heading, speed, timestamp
        FROM realtime_vehicles
        WHERE vehicle_id = %s
        ORDER BY timestamp DESC
        LIMIT 1
    """
    results = execute_query(query, (vehicle_id,))
    return results[0] if results else {}


def get_vehicle_trajectory(vehicle_id: str, start_time: str, end_time: str) -> List[Dict[str, Any]]:
    """
    Retrieve trajectory of a vehicle between two timestamps
    
    Args:
        vehicle_id: The vehicle ID
        start_time: Start timestamp (ISO format)
        end_time: End timestamp (ISO format)
    """
    query = """
        SELECT vehicle_id, route_id, latitude, longitude, heading, speed, timestamp
        FROM realtime_vehicles
        WHERE vehicle_id = %s AND timestamp >= %s AND timestamp <= %s
        ORDER BY timestamp ASC
    """
    return execute_query(query, (vehicle_id, start_time, end_time))


def insert_realtime_vehicle(vehicle_id: str, route_id: str, latitude: float, 
                           longitude: float, heading: Optional[float] = None,
                           speed: Optional[float] = None) -> int:
    """
    Insert or update a vehicle's real-time position
    """
    query = """
        INSERT INTO realtime_vehicles (vehicle_id, route_id, latitude, longitude, heading, speed, timestamp)
        VALUES (%s, %s, %s, %s, %s, %s, NOW())
        ON CONFLICT (vehicle_id, timestamp) DO UPDATE SET
            route_id = EXCLUDED.route_id,
            latitude = EXCLUDED.latitude,
            longitude = EXCLUDED.longitude,
            heading = EXCLUDED.heading,
            speed = EXCLUDED.speed
    """
    return update_insert_delete_query(query, (vehicle_id, route_id, latitude, longitude, heading, speed))


# ============================================================================
# PGROUTING QUERIES (Spatial Routing)
# ============================================================================

def get_shortest_path(start_stop_id: str, end_stop_id: str) -> List[Dict[str, Any]]:
    """
    Find shortest path between two stops using pgRouting Dijkstra algorithm.
    Requires pgRouting to be installed and routing network tables to be set up.
    
    Args:
        start_stop_id: Starting stop ID
        end_stop_id: Ending stop ID
        
    Returns:
        List of stops along the shortest path
    """
    query = """
        WITH route AS (
            SELECT seq, path_seq, start_vid, end_vid, node, edge, cost, agg_cost
            FROM pgr_dijkstra(
                'SELECT id, source, target, cost FROM ways',
                (SELECT stop_id FROM stops WHERE stop_id = %s LIMIT 1)::INTEGER,
                (SELECT stop_id FROM stops WHERE stop_id = %s LIMIT 1)::INTEGER,
                directed := true
            )
        )
        SELECT r.node, s.stop_id, s.stop_name, s.stop_lat, s.stop_lon, r.agg_cost as cost
        FROM route r
        LEFT JOIN stops s ON r.node::TEXT = s.stop_id
        ORDER BY r.seq ASC
    """
    return execute_query(query, (start_stop_id, end_stop_id))


def get_isochrone_stops(center_stop_id: str, max_cost: float) -> List[Dict[str, Any]]:
    """
    Find all stops reachable from a center stop within a cost threshold using pgRouting.
    Cost can represent distance, time, or other metrics depending on your network setup.
    
    Args:
        center_stop_id: Center stop ID
        max_cost: Maximum cost threshold (distance, time, etc.)
        
    Returns:
        List of stops within the cost threshold, ordered by cost
    """
    query = """
        WITH isochrone AS (
            SELECT seq, start_vid, node, edge, cost, agg_cost
            FROM pgr_drivingDistance(
                'SELECT id, source, target, cost FROM ways',
                (SELECT stop_id FROM stops WHERE stop_id = %s LIMIT 1)::INTEGER,
                %s,
                directed := true
            )
        )
        SELECT iso.node, s.stop_id, s.stop_name, s.stop_lat, s.stop_lon, 
               iso.agg_cost as cost, iso.seq
        FROM isochrone iso
        LEFT JOIN stops s ON iso.node::TEXT = s.stop_id
        WHERE s.stop_id IS NOT NULL
        ORDER BY iso.agg_cost ASC
    """
    return execute_query(query, (center_stop_id, max_cost))


def get_many_to_many_paths(start_stops: List[str], end_stops: List[str]) -> List[Dict[str, Any]]:
    """
    Find shortest paths from multiple start stops to multiple end stops.
    
    Args:
        start_stops: List of starting stop IDs
        end_stops: List of ending stop IDs
        
    Returns:
        List of paths for each start-end pair
    """
    # Build SQL array from stop IDs
    start_array = ', '.join([f"'{sid}'" for sid in start_stops])
    end_array = ', '.join([f"'{sid}'" for sid in end_stops])
    
    query = f"""
        WITH route AS (
            SELECT seq, path_seq, start_vid, end_vid, node, edge, cost, agg_cost
            FROM pgr_dijkstra(
                'SELECT id, source, target, cost FROM ways',
                ARRAY(SELECT stop_id FROM stops WHERE stop_id IN ({start_array}) LIMIT 10)::INTEGER[],
                ARRAY(SELECT stop_id FROM stops WHERE stop_id IN ({end_array}) LIMIT 10)::INTEGER[],
                directed := true
            )
        )
        SELECT r.start_vid, r.end_vid, r.node, s.stop_id, s.stop_name, 
               s.stop_lat, s.stop_lon, r.agg_cost as cost
        FROM route r
        LEFT JOIN stops s ON r.node::TEXT = s.stop_id
        ORDER BY r.start_vid, r.end_vid, r.seq ASC
    """
    return execute_query(query)


# ============================================================================
# TRIPS TABLE QUERIES
# ============================================================================

def get_all_trips() -> List[Dict[str, Any]]:
    """Retrieve all trips"""
    query = """
        SELECT trip_id, route_id, service_id, trip_headsign, direction_id, 
               block_id, shape_id, wheelchair_accessible, bikes_allowed
        FROM trips
        ORDER BY route_id, trip_headsign
    """
    return execute_query(query)


def get_trip_by_id(trip_id: str) -> Dict[str, Any]:
    """Retrieve a specific trip by ID"""
    query = """
        SELECT trip_id, route_id, service_id, trip_headsign, direction_id, 
               block_id, shape_id, wheelchair_accessible, bikes_allowed
        FROM trips
        WHERE trip_id = %s
    """
    results = execute_query(query, (trip_id,))
    return results[0] if results else {}


def get_trips_by_route(route_id: str, service_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Retrieve all trips for a specific route, optionally filtered by service
    
    Args:
        route_id: The route ID
        service_id: Optional service ID filter
    """
    if service_id:
        query = """
            SELECT trip_id, route_id, service_id, trip_headsign, direction_id, 
                   block_id, shape_id, wheelchair_accessible, bikes_allowed
            FROM trips
            WHERE route_id = %s AND service_id = %s
            ORDER BY trip_headsign
        """
        return execute_query(query, (route_id, service_id))
    else:
        query = """
            SELECT trip_id, route_id, service_id, trip_headsign, direction_id, 
                   block_id, shape_id, wheelchair_accessible, bikes_allowed
            FROM trips
            WHERE route_id = %s
            ORDER BY trip_headsign
        """
        return execute_query(query, (route_id,))


# ============================================================================
# STOP_TIMES TABLE QUERIES (Timetable)
# ============================================================================

def get_stop_times_by_trip(trip_id: str) -> List[Dict[str, Any]]:
    """Retrieve all stop times for a specific trip"""
    query = """
        SELECT st.trip_id, st.arrival_time, st.departure_time, st.stop_sequence,
               st.stop_id, st.stop_headsign, st.pickup_type, st.drop_off_type,
               s.stop_name, s.stop_lat, s.stop_lon
        FROM stop_times st
        JOIN stops s ON st.stop_id = s.stop_id
        WHERE st.trip_id = %s
        ORDER BY st.stop_sequence ASC
    """
    return execute_query(query, (trip_id,))


def get_timetable_by_route_date(route_id: str, service_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Retrieve timetable information for a route on a specific service day
    Returns all trips and their stop times
    """
    if service_id:
        query = """
            SELECT t.trip_id, t.route_id, t.service_id, t.trip_headsign,
                   st.arrival_time, st.departure_time, st.stop_sequence,
                   st.stop_id, s.stop_name, s.stop_lat, s.stop_lon
            FROM trips t
            JOIN stop_times st ON t.trip_id = st.trip_id
            JOIN stops s ON st.stop_id = s.stop_id
            WHERE t.route_id = %s AND t.service_id = %s
            ORDER BY t.trip_headsign, st.stop_sequence ASC
        """
        return execute_query(query, (route_id, service_id))
    else:
        query = """
            SELECT t.trip_id, t.route_id, t.service_id, t.trip_headsign,
                   st.arrival_time, st.departure_time, st.stop_sequence,
                   st.stop_id, s.stop_name, s.stop_lat, s.stop_lon
            FROM trips t
            JOIN stop_times st ON t.trip_id = st.trip_id
            JOIN stops s ON st.stop_id = s.stop_id
            WHERE t.route_id = %s
            ORDER BY t.trip_headsign, st.stop_sequence ASC
        """
        return execute_query(query, (route_id,))


def get_paths_for_route_date(route_id: str, service_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Get unique paths (sequences of stops) for a route on a specific service day
    Deduplicates paths that appear multiple times
    """
    if service_id:
        query = """
            SELECT DISTINCT t.trip_id, st.stop_id, st.stop_sequence,
                   s.stop_name, s.stop_lat, s.stop_lon
            FROM trips t
            JOIN stop_times st ON t.trip_id = st.trip_id
            JOIN stops s ON st.stop_id = s.stop_id
            WHERE t.route_id = %s AND t.service_id = %s
            ORDER BY t.trip_id, st.stop_sequence ASC
        """
        return execute_query(query, (route_id, service_id))
    else:
        query = """
            SELECT DISTINCT t.trip_id, st.stop_id, st.stop_sequence,
                   s.stop_name, s.stop_lat, s.stop_lon
            FROM trips t
            JOIN stop_times st ON t.trip_id = st.trip_id
            JOIN stops s ON st.stop_id = s.stop_id
            WHERE t.route_id = %s
            ORDER BY t.trip_id, st.stop_sequence ASC
        """
        return execute_query(query, (route_id,))



