from database_Creation import execute_query

print("\n" + "="*80)
print("CHECKING IF 564/565 ARE STOP CODES")
print("="*80)

for code in ['564', '565']:
    result = execute_query("SELECT stop_id, stop_code, stop_name FROM stops WHERE stop_code = %s LIMIT 1", (code,))
    if result:
        print(f"\n✓ Found! stop_code '{code}'")
        print(f"    stop_id: {result[0]['stop_id']}")
        print(f"    stop_name: {result[0]['stop_name']}")
    else:
        print(f"\n✗ No stop with code '{code}'")

print("\n" + "="*80)
print("SAMPLE OF VALID STOP CODES (first 30)")
print("="*80)
result = execute_query("""
    SELECT stop_code, stop_id, stop_name 
    FROM stops 
    WHERE stop_code IS NOT NULL 
    ORDER BY stop_code
    LIMIT 30
""")
for r in result:
    print(f"  Code: {str(r['stop_code']):10} | ID: {str(r['stop_id']):10} | Name: {r['stop_name'][:30]}")
