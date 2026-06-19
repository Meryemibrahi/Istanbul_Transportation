"""
FastAPI router for advanced pathfinding and network analysis features
done! -> complete
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict


from database_Creation import execute_query, connect_Database


from Query_working_algorithms import (
    get_tsp_selected_stops_query,
    get_tsp_order_query,
    get_dijkstra_stop_list_query,
    get_dijkstra_geometry_query,
    get_dijkstra_summary_query,
    get_astar_stop_list_query,
    get_astar_geometry_query,
    get_astar_summary_query,
    get_full_network_query
)

from Query_extra import (
    get_top_routes_by_trip_count,
    get_route_with_stops
)


router = APIRouter()


@router.get("/network")
def full_network():
    network = get_full_network_query()
    return network

@router.get("/dijkstra")
def get_dijkstra_route(start_id: int, end_id: int):
    stops = get_dijkstra_stop_list_query(start_id, end_id)
    
    if not stops:
        raise HTTPException(status_code=404, detail="No path found")

    return {
        "summary": get_dijkstra_summary_query(start_id, end_id),
        "stops": stops,
        "geometry": get_dijkstra_geometry_query(start_id, end_id)
    }


@router.get("/astar")
def get_astar_route(start_id: int, end_id: int):
    stops = get_astar_stop_list_query(start_id, end_id)
    
    if not stops:
        raise HTTPException(status_code=404, detail="No path found")

    return {
        "summary": get_astar_summary_query(start_id, end_id),
        "stops": stops,
        "geometry": get_astar_geometry_query(start_id, end_id)
    }

@router.get("/tsp")
def get_tsp_route(start_id: int, stop_ids: list[int] = Query(...)):
    conn = connect_Database()
    try:
        stops = get_tsp_selected_stops_query(stop_ids)
        if not stops:
            raise HTTPException(status_code=404, detail="No stops found")

        tsp_order = get_tsp_order_query(conn, stop_ids, start_id)

        return {
            "stops": stops,
            "order": tsp_order
        }
    finally:
        conn.close()



@router.get("/top-routes")
def top_routes(limit: int = Query(10, ge=1, le=100)):
    routes = get_top_routes_by_trip_count(limit)
    if not routes:
        raise HTTPException(status_code=404, detail="No routes found")
    return {
        "top_routes": routes,
        "total_routes_returned": len(routes)
    }


@router.get("/route/{route_id}")
def route_details(route_id: str):
    result = get_route_with_stops(route_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result