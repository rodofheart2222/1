#!/usr/bin/env python3
"""
Apply the UUID migration directly
"""

import sqlite3
import os
from pathlib import Path

# Database path
db_path = os.getenv("DATABASE_PATH", "data/mt5_dashboard.db")

print(f"Connecting to database: {db_path}")

try:
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if instance_uuid column already exists
    cursor.execute("PRAGMA table_info(eas)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'instance_uuid' in columns:
        print("✅ instance_uuid column already exists!")
        conn.close()
        exit(0)
    
    print("Adding instance_uuid column to eas table...")
    
    # Read and execute the migration
    migration_file = Path("backend/database/migrations/20241218_000001_add_uuid_to_eas.sql")
    
    if not migration_file.exists():
        print(f"❌ Migration file not found: {migration_file}")
        exit(1)
    
    with open(migration_file, 'r') as f:
        migration_sql = f.read()
    
    # Execute the migration
    cursor.executescript(migration_sql)
    
    # Commit changes
    conn.commit()
    conn.close()
    
    print("✅ Migration applied successfully!")
    
except Exception as e:
    print(f"❌ Migration failed: {e}")
    if 'conn' in locals():
        conn.close()
    exit(1)


