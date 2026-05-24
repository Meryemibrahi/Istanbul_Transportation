"""
Stops API endpoints
done!
"""

from fastapi import APIRouter, FastAPI, HTTPException, Path, Query
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from math import radians, cos, sin, asin, sqrt
from Query_tables import (
    get_all_stops,
    get_stop_by_id,
    get_stops_near,
    get_stops_by_zone,
    get_stops_by_area,
    get_timetable_by_route_date
)


router = APIRouter()

class Stop(BaseModel):
    stop_id: str
    stop_code: Optional[str] = None
    stop_name: str
    stop_desc: Optional[str] = None
    stop_lat: float
    stop_lon: float
    zone_id: Optional[str] = None
    stop_url: Optional[str] = None
    location_type: Optional[int] = None
    parent_station: Optional[str] = None
    stop_timezone: Optional[str] = None
    wheelchair_boarding: Optional[int] = None


@router.get("/{stop_id}", response_model=Stop)
def get_stop(stop_id: str = Path(..., description="The ID of the stop to retrieve")) -> Stop:
    stop_data = get_stop_by_id(stop_id)
    if not stop_data:
        raise HTTPException(status_code=404, detail="Stop not found")
    return Stop(**stop_data)


@router.get("/nearest", response_model=List[Stop])
def get_nearest_stops(lat: float = Query(..., description="Latitude"), lon: float = Query(..., description="Longitude"), radius: int = Query(500, description="Search radius in meters")) -> List[Stop]:
    stops_data = get_stops_near(lat, lon, radius)
    return [Stop(**stop) for stop in stops_data]

@router.get("/route", response_model=List[Stop])
def get_route_between_stops(start: str = Query(..., description="Start stop ID"), end: str = Query(..., description="End stop ID")) -> List[Stop]:
    route_stops_data = get_timetable_by_route_date(start, end)
    return [Stop(**stop) for stop in route_stops_data]

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

@router.get("/inarea", response_model=List[Stop])
def get_stops_in_area(min_lat: float = Query(..., description="Minimum latitude"), max_lat: float = Query(..., description="Maximum latitude"), min_lon: float = Query(..., description="Minimum longitude"), max_lon: float = Query(..., description="Maximum longitude")) -> List[Stop]:
    stops_data = get_stops_by_area(min_lat, max_lat, min_lon, max_lon)
    return [Stop(**stop) for stop in stops_data]

