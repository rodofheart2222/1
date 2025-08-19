#!/usr/bin/env python3
"""
Debug API response step by step
"""
import requests
import json
import sqlite3

def debug_api():
    print("🔍 Step 1: Check database directly")
    try:
        conn = sqlite3.connect('data/mt5_dashboard.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT instance_uuid, magic_number, symbol FROM eas LIMIT 3')
        db_rows = cursor.fetchall()
        
        print("Database rows:")
        for row in db_rows:
            uuid_val = row[0] if row[0] else "NULL"
            print(f"  UUID: {uuid_val}, Magic: {row[1]}, Symbol: {row[2]}")
        
        conn.close()
    except Exception as e:
        print(f"❌ Database error: {e}")
    
    print("\n🔍 Step 2: Test API response")
    try:
        response = requests.get('http://127.0.0.1:80/api/ea/status/all', timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            eas = data.get('eas', [])
            
            print(f"API returned {len(eas)} EAs")
            
            # Check first few EAs
            for i, ea in enumerate(eas[:3], 1):
                print(f"\nEA {i}:")
                print(f"  instanceUuid: {ea.get('instanceUuid')}")
                print(f"  instance_uuid: {ea.get('instance_uuid')}")
                print(f"  magicNumber: {ea.get('magicNumber')}")
                print(f"  symbol: {ea.get('symbol')}")
                
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            
    except Exception as e:
        print(f"❌ API error: {e}")

if __name__ == "__main__":
    debug_api()


