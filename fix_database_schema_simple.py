#!/usr/bin/env python3
"""
Fix Database Schema Alignment (Simple Version)
Ensures the database has all required tables with correct structure
"""

import sqlite3
import os
from pathlib import Path

def get_db_path():
    """Get database path from environment or default"""
    return os.getenv("DATABASE_PATH", "data/mt5_dashboard.db")

def ensure_directory_exists(db_path):
    """Ensure the database directory exists"""
    db_dir = os.path.dirname(db_path)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)

def run_migrations(conn):
    """Run migration SQL files"""
    cursor = conn.cursor()
    
    # Check for migration files
    migrations_dir = Path(__file__).parent / "backend" / "database" / "migrations"
    if migrations_dir.exists():
        migration_files = sorted(migrations_dir.glob("*.sql"))
        print(f"Found {len(migration_files)} migration files")
        
        for migration_file in migration_files:
            print(f"Running migration: {migration_file.name}")
            with open(migration_file, 'r') as f:
                sql_content = f.read()
                # Split by semicolon and execute each statement
                statements = [s.strip() for s in sql_content.split(';') if s.strip()]
                for statement in statements:
                    if statement and not statement.startswith('--'):
                        try:
                            cursor.execute(statement)
                        except sqlite3.Error as e:
                            print(f"  Warning: {e}")

def create_all_tables(conn):
    """Create all required tables"""
    cursor = conn.cursor()
    
    # Enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON")
    
    # Read and execute schema.sql
    schema_file = Path(__file__).parent / "backend" / "database" / "schema.sql"
    if schema_file.exists():
        print("Executing schema.sql...")
        with open(schema_file, 'r') as f:
            sql_content = f.read()
            # Split by semicolon and execute each statement
            statements = [s.strip() for s in sql_content.split(';') if s.strip()]
            for statement in statements:
                if statement and not statement.startswith('--'):
                    try:
                        cursor.execute(statement)
                    except sqlite3.Error as e:
                        print(f"  Warning: {e}")
    
    # Additional tables from init_db.py that might be missing
    additional_tables = [
        """CREATE TABLE IF NOT EXISTS commands (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            command_id TEXT UNIQUE NOT NULL,
            magic_number INTEGER NOT NULL,
            command_type TEXT NOT NULL,
            parameters TEXT,
            status TEXT DEFAULT 'pending',
            response TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            processed_at TIMESTAMP
        )""",
        
        """CREATE TABLE IF NOT EXISTS news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT,
            impact TEXT,
            currency TEXT,
            event_time TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""",
        
        """CREATE TABLE IF NOT EXISTS backtests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            backtest_id TEXT UNIQUE NOT NULL,
            ea_name TEXT NOT NULL,
            symbol TEXT NOT NULL,
            timeframe TEXT NOT NULL,
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            initial_balance REAL NOT NULL,
            final_balance REAL NOT NULL,
            total_trades INTEGER DEFAULT 0,
            winning_trades INTEGER DEFAULT 0,
            losing_trades INTEGER DEFAULT 0,
            profit_factor REAL DEFAULT 0.0,
            max_drawdown REAL DEFAULT 0.0,
            sharpe_ratio REAL DEFAULT 0.0,
            parameters TEXT,
            results TEXT,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP
        )"""
    ]
    
    for create_sql in additional_tables:
        try:
            cursor.execute(create_sql)
        except sqlite3.Error as e:
            print(f"  Warning creating additional table: {e}")
    
    # Ensure eas table has all required columns
    cursor.execute("PRAGMA table_info(eas)")
    existing_columns = {row[1] for row in cursor.fetchall()}
    
    # Add missing columns to eas table if needed
    columns_to_add = {
        'ea_name': 'TEXT',
        'strategy_tag': 'TEXT',
        'risk_config': 'REAL DEFAULT 1.0',
        'timeframe': "TEXT DEFAULT 'M1'",
        'last_heartbeat': 'TIMESTAMP',
        'account_number': 'TEXT',
        'broker': 'TEXT',
        'balance': 'REAL DEFAULT 0.0',
        'equity': 'REAL DEFAULT 0.0',
        'margin': 'REAL DEFAULT 0.0',
        'free_margin': 'REAL DEFAULT 0.0',
        'margin_level': 'REAL DEFAULT 0.0',
        'total_trades': 'INTEGER DEFAULT 0',
        'active_trades': 'INTEGER DEFAULT 0',
        'total_profit': 'REAL DEFAULT 0.0',
        'updated_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'
    }
    
    for col_name, col_type in columns_to_add.items():
        if col_name not in existing_columns:
            try:
                cursor.execute(f"ALTER TABLE eas ADD COLUMN {col_name} {col_type}")
                print(f"Added column {col_name} to eas table")
            except sqlite3.Error as e:
                print(f"  Warning adding column {col_name}: {e}")
    
    # Add magic_number column to backtest_benchmarks if missing
    cursor.execute("PRAGMA table_info(backtest_benchmarks)")
    bb_columns = {row[1] for row in cursor.fetchall()}
    if 'magic_number' not in bb_columns:
        try:
            cursor.execute("ALTER TABLE backtest_benchmarks ADD COLUMN magic_number INTEGER")
            print("Added magic_number column to backtest_benchmarks table")
        except sqlite3.Error as e:
            print(f"  Warning adding magic_number column: {e}")
    
    conn.commit()

def verify_database(conn):
    """Verify database structure"""
    cursor = conn.cursor()
    
    print("\n=== Database Verification ===")
    
    # List all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = cursor.fetchall()
    
    print(f"\nFound {len(tables)} tables:")
    for table in tables:
        table_name = table[0]
        if table_name == 'sqlite_sequence':
            continue
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        print(f"  ✓ {table_name}: {count} records")
    
    # Check required tables
    required_tables = [
        'eas', 'ea_status', 'trades', 'performance_history',
        'backtest_benchmarks', 'news_events', 'command_queue',
        'commands', 'news', 'backtests'
    ]
    
    existing_table_names = {t[0] for t in tables}
    missing_tables = [t for t in required_tables if t not in existing_table_names]
    
    if missing_tables:
        print(f"\n⚠️  Missing tables: {missing_tables}")
        return False
    else:
        print("\n✓ All required tables exist")
        return True

def main():
    """Main execution"""
    print("=== Database Schema Setup ===\n")
    
    # Get database path
    db_path = get_db_path()
    print(f"Database path: {db_path}")
    
    # Ensure directory exists
    ensure_directory_exists(db_path)
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    
    try:
        # Create all tables
        create_all_tables(conn)
        
        # Run migrations
        run_migrations(conn)
        
        # Verify database
        is_valid = verify_database(conn)
        
        if is_valid:
            print("\n✅ Database is properly set up and ready for backend use!")
        else:
            print("\n⚠️  Some required tables are missing")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    main()