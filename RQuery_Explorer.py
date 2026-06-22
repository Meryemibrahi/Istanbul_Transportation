'''
Done!
'''
from http.client import HTTPException
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


def get_route_with_stops(route_id: str) -> Dict[str, Any]:
    """Get a specific route and all its stops in order"""

    route_query = """
        SELECT 
            r.route_id,
            r.route_short_name,
            r.route_long_name,
            r.route_type,
            r.route_color,
            COUNT(DISTINCT t.trip_id) AS trip_count
        FROM routes r
        LEFT JOIN trips t ON r.route_id = t.route_id
        WHERE r.route_id = %s
        GROUP BY 
            r.route_id,
            r.route_short_name,
            r.route_long_name,
            r.route_type,
            r.route_color
    """

    route_data = execute_query(route_query, (route_id,))

    if not route_data:
        return {"error": f"Route {route_id} not found"}

    route = route_data[0]

    trip_query = """
        SELECT 
            t.trip_id
        FROM trips t
        JOIN stop_times st ON st.trip_id = t.trip_id
        WHERE t.route_id = %s
        GROUP BY t.trip_id
        ORDER BY COUNT(st.stop_id) DESC
        LIMIT 1
    """

    trip_data = execute_query(trip_query, (route_id,))

    if not trip_data:
        return {"error": f"No trips found for route {route_id}"}

    trip_id = trip_data[0]["trip_id"]

    stops_query = """
        SELECT
            s.stop_id,
            s.stop_code,
            s.stop_name,
            s.stop_lat,
            s.stop_lon,
            st.stop_sequence
        FROM stop_times st
        JOIN stops s ON s.stop_id = st.stop_id
        WHERE st.trip_id = %s
        ORDER BY st.stop_sequence
    """

    stops = execute_query(stops_query, (trip_id,))

    if not stops:
        return {"error": f"No stops found for route {route_id}"}

    return {
        "route": route,
        "stop_count": len(stops),
        "stops": stops
    }