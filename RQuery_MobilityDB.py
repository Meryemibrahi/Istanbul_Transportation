from typing import List, Dict, Any
from database_Creation import execute_query


def get_vehicle_position_at_time(trip_id: str, timestamp: str) -> List[Dict[str, Any]]:
    """Return numeric lon/lat for one trip at one timestamp."""
    query = """
        WITH positions AS (
            SELECT
                trip_id,
                route_id,
                service_id,
                date,
                valueAtTimestamp(trip, %s::timestamptz) AS geom
            FROM trips_mdb
            WHERE trip_id = %s
        )
        SELECT
            trip_id,
            route_id,
            service_id,
            date,
            ST_X(geom::geometry) AS lon,
            ST_Y(geom::geometry) AS lat,
            ST_AsGeoJSON(geom::geometry)::json AS geojson
        FROM positions
        WHERE geom IS NOT NULL
        ORDER BY date
        LIMIT 20;
    """
    return execute_query(query, (timestamp, trip_id))


def animated_vehicle_positions(trip_id: str) -> List[Dict[str, Any]]:
    """Return ordered movement points for a trip animation."""
    query = """
        SELECT
            trip_id,
            route_id,
            service_id,
            date,
            ST_AsGeoJSON(trajectory(trip))::json AS geojson,
            json_agg(
                json_build_object(
                    'time', getTimestamp(inst),
                    'lon', ST_X(getValue(inst)::geometry),
                    'lat', ST_Y(getValue(inst)::geometry)
                )
                ORDER BY getTimestamp(inst)
            ) AS positions
        FROM trips_mdb,
            LATERAL unnest(instants(trip)) AS inst
        WHERE trip_id = %s
        GROUP BY trip_id, route_id, service_id, date, trip
        ORDER BY date
        LIMIT 20;
    """
    return execute_query(query, (trip_id,))


def get_distance_traveled(trip_id: str) -> List[Dict[str, Any]]:
    query = """
        SELECT trip_id, route_id, service_id, date, length(trip) AS distance_m
        FROM trips_mdb
        WHERE trip_id = %s
        ORDER BY date
        LIMIT 20;
    """
    return execute_query(query, (trip_id,))


def get_trips_in_area(
    min_lon: float,
    min_lat: float,
    max_lon: float,
    max_lat: float,
    date: str,
) -> List[Dict[str, Any]]:
    """Return trips whose trajectory intersects the selected map window on the selected date."""
    query = """
        SELECT
            trip_id,
            route_id,
            service_id,
            date,
            ST_AsGeoJSON(trajectory(trip))::json AS geojson
        FROM trips_mdb
        WHERE date = %s::date
          AND ST_Intersects(
                trajectory(trip),
                ST_MakeEnvelope(%s, %s, %s, %s, 4326)
          )
        ORDER BY route_id, trip_id
        LIMIT 150;
    """
    return execute_query(query, (date, min_lon, min_lat, max_lon, max_lat))


def get_all_vehicle_positions_at_time(date: str, start_timestamp: str, end_timestamp: str) -> List[Dict[str, Any]]:
    """Return visible vehicle positions at the chosen timestamp.

    The current router passes both start_timestamp and end_timestamp. The frontend uses
    start_timestamp as the display time and keeps end_timestamp for compatibility.
    """
    query = """
        SELECT
            trip_id,
            route_id,
            service_id,
            date,
            ST_X(valueAtTimestamp(trip, %s::timestamptz)::geometry) AS lon,
            ST_Y(valueAtTimestamp(trip, %s::timestamptz)::geometry) AS lat
        FROM trips_mdb
        WHERE date = %s::date
          AND valueAtTimestamp(trip, %s::timestamptz) IS NOT NULL
        ORDER BY route_id, trip_id
        LIMIT 500;
    """
    return execute_query(query, (start_timestamp, start_timestamp, date, start_timestamp))
