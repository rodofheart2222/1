#!/usr/bin/env python3
"""
Check database UUID state
"""
import sqlite3

def check_database():
    try:
        conn = sqlite3.connect('data/mt5_dashboard.db')
        cursor = conn.cursor()
        
        # Check total count
        cursor.execute('SELECT COUNT(*) FROM eas')
        total_count = cursor.fetchone()[0]
        print(f"📊 Total EAs in database: {total_count}")
        
        # Check UUIDs
        cursor.execute('SELECT COUNT(*) FROM eas WHERE instance_uuid IS NOT NULL')
        uuid_count = cursor.fetchone()[0]
        print(f"🆔 EAs with UUIDs: {uuid_count}")
        
        # Show sample data
        cursor.execute('SELECT instance_uuid, magic_number, symbol, strategy_tag FROM eas')
        rows = cursor.fetchall()
        
        print("\n📋 Current EA entries:")
        for i, row in enumerate(rows, 1):
            uuid_display = row[0][:8] + "..." if row[0] else "None"
            print(f"  {i}. UUID: {uuid_display}, Magic: {row[1]}, Symbol: {row[2]}, Strategy: {row[3]}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error checking database: {e}")

if __name__ == "__main__":
    check_database()


