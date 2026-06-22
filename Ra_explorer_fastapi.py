"""
Stops API endpoints
done!
"""

from fastapi import APIRouter, FastAPI, HTTPException, Path, Query
from typing import List, Dict, Any, Optional
from math import radians, cos, sin, asin, sqrt
from database_Creation import execute_query, connect_Database

from RQuery_Explorer import (
    get_all_routes,
    get_full_network_query,
    get_stop_by_id,
    get_route_by_id,
    get_all_stops
)

router = APIRouter()

@router.get("")
def get_all_stops_endpoint() -> List[Dict[str, Any]]:
    stops_data = get_all_stops()
    return stops_data

@router.get("/{stop_id}")
def get_stop(stop_id: str = Path(..., description="The ID of the stop to retrieve")) -> Dict[str, Any]:
    stop_data = get_stop_by_id(stop_id)
    if not stop_data:
        raise HTTPException(status_code=404, detail="Stop not found")
    return stop_data

@router.get("/routes")
def get_routes() -> List[Dict[str, Any]]:
    return get_all_routes()
