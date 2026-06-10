#____________________________________________
#____________________________________________
#____________________________________________
#____________________________________________


# -> working algorithms
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


# @router.get("/busiest-stops")
# def busiest_stops(
#     start_hour: int = Query(0, ge=0, le=23),
#     end_hour: int = Query(23, ge=0, le=23)
# ):
#     """
#     Get busiest stops by arrival/departure count during a specific time range
#     """
#     if start_hour > end_hour:
#         raise HTTPException(status_code=400, detail="start_hour must be <= end_hour")
    
#     stops = get_busiest_stops_by_time(start_hour, end_hour)
#     if not stops:
#         raise HTTPException(status_code=404, detail="No stops found for the given time range")
    
#     return {
#         "time_range": f"{start_hour:02d}:00 - {end_hour:02d}:59",
#         "busiest_stops": stops,
#         "total_stops_returned": len(stops)
#     }



#____________________________________________
#____________________________________________
#____________________________________________
#____________________________________________

#table_creation_queries


def create_agency_table():
    return """
    CREATE TABLE agency (
    agency_id TEXT PRIMARY KEY,
    agency_name TEXT,
    agency_url TEXT,
    agency_timezone TEXT,
    agency_lang TEXT,
    agency_phone TEXT,
    agency_fare_url TEXT,
    agency_email TEXT
    );"""

def create_stops_table():
    return """
    CREATE TABLE stops (
    stop_id TEXT PRIMARY KEY,
    stop_code TEXT,
    stop_name TEXT,
    stop_desc TEXT,
    stop_lat DOUBLE PRECISION,
    stop_lon DOUBLE PRECISION,
    zone_id TEXT,
    stop_url TEXT,
    location_type INTEGER,
    parent_station TEXT,
    stop_timezone TEXT,
    wheelchair_boarding INTEGER
    );"""

def create_calendar_table():
    return """
    CREATE TABLE calendar (
    service_id TEXT PRIMARY KEY,
    monday INTEGER,
    tuesday INTEGER,
    wednesday INTEGER,
    thursday INTEGER,
    friday INTEGER,
    saturday INTEGER,
    sunday INTEGER,
    start_date TEXT,
    end_date TEXT
    );"""

def create_routes_table():
    return """
    CREATE TABLE routes (
    route_id TEXT PRIMARY KEY,
    agency_id TEXT,
    route_short_name TEXT,
    route_long_name TEXT,
    route_desc TEXT,
    route_type INTEGER,
    route_url TEXT,
    route_color TEXT,
    route_text_color TEXT
);"""


def create_shapes_table():
    return """
    CREATE TABLE shapes (
    shape_id TEXT,
    shape_pt_lat DOUBLE PRECISION,
    shape_pt_lon DOUBLE PRECISION,
    shape_pt_sequence INTEGER,
    shape_dist_traveled DOUBLE PRECISION,
    PRIMARY KEY (shape_id, shape_pt_sequence)
);"""

def create_trips_table():
    return """
    CREATE TABLE trips (
    route_id TEXT,
    service_id TEXT,
    trip_id TEXT PRIMARY KEY,
    trip_headsign TEXT,
    trip_short_name TEXT,
    direction_id INTEGER,
    block_id TEXT,
    shape_id TEXT,
    wheelchair_accessible INTEGER,
    bikes_allowed INTEGER
);"""

def create_stop_times_table():
    return """
    CREATE TABLE stop_times (
    trip_id TEXT,
    arrival_time TEXT,
    departure_time TEXT,
    stop_id TEXT,
    stop_sequence INTEGER,
    stop_headsign TEXT,
    pickup_type INTEGER,
    drop_off_type INTEGER,
    shape_dist_traveled DOUBLE PRECISION,
    timepoint INTEGER,
    PRIMARY KEY (trip_id, stop_sequence)
);"""

#____________________________________________
#____________________________________________
#____________________________________________
#____________________________________________