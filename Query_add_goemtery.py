"""
add_geometry sql
done!
 """

def add_geometry():
    return """
    ALTER TABLE stops ADD COLUMN geom geometry(Point, 4326);

    UPDATE stops
    SET geom = ST_SetSRID(ST_MakePoint(stop_lon, stop_lat), 4326);


    DROP TABLE IF EXISTS shape_geoms;

    CREATE TABLE shape_geoms AS
    SELECT
        shape_id,
        ST_MakeLine(
            ST_SetSRID(ST_MakePoint(shape_pt_lon, shape_pt_lat), 4326)
            ORDER BY shape_pt_sequence
        ) AS geom
    FROM shapes
    GROUP BY shape_id;
    """


def add_time_to_seconds_function():
    return """
    CREATE OR REPLACE FUNCTION gtfs_time_to_seconds(t text)
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