from typing import List, Dict, Any
from database_Creation import execute_query


def get_vehicle_position_at_time(trip_id: str, timestamp: str) -> List[Dict[str, Any]]:
    query = """
        SELECT valueAtTimestamp(trip, %s) AS position
        FROM trips_mdb
        WHERE trip_id = %s;
    """
    return execute_query(query, (timestamp, trip_id))

def get_vehicle_speed(trip_id: str) -> List[Dict[str, Any]]:
    query = """
        SELECT trip_id, speed(trip) AS speed_m_per_s
        FROM trips_mdb
        WHERE trip_id = %s;
    """
    return execute_query(query, (trip_id,))

def get_distance_traveled(trip_id: str) -> List[Dict[str, Any]]:
    query = """
        SELECT trip_id, length(trip) AS distance_m
        FROM trips_mdb
        WHERE trip_id = %s;
    """
    return execute_query(query, (trip_id,))

def get_trips_in_area(min_lon: float, min_lat: float, max_lon: float, max_lat: float) -> List[Dict[str, Any]]:
    query = """
        SELECT trip_id, route_id
        FROM trips_mdb
        WHERE ST_Intersects(trajectory(trip), ST_MakeEnvelope(%s, %s, %s, %s, 4326));
    """
    return execute_query(query, (min_lon, min_lat, max_lon, max_lat))

def get_vehicle_positions_over_time(trip_id: str, start_time: str, end_time: str) -> List[Dict[str, Any]]:
    query = """
        SELECT trip_id, route_id,
            unnest(instants(atTime(trip, tstzspan(%s, %s)))) AS position
        FROM trips_mdb
        WHERE trip_id = %s;
    """
    return execute_query(query, (start_time, end_time, trip_id))