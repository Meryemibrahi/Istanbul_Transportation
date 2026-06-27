"""
FastAPI router for advanced pathfinding and network analysis features
done! -> complete
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict


from RQuery_routing import (
    get_dijkstra_stop_list_query,
    get_astar_stop_list_query,
    get_vertex_id_from_stop_id,
)


router = APIRouter()


@router.get("/dijkstra")
def get_dijkstra_route(start_id: str, end_id: str):
    """
    Find shortest path using Dijkstra algorithm.
    Accepts stop IDs and converts them to vertex IDs internally.
    
    Args:
        start_id: Starting stop ID (string, e.g., "stop123")
        end_id: Ending stop ID (string, e.g., "stop456")
    """
    start_vertex_id = get_vertex_id_from_stop_id(start_id)
    end_vertex_id = get_vertex_id_from_stop_id(end_id)
    
    if start_vertex_id is None:
        raise HTTPException(status_code=404, detail=f"Start stop '{start_id}' not found in routing graph")
    if end_vertex_id is None:
        raise HTTPException(status_code=404, detail=f"End stop '{end_id}' not found in routing graph")
    
    stops = get_dijkstra_stop_list_query(start_vertex_id, end_vertex_id)
    
    if not stops:
        raise HTTPException(status_code=404, detail="No path found")

    # Calculate total distance and hops
    total_distance = stops[-1]['agg_cost'] if stops else 0
    hops = len(stops)
    
    return {
        "algorithm": "Dijkstra",
        "stops": stops,
        "total_distance": total_distance,
        "hops": hops
    }


@router.get("/astar")
def get_astar_route(start_id: str, end_id: str):
    """
    Find shortest path using A* algorithm.
    Accepts stop IDs and converts them to vertex IDs internally.
    
    Args:
        start_id: Starting stop ID (string, e.g., "stop123")
        end_id: Ending stop ID (string, e.g., "stop456")
    """
    start_vertex_id = get_vertex_id_from_stop_id(start_id)
    end_vertex_id = get_vertex_id_from_stop_id(end_id)
    
    if start_vertex_id is None:
        raise HTTPException(status_code=404, detail=f"Start stop '{start_id}' not found in routing graph")
    if end_vertex_id is None:
        raise HTTPException(status_code=404, detail=f"End stop '{end_id}' not found in routing graph")
    
    stops = get_astar_stop_list_query(start_vertex_id, end_vertex_id)
    
    if not stops:
        raise HTTPException(status_code=404, detail="No path found")

    # Calculate total distance and hops
    total_distance = stops[-1]['agg_cost'] if stops else 0
    hops = len(stops)
    
    return {
        "algorithm": "A*",
        "stops": stops,
        "total_distance": total_distance,
        "hops": hops
    }
