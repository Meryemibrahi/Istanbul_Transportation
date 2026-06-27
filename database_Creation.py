"""
Connecting the database
Done!

"""

import os
import psycopg2
import psycopg2.extras
import logging

from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


def connect_Database():
    conn = None

    try: 
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"),
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD")
        )
        logger.info("Connected to the database.")
        return conn

    except Exception as e:
        logger.error("An error occurred while connecting to the database: %s", e)


def execute_query(query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
    conn = None
    cur = None
    results = []

    try:
        conn = connect_Database()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute(query, params)
        results = [dict(row) for row in cur.fetchall()]
        logger.info("Query executed successfully.")

    except Exception as e:
        logger.exception("An error occurred while executing the query")
        raise

    finally:
        if cur is not None:
            cur.close()
        if conn is not None:
            conn.close()

    return results

def test_database_connection():
    try:
        conn = connect_Database()
        cur = conn.cursor()
        cur.execute('SELECT version()')
        db_version = cur.fetchone()
        logger.info("Database version: %s", db_version)
    except Exception as e:
        logger.error("An error occurred while connecting to the database: %s", e)
        raise
    finally:
        if conn is not None:
            conn.close()


if __name__ == '__main__':
    connect_Database()