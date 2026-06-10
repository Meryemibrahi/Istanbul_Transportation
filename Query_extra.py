"""
Needed
"""

from typing import Dict, List
from database_Creation import execute_query


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
