'''
Done!
'''
from typing import List, Dict, Any
from database_Creation import execute_query


def get_stops_by_area(min_lat: float, max_lat: float, min_lon: float, max_lon: float) -> List[Dict[str, Any]]:
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


def get_stops_near(lat: float, lon: float, radius: int = 500) -> List[Dict[str, Any]]:
    query = """
        SELECT stop_id, stop_code, stop_name, stop_desc, stop_lat, stop_lon,
               zone_id, stop_url, location_type, parent_station,
               stop_timezone, wheelchair_boarding,
               ST_Distance(
                   ST_Transform(ST_SetSRID(ST_MakePoint(stop_lon, stop_lat), 4326), 32635),
                   ST_Transform(ST_GeomFromText(%s, 4326), 32635)
               )::numeric AS distance_m
        FROM stops
        WHERE ST_DWithin(
            ST_Transform(ST_SetSRID(ST_MakePoint(stop_lon, stop_lat), 4326), 32635),
            ST_Transform(ST_GeomFromText(%s, 4326), 32635),
            %s
        )
        ORDER BY distance_m ASC
    """
    point = f"POINT({lon} {lat})"
    return execute_query(query, (point, point, radius))

def get_busy_stops(hour1: int, hour2: int) -> List[Dict[str, Any]]:
    query = """
        SELECT
            s.stop_id,
            s.stop_name,
            s.stop_lat,
            s.stop_lon,
            COUNT(DISTINCT st.trip_id) AS total_visits,
            COUNT(DISTINCT t.route_id) AS unique_routes
        FROM stop_times st
        JOIN stops s ON st.stop_id = s.stop_id
        JOIN trips t ON st.trip_id = t.trip_id
        WHERE CAST(SPLIT_PART(st.arrival_time, ':', 1) AS INTEGER) >= %s AND CAST(SPLIT_PART(st.arrival_time, ':', 1) AS INTEGER) < %s
        GROUP BY s.stop_id, s.stop_name, s.stop_lat, s.stop_lon
        ORDER BY total_visits DESC
        LIMIT 20;
    """
    return execute_query(query, (hour1, hour2))