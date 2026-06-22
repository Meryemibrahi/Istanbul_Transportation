'''
Done!
'''
from typing import Optional, List, Dict, Any
from database_Creation import execute_query


def get_stop_by_code(stop_code: str) -> Dict[str, Any]:
    query = """
        SELECT stop_id, stop_code, stop_name, stop_desc, stop_lat, stop_lon,
               zone_id, stop_url, location_type, parent_station, 
               stop_timezone, wheelchair_boarding
        FROM stops
        WHERE stop_code = %s
    """
    results = execute_query(query, (stop_code,))
    return results[0] if results else {}


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