"""
Show all available stops so you know what valid IDs to use
"""
from database_Creation import execute_query

print("\n" + "="*100)
print("VALID STOP IDs IN YOUR DATABASE - Use these for testing!")
print("="*100)

# Get a good sample of stops
result = execute_query("""
    SELECT stop_id, stop_code, stop_name 
    FROM stops 
    ORDER BY stop_id
    LIMIT 50
""")

print("\nFirst 50 stops - Copy any of these stop_id values to test:")
print("-" * 100)
for i, r in enumerate(result):
    if i % 5 == 0:
        print()
    print(f"  {str(r['stop_id']):10} | {str(r['stop_code'] or 'N/A')[:10]:10} | {r['stop_name'][:30]}", end="")

print("\n" + "="*100)
print("QUICK TEST TIPS:")
print("="*100)
print("✓ Use: /stops/18926")
print("✓ Use: /stops/12258")
print("✓ Use: /stops/91618")
print("✗ Don't use: /stops/564 (doesn't exist)")
print("✗ Don't use: /stops/565 (doesn't exist)")

print("\n" + "="*100)
print("OR search by code using the new endpoint:")
print("="*100)
print("✓ Use: /stops/by-code/A0005C")
print("✓ Use: /stops/by-code/A (finds all codes starting with A)")
