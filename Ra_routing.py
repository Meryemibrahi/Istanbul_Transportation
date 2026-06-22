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
)


router = APIRouter()


@router.get("/dijkstra")
def get_dijkstra_route(start_id: int, end_id: int):
    stops = get_dijkstra_stop_list_query(start_id, end_id)
    
    if not stops:
        raise HTTPException(status_code=404, detail="No path found")

    return {
        "stops": stops,
        }  


@router.get("/astar")
def get_astar_route(start_id: int, end_id: int):
    stops = get_astar_stop_list_query(start_id, end_id)
    
    if not stops:
        raise HTTPException(status_code=404, detail="No path found")

    return {
        "stops": stops,
    }

@router.get("/tsp")
def get_tsp_route(start_id: int, stop_ids: list[int] = Query(...)):
    conn = connect_Database()
    try:
        stops = get_tsp_selected_stops_query(stop_ids)
        if not stops:
            raise HTTPException(status_code=404, detail="No stops found")

        cost_matrix = get_tsp_cost_matrix_query(stop_ids)
        tsp_order = get_tsp_order_query(conn, cost_matrix, start_id) 
        
        return {
            "stops": stops,
            "order": tsp_order
        }
    finally:
        conn.close()
