"""
Load GTFS data from CSV files into PostgreSQL database
"""

import os
import psycopg2
import psycopg2.extras
import pandas as pd
import logging
from dotenv import load_dotenv

POSSIBLE_ENCODINGS = [
    "utf-8",
    "utf-8-sig",
    "cp1254",
    "iso-8859-9",
    "latin-1",
    "iso-8859-1",
    "cp1252",
    "utf-16"
]


load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def read_csv_with_encoding(file_path):
    last_error = None

    for encoding in POSSIBLE_ENCODINGS:
        try:
            logger.info(f"Trying to read {file_path} with encoding: {encoding}")
            df = pd.read_csv(file_path, encoding=encoding)
            logger.info(f"Successfully read {file_path} with encoding: {encoding}")
            return df

        except UnicodeDecodeError as e:
            last_error = e
            logger.warning(f"Failed with encoding {encoding}: {e}")

    raise last_error

def get_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME", "gtfs_db"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD")
    )

def load_csv_to_table(csv_file, table_name):
    try:
        logger.info(f"Loading {csv_file} into {table_name}...")
        
        # Read CSV
        df = read_csv_with_encoding(f"data/{csv_file}")        
        # Connect to database
        conn = get_connection()
        cur = conn.cursor()
        
        # Clear data from before
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
