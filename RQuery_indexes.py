"""
DONE!
"""

def create_gtfs_indexes(conn):
    queries = [
        "CREATE INDEX IF NOT EXISTS trips_route_id_idx ON trips(route_id);",
        "CREATE INDEX IF NOT EXISTS trips_shape_id_idx ON trips(shape_id);",
        "CREATE INDEX IF NOT EXISTS stop_times_trip_id_idx ON stop_times(trip_id);",
        "CREATE INDEX IF NOT EXISTS stop_times_stop_id_idx ON stop_times(stop_id);",
        "CREATE INDEX IF NOT EXISTS routes_short_name_idx ON routes(route_short_name);",
        "CREATE INDEX IF NOT EXISTS shape_geoms_shape_id_idx ON shape_geoms(shape_id);",
        "CREATE INDEX IF NOT EXISTS trips_service_id_idx ON trips(service_id);",
        "CREATE INDEX IF NOT EXISTS transit_edges_source_idx ON transit_edges(source);",
        "CREATE INDEX IF NOT EXISTS transit_edges_target_idx ON transit_edges(target);",
        "CREATE INDEX IF NOT EXISTS transit_edges_geom_gix ON transit_edges USING GIST (geom);",
        "CREATE INDEX IF NOT EXISTS transit_edges_from_stop_idx ON transit_edges(from_stop_id);",
        "CREATE INDEX IF NOT EXISTS transit_edges_to_stop_idx ON transit_edges(to_stop_id);",
        "CREATE INDEX IF NOT EXISTS stop_vertices_geom_gix ON stop_vertices USING GIST (geom);"
    ]

    with conn.cursor() as cur:
        for q in queries:
            cur.execute(q)

    conn.commit()

def enable_postgres_extensions(conn):
    queries = [
        "CREATE EXTENSION IF NOT EXISTS postgis;",
        "CREATE EXTENSION IF NOT EXISTS pgrouting;"
        "CREATE EXTENSION IF NOT EXISTS mobility;"
        "CREATE EXTENSION IF NOT EXISTS mobilityDB;"
    ]

    with conn.cursor() as cur:
        for q in queries:
            cur.execute(q)

    conn.commit()