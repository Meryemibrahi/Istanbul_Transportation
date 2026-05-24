
from fastapi import APIRouter, HTTPException, Path, Query
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from Query_tables import (
    get_all_routes,
    get_route_by_id,
    get_paths_for_route_date,
    get_trip_by_id,
    get_timetable_by_route_date,
    get_shape_by_id
)

router = APIRouter()


@router.get("/routes")
def get_routes() -> List[Dict[str, Any]]:
    return get_all_routes()


@router.get("/routes/{route_id}")
def get_route(route_id: str = Path(..., description="The ID of the route to retrieve")) -> Dict[str, Any]:
    route_data = get_route_by_id(route_id)
    if not route_data:
        raise HTTPException(status_code=404, detail="Route not found")
    return route_data

@router.get("/paths")
def get_paths(route_id: str = Query(..., description="The ID of the route for which to retrieve paths"), date: str = Query(..., description="The date for which to retrieve paths")) -> List[Dict[str, Any]]:
    return get_paths_for_route_date(route_id, date)

@router.get("/trips/{trip_id}")
def get_trip(trip_id: str = Path(..., description="The ID of the trip to retrieve")) -> Dict[str, Any]:
    """
    Retrieve a specific trip by its ID.
    """
    trip_data = get_trip_by_id(trip_id)
    if not trip_data:
        raise HTTPException(status_code=404, detail="Trip not found")
    return trip_data

@router.get("/timetable")
def get_timetable(route_id: str = Query(..., description="The ID of the route for which to retrieve the timetable"), date: str = Query(..., description="The date for which to retrieve the timetable")) -> List[Dict[str, Any]]:
    return get_timetable_by_route_date(route_id, date)


@router.get("/shapes/{shape_id}")
def get_shape(shape_id: str = Path(..., description="The ID of the shape to retrieve")) -> Dict[str, Any]:
    shape_data = get_shape_by_id(shape_id)
    if not shape_data:
        raise HTTPException(status_code=404, detail="Shape not found")
    return shape_data

