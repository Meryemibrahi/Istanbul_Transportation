"""
Connecting the database
Prepareing it for MobilityDB and live data insertion
"""

import os
import psycopg2
import psycopg2.extras
import logging
from typing import Optional, List, Dict, Any

from contextlib import contextmanager
from configuration import config, load_config

logger = logging.getLogger(__name__)

params_ = config()

conn = psycopg2.connect(**params_)
cur = conn.cursor()

#connecting to the database
def connect():
    conn = None
    try:
        params = config()
 
        print('Connecting to the PostgreSQL database...')
        conn = psycopg2.connect(**params)
      
        cur = conn.cursor()
        
        print('PostgreSQL database version:')
        cur.execute('SELECT version()')
 
        db_version = cur.fetchone()
        print(db_version)
       
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()
            print('Database connection closed.')
 
 
if __name__ == '__main__':
    connect()

def load_config():
    try:
        load_config()
        logger.info("Configuration loaded successfully.")
    except Exception as e:
        logger.error("An error occurred while loading the configuration: %s", e)

def query_database(query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
    conn = None
    cur = None
    results = []

    try:
        conn = psycopg2.connect(**config())
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute(query, params)
        results = cur.fetchall()
        logger.info("Query executed successfully.")

    except Exception as e:
        logger.error("An error occurred while executing the query: %s", e)
    finally:
        if conn is not None:
            conn.close()
        if cur is not None:
            cur.close()

    return results





