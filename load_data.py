"""
Load GTFS data from CSV files into PostgreSQL database
DONE!
"""

import os
import logging
from dotenv import load_dotenv

from database_Creation import connect_Database

from RQuery_table_creation import (
    create_stop_vertices_table,
    firststep_transit_edges,
    add_time_to_seconds_function,
    create_transit_edges,
    create_location_types_table,
    create_shape_geoms_table
)

from RQuery_indexes import (
    create_gtfs_indexes,
    enable_postgres_extensions
)


from RQuery_MobilityDB_Tranformation import(
        create_trips_mdb,
        create_trips_input_table,
        trips_point_table,
        create_trip_segments_table,
        create_trips_stops_table,
        servis_id_table
)


load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def other_functions():
    try:
        logger.info(f"Creating more tables and indexes...")
            
        conn = connect_Database()
        cur = conn.cursor()

        cur.execute(add_time_to_seconds_function())
        cur.execute(create_stop_vertices_table())
        cur.execute(firststep_transit_edges())
        cur.execute(create_transit_edges())
        cur.execute(create_shape_geoms_table())
        cur.execute(create_location_types_table())

        conn.commit()

        enable_postgres_extensions(conn)

        logger.info(f"Ready to start!")
    
        cur.close()
        conn.close()

    except Exception as e:
        logger.error(f"Error loading other functions : {e}")
        raise

def moblility_tables():
    try:
        logger.info(f"Creating MobilityDB tables...")
            
        conn = connect_Database()
        cur = conn.cursor()

        cur.execute(servis_id_table())
        cur.execute(create_trips_stops_table())
        cur.execute(create_trip_segments_table())
        cur.execute(trips_point_table())
        cur.execute(create_trips_input_table())
        cur.execute(create_trips_mdb())
        create_gtfs_indexes(conn)

        conn.commit()

        logger.info(f"MobilityDB tables created successfully!")
    
        cur.close()
        conn.close()

    except Exception as e:
        logger.error(f"Error creating MobilityDB tables: {e}")
        raise


def main():
    logger.info("Starting GTFS data import...")
    
    try:
        logger.info("All data loaded successfully!")
        other_functions()
        moblility_tables()
        
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        raise



if __name__ == "__main__":
    main()