"""
Load GTFS data from CSV files into PostgreSQL database
"""

import os
import psycopg2
import psycopg2.extras
import pandas as pd
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )

def load_csv_to_table(csv_file, table_name):
    """Load a CSV file into a PostgreSQL table"""
    try:
        logger.info(f"Loading {csv_file} into {table_name}...")
        
        # Read CSV
        df = pd.read_csv(f"data/{csv_file}")
        
        # Connect to database
        conn = get_connection()
        cur = conn.cursor()
        
        # Clear existing data
        cur.execute(f"TRUNCATE TABLE {table_name};")
        
        # Insert data
        for _, row in df.iterrows():
            columns = ", ".join(df.columns)
            placeholders = ", ".join(["%s"] * len(df.columns))
            insert_query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
            cur.execute(insert_query, tuple(row))
        
        conn.commit()
        logger.info(f"✓ Loaded {len(df)} rows into {table_name}")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        logger.error(f"Error loading {csv_file}: {e}")
        raise

def main():
    """Load all GTFS data"""
    logger.info("Starting GTFS data import...")
    
    try:
        load_csv_to_table("agency.csv", "agency")
        load_csv_to_table("stops.csv", "stops")
        load_csv_to_table("routes.csv", "routes")
        load_csv_to_table("trips.csv", "trips")
        load_csv_to_table("stop_times.csv", "stop_times")
        load_csv_to_table("shapes.csv", "shapes")
        load_csv_to_table("calendar.csv", "calendar")
        
        logger.info("✓ All data loaded successfully!")
        
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        raise

if __name__ == "__main__":
    main()
