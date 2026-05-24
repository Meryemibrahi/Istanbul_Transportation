"""
removes all tables
done!
"""

def drop_tables():
    return """
    DROP TABLE IF EXISTS stop_times;
    DROP TABLE IF EXISTS trips;
    DROP TABLE IF EXISTS shapes;
    DROP TABLE IF EXISTS stops;
    DROP TABLE IF EXISTS routes;
    DROP TABLE IF EXISTS calendar;
    DROP TABLE IF EXISTS agency;
    DROP TABLE IF EXISTS stop_vertices;
        """