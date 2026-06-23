"""
Creation of the tables in the database
DONE! -> complete
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
    $$ LANGUAGE sql IMMUTABLE;
    """

def add_route_types_table():
    return """
    DROP TABLE IF EXISTS route_types;

    CREATE TABLE route_types (
        route_type INTEGER PRIMARY KEY,
        type_name VARCHAR(50) NOT NULL,
        description TEXT
    );

    INSERT INTO route_types (route_type, type_name, description)
    VALUES
        (0, 'Tram', 'Tram, streetcar, or light rail.'),
        (1, 'Subway / Metro', 'Underground rail system within a metropolitan area.'),
        (2, 'Rail', 'Intercity or long-distance rail service.'),
        (3, 'Bus', 'Short- or long-distance bus service.'),
        (4, 'Ferry', 'Short- or long-distance boat service.'),
        (5, 'Cable tram', 'Street-level rail cars pulled by an underground cable.'),
        (6, 'Aerial lift', 'Cabins or chairs suspended from cables.'),
        (7, 'Funicular', 'Rail system designed for steep inclines.'),
        (9, 'Minibus', 'Minibus transportation service.'),
        (10, 'Taxi Minibus', 'Shared taxi or taxi-minibus service.'),
        (11, 'Trolleybus', 'Electric bus powered through overhead wires.'),
        (12, 'Monorail', 'Rail system operating on a single rail or beam.');

    ALTER TABLE routes
    ADD CONSTRAINT fk_routes_route_type
    FOREIGN KEY (route_type) REFERENCES route_types(route_type);
    """

def create_shape_geoms_table():
    return """
    UPDATE shapes
    SET shape_id = regexp_replace(shape_id, '\.0+$', '')
    WHERE shape_id ~ '\.0+$';

    DROP TABLE IF EXISTS shape_geoms CASCADE;
    CREATE TABLE shape_geoms AS
    SELECT
        shape_id,
        ST_MakeLine(ST_SetSRID(ST_MakePoint(shape_pt_lon, shape_pt_lat), 4326) ORDER BY shape_pt_sequence) AS geom
    FROM shapes
    GROUP BY shape_id;
    ALTER TABLE shape_geoms ADD PRIMARY KEY (shape_id);
    """

def create_location_types_table():
    return """
    DROP TABLE IF EXISTS location_types;

    CREATE TABLE location_types (
        location_type INTEGER PRIMARY KEY,
        type_name VARCHAR(50) NOT NULL,
        description TEXT
    );

    INSERT INTO location_types (location_type, type_name, description)
    VALUES
        (0, 'Stop', 'A stop or station.'),
        (1, 'Station', 'A station.'),
        (2, 'Entrance/Exit', 'An entrance/exit point to a station.'),
        (3, 'Generic Node', 'A generic node in a network.'),
        (4, 'Boarding Area', 'A specific boarding area within a station.');
    
    ALTER TABLE stops
    ADD CONSTRAINT fk_stops_location_type
    FOREIGN KEY (location_type) REFERENCES location_types(location_type);
    """