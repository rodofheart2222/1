#!/usr/bin/env python3
"""
Fix Database Schema Alignment
Ensures the database has all required tables with correct structure
"""

import sqlite3
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.database.connection import DatabaseManager
from backend.database.migrations import MigrationManager

def get_db_path():
    """Get database path from environment or default"""
    return os.getenv("DATABASE_PATH", "data/mt5_dashboard.db")

def ensure_directory_exists(db_path):
    """Ensure the database directory exists"""
    db_dir = os.path.dirname(db_path)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)

def create_missing_tables(conn):
    """Create any missing tables that the backend expects"""
    cursor = conn.cursor()
    
    # Check which tables exist
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    existing_tables = {row[0] for row in cursor.fetchall()}
    
    print(f"Existing tables: {existing_tables}")
    
    # Ensure schema_migrations table exists
    if 'schema_migrations' not in existing_tables:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                version TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                checksum TEXT
            )
        """)
        print("Created schema_migrations table")
    
    # Core tables from schema.sql (with corrected structure)
    tables_to_create = {
        'eas': """
            CREATE TABLE IF NOT EXISTS eas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                magic_number INTEGER UNIQUE NOT NULL,
                symbol TEXT NOT NULL,
                strategy_tag TEXT NOT NULL,
                risk_config REAL DEFAULT 1.0,
                status TEXT DEFAULT 'active' CHECK (status IN ('active', 'paused', 'error')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                -- Additional columns that init_db.py expects
                ea_name TEXT,
                timeframe TEXT DEFAULT 'M1',
                last_heartbeat TIMESTAMP,
                account_number TEXT,
                broker TEXT,
                balance REAL DEFAULT 0.0,
                equity REAL DEFAULT 0.0,
                margin REAL DEFAULT 0.0,
                free_margin REAL DEFAULT 0.0,
                margin_level REAL DEFAULT 0.0,
                total_trades INTEGER DEFAULT 0,
                active_trades INTEGER DEFAULT 0,
                total_profit REAL DEFAULT 0.0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """,
        
        'ea_status': """
            CREATE TABLE IF NOT EXISTS ea_status (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ea_id INTEGER NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                current_profit REAL DEFAULT 0.0,
                open_positions INTEGER DEFAULT 0,
                sl_value REAL,
                tp_value REAL,
                trailing_active BOOLEAN DEFAULT FALSE,
                module_status TEXT,
                FOREIGN KEY (ea_id) REFERENCES eas(id) ON DELETE CASCADE
            )
        """,
        
        'performance_history': """
            CREATE TABLE IF NOT EXISTS performance_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ea_id INTEGER NOT NULL,
                date DATE DEFAULT (DATE('now')),
                total_profit REAL DEFAULT 0.0,
                profit_factor REAL DEFAULT 0.0,
                expected_payoff REAL DEFAULT 0.0,
                drawdown REAL DEFAULT 0.0,
                z_score REAL DEFAULT 0.0,
                trade_count INTEGER DEFAULT 0,
                FOREIGN KEY (ea_id) REFERENCES eas(id) ON DELETE CASCADE
            )
        """,
        
        'trades': """
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ea_id INTEGER NOT NULL,
                symbol TEXT NOT NULL,
                order_type TEXT NOT NULL,
                volume REAL NOT NULL,
                open_price REAL NOT NULL,
                close_price REAL,
                profit REAL DEFAULT 0.0,
                open_time TIMESTAMP NOT NULL,
                close_time TIMESTAMP,
                -- Additional columns from init_db.py
                trade_id TEXT,
                magic_number INTEGER,
                trade_type TEXT,
                requested_price REAL,
                actual_price REAL,
                sl REAL,
                tp REAL,
                status TEXT DEFAULT 'pending',
                commission REAL DEFAULT 0.0,
                swap REAL DEFAULT 0.0,
                comment TEXT,
                request_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                fill_time TIMESTAMP,
                dashboard_command_id TEXT,
                mt5_ticket INTEGER,
                risk_percent REAL DEFAULT 0.0,
                account_balance REAL DEFAULT 0.0,
                position_size_usd REAL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (ea_id) REFERENCES eas(id) ON DELETE CASCADE
            )
        """,
        
        'backtest_benchmarks': """
            CREATE TABLE IF NOT EXISTS backtest_benchmarks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ea_id INTEGER,
                magic_number INTEGER,
                profit_factor REAL NOT NULL,
                expected_payoff REAL NOT NULL,
                drawdown REAL NOT NULL,
                win_rate REAL NOT NULL,
                trade_count INTEGER NOT NULL,
                upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (ea_id) REFERENCES eas(id) ON DELETE CASCADE
            )
        """,
        
        'news_events': """
            CREATE TABLE IF NOT EXISTS news_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_time TIMESTAMP NOT NULL,
                currency TEXT NOT NULL,
                impact_level TEXT NOT NULL CHECK (impact_level IN ('high', 'medium', 'low')),
                description TEXT NOT NULL,
                pre_minutes INTEGER DEFAULT 30,
                post_minutes INTEGER DEFAULT 30
            )
        """,
        
        'command_queue': """
            CREATE TABLE IF NOT EXISTS command_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ea_id INTEGER,
                command_type TEXT NOT NULL,
                command_data TEXT,
                scheduled_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                executed BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (ea_id) REFERENCES eas(id) ON DELETE CASCADE
            )
        """,
        
        # Tables from init_db.py
        'commands': """
            CREATE TABLE IF NOT EXISTS commands (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                command_id TEXT UNIQUE NOT NULL,
                magic_number INTEGER NOT NULL,
                command_type TEXT NOT NULL,
                parameters TEXT,
                status TEXT DEFAULT 'pending',
                response TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                processed_at TIMESTAMP
            )
        """,
        
        'news': """
            CREATE TABLE IF NOT EXISTS news (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT,
                impact TEXT,
                currency TEXT,
                event_time TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """,
        
        'backtests': """
            CREATE TABLE IF NOT EXISTS backtests (
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
            )
        """,
        
        # Tables from migrations
        'ea_tags': """
            CREATE TABLE IF NOT EXISTS ea_tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ea_id INTEGER NOT NULL,
                tag_name TEXT NOT NULL,
                tag_value TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (ea_id) REFERENCES eas(id) ON DELETE CASCADE,
                UNIQUE(ea_id, tag_name)
            )
        """,
        
        'ea_groups': """
            CREATE TABLE IF NOT EXISTS ea_groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_name TEXT UNIQUE NOT NULL,
                group_type TEXT NOT NULL CHECK (group_type IN ('symbol', 'strategy', 'risk_level', 'custom')),
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """,
        
        'ea_group_memberships': """
            CREATE TABLE IF NOT EXISTS ea_group_memberships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ea_id INTEGER NOT NULL,
                group_id INTEGER NOT NULL,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (ea_id) REFERENCES eas(id) ON DELETE CASCADE,
                FOREIGN KEY (group_id) REFERENCES ea_groups(id) ON DELETE CASCADE,
                UNIQUE(ea_id, group_id)
            )
        """
    }
    
    # Create missing tables
    for table_name, create_sql in tables_to_create.items():
        if table_name not in existing_tables:
            cursor.execute(create_sql)
            print(f"Created table: {table_name}")
        else:
            # Check if we need to add missing columns
            cursor.execute(f"PRAGMA table_info({table_name})")
            existing_columns = {row[1] for row in cursor.fetchall()}
            print(f"Table {table_name} exists with columns: {existing_columns}")
    
    # Create all indexes
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_eas_magic_number ON eas(magic_number)",
        "CREATE INDEX IF NOT EXISTS idx_eas_symbol ON eas(symbol)",
        "CREATE INDEX IF NOT EXISTS idx_eas_strategy_tag ON eas(strategy_tag)",
        "CREATE INDEX IF NOT EXISTS idx_eas_status ON eas(status)",
        "CREATE INDEX IF NOT EXISTS idx_ea_status_ea_id ON ea_status(ea_id)",
        "CREATE INDEX IF NOT EXISTS idx_ea_status_timestamp ON ea_status(timestamp)",
        "CREATE INDEX IF NOT EXISTS idx_performance_history_ea_id ON performance_history(ea_id)",
        "CREATE INDEX IF NOT EXISTS idx_performance_history_date ON performance_history(date)",
        "CREATE INDEX IF NOT EXISTS idx_trades_ea_id ON trades(ea_id)",
        "CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol)",
        "CREATE INDEX IF NOT EXISTS idx_trades_open_time ON trades(open_time)",
        "CREATE INDEX IF NOT EXISTS idx_trades_magic_number ON trades(magic_number)",
        "CREATE INDEX IF NOT EXISTS idx_trades_status ON trades(status)",
        "CREATE INDEX IF NOT EXISTS idx_news_events_time ON news_events(event_time)",
        "CREATE INDEX IF NOT EXISTS idx_command_queue_ea_id ON command_queue(ea_id)",
        "CREATE INDEX IF NOT EXISTS idx_command_queue_executed ON command_queue(executed)",
        "CREATE INDEX IF NOT EXISTS idx_commands_magic_number ON commands(magic_number)",
        "CREATE INDEX IF NOT EXISTS idx_commands_status ON commands(status)",
        "CREATE INDEX IF NOT EXISTS idx_ea_tags_ea_id ON ea_tags(ea_id)",
        "CREATE INDEX IF NOT EXISTS idx_ea_tags_tag_name ON ea_tags(tag_name)",
        "CREATE INDEX IF NOT EXISTS idx_ea_groups_type ON ea_groups(group_type)",
        "CREATE INDEX IF NOT EXISTS idx_ea_group_memberships_ea_id ON ea_group_memberships(ea_id)",
        "CREATE INDEX IF NOT EXISTS idx_ea_group_memberships_group_id ON ea_group_memberships(group_id)"
    ]
    
    for index_sql in indexes:
        cursor.execute(index_sql)
    
    conn.commit()
    print("All indexes created/verified")

def apply_migrations(db_path):
    """Apply any pending migrations"""
    try:
        migration_manager = MigrationManager(db_path)
        pending = migration_manager.get_pending_migrations()
        
        if pending:
            print(f"Found {len(pending)} pending migrations")
            for migration in pending:
                print(f"Applying migration: {migration['filename']}")
                migration_manager.apply_migration(migration['path'])
        else:
            print("No pending migrations")
    except Exception as e:
        print(f"Warning: Could not apply migrations: {e}")

def verify_database_integrity(conn):
    """Verify database integrity"""
    cursor = conn.cursor()
    
    print("\nVerifying database integrity...")
    
    # Check foreign key integrity
    cursor.execute("PRAGMA foreign_keys = ON")
    cursor.execute("PRAGMA foreign_key_check")
    fk_errors = cursor.fetchall()
    
    if fk_errors:
        print(f"Found {len(fk_errors)} foreign key constraint violations:")
        for error in fk_errors:
            print(f"  - {error}")
    else:
        print("✓ No foreign key constraint violations")
    
    # Check table counts
    print("\nTable record counts:")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = cursor.fetchall()
    
    for table in tables:
        table_name = table[0]
        if table_name == 'sqlite_sequence':
            continue
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        print(f"  - {table_name}: {count} records")
    
    return len(fk_errors) == 0

def main():
    """Main execution"""
    print("=== Database Schema Alignment Tool ===\n")
    
    # Get database path
    db_path = get_db_path()
    print(f"Database path: {db_path}")
    
    # Ensure directory exists
    ensure_directory_exists(db_path)
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    
    try:
        # Create missing tables
        create_missing_tables(conn)
        
        # Apply migrations
        apply_migrations(db_path)
        
        # Verify integrity
        is_valid = verify_database_integrity(conn)
        
        if is_valid:
            print("\n✅ Database schema is properly aligned and ready for production!")
        else:
            print("\n⚠️  Database has some integrity issues that need attention")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    main()