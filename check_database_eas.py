#!/usr/bin/env python3
"""
Check Database EAs
See what EAs are currently in the database
"""

import sqlite3
import os
from datetime import datetime

def check_database_eas():
    """Check what EAs are in the database"""
    try:
        db_path = os.getenv("DATABASE_PATH", "data/mt5_dashboard.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("=== EAs in Database ===")
        
        # Get all EAs
        cursor.execute("""
            SELECT e.magic_number, e.ea_name, e.symbol, e.strategy_tag, e.status,
                   e.last_heartbeat, e.last_seen,
                   s.current_profit, s.open_positions, s.timestamp as status_timestamp
            FROM eas e
            LEFT JOIN ea_status s ON s.ea_id = e.id
            ORDER BY e.magic_number
        """)
        
        eas = cursor.fetchall()
        
        print(f"Total EAs found: {len(eas)}")
        print()
        
        for ea in eas:
            magic, name, symbol, strategy, status, heartbeat, last_seen, profit, positions, status_time = ea
            print(f"EA {magic}:")
            print(f"  Name: {name}")
            print(f"  Symbol: {symbol}")
            print(f"  Strategy: {strategy}")
            print(f"  Status: {status}")
            print(f"  Profit: {profit}")
            print(f"  Positions: {positions}")
            print(f"  Last Heartbeat: {heartbeat}")
            print(f"  Last Seen: {last_seen}")
            print(f"  Status Time: {status_time}")
            print()
        
        conn.close()
        
        # Identify which are real vs mock
        real_eas = [10981, 14598]  # The ones we found from MT5
        
        print("=== Analysis ===")
        for ea in eas:
            magic = ea[0]
            if magic in real_eas:
                print(f"EA {magic}: REAL (from MT5)")
            else:
                print(f"EA {magic}: MOCK/SAMPLE (should be removed)")
        
        return eas
        
    except Exception as e:
        print(f"Error checking database: {e}")
        return []

def clean_database_eas():
    """Remove mock/sample EAs, keep only real ones"""
    try:
        db_path = os.getenv("DATABASE_PATH", "data/mt5_dashboard.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Real EAs from MT5
        real_eas = [10981, 14598]
        
        print("=== Cleaning Database ===")
        
        # Get all EA IDs that are NOT real
        cursor.execute("""
            SELECT id, magic_number FROM eas 
            WHERE magic_number NOT IN (?, ?)
        """, real_eas)
        
        mock_eas = cursor.fetchall()
        
        if not mock_eas:
            print("No mock EAs to remove")
            return True
        
        print(f"Found {len(mock_eas)} mock EAs to remove:")
        for ea_id, magic in mock_eas:
            print(f"  EA {magic} (ID: {ea_id})")
        
        # Remove EA status records for mock EAs
        for ea_id, magic in mock_eas:
            cursor.execute("DELETE FROM ea_status WHERE ea_id = ?", (ea_id,))
            print(f"  Removed status records for EA {magic}")
        
        # Remove mock EAs
        cursor.execute("""
            DELETE FROM eas 
            WHERE magic_number NOT IN (?, ?)
        """, real_eas)
        
        removed_count = cursor.rowcount
        print(f"Removed {removed_count} mock EAs")
        
        # Commit changes
        conn.commit()
        conn.close()
        
        print("✅ Database cleaned successfully")
        return True
        
    except Exception as e:
        print(f"Error cleaning database: {e}")
        return False

def verify_cleanup():
    """Verify the cleanup worked"""
    print("\n=== Verification ===")
    eas = check_database_eas()
    
    real_eas = [10981, 14598]
    remaining_eas = [ea[0] for ea in eas]
    
    if set(remaining_eas) == set(real_eas):
        print("✅ Cleanup successful - only real EAs remain")
        return True
    else:
        print("❌ Cleanup failed - unexpected EAs still present")
        print(f"Expected: {real_eas}")
        print(f"Found: {remaining_eas}")
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Check and Clean Database EAs")
    parser.add_argument("--check", action="store_true", help="Check current EAs in database")
    parser.add_argument("--clean", action="store_true", help="Remove mock EAs, keep only real ones")
    parser.add_argument("--verify", action="store_true", help="Verify cleanup")
    
    args = parser.parse_args()
    
    if args.check:
        check_database_eas()
    elif args.clean:
        success = clean_database_eas()
        if success:
            verify_cleanup()
    elif args.verify:
        verify_cleanup()
    else:
        print("Use --check to see EAs, --clean to remove mock EAs, or --verify to check cleanup")