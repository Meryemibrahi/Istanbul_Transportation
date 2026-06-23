"""
Run this ONCE after the GTFS tables are imported.
It creates the MobilityDB helper tables, especially trips_mdb.

Usage from the project root:
    python run_mobilitydb_transformation_v2.py
"""

from dotenv import load_dotenv
from database_Creation import connect_Database
from RQuery_MobilityDB_Tranformation import (
    create_trips_stops_table,
    create_trip_segments_table,
    trips_point_table,
    create_trips_input_table,
    create_trips_mdb,
)


def clean_sql(sql: str) -> str:
    sql = sql.strip()
    if sql.startswith('"'):
        sql = sql[1:].lstrip()
    return sql


# Safer version because in your database calendar.start_date/end_date are TEXT.
# GTFS dates are usually like 20240107, so we convert them with to_date(..., 'YYYYMMDD').
def fixed_service_dates_sql() -> str:
    return """
    DROP TABLE IF EXISTS service_dates;
    CREATE TABLE service_dates AS
    SELECT
        service_id,
        d::date AS date
    FROM calendar c
    CROSS JOIN LATERAL generate_series(
        to_date(c.start_date::text, 'YYYYMMDD'),
        to_date(c.end_date::text, 'YYYYMMDD'),
        interval '1 day'
    ) AS d
    WHERE
        (c.monday = 1 AND extract(isodow FROM d) = 1) OR
        (c.tuesday = 1 AND extract(isodow FROM d) = 2) OR
        (c.wednesday = 1 AND extract(isodow FROM d) = 3) OR
        (c.thursday = 1 AND extract(isodow FROM d) = 4) OR
        (c.friday = 1 AND extract(isodow FROM d) = 5) OR
        (c.saturday = 1 AND extract(isodow FROM d) = 6) OR
        (c.sunday = 1 AND extract(isodow FROM d) = 7);
    """


def run_step(cur, name: str, sql: str):
    print(f"\nRunning: {name} ...")
    cur.execute(clean_sql(sql))
    print(f"Done: {name}")


def main():
    load_dotenv()

    conn = connect_Database()
    if conn is None:
        raise RuntimeError("Database connection failed. Check your .env database settings.")

    try:
        with conn:
            with conn.cursor() as cur:
                print("Connected to database.")

                cur.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
                cur.execute("CREATE EXTENSION IF NOT EXISTS mobilitydb;")

                steps = [
                    ("service_dates", fixed_service_dates_sql()),
                    ("trip_stops", create_trips_stops_table()),
                    ("trip_segs", create_trip_segments_table()),
                    ("trip_points", trips_point_table()),
                    ("trips_input", create_trips_input_table()),
                    ("trips_mdb", create_trips_mdb()),
                ]

                for name, sql in steps:
                    run_step(cur, name, sql)

                cur.execute("SELECT COUNT(*) FROM trips_mdb;")
                count = cur.fetchone()[0]

                print("\nSUCCESS!")
                print(f"trips_mdb was created with {count} rows.")

    finally:
        conn.close()
        print("Database connection closed.")


if __name__ == "__main__":
    main()
