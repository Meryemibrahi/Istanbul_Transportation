"""
Export all stop IDs to a CSV file for reference
"""
import csv
from database_Creation import execute_query

print("\n" + "="*80)
print("EXPORTING ALL STOPS TO CSV")
print("="*80)

# Get all stops
query = """
    SELECT stop_id, stop_code, stop_name, stop_lat, stop_lon, 
           stop_desc, zone_id, location_type
    FROM stops 
    ORDER BY stop_id
"""

stops = execute_query(query)

# Write to CSV
output_file = "all_stops.csv"
with open(output_file, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['stop_id', 'stop_code', 'stop_name', 'stop_lat', 'stop_lon', 'stop_desc', 'zone_id', 'location_type'])
    writer.writeheader()
    writer.writerows(stops)

print(f"✓ Exported {len(stops)} stops to {output_file}")
print(f"  File location: {output_file}")
print("\nFirst 5 stops:")
for i, stop in enumerate(stops[:5]):
    print(f"  {stop['stop_id']}: {stop['stop_name']}")
print(f"\nLast 5 stops:")
for i, stop in enumerate(stops[-5:]):
    print(f"  {stop['stop_id']}: {stop['stop_name']}")
