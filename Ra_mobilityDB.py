from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict


from database_Creation import execute_query, connect_Database
from RQuery_MobilityDB import (
    get_vehicle_position_at_time,
    get_vehicle_speed,
    get_distance_traveled,
    get_trips_in_area,
    get_vehicle_positions_over_time,
)


router = APIRouter()

@router.get("/vehicle_position_at_time")
def vehicle_position_at_time(trip_id: str, timestamp: str):
    positions = get_vehicle_position_at_time(trip_id, timestamp)
    
    if not positions:
        raise HTTPException(status_code=404, detail="No position found for the given trip and timestamp")
    
    return positions

@router.get("/vehicle_speed")
def vehicle_speed(trip_id: str):
    speeds = get_vehicle_speed(trip_id)
    
    if not speeds:
        raise HTTPException(status_code=404, detail="No speed data found for the given trip")
    
    return speeds


@router.get("/distance_traveled")
def distance_traveled(trip_id: str):
    distances = get_distance_traveled(trip_id)
    
    if not distances:
        raise HTTPException(status_code=404, detail="No distance data found for the given trip")
    
    return distances


@router.get("/trips_in_area")
def trips_in_area(min_lon: float, min_lat: float, max_lon: float, max_lat: float):
    trips = get_trips_in_area(min_lon, min_lat, max_lon, max_lat)
    
    if not trips:
        raise HTTPException(status_code=404, detail="No trips found in the specified area")
    
    return trips

@router.get("/vehicle_positions_over_time")
def vehicle_positions_over_time(trip_id: str, start_timestamp: str, end_timestamp: str):
    positions = get_vehicle_positions_over_time(trip_id, start_timestamp, end_timestamp)
    
    if not positions:
        raise HTTPException(status_code=404, detail="No position data found for the given trip and time range")
    
    return positions