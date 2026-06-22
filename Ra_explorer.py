"""
Stops API endpoints
done!
"""

from fastapi import APIRouter, HTTPException, Path
from typing import List, Dict, Any

from RQuery_Explorer import (
    get_all_routes,
    get_full_network,
    get_stop_by_id,
    get_all_stops,
    get_route_with_stops
)

router = APIRouter()

@router.get("")
def get_all_stops_endpoint():
    return get_all_stops()

@router.get("/routes")
def get_routes():
    return get_all_routes()

@router.get("/network")
def full_network():
    return get_full_network()

@router.get("/route/{route_id}")
def route_details(route_id: str):
    result = get_route_with_stops(route_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result

@router.get("/{stop_id}")
def get_stop(stop_id: str):
    stop_data = get_stop_by_id(stop_id)
    if not stop_data:
        raise HTTPException(status_code=404, detail="Stop not found")
    return stop_data


