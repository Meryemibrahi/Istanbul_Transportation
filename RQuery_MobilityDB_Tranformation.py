def servis_id_table():
    return """
    DROP TABLE IF EXISTS service_dates;
    CREATE TABLE service_dates AS (
    SELECT service_id, date_trunc('day', d)::date AS date
    FROM calendar c, generate_series(start_date, end_date, '1 day'::interval) AS d
    WHERE (
        (monday = 1 AND extract(isodow FROM d) = 1) OR
        (tuesday = 1 AND extract(isodow FROM d) = 2) OR
        (wednesday = 1 AND extract(isodow FROM d) = 3) OR
        (thursday = 1 AND extract(isodow FROM d) = 4) OR
        (friday = 1 AND extract(isodow FROM d) = 5) OR
        (saturday = 1 AND extract(isodow FROM d) = 6) OR
        (sunday = 1 AND extract(isodow FROM d) = 7)
    ));"""

def create_trips_stops_table():
    return """
    DROP TABLE IF EXISTS trip_stops;
    CREATE TABLE trip_stops (
    trip_id text,
    stop_sequence integer,
    no_stops integer,
    route_id text,
    service_id text,
    shape_id text,
    stop_id text,
    arrival_time interval,
    perc float
    );

    INSERT INTO trip_stops (trip_id, stop_sequence, no_stops, route_id, service_id,
    shape_id, stop_id, arrival_time)
    SELECT t.trip_id, stop_sequence, MAX(stop_sequence) OVER (PARTITION BY t.trip_id),
    route_id, service_id, shape_id, stop_id, NULLIF(TRIM(s.arrival_time), '')::interval
    FROM trips t JOIN stop_times s ON t.trip_id = s.trip_id;

    UPDATE trip_stops t
    SET perc = CASE
    WHEN stop_sequence =  1 then 0.0
    ELSE ST_LineLocatePoint(g.geom, ST_SetSRID(ST_MakePoint(s.stop_lon, s.stop_lat), 4326))
    END
    FROM shape_geoms g, stops s
    WHERE t.shape_id = g.shape_id AND t.stop_id = s.stop_id;
    """

def create_trip_segments_table():
    return """
    DROP TABLE IF EXISTS trip_segs;
    CREATE TABLE trip_segs (
    trip_id text,
    route_id text,
    service_id text,
    stop1_sequence integer,
    stop2_sequence integer,
    no_stops integer,
    shape_id text,
    stop1_arrival_time interval,
    stop2_arrival_time interval,
    perc1 float,
    perc2 float,
    seg_geom geometry,
    seg_length float,
    no_points integer,
    PRIMARY KEY (trip_id, stop1_sequence)
    );

    INSERT INTO trip_segs (trip_id, route_id, service_id, stop1_sequence, stop2_sequence,
    no_stops, shape_id, stop1_arrival_time, stop2_arrival_time, perc1, perc2)  
    WITH temp AS (
    SELECT trip_id, route_id, service_id, stop_sequence,
        LEAD(stop_sequence) OVER w AS stop_sequence2,
    MAX(stop_sequence) OVER (PARTITION BY trip_id),
    shape_id, arrival_time, LEAD(arrival_time) OVER w, perc, LEAD(perc) OVER w
    FROM trip_stops WINDOW w AS (PARTITION BY trip_id ORDER BY stop_sequence)
    )
    SELECT * FROM temp WHERE stop_sequence2 IS NOT null;

    DELETE FROM trip_segs
    WHERE trip_id IN (
        SELECT DISTINCT trip_id 
        FROM trip_segs 
        WHERE perc1 >= perc2
    );

    UPDATE trip_segs t
    SET seg_geom = ST_LineSubstring(g.geom, perc1, perc2)
    FROM shape_geoms g
    WHERE t.shape_id = g.shape_id;

    UPDATE trip_segs
    SET seg_length = ST_Length(seg_geom), no_points = ST_NumPoints(seg_geom);
    """

def trips_point_table():
    return """
    DROP TABLE IF EXISTS trip_points;
    CREATE TABLE trip_points (
    trip_id text,
    route_id text,
    service_id text,
    stop1_sequence integer,
    point_sequence integer,
    point_geom geometry,
    point_arrival_time interval,
    PRIMARY KEY (trip_id, stop1_sequence, point_sequence)
    );

    INSERT INTO trip_points (trip_id, route_id, service_id, stop1_sequence,
    point_sequence, point_geom, point_arrival_time)
    WITH temp1 AS (
    SELECT trip_id, route_id, service_id, stop1_sequence, stop2_sequence,
        no_stops, stop1_arrival_time, stop2_arrival_time, seg_length,
        (dp).path[1] AS point_sequence, no_points, (dp).geom as point_geom
    FROM trip_segs, ST_DumpPoints(seg_geom) AS dp
    ),
    temp2 AS (
    SELECT trip_id, route_id, service_id, stop1_sequence, stop1_arrival_time,
        stop2_arrival_time, seg_length, point_sequence, no_points, point_geom
    FROM temp1
    WHERE point_sequence <> no_points OR stop2_sequence = no_stops
    ),
    temp3 AS (
    SELECT trip_id, route_id, service_id, stop1_sequence, stop1_arrival_time,
        stop2_arrival_time, point_sequence, no_points, point_geom,
        ST_Length(ST_MakeLine(array_agg(point_geom) OVER w)) / seg_length AS perc
    FROM temp2 WINDOW w AS (PARTITION BY trip_id, service_id, stop1_sequence
        ORDER BY point_sequence)
    )
    SELECT trip_id, route_id, service_id, stop1_sequence, point_sequence, point_geom,
    CASE
    WHEN point_sequence = 1 then stop1_arrival_time
    WHEN point_sequence = no_points then stop2_arrival_time
    ELSE stop1_arrival_time + ((stop2_arrival_time - stop1_arrival_time) * perc)
    END AS point_arrival_time
    FROM temp3;
    """

def create_trips_input_table():
    return """
    DROP TABLE IF EXISTS trips_input;
    CREATE TABLE trips_input (
    trip_id text,
    route_id text,
    service_id text,
    date date,
    point_geom geometry,
    t timestamptz
    );

    INSERT INTO trips_input
    SELECT trip_id, route_id, t.service_id, date, point_geom, date + point_arrival_time AS t
    FROM trip_points t JOIN
    ( SELECT service_id, MIN(date) AS date FROM service_dates GROUP BY service_id) s
    ON t.service_id = s.service_id;"""

def create_trips_mdb():
    return """
    DROP TABLE IF EXISTS trips_mdb;
    CREATE TABLE trips_mdb (
    trip_id text NOT NULL,
    route_id text NOT NULL,
    service_id text NOT NULL,
    date date NOT NULL,
    trip tgeompoint,
    PRIMARY KEY (trip_id, date)
    );

    INSERT INTO trips_mdb(trip_id, route_id, service_id, date, trip)
    SELECT trip_id, route_id, service_id, date,
        tgeompointseq(array_agg(tgeompoint(point_geom, t) ORDER BY t))
    FROM (
        SELECT trip_id, route_id, service_id, date, point_geom,
            t + (ROW_NUMBER() OVER (PARTITION BY trip_id, t ORDER BY t) - 1) 
                * interval '1 microsecond' AS t
        FROM trips_input
    ) deduped
    GROUP BY trip_id, route_id, service_id, date;

    INSERT INTO trips_mdb(trip_id, route_id, service_id, date, trip)
    SELECT t.trip_id, t.route_id, t.service_id, d.date,
        shiftTime(trip, make_interval(days => d.date - t.date))
    FROM trips_mdb t 
    JOIN service_dates d ON t.service_id = d.service_id AND t.date <> d.date;
    """