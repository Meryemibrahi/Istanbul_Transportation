"""
Stops API endpoints
done!
"""

from fastapi import APIRouter, Query
from typing import List, Dict, Any

from RQuery_Spail_tools import (
    get_stops_near,
    get_stops_by_area,
    get_busy_stops
)

router = APIRouter()

@router.get("/inarea")
def get_stops_in_area(min_lat: float = Query(..., description="Minimum latitude"), max_lat: float = Query(..., description="Maximum latitude"), min_lon: float = Query(..., description="Minimum longitude"), max_lon: float = Query(..., description="Maximum longitude")) -> List[Dict[str, Any]]:
    stops_data = get_stops_by_area(min_lat, max_lat, min_lon, max_lon)
    return stops_data

@router.get("/nearest")
def get_nearest_stops(lat: float = Query(..., description="Latitude"), lon: float = Query(..., description="Longitude"), radius: int = Query(500, description="Search radius in meters")) -> List[Dict[str, Any]]:
    stops_data = get_stops_near(lat, lon, radius)
    return stops_data

@router.get("/busy")
def return_busy_stops(start_time: str = Query(..., description="Start time"), end_time: str = Query(..., description="End time")) -> List[Dict[str, Any]]:
    busy_stops_data = get_busy_stops(start_time, end_time)
    return busy_stops_data