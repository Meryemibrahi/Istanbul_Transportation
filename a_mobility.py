import json
import logging
from fastapi import APIRouter, HTTPException, Query
from RQuery_Explorer import (
    get_mobility_trajectories,
    get_mobility_positions_at_time,
    get_mobility_trajectories_in_window,
    get_mobility_clipped_trajectories_in_window
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["mobility"])


def rows_to_feature_collection(rows):
    """
    Convert rows with a 'geojson' column into a GeoJSON FeatureCollection.
    """
    features = []

    for row in rows:
        geojson_text = row.get("geojson")
        if not geojson_text:
            continue

        geometry = json.loads(geojson_text)
        properties = {k: v for k, v in row.items() if k != "geojson"}

        features.append({
            "type": "Feature",
            "geometry": geometry,
            "properties": properties
        })

    return {
        "type": "FeatureCollection",
        "features": features
    }


@router.get("/trajectories")
def mobility_trajectories():
    """
    Return all full trajectories as GeoJSON.
    """
    try:
        rows = get_mobility_trajectories()
        return rows_to_feature_collection(rows)
    except Exception as e:
        logger.exception("Error fetching mobility trajectories")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/at-time")
def mobility_at_time(
    timestamp: str = Query(..., description="Example: 2026-05-25 08:05:00+03")
):
    """
    Return vehicle positions at a specific time as GeoJSON points.
    """
    try:
        rows = get_mobility_positions_at_time(timestamp)
        return rows_to_feature_collection(rows)
    except Exception as e:
        logger.exception("Error fetching mobility positions at time")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/in-window")
def mobility_in_window(
    min_lon: float = Query(...),
    min_lat: float = Query(...),
    max_lon: float = Query(...),
    max_lat: float = Query(...)
):
    """
    Return full trajectories that intersect a spatial window.
    """
    try:
        rows = get_mobility_trajectories_in_window(min_lon, min_lat, max_lon, max_lat)
        return rows_to_feature_collection(rows)
    except Exception as e:
        logger.exception("Error fetching mobility trajectories in window")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/clipped-window")
def mobility_clipped_window(
    min_lon: float = Query(...),
    min_lat: float = Query(...),
    max_lon: float = Query(...),
    max_lat: float = Query(...)
):
    """
    Return only the clipped parts of trajectories inside a spatial window.
    """
    try:
        rows = get_mobility_clipped_trajectories_in_window(min_lon, min_lat, max_lon, max_lat)
        return rows_to_feature_collection(rows)
    except Exception as e:
        logger.exception("Error fetching clipped mobility trajectories")
        raise HTTPException(status_code=500, detail=str(e))