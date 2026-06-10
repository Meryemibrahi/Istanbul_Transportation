"""
Quick test script to check what stops exist in the database
"""
from database_Creation import execute_query

print("=" * 80)
print("TESTING STOPS IN DATABASE")
print("=" * 80)

# Get total count
result = execute_query("SELECT COUNT(*) as count FROM stops")
print(f"\nTotal stops in database: {result[0]['count']}")

# Get first 10 stops
print("\nFirst 10 stops in database:")
stops = execute_query("""
    SELECT stop_id, stop_name, stop_lat, stop_lon
    FROM stops
    ORDER BY stop_id
    LIMIT 10
""")
for stop in stops:
    print(f"  ID: {stop['stop_id']:10} | Name: {stop['stop_name']}")

# Check if specific IDs exist
print("\nChecking for specific stop IDs:")
for stop_id in ['565', '564', '18926', '18917']:
    result = execute_query("SELECT stop_id, stop_name FROM stops WHERE stop_id = %s", (stop_id,))
    if result:
        print(f"  ✓ Stop {stop_id} found: {result[0]['stop_name']}")
    else:
        print(f"  ✗ Stop {stop_id} NOT FOUND")

# Get min and max stop IDs
print("\nStop ID range:")
result = execute_query("SELECT MIN(CAST(stop_id AS INTEGER)) as min_id, MAX(CAST(stop_id AS INTEGER)) as max_id FROM stops")
if result:
    print(f"  Min: {result[0]['min_id']}, Max: {result[0]['max_id']}")
