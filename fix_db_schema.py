#!/usr/bin/env python3
"""
Fix database schema to add instance_uuid column
"""

import sqlite3
import os
from pathlib import Path

def fix_database_schema():
    """Add instance_uuid column to the correct database"""
    
    # Try both possible database locations
    db_paths = [
        "../data/mt5_dashboard.db",
        "data/mt5_dashboard.db"
    ]
    
    for db_path in db_paths:
        if os.path.exists(db_path):
            print(f"Found database: {db_path}")
            
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Check current schema
                cursor.execute("PRAGMA table_info(eas)")
                columns = [col[1] for col in cursor.fetchall()]
                print(f"Current columns: {columns}")
                
                if 'instance_uuid' in columns:
                    print("✅ instance_uuid column already exists!")
                    conn.close()
                    continue
                
                print("Adding instance_uuid column...")
                
                # Add instance_uuid column
                cursor.execute("ALTER TABLE eas ADD COLUMN instance_uuid TEXT")
                
                # Generate UUIDs for existing records
                cursor.execute("SELECT id, magic_number FROM eas")
                existing_eas = cursor.fetchall()
                
                import uuid
                for ea_id, magic_number in existing_eas:
                    instance_uuid = str(uuid.uuid4())
                    cursor.execute(
                        "UPDATE eas SET instance_uuid = ? WHERE id = ?",
                        (instance_uuid, ea_id)
                    )
                    print(f"Generated UUID {instance_uuid} for EA {magic_number}")
                
                # Create index for performance
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_eas_instance_uuid ON eas(instance_uuid)")
                
                conn.commit()
                conn.close()
                
                print(f"✅ Database {db_path} fixed successfully!")
                
                # Verify the fix
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("PRAGMA table_info(eas)")
                new_columns = [col[1] for col in cursor.fetchall()]
                print(f"New columns: {new_columns}")
                print(f"instance_uuid exists: {'instance_uuid' in new_columns}")
                conn.close()
                
            except Exception as e:
                print(f"❌ Error fixing database {db_path}: {e}")
        else:
            print(f"Database not found: {db_path}")

if __name__ == "__main__":
    fix_database_schema()


