"""
Query functions for all paths
DONE! -> complete
"""

from database_Creation import execute_query, connect_Database
from fastapi import HTTPException

# -----------------------------
# DIJKSTRA
# -----------------------------

def get_dijkstra_stop_list_query(start_vertex_id, end_vertex_id):
    query = """
    WITH path AS (
        SELECT *
        FROM pgr_dijkstra(
            'SELECT id, source, target, cost FROM transit_edges',
            %s,
            %s,
            directed := true
        )
    )
    SELECT
        p.seq,
        p.node,
        sv.stop_id,
        sv.stop_name,
        p.edge,
        p.cost,
        p.agg_cost
    FROM path p
    LEFT JOIN stop_vertices sv
        ON p.node = sv.vertex_id
    ORDER BY p.seq;
    """
    return execute_query(query, [start_vertex_id, end_vertex_id])


# -----------------------------
# A* ALGORITHM
# -----------------------------

def get_astar_stop_list_query(start_vertex_id, end_vertex_id):
    """
    Find shortest path using A* algorithm with heuristics.
    Returns sequence of stops visited.
    
    Args:
        start_vertex_id: Starting vertex ID
        end_vertex_id: Ending vertex ID
    """
    query = """
    WITH path AS (
        SELECT *
        FROM pgr_astar(
            'SELECT id, source, target, cost, x1, y1, x2, y2 FROM transit_edges',
            %s,
            %s,
            directed := true
        )
    )
    SELECT
        p.seq,
        p.node,
        sv.stop_id,
        sv.stop_name,
        p.edge,
        p.cost,
        p.agg_cost
    FROM path p
    LEFT JOIN stop_vertices sv
        ON p.node = sv.vertex_id
    ORDER BY p.seq;
    """
    return execute_query(query, [start_vertex_id, end_vertex_id])


# -----------------------------
# TSP 
# ----------------------------- 

def get_tsp_selected_stops_query(vertex_ids):
    query = """
    SELECT *
    FROM stop_vertices
    WHERE vertex_id = ANY(%s);
    """
    return execute_query(query, [vertex_ids])


def get_tsp_cost_matrix_query(vertex_ids):
    query = """
    SELECT *
    FROM pgr_dijkstraCostMatrix(
        'SELECT id, source, target, cost, cost AS reverse_cost FROM transit_edges',
        %s,
        directed := false
    );
    """
    return execute_query(query, [vertex_ids])


def get_tsp_order_query(conn, cost_matrix, start_id):

    try:
        conn = connect_Database()
        cur = conn.cursor()
        cur.execute("""
            CREATE TEMP TABLE tsp_matrix AS
            SELECT * FROM pgr_dijkstraCostMatrix(
                 'SELECT id, source, target, cost, cost AS reverse_cost FROM transit_edges',
                  %s,
                   directed := false
             );
        """, [cost_matrix])

        cur.execute("""
            SELECT *
            FROM pgr_TSP(
                $$ SELECT * FROM tsp_matrix $$,
                start_id := %s
                );
            """, [start_id])

        results = cur.fetchall()

        cur.execute("DROP TABLE IF EXISTS tsp_matrix;")
        conn.commit()

        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



