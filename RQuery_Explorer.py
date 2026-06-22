'''
Done!
'''
from typing import Optional, List, Dict, Any
from database_Creation import execute_query


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

def get_full_network():
    query = """
    SELECT DISTINCT ON (r.route_id)
        r.route_id,
        r.route_short_name,
        r.route_long_name,
        ST_AsGeoJSON(
            ST_MakeLine(
                ST_MakePoint(s.shape_pt_lon, s.shape_pt_lat)
                ORDER BY s.shape_pt_sequence
            )
        ) AS geojson
    FROM shapes s
    JOIN trips t ON t.shape_id = s.shape_id
    JOIN routes r ON r.route_id = t.route_id
    GROUP BY r.route_id, r.route_short_name, r.route_long_name, s.shape_id;
    """
    return execute_query(query)

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
