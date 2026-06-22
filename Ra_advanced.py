"""
Stops API endpoints
done!
"""

from fastapi import APIRouter, HTTPException, Path
from typing import List, Dict, Any

from RQuery_advanced import (
    get_stop_by_code,
    get_top_routes_by_trip_count
)


router = APIRouter()

@router.get("/{stop_code}")
def get_stop(stop_code: str = Path(..., description="The code of the stop to retrieve")) -> Dict[str, Any]:
    stop_data = get_stop_by_code(stop_code)
    if not stop_data:
        raise HTTPException(status_code=404, detail="Stop not found")
    return stop_data

@router.get("/top-routes")
def get_top_routes(limit: int = 10) -> List[Dict]:
    return get_top_routes_by_trip_count(limit)