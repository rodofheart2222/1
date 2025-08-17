#!/usr/bin/env python3
"""
Recreate Database with Proper Schema
"""

import sqlite3
import os
import shutil
from datetime import datetime

def backup_existing_db(db_path):
    """Backup existing database if it exists"""
    if os.path.exists(db_path):
        backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy2(db_path, backup_path)
        print(f"Backed up existing database to: {backup_path}")
        return backup_path
    return None

def recreate_database(db_path):
    """Recreate database with proper schema"""
    # Ensure directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    # Remove old database
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"Removed old database: {db_path}")
    
    # Create new database connection
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON")
    
    print("Creating tables...")
    
    # Create all tables with proper structure
    sql_statements = [
        # Core EA table
        """CREATE TABLE eas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            magic_number INTEGER UNIQUE NOT NULL,
            symbol TEXT NOT NULL,
            strategy_tag TEXT,
            risk_config REAL DEFAULT 1.0,
            status TEXT DEFAULT 'active' CHECK (status IN ('active', 'paused', 'error')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
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
        )""",
        
        # EA Status
        """CREATE TABLE ea_status (
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
        )""",
        
        # Performance History
        """CREATE TABLE performance_history (
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
        )""",
        
        # Trades
        """CREATE TABLE trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ea_id INTEGER,
            symbol TEXT NOT NULL,
            order_type TEXT,
            volume REAL NOT NULL,
            open_price REAL NOT NULL,
            close_price REAL,
            profit REAL DEFAULT 0.0,
            open_time TIMESTAMP NOT NULL,
            close_time TIMESTAMP,
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
        )""",
        
        # Backtest Benchmarks
        """CREATE TABLE backtest_benchmarks (
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
        )""",
        
        # News Events
        """CREATE TABLE news_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_time TIMESTAMP NOT NULL,
            currency TEXT NOT NULL,
            impact_level TEXT NOT NULL CHECK (impact_level IN ('high', 'medium', 'low')),
            description TEXT NOT NULL,
            pre_minutes INTEGER DEFAULT 30,
            post_minutes INTEGER DEFAULT 30
        )""",
        
        # Command Queue
        """CREATE TABLE command_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ea_id INTEGER,
            command_type TEXT NOT NULL,
            command_data TEXT,
            scheduled_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            executed BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (ea_id) REFERENCES eas(id) ON DELETE CASCADE
        )""",
        
        # Commands (from init_db.py)
        """CREATE TABLE commands (
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
        
        # News (from init_db.py)
        """CREATE TABLE news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT,
            impact TEXT,
            currency TEXT,
            event_time TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""",
        
        # Backtests (from init_db.py)
        """CREATE TABLE backtests (
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
        )""",
        
        # EA Tags
        """CREATE TABLE ea_tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ea_id INTEGER NOT NULL,
            tag_name TEXT NOT NULL,
            tag_value TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (ea_id) REFERENCES eas(id) ON DELETE CASCADE,
            UNIQUE(ea_id, tag_name)
        )""",
        
        # EA Groups
        """CREATE TABLE ea_groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_name TEXT UNIQUE NOT NULL,
            group_type TEXT NOT NULL CHECK (group_type IN ('symbol', 'strategy', 'risk_level', 'custom')),
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""",
        
        # EA Group Memberships
        """CREATE TABLE ea_group_memberships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ea_id INTEGER NOT NULL,
            group_id INTEGER NOT NULL,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (ea_id) REFERENCES eas(id) ON DELETE CASCADE,
            FOREIGN KEY (group_id) REFERENCES ea_groups(id) ON DELETE CASCADE,
            UNIQUE(ea_id, group_id)
        )""",
        
        # Schema Migrations
        """CREATE TABLE schema_migrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            version TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            checksum TEXT
        )"""
    ]
    
    # Execute each statement
    for i, sql in enumerate(sql_statements):
        try:
            cursor.execute(sql)
            table_name = sql.split()[2]  # Extract table name
            print(f"  ✓ Created table: {table_name}")
        except Exception as e:
            print(f"  ❌ Error creating table: {e}")
    
    # Create indexes
    print("\nCreating indexes...")
    indexes = [
        "CREATE INDEX idx_eas_magic_number ON eas(magic_number)",
        "CREATE INDEX idx_eas_symbol ON eas(symbol)",
        "CREATE INDEX idx_eas_strategy_tag ON eas(strategy_tag)",
        "CREATE INDEX idx_eas_status ON eas(status)",
        "CREATE INDEX idx_ea_status_ea_id ON ea_status(ea_id)",
        "CREATE INDEX idx_ea_status_timestamp ON ea_status(timestamp)",
        "CREATE INDEX idx_performance_history_ea_id ON performance_history(ea_id)",
        "CREATE INDEX idx_performance_history_date ON performance_history(date)",
        "CREATE INDEX idx_trades_ea_id ON trades(ea_id)",
        "CREATE INDEX idx_trades_symbol ON trades(symbol)",
        "CREATE INDEX idx_trades_open_time ON trades(open_time)",
        "CREATE INDEX idx_trades_magic_number ON trades(magic_number)",
        "CREATE INDEX idx_trades_status ON trades(status)",
        "CREATE INDEX idx_news_events_time ON news_events(event_time)",
        "CREATE INDEX idx_command_queue_ea_id ON command_queue(ea_id)",
        "CREATE INDEX idx_command_queue_executed ON command_queue(executed)",
        "CREATE INDEX idx_commands_magic_number ON commands(magic_number)",
        "CREATE INDEX idx_commands_status ON commands(status)",
        "CREATE INDEX idx_ea_tags_ea_id ON ea_tags(ea_id)",
        "CREATE INDEX idx_ea_tags_tag_name ON ea_tags(tag_name)",
        "CREATE INDEX idx_ea_groups_type ON ea_groups(group_type)",
        "CREATE INDEX idx_ea_group_memberships_ea_id ON ea_group_memberships(ea_id)",
        "CREATE INDEX idx_ea_group_memberships_group_id ON ea_group_memberships(group_id)"
    ]
    
    for index_sql in indexes:
        try:
            cursor.execute(index_sql)
            index_name = index_sql.split()[2]  # Extract index name
            print(f"  ✓ Created index: {index_name}")
        except Exception as e:
            print(f"  ❌ Error creating index: {e}")
    
    # Commit changes
    conn.commit()
    
    # Verify tables
    print("\nVerifying database...")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = cursor.fetchall()
    
    print(f"\nCreated {len(tables)} tables:")
    for table in tables:
        table_name = table[0]
        if table_name == 'sqlite_sequence':
            continue
        print(f"  ✓ {table_name}")
    
    conn.close()
    print(f"\n✅ Database recreated successfully at: {db_path}")

def main():
    """Main execution"""
    print("=== Database Recreation Tool ===\n")
    
    db_path = os.getenv("DATABASE_PATH", "data/mt5_dashboard.db")
    
    # Backup existing database
    backup_path = backup_existing_db(db_path)
    
    # Recreate database
    recreate_database(db_path)
    
    if backup_path:
        print(f"\nNote: Your old database is backed up at: {backup_path}")

if __name__ == "__main__":
    main()