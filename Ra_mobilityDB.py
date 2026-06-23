from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict

from database_Creation import execute_query, connect_Database
from RQuery_MobilityDB import (
    get_vehicle_position_at_time,
    animated_vehicle_positions,
    get_distance_traveled,
    get_trips_in_area,
    get_all_vehicle_positions_at_time,
)

router = APIRouter()

@router.get("/vehicle_position_at_time")
def vehicle_position_at_time(trip_id: str, timestamp: str):
    positions = get_vehicle_position_at_time(trip_id, timestamp)
    if not positions:
        raise HTTPException(status_code=404, detail="No position found for the given trip and timestamp")
    return positions

@router.get("/animated_vehicle_positions")
def animated_positions(trip_id: str):
    positions = animated_vehicle_positions(trip_id)
    if not positions:
        raise HTTPException(status_code=404, detail="No positions found for the given trip")
    return positions


@router.get("/trips_in_area")
def trips_in_area(min_lon: float, min_lat: float, max_lon: float,
        max_lat: float, date: str):
        trips = get_trips_in_area(min_lon, min_lat, max_lon, max_lat, date)
        if not trips:
            raise HTTPException(status_code=404, detail="No trips found in the specified area and date")
        return trips

@router.get("/all_vehicle_positions_at_time")
def all_vehicle_positions_at_time(date: str, start_timestamp: str, end_timestamp: str
):
    positions = get_all_vehicle_positions_at_time(date, start_timestamp, end_timestamp)
    if not positions:
        raise HTTPException(status_code=404, detail="No vehicle positions found for the given time range")
    return positions