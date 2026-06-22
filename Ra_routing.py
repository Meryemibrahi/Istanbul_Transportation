"""
FastAPI router for advanced pathfinding and network analysis features
done! -> complete
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict


from database_Creation import execute_query, connect_Database


from RQuery_routing import (
    get_tsp_cost_matrix_query,
    get_tsp_selected_stops_query,
    get_tsp_order_query,
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

@router.get("/tsp")
def get_tsp_route(start_id: str, stop_ids: list[str] = Query(...)):
    """
    Find optimal TSP route through multiple stops.
    Accepts stop IDs (strings) and converts them to vertex IDs internally.
    
    Args:
        start_id: Starting stop ID (string, e.g., "stop123")
        stop_ids: List of stop IDs to visit (strings)
    """
    # Convert start_id to vertex_id
    start_vertex_id = get_vertex_id_from_stop_id(start_id)
    if start_vertex_id is None:
        raise HTTPException(status_code=404, detail=f"Start stop '{start_id}' not found in routing graph")
    
    # Convert all stop_ids to vertex_ids
    vertex_ids = []
    for stop_id in stop_ids:
        vertex_id = get_vertex_id_from_stop_id(stop_id)
        if vertex_id is None:
            raise HTTPException(status_code=404, detail=f"Stop '{stop_id}' not found in routing graph")
        vertex_ids.append(vertex_id)
    
    if not vertex_ids:
        raise HTTPException(status_code=400, detail="No valid stops provided")
    
    conn = connect_Database()
    try:
        stops = get_tsp_selected_stops_query(vertex_ids)
        if not stops:
            raise HTTPException(status_code=404, detail="No stops found")
            
        # Pass vertex_ids directly to tsp_order_query, not the cost_matrix result
        tsp_order = get_tsp_order_query(conn, vertex_ids, start_vertex_id) 
        
        return {
            "stops": stops,
            "order": tsp_order,
            "message": f"TSP optimization complete for {len(vertex_ids)} stops"
        }
    finally:
        conn.close()
