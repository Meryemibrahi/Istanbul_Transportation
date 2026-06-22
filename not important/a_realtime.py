# """
# done!
# """

from fastapi import APIRouter, HTTPException, Path, Query
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

# # from RQuery_Explorer import (
# #     get_all_realtime_vehicles,
# #     get_realtime_vehicle_by_id,
# #     get_vehicle_trajectory,
# # )

router = APIRouter()

# class VehiclePosition(BaseModel):
#     """Pydantic model for vehicle position"""
#     vehicle_id: str
#     route_id: str
#     latitude: float
#     longitude: float
#     heading: Optional[float] = None
#     speed: Optional[float] = None
#     timestamp: str


# class VehicleTrajectoryPoint(BaseModel):
#     """Pydantic model for a trajectory point"""
#     vehicle_id: str
#     latitude: float
#     longitude: float
#     heading: Optional[float] = None
#     speed: Optional[float] = None
#     timestamp: str


# @router.get("/vehicles")
# def get_realtime_vehicles() -> List[VehiclePosition]:
#     """
#     Retrieve real-time information about all vehicles.
#     """
#     return get_all_realtime_vehicles()

# @router.get("/vehicles/{vehicle_id}")
# def get_vehicle(vehicle_id: str = Path(..., description="The ID of the vehicle to retrieve")) -> Dict[str, Any]:
#     """
#     Retrieve real-time information about a specific vehicle by its ID.
#     """
#     vehicle_data = get_realtime_vehicle_by_id(vehicle_id)
#     if not vehicle_data:
#         raise HTTPException(status_code=404, detail="Vehicle not found")
#     return vehicle_data

# @router.get("/vehicles/{vehicle_id}/trajectory")
# def get_vehicle_trajectory_endpoint(vehicle_id: str = Path(..., description="The ID of the vehicle"), start: str = Query(..., description="Start timestamp (ISO format)"), end: str = Query(..., description="End timestamp (ISO format)")) -> List[Dict[str, Any]]:
#     """
#     Retrieve the trajectory of a specific vehicle between two timestamps.
#     """
#     try:
#         start_dt = datetime.fromisoformat(start)
#         end_dt = datetime.fromisoformat(end)
#     except ValueError:
#         raise HTTPException(status_code=400, detail="Invalid timestamp format. Use ISO format (YYYY-MM-DDTHH:MM:SS)")

#     if start_dt >= end_dt:
#         raise HTTPException(status_code=400, detail="Start timestamp must be before end timestamp")

#     trajectory_data = get_vehicle_trajectory(vehicle_id, start, end)
#     if not trajectory_data:
#         raise HTTPException(status_code=404, detail="No trajectory data found for this vehicle in the specified time range")
    
#     return trajectory_data

# # @router.get("/realtime/stops/{stop_id}/vehicles")
# # def get_vehicles_at_stop_endpoint(stop_id: str = Path(..., description="The ID of the stop"), within_meters: int = Query(500, description="Search radius in meters")) -> List[Dict[str, Any]]:
# #     """
# #     Retrieve vehicles that are currently at or near a specific stop.
# #     """
# #     vehicles_data = get_vehicles_at_stop(stop_id, within_meters)
# #     return vehicles_data