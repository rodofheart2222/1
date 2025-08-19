#!/usr/bin/env python3
"""
Debug database connection and schema from backend perspective
"""

import os
import sqlite3
import sys
sys.path.append('.')

try:
    from config.central_config import DATABASE_PATH
    print(f"Backend configured DATABASE_PATH: {DATABASE_PATH}")
    print(f"Database file exists: {os.path.exists(DATABASE_PATH)}")
    print(f"Absolute path: {os.path.abspath(DATABASE_PATH)}")
except Exception as e:
    print(f"Error importing DATABASE_PATH: {e}")
    DATABASE_PATH = "data/mt5_dashboard.db"
    print(f"Using fallback DATABASE_PATH: {DATABASE_PATH}")

# Test database connection exactly as backend does
def test_database():
    try:
        conn = sqlite3.connect(DATABASE_PATH, timeout=30.0)
        cursor = conn.cursor()
        
        print("\n=== Database Schema ===")
        cursor.execute("PRAGMA table_info(eas)")
        columns = cursor.fetchall()
        print("eas table columns:")
        for col in columns:
            print(f"  {col[1]} ({col[2]}) - NOT NULL: {col[3]} - DEFAULT: {col[4]}")
        
        print(f"\ninstance_uuid column exists: {'instance_uuid' in [col[1] for col in columns]}")
        
        print("\n=== Test Query ===")
        # Test the exact query that's failing
        cursor.execute("""
            SELECT e.instance_uuid, e.magic_number, e.symbol, e.strategy_tag, e.status
            FROM eas e
            LIMIT 1
        """)
        rows = cursor.fetchall()
        print(f"Query successful! Found {len(rows)} rows")
        
        if rows:
            print("Sample row:", rows[0])
        
        print("\n=== All EAs ===")
        cursor.execute("SELECT id, instance_uuid, magic_number, symbol FROM eas")
        all_eas = cursor.fetchall()
        print(f"Total EAs in database: {len(all_eas)}")
        for ea in all_eas:
            print(f"  ID: {ea[0]}, UUID: {ea[1]}, Magic: {ea[2]}, Symbol: {ea[3]}")
        
        conn.close()
        print("\n✅ Database connection and query successful!")
        
    except Exception as e:
        print(f"\n❌ Database error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_database()


