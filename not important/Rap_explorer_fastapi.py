"""
Stops API endpoints
done!
"""

from fastapi import APIRouter, HTTPException, Path, Query
from typing import List, Dict, Any, Optional
from math import radians, cos, sin, asin, sqrt
from database_Creation import execute_query, connect_Database

from RQuery_Explorer import (
    get_all_stops,
    get_stop_by_id,
    get_stops_near,
    get_stops_by_area,
    get_timetable_by_route_date
)

router = APIRouter()

@router.get("")
def get_all_stops_endpoint() -> List[Dict[str, Any]]:
    """Get all stops from the database"""
    stops_data = get_all_stops()
    return stops_data

@router.get("/nearest")
def get_nearest_stops(lat: float = Query(..., description="Latitude"), lon: float = Query(..., description="Longitude"), radius: int = Query(500, description="Search radius in meters")) -> List[Dict[str, Any]]:
    stops_data = get_stops_near(lat, lon, radius)
    return stops_data

@router.get("/route")
def get_route_between_stops(start: str = Query(..., description="Start stop ID"), end: str = Query(..., description="End stop ID")) -> List[Dict[str, Any]]:
    route_stops_data = get_timetable_by_route_date(start, end)
    return route_stops_data

@router.get("/distance")
def calculate_distance(stop1: str = Query(..., description="First stop ID"), stop2: str = Query(..., description="Second stop ID")) -> float:
    stop1_data = get_stop_by_id(stop1)
    stop2_data = get_stop_by_id(stop2)

    if not stop1_data or not stop2_data:
        raise HTTPException(status_code=404, detail="One or both stops not found")

    lat1, lon1 = stop1_data['stop_lat'], stop1_data['stop_lon']
    lat2, lon2 = stop2_data['stop_lat'], stop2_data['stop_lon']

    # Haversine formula
    R = 6371000  # Radius of Earth in meters
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    distance = R * c
    return distance

@router.get("/{stop_id}")
def get_stop(stop_id: str = Path(..., description="The ID of the stop to retrieve")) -> Dict[str, Any]:
    stop_data = get_stop_by_id(stop_id)
    if not stop_data:
        raise HTTPException(status_code=404, detail="Stop not found")
    return stop_data