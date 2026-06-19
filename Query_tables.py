'''
Work in progress -> not done
'''
from typing import Optional, List, Dict, Any
from database_Creation import execute_query, update_insert_delete_query


def get_all_routes() -> List[Dict[str, Any]]:
    query = """
    SELECT 
        r.route_id,
        r.route_short_name,
        r.route_long_name,
        r.route_type,
        r.agency_id,
        r.route_color,
        COUNT(DISTINCT t.trip_id) AS trip_count
    FROM routes r
    LEFT JOIN trips t ON r.route_id = t.route_id
    GROUP BY 
        r.route_id,
        r.route_short_name,
        r.route_long_name,
        r.route_type,
        r.agency_id,
        r.route_color
    ORDER BY r.route_short_name
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



def get_all_stops() -> List[Dict[str, Any]]:
    query = """
        SELECT stop_id, stop_code, stop_name, stop_desc, stop_lat, stop_lon,
               zone_id, stop_url, location_type, parent_station, 
               stop_timezone, wheelchair_boarding
        FROM stops
        ORDER BY stop_name
    """
    return execute_query(query)


def get_stop_by_id(stop_id: str) -> Dict[str, Any]:
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
    query = """
        SELECT stop_id, stop_code, stop_name, stop_desc, stop_lat, stop_lon,
               zone_id, stop_url, location_type, parent_station,
               stop_timezone, wheelchair_boarding,
               ST_Distance(
                   ST_SetSRID(ST_MakePoint(stop_lon, stop_lat), 4326)::geography,
                   ST_GeomFromText(%s, 4326)::geography
               )::numeric AS distance_m
        FROM stops
        WHERE ST_DWithin(
            ST_SetSRID(ST_MakePoint(stop_lon, stop_lat), 4326)::geography,
            ST_GeomFromText(%s, 4326)::geography,
            %s
        )
        ORDER BY distance_m ASC
    """
    point = f"POINT({lon} {lat})"
    return execute_query(query, (point, point, radius))


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


def get_mobility_trajectories() -> List[Dict[str, Any]]:
    """
    Retrieve full vehicle trajectories as GeoJSON lines.
    """
    query = """
        SELECT
            vehicle_id,
            route_id,
            ST_AsGeoJSON(trajectory(traj)) AS geojson
        FROM vehicle_trajectories
    """
    return execute_query(query)


def get_mobility_positions_at_time(timestamp: str) -> List[Dict[str, Any]]:
    """
    Retrieve vehicle positions at a specific timestamp as GeoJSON points.
    """
    query = """
        SELECT
            vehicle_id,
            route_id,
            ST_AsGeoJSON(valueAtTimestamp(traj, %s::timestamptz)) AS geojson
        FROM vehicle_trajectories
        WHERE valueAtTimestamp(traj, %s::timestamptz) IS NOT NULL
    """
    return execute_query(query, (timestamp, timestamp))


def get_mobility_trajectories_in_window(
    min_lon: float,
    min_lat: float,
    max_lon: float,
    max_lat: float
) -> List[Dict[str, Any]]:
    """
    Retrieve trajectories whose path intersects the selected spatial window.
    """
    query = """
        SELECT
            vehicle_id,
            route_id,
            ST_AsGeoJSON(trajectory(traj)) AS geojson
        FROM vehicle_trajectories
        WHERE ST_Intersects(
            trajectory(traj),
            ST_MakeEnvelope(%s, %s, %s, %s, 4326)
        )
    """
    return execute_query(query, (min_lon, min_lat, max_lon, max_lat))


def get_mobility_clipped_trajectories_in_window(
    min_lon: float,
    min_lat: float,
    max_lon: float,
    max_lat: float
) -> List[Dict[str, Any]]:
    """
    Retrieve only the part of each trajectory inside the selected window.
    """
    query = """
        SELECT
            vehicle_id,
            route_id,
            ST_AsGeoJSON(
                trajectory(
                    atGeometry(traj, ST_MakeEnvelope(%s, %s, %s, %s, 4326))
                )
            ) AS geojson
        FROM vehicle_trajectories
        WHERE atGeometry(traj, ST_MakeEnvelope(%s, %s, %s, %s, 4326)) IS NOT NULL
    """
    return execute_query(
        query,
        (
            min_lon, min_lat, max_lon, max_lat,
            min_lon, min_lat, max_lon, max_lat
        )
    )