from typing import List, Dict, Any
from database_Creation import execute_query

def get_vehicle_position_at_time(trip_id: str, timestamp: str) -> List[Dict[str, Any]]:
    query = """
        SELECT valueAtTimestamp(trip, %s) AS position
        FROM trips_mdb
        WHERE trip_id = %s;
    """
    return execute_query(query, (timestamp, trip_id))

def animated_vehicle_positions(trip_id: str) -> List[Dict[str, Any]]:
    query = """
        SELECT trip_id,
            json_agg(json_build_object(
                'time', getTimestamp(inst),
                'lon', ST_X(getValue(inst)::geometry),
                'lat', ST_Y(getValue(inst)::geometry)
            ) ORDER BY getTimestamp(inst)) AS positions
        FROM trips_mdb,
            LATERAL unnest(instants(trip)) AS inst
        WHERE trip_id = %s
        GROUP BY trip_id;
    """
    return execute_query(query, (trip_id,))

def get_distance_traveled(trip_id: str) -> List[Dict[str, Any]]:
    query = """
        SELECT trip_id, length(trip) AS distance_m
        FROM trips_mdb
        WHERE trip_id = %s;
    """
    return execute_query(query, (trip_id,))

def get_trips_in_area(min_lon: float, min_lat: float, max_lon: float, max_lat: float, date: str) -> List[Dict[str, Any]]:
    query = """
        SELECT trip_id, route_id
        FROM trips_mdb
        WHERE ST_Intersects(
            trajectory(atTime(trip, tstzspan(%s, %s, true, true))),
            ST_MakeEnvelope(%s, %s, %s, %s, 4326)
        )
        AND date = %s;
    """
    return execute_query(query, (min_lon, min_lat, max_lon, max_lat, date))

def get_all_vehicle_positions_at_time(date: str, start_timestamp: str, end_timestamp: str) -> List[Dict[str, Any]]:
    query = """
        SELECT trip_id, route_id,
        ST_X(valueAtTimestamp(trip, %s)::geometry) AS lon,
        ST_Y(valueAtTimestamp(trip, %s)::geometry) AS lat
        FROM trips_mdb
        WHERE trip && %s::timestamptz
        AND date = %s;
    """
    return execute_query(query, (date, start_timestamp, end_timestamp))


