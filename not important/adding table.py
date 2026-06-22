def execute_scalar_query(query: str, params: Optional[tuple] = None) -> Any:
    conn = None
    cur = None
    result = None

    try:
        conn = connect_Database()
        cur = conn.cursor()
        cur.execute(query, params or ())
        result = cur.fetchone()[0]
        logger.info("Scalar query executed successfully.")

    except Exception as e:
        logger.error("An error occurred while executing the scalar query: %s", e)
    finally:
        if conn is not None:
            conn.close()
        if cur is not None:
            cur.close()

    return result


def update_insert_delete_query(query: str, params: Optional[tuple] = None) -> None:
    conn = None
    cur = None

    try:
        conn = connect_Database()
        cur = conn.cursor()
        cur.execute(query, params or ())
        conn.commit()
        logger.info("Update/Insert/Delete query executed successfully.")

    except Exception as e:
        logger.error("An error occurred while executing the update/insert/delete query: %s", e)
        if conn is not None:
            conn.rollback()
    finally:
        if conn is not None:
            conn.close()
        if cur is not None:
            cur.close()
