"""
Stops API endpoints
done!
"""

from fastapi import APIRouter, FastAPI, HTTPException, Path, Query
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from RQuery_Explorer import (
    get_isochrone_stops,
    get_shortest_path,
)

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


router = APIRouter()

@router.get("/shortest", response_model=List[Stop])
def get_shortest_route(start: str = Query(..., description="Start stop ID"), end: str = Query(..., description="End stop ID")) -> List[Stop]:
    return get_shortest_path(start, end)

@router.get("/isochrone", response_model=List[Stop])
def get_isochrone_route(stop_id: str = Query(..., description="Center stop ID"), max_cost: float = Query(..., description="Maximum cost threshold")) -> List[Stop]:
    return get_isochrone_stops(stop_id, max_cost)