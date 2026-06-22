"""
BIG ERROR EXSITS... NEEDS WORK AND FIXING"""


from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict
# from advanced_algorithms import (
#     dijkstra_shortest_path,
#     a_star_shortest_path,
#     get_top_routes_by_trip_count,
#     get_busiest_stops_by_time,
#     get_full_network,
#     get_route_with_stops
# )
from RQuery_Explorer import (
    get_tsp_selected_stops,
    get_tsp_cost_matrix,
    get_tsp_optimal_order,
    dijkstra_route_by_stops,
    dijkstra_geometry_by_stops,
    astar_route_by_stops,
    astar_geometry_by_stops
)

router = APIRouter()

# ============================================================================
# PATHFINDING ALGORITHMS
# ============================================================================

@router.get("/dijkstra")
def dijkstra_path(
    start: str = Query(..., description="Start stop ID"),
    end: str = Query(..., description="End stop ID")
):
    """
    Find shortest path between two stops using Dijkstra's algorithm
    """
    result = dijkstra_shortest_path(start, end)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/astar")
def astar_path(
    start: str = Query(..., description="Start stop ID"),
    end: str = Query(..., description="End stop ID")
):
    """
    Find shortest path between two stops using A* algorithm
    """
    result = a_star_shortest_path(start, end)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/compare-paths")
def compare_paths(
    start: str = Query(..., description="Start stop ID"),
    end: str = Query(..., description="End stop ID")
):
    """
    Compare Dijkstra and A* pathfinding algorithms
    Returns both paths with metrics
    """
    dijkstra = dijkstra_shortest_path(start, end)
    astar = a_star_shortest_path(start, end)
    
    if "error" in dijkstra:
        raise HTTPException(status_code=404, detail=dijkstra["error"])
    
    return {
        "dijkstra": dijkstra,
        "astar": astar,
        "comparison": {
            "dijkstra_distance": dijkstra.get("total_distance", 0),
            "astar_distance": astar.get("total_distance", 0),
            "dijkstra_hops": dijkstra.get("hops", 0),
            "astar_hops": astar.get("hops", 0),
            "same_path": dijkstra.get("path") == astar.get("path")
        }
    }


# ============================================================================
# PROUTING-BASED PATHFINDING (ALTERNATIVE ALGORITHMS)
# ============================================================================

@router.get("/dijkstra-pg")
def dijkstra_path_pg(
    start: str = Query(..., description="Start stop ID"),
    end: str = Query(..., description="End stop ID")
):
    """
    Find shortest path using Dijkstra's algorithm via pgRouting.
    Uses transit_edges graph built from GTFS data.
    
    Args:
        start: Start stop ID
        end: End stop ID
    
    Returns:
        Path with stops and total cost
    """
    result = dijkstra_route_by_stops(start, end)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/dijkstra-pg/geometry")
def dijkstra_geometry_pg(
    start: str = Query(..., description="Start stop ID"),
    end: str = Query(..., description="End stop ID")
):
    """
    Get GeoJSON geometries for Dijkstra path via pgRouting.
    """
    result = dijkstra_geometry_by_stops(start, end)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/astar-pg")
def astar_path_pg(
    start: str = Query(..., description="Start stop ID"),
    end: str = Query(..., description="End stop ID")
):
    """
    Find shortest path using A* algorithm via pgRouting.
    Uses transit_edges graph with heuristic guidance.
    
    Args:
        start: Start stop ID
        end: End stop ID
    
    Returns:
        Path with stops and total cost
    """
    result = astar_route_by_stops(start, end)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/astar-pg/geometry")
def astar_geometry_pg(
    start: str = Query(..., description="Start stop ID"),
    end: str = Query(..., description="End stop ID")
):
    """
    Get GeoJSON geometries for A* path via pgRouting.
    """
    result = astar_geometry_by_stops(start, end)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


# ============================================================================
# NETWORK ANALYSIS
# ============================================================================

@router.get("/top-routes")
def top_routes(limit: int = Query(10, ge=1, le=100)):
    """
    Get top routes by trip count
    """
    routes = get_top_routes_by_trip_count(limit)
    if not routes:
        raise HTTPException(status_code=404, detail="No routes found")
    return {
        "top_routes": routes,
        "total_routes_returned": len(routes)
    }


@router.get("/busiest-stops")
def busiest_stops(
    start_hour: int = Query(0, ge=0, le=23),
    end_hour: int = Query(23, ge=0, le=23)
):
    """
    Get busiest stops by arrival/departure count during a specific time range
    """
    if start_hour > end_hour:
        raise HTTPException(status_code=400, detail="start_hour must be <= end_hour")
    
    stops = get_busiest_stops_by_time(start_hour, end_hour)
    if not stops:
        raise HTTPException(status_code=404, detail="No stops found for the given time range")
    
    return {
        "time_range": f"{start_hour:02d}:00 - {end_hour:02d}:59",
        "busiest_stops": stops,
        "total_stops_returned": len(stops)
    }


@router.get("/network")
def full_network():
    """
    Get full transit network: all stops and routes
    Useful for full network visualization
    """
    network = get_full_network()
    return network


@router.get("/route/{route_id}")
def route_details(route_id: str):
    """
    Get a specific route and all its stops in sequence
    """
    result = get_route_with_stops(route_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


# ============================================================================
# TRAVELING SALESMAN PROBLEM (TSP)
# ============================================================================

@router.get("/tsp")
def solve_tsp(
    vertex_ids: str = Query(..., description="Comma-separated list of vertex IDs (e.g., '1,5,10,15')"),
    start_id: int = Query(..., description="Starting vertex ID")
):
    """
    Solve Traveling Salesman Problem for given stops.
    Finds the shortest route visiting all selected stops starting from start_id.
    
    Args:
        vertex_ids: Comma-separated vertex IDs to visit
        start_id: Starting vertex ID
    
    Returns:
        Optimal order of stops with cost information
    """
    try:
        # Parse vertex IDs
        vertices = [int(v.strip()) for v in vertex_ids.split(",")]
        
        if not vertices:
            raise HTTPException(status_code=400, detail="vertex_ids cannot be empty")
        
        if start_id not in vertices:
            raise HTTPException(status_code=400, detail="start_id must be in vertex_ids list")
        
        # Get selected stops details
        stops = get_tsp_selected_stops(vertices)
        
        # Get cost matrix
        cost_matrix = get_tsp_cost_matrix(vertices)
        
        # Get optimal order
        optimal_order = get_tsp_optimal_order(vertices, start_id)
        
        return {
            "selected_stops": stops,
            "cost_matrix": cost_matrix,
            "optimal_order": optimal_order,
            "start_id": start_id
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid vertex_ids format: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TSP calculation failed: {str(e)}")
