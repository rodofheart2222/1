#!/usr/bin/env python3
"""
Fix Database Schema - Add missing ea_status table
"""

import os
import sqlite3
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_missing_tables():
    """Add missing tables to the database"""
    try:
        # Database path
        db_path = os.getenv("DATABASE_PATH", "data/mt5_dashboard.db")
        
        # Ensure data directory exists
        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)
        
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if ea_status table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ea_status'")
        if cursor.fetchone():
            logger.info("ea_status table already exists")
        else:
            logger.info("Creating ea_status table...")
            
            # Create ea_status table with correct structure
            cursor.execute("""
                CREATE TABLE ea_status (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ea_id INTEGER NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    current_profit REAL DEFAULT 0.0,
                    open_positions INTEGER DEFAULT 0,
                    sl_value REAL,
                    tp_value REAL,
                    trailing_active BOOLEAN DEFAULT FALSE,
                    module_status TEXT,
                    FOREIGN KEY (ea_id) REFERENCES eas (id)
                )
            """)
            
            # Create indexes for better performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_ea_status_ea_id ON ea_status (ea_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_ea_status_timestamp ON ea_status (timestamp)")
            
            logger.info("ea_status table created successfully")
        
        # Check if other missing tables exist and create them
        missing_tables = {
            'ea_tags': """
                CREATE TABLE ea_tags (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ea_id INTEGER NOT NULL,
                    tag_name TEXT NOT NULL,
                    tag_value TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (ea_id) REFERENCES eas (id),
                    UNIQUE(ea_id, tag_name)
                )
            """,
            'ea_groups': """
                CREATE TABLE ea_groups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    group_name TEXT UNIQUE NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """,
            'ea_group_memberships': """
                CREATE TABLE ea_group_memberships (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ea_id INTEGER NOT NULL,
                    group_id INTEGER NOT NULL,
                    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (ea_id) REFERENCES eas (id),
                    FOREIGN KEY (group_id) REFERENCES ea_groups (id),
                    UNIQUE(ea_id, group_id)
                )
            """,
            'news_events': """
                CREATE TABLE news_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT,
                    currency TEXT,
                    impact_level TEXT,
                    event_time TIMESTAMP,
                    actual_value TEXT,
                    forecast_value TEXT,
                    previous_value TEXT,
                    pre_minutes INTEGER DEFAULT 15,
                    post_minutes INTEGER DEFAULT 15,
                    source TEXT DEFAULT 'forexfactory',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
        }
        
        for table_name, create_sql in missing_tables.items():
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
            if cursor.fetchone():
                logger.info(f"{table_name} table already exists")
            else:
                logger.info(f"Creating {table_name} table...")
                cursor.execute(create_sql)
                logger.info(f"{table_name} table created successfully")
        
        # Add missing columns to existing tables if needed
        add_missing_columns(cursor)
        
        # Commit changes
        conn.commit()
        conn.close()
        
        logger.info("Database schema updated successfully")
        return True
        
    except Exception as e:
        logger.error(f"Database schema update failed: {e}")
        return False

def add_missing_columns(cursor):
    """Add missing columns to existing tables"""
    try:
        # Check if eas table has all required columns
        cursor.execute("PRAGMA table_info(eas)")
        columns = [row[1] for row in cursor.fetchall()]
        
        missing_columns = {
            'strategy_tag': 'TEXT',
            'last_seen': 'TIMESTAMP',
            'risk_config': 'REAL DEFAULT 1.0'
        }
        
        for column_name, column_type in missing_columns.items():
            if column_name not in columns:
                logger.info(f"Adding missing column {column_name} to eas table...")
                cursor.execute(f"ALTER TABLE eas ADD COLUMN {column_name} {column_type}")
        
    except Exception as e:
        logger.warning(f"Could not add missing columns: {e}")

def verify_schema():
    """Verify the database schema is correct"""
    try:
        db_path = os.getenv("DATABASE_PATH", "data/mt5_dashboard.db")
        
        if not os.path.exists(db_path):
            logger.error("Database file does not exist")
            return False
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check required tables
        required_tables = ['eas', 'ea_status', 'trades', 'commands', 'news', 'backtests']
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = [row[0] for row in cursor.fetchall()]
        
        missing_tables = [table for table in required_tables if table not in existing_tables]
        
        if missing_tables:
            logger.error(f"Missing tables: {missing_tables}")
            conn.close()
            return False
        
        # Test ea_status table structure
        cursor.execute("PRAGMA table_info(ea_status)")
        ea_status_columns = [row[1] for row in cursor.fetchall()]
        
        required_ea_status_columns = ['id', 'ea_id', 'timestamp', 'current_profit', 'open_positions']
        missing_columns = [col for col in required_ea_status_columns if col not in ea_status_columns]
        
        if missing_columns:
            logger.error(f"Missing columns in ea_status table: {missing_columns}")
            conn.close()
            return False
        
        conn.close()
        logger.info("Database schema verification passed")
        return True
        
    except Exception as e:
        logger.error(f"Schema verification failed: {e}")
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Fix Database Schema")
    parser.add_argument("--fix", action="store_true", help="Fix missing tables and columns")
    parser.add_argument("--verify", action="store_true", help="Verify database schema")
    
    args = parser.parse_args()
    
    if args.fix:
        success = add_missing_tables()
        print(f"Schema fix: {'SUCCESS' if success else 'FAILED'}")
    elif args.verify:
        valid = verify_schema()
        print(f"Schema verification: {'PASSED' if valid else 'FAILED'}")
    else:
        print("Use --fix to fix the schema or --verify to check it")