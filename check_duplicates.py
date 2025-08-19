#!/usr/bin/env python3
"""
Check for duplicate magic numbers that should show as multiple instances
"""
import sqlite3

def check_duplicates():
    try:
        conn = sqlite3.connect('data/mt5_dashboard.db')
        cursor = conn.cursor()
        
        # Check for magic numbers with multiple instances
        cursor.execute('''
            SELECT magic_number, COUNT(*) as count 
            FROM eas 
            GROUP BY magic_number 
            HAVING COUNT(*) > 1
        ''')
        duplicates = cursor.fetchall()
        
        print("🔍 Magic numbers with multiple instances:")
        if duplicates:
            for row in duplicates:
                print(f"   Magic {row[0]}: {row[1]} instances")
        else:
            print("   None found")
        
        # Show all EAs grouped by magic number
        cursor.execute('''
            SELECT magic_number, instance_uuid, symbol, strategy_tag, account_number, broker
            FROM eas 
            ORDER BY magic_number
        ''')
        all_eas = cursor.fetchall()
        
        print(f"\n📋 All {len(all_eas)} EAs in database:")
        current_magic = None
        for ea in all_eas:
            magic, uuid, symbol, strategy, account, broker = ea
            if magic != current_magic:
                print(f"\n🎯 Magic Number {magic}:")
                current_magic = magic
            
            uuid_display = uuid[:8] + "..." if uuid else "None"
            print(f"   • UUID: {uuid_display}, Symbol: {symbol}, Strategy: {strategy}")
            if account:
                print(f"     Account: {account}, Broker: {broker or 'N/A'}")
        
        conn.close()
        
        # If no duplicates, suggest creating some for testing
        if not duplicates:
            print(f"\n💡 To test multiple instances, you could:")
            print("   1. Run the same EA on different MT5 accounts")
            print("   2. Run the same EA on different symbols") 
            print("   3. Add test data with same magic number but different UUIDs")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_duplicates()


