#!/usr/bin/env python3
"""
Recreate the database with the correct schema including instance_uuid
"""

import os
import sqlite3
from pathlib import Path

def recreate_database():
    """Recreate database with proper schema"""
    
    # Database path
    db_path = os.getenv("DATABASE_PATH", "data/mt5_dashboard.db")
    
    print(f"Recreating database: {db_path}")
    
    # Ensure data directory exists
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    # Remove existing database file
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"✅ Removed existing database: {db_path}")
    
    try:
        # Connect to database (this will create a new file)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("Creating database tables...")
        
        # EAs table with instance_uuid support
        cursor.execute("""
            CREATE TABLE eas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                instance_uuid TEXT UNIQUE NOT NULL,
                magic_number INTEGER NOT NULL,
                ea_name TEXT NOT NULL,
                symbol TEXT NOT NULL,
                timeframe TEXT DEFAULT 'M1',
                status TEXT DEFAULT 'active',
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
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # EA Status table (real-time status updates)
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
                FOREIGN KEY (ea_id) REFERENCES eas(id) ON DELETE CASCADE
            )
        """)
        
        # Trades table
        cursor.execute("""
            CREATE TABLE trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trade_id TEXT UNIQUE NOT NULL,
                ea_id INTEGER,
                magic_number INTEGER NOT NULL,
                symbol TEXT NOT NULL,
                trade_type TEXT NOT NULL,
                volume REAL NOT NULL,
                requested_price REAL NOT NULL,
                actual_price REAL,
                sl REAL,
                tp REAL,
                status TEXT DEFAULT 'pending',
                profit REAL DEFAULT 0.0,
                commission REAL DEFAULT 0.0,
                swap REAL DEFAULT 0.0,
                comment TEXT,
                request_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                fill_time TIMESTAMP,
                close_time TIMESTAMP,
                dashboard_command_id TEXT,
                mt5_ticket INTEGER,
                risk_percent REAL DEFAULT 0.0,
                account_balance REAL DEFAULT 0.0,
                position_size_usd REAL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (ea_id) REFERENCES eas (id)
            )
        """)
        
        # Commands table
        cursor.execute("""
            CREATE TABLE commands (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                command_id TEXT UNIQUE NOT NULL,
                magic_number INTEGER NOT NULL,
                command_type TEXT NOT NULL,
                parameters TEXT,
                status TEXT DEFAULT 'pending',
                response TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                processed_at TIMESTAMP,
                FOREIGN KEY (magic_number) REFERENCES eas (magic_number)
            )
        """)
        
        # News Events table
        cursor.execute("""
            CREATE TABLE news_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_time TIMESTAMP NOT NULL,
                currency TEXT NOT NULL,
                impact_level TEXT NOT NULL CHECK (impact_level IN ('high', 'medium', 'low')),
                description TEXT NOT NULL,
                pre_minutes INTEGER DEFAULT 30,
                post_minutes INTEGER DEFAULT 30
            )
        """)
        
        # Backtests table
        cursor.execute("""
            CREATE TABLE backtests (
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
        """)
        
        # Create indexes for better performance
        indexes = [
            "CREATE INDEX idx_eas_instance_uuid ON eas (instance_uuid)",
            "CREATE INDEX idx_eas_magic_number ON eas (magic_number)",
            "CREATE INDEX idx_eas_symbol ON eas (symbol)",
            "CREATE INDEX idx_eas_status ON eas (status)",
            "CREATE INDEX idx_ea_status_ea_id ON ea_status (ea_id)",
            "CREATE INDEX idx_ea_status_timestamp ON ea_status (timestamp)",
            "CREATE INDEX idx_trades_ea_id ON trades (ea_id)",
            "CREATE INDEX idx_trades_magic_number ON trades (magic_number)",
            "CREATE INDEX idx_trades_status ON trades (status)",
            "CREATE INDEX idx_trades_symbol ON trades (symbol)",
            "CREATE INDEX idx_commands_magic_number ON commands (magic_number)",
            "CREATE INDEX idx_commands_status ON commands (status)",
            "CREATE INDEX idx_news_events_time ON news_events (event_time)"
        ]
        
        for index_sql in indexes:
            cursor.execute(index_sql)
        
        # Commit changes
        conn.commit()
        conn.close()
        
        print("✅ Database recreated successfully!")
        
        # Verify the schema
        verify_database_schema()
        
        return True
        
    except Exception as e:
        print(f"❌ Database recreation failed: {e}")
        return False

def verify_database_schema():
    """Verify the database schema is correct"""
    try:
        db_path = os.getenv("DATABASE_PATH", "data/mt5_dashboard.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check eas table schema
        cursor.execute("PRAGMA table_info(eas)")
        columns = [col[1] for col in cursor.fetchall()]
        
        required_columns = ['instance_uuid', 'magic_number', 'ea_name', 'symbol']
        missing_columns = [col for col in required_columns if col not in columns]
        
        if missing_columns:
            print(f"❌ Missing columns in eas table: {missing_columns}")
        else:
            print("✅ EAs table schema is correct")
            print(f"   Columns: {columns}")
        
        # Check table count
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"✅ Created tables: {tables}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Schema verification failed: {e}")

if __name__ == "__main__":
    recreate_database()


