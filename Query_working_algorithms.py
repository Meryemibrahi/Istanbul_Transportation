"""
done!
"""

# -----------------------------
# FULL NETWORK
# -----------------------------

def get_full_network_query():
    return """
    SELECT
        route_id,
        route_short_name,
        route_long_name,
        ST_AsGeoJSON(geom) AS geojson
    FROM route_shapes;
    """


# -----------------------------
# ROUTE + STOPS
# -----------------------------

def get_route_stops_query():
    return """
    WITH one_trip AS (
        SELECT trip_id, shape_id
        FROM trips
        WHERE route_id = %s
        LIMIT 1
    )
    SELECT
        s.stop_id,
        s.stop_name,
        st.stop_sequence,
        ST_AsGeoJSON(s.geom) AS stop_geojson
    FROM one_trip ot
    JOIN stop_times st ON ot.trip_id = st.trip_id
    JOIN stops s ON st.stop_id = s.stop_id
    ORDER BY st.stop_sequence;
    """


# -----------------------------
# BUSIEST ROUTES
# -----------------------------

def get_busiest_routes_query():
    return """
    SELECT
        r.route_id,
        r.route_short_name,
        r.route_long_name,
        COUNT(t.trip_id) AS trip_count
    FROM routes r
    JOIN trips t ON r.route_id = t.route_id
    GROUP BY r.route_id, r.route_short_name, r.route_long_name
    ORDER BY trip_count DESC
    LIMIT %s;
    """


# -----------------------------
# BUSIEST STOPS
# -----------------------------

def get_busiest_stops_query():
    return """
    SELECT
        s.stop_id,
        s.stop_name,
        COUNT(*) AS morning_arrivals,
        ST_AsGeoJSON(s.geom) AS geojson
    FROM stop_times st
    JOIN stops s ON st.stop_id = s.stop_id
    WHERE st.arrival_time >= %s
      AND st.arrival_time < %s
    GROUP BY s.stop_id, s.stop_name, s.geom
    ORDER BY morning_arrivals DESC
    LIMIT %s;
    """


# -----------------------------
# DEBUG / METRICS
# -----------------------------

def get_stop_vertex_count_query():
    return "SELECT COUNT(*) FROM stop_vertices;"


def get_transit_edges_raw_count_query():
    return "SELECT COUNT(*) FROM transit_edges_raw;"


def get_transit_edges_count_query():
    return "SELECT COUNT(*) FROM transit_edges;"


def get_sample_edges_query():
    return """
    SELECT *
    FROM transit_edges
    LIMIT 10;
    """


def search_stops_query():
    return """
    SELECT vertex_id, stop_id, stop_name
    FROM stop_vertices
    WHERE stop_name ILIKE %s
    LIMIT %s;
    """


# -----------------------------
# DIJKSTRA
# -----------------------------

def get_dijkstra_stop_list_query():
    return """
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


def get_dijkstra_geometry_query():
    return """
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
        e.from_stop_id,
        e.to_stop_id,
        e.cost,
        ST_AsGeoJSON(e.geom) AS edge_geojson
    FROM path p
    JOIN transit_edges e
        ON p.edge = e.id
    ORDER BY p.seq;
    """


def get_dijkstra_summary_query():
    return """
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
        COUNT(*) AS step_count,
        MAX(agg_cost) AS total_cost
    FROM path;
    """


# -----------------------------
# A* ALGORITHM
# -----------------------------

def get_astar_stop_list_query():
    return """
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


def get_astar_geometry_query():
    return """
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
        e.from_stop_id,
        e.to_stop_id,
        e.cost,
        ST_AsGeoJSON(e.geom) AS edge_geojson
    FROM path p
    JOIN transit_edges e
        ON p.edge = e.id
    ORDER BY p.seq;
    """


def get_astar_summary_query():
    return """
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
        COUNT(*) AS step_count,
        MAX(agg_cost) AS total_cost
    FROM path;
    """


# -----------------------------
# TSP 
# -----------------------------

def get_tsp_selected_stops_query():
    return """
    SELECT *
    FROM stop_vertices
    WHERE vertex_id = ANY(%s);
    """


def get_tsp_cost_matrix_query():
    return """
    SELECT *
    FROM pgr_dijkstraCostMatrix(
        'SELECT id, source, target, cost, cost AS reverse_cost FROM transit_edges',
        %s,
        directed := false
    );
    """


def get_tsp_order_query():
    return """
    SELECT *
    FROM pgr_TSP(
        $$ SELECT * FROM tsp_cost_matrix $$,
        start_id := %s
    );
    """




