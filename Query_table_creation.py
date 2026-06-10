"""
Creation of the tables in the database
"""

def create_stop_vertices_table():
    return """
    DROP TABLE IF EXISTS stop_vertices;
    CREATE TABLE stop_vertices AS
    SELECT
        stop_id::integer AS vertex_id,
        stop_id,
        stop_name,
        ST_SetSRID(ST_MakePoint(stop_lon, stop_lat), 4326) AS geom
    FROM stops;
    ALTER TABLE stop_vertices ADD PRIMARY KEY (vertex_id);
    """

def firststep_transit_edges():
    return """
    DROP TABLE IF EXISTS transit_edges_step1;

    CREATE TABLE transit_edges_step1 AS
    SELECT
        st1.trip_id,
        st1.stop_id AS from_stop_id,
        st2.stop_id AS to_stop_id,
        st1.stop_sequence AS from_seq,
        st2.stop_sequence AS to_seq,
        GREATEST(
            turn_to_seconds(st2.arrival_time) -
            turn_to_seconds(st1.departure_time),
            1
        ) AS secondsTraveled
    FROM stop_times st1
    JOIN stop_times st2
    ON st1.trip_id = st2.trip_id
    AND st2.stop_sequence = st1.stop_sequence + 1
    WHERE st1.stop_id <> st2.stop_id;
    """

def create_transit_edges():
    return """
    DROP TABLE IF EXISTS transit_edges;
    CREATE TABLE transit_edges AS
    SELECT
        row_number() OVER () AS id,
        r.from_stop_id::integer AS source,
        r.to_stop_id::integer AS target,
        r.from_stop_id,
        r.to_stop_id,
        AVG(r.secondsTraveled)::double precision AS cost,
        ST_MakeLine(
            ST_SetSRID(ST_MakePoint(s1.stop_lon, s1.stop_lat), 4326),
            ST_SetSRID(ST_MakePoint(s2.stop_lon, s2.stop_lat), 4326)
        )::geometry(LineString, 4326) AS geom,
        s1.stop_lon AS x1,
        s1.stop_lat AS y1,
        s2.stop_lon AS x2,
        s2.stop_lat AS y2
    FROM transit_edges_step1 r
    JOIN stops s1 ON r.from_stop_id = s1.stop_id
    JOIN stops s2 ON r.to_stop_id = s2.stop_id
    GROUP BY
        r.from_stop_id, r.to_stop_id,
        s1.stop_lon, s1.stop_lat,
        s2.stop_lon, s2.stop_lat;
    ALTER TABLE transit_edges ADD PRIMARY KEY (id);
    """


def add_time_to_seconds_function():
    return """
    CREATE OR REPLACE FUNCTION turn_to_seconds(t text)
    RETURNS integer AS $$
    SELECT
        CASE
            WHEN t ~ '^\d+:\d{2}:\d{2}$' THEN
                split_part(t, ':', 1)::int * 3600 +
                split_part(t, ':', 2)::int * 60 +
                split_part(t, ':', 3)::int
            ELSE NULL
        END
    $$ LANGUAGE sql plpgsql;
    """