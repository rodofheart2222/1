"""
Database Initialization

Initialize database tables and verify integrity
"""

import os
import logging
import sqlite3
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)


def init_database():
    """Initialize database with required tables"""
    try:
        # Ensure data directory exists
        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)
        
        # Database path
        db_path = os.getenv("DATABASE_PATH", "data/mt5_dashboard.db")
        
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create base tables
        create_tables(cursor)
        
        # Ensure compatibility with current code expectations
        _ensure_schema_compatibility(cursor)
        
        # Commit changes
        conn.commit()
        conn.close()
        
        logger.info(f"Database initialized successfully: {db_path}")
        return True
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return False


def create_tables(cursor):
    """Create all required database tables"""
    
    # EAs table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS eas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            magic_number INTEGER UNIQUE NOT NULL,
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
    
    # Trades table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trades (
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
        CREATE TABLE IF NOT EXISTS commands (
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
    
    # News table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT,
            impact TEXT,
            currency TEXT,
            event_time TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Backtests table
    cursor.execute("""
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
    """)
    
    # Create indexes for better performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_trades_magic_number ON trades (magic_number)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_trades_status ON trades (status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades (symbol)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_eas_magic_number ON eas (magic_number)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_eas_status ON eas (status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_commands_magic_number ON commands (magic_number)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_commands_status ON commands (status)")
    
    logger.info("Database tables created successfully")


def verify_database_integrity() -> bool:
    """Verify database integrity and structure"""
    try:
        db_path = os.getenv("DATABASE_PATH", "data/mt5_dashboard.db")
        
        if not os.path.exists(db_path):
            logger.warning("Database file does not exist")
            return False
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if required tables exist
        required_tables = ['eas', 'trades', 'commands', 'news', 'backtests']
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = [row[0] for row in cursor.fetchall()]
        
        missing_tables = [table for table in required_tables if table not in existing_tables]
        
        if missing_tables:
            logger.warning(f"Missing database tables: {missing_tables}")
            conn.close()
            return False
        
        # Test basic operations
        cursor.execute("SELECT COUNT(*) FROM eas")
        ea_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM trades")
        trade_count = cursor.fetchone()[0]
        
        conn.close()
        
        logger.info(f"Database integrity verified - EAs: {ea_count}, Trades: {trade_count}")
        return True
        
    except Exception as e:
        logger.error(f"Database integrity check failed: {e}")
        return False


def get_database_stats() -> Dict[str, Any]:
    """Get database statistics"""
    try:
        db_path = os.getenv("DATABASE_PATH", "data/mt5_dashboard.db")
        
        if not os.path.exists(db_path):
            return {"error": "Database file does not exist"}
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        stats = {}
        
        # Count records in each table
        tables = ['eas', 'trades', 'commands', 'news', 'backtests']
        
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                stats[f"{table}_count"] = cursor.fetchone()[0]
            except Exception as e:
                stats[f"{table}_count"] = f"Error: {e}"
        
        # Get database file size
        stats["database_size_mb"] = round(os.path.getsize(db_path) / (1024 * 1024), 2)
        
        # Get active EAs
        try:
            cursor.execute("SELECT COUNT(*) FROM eas WHERE status = 'active'")
            stats["active_eas"] = cursor.fetchone()[0]
        except:
            stats["active_eas"] = 0
        
        # Get active trades
        try:
            cursor.execute("SELECT COUNT(*) FROM trades WHERE status IN ('pending', 'filled')")
            stats["active_trades"] = cursor.fetchone()[0]
        except:
            stats["active_trades"] = 0
        
        conn.close()
        
        return stats
        
    except Exception as e:
        return {"error": str(e)}


def reset_database():
    """Reset database (drop and recreate all tables)"""
    try:
        db_path = os.getenv("DATABASE_PATH", "data/mt5_dashboard.db")
        
        # Remove existing database file
        if os.path.exists(db_path):
            os.remove(db_path)
            logger.info("Existing database file removed")
        
        # Reinitialize database
        success = init_database()
        
        if success:
            logger.info("Database reset successfully")
        else:
            logger.error("Database reset failed")
        
        return success
        
    except Exception as e:
        logger.error(f"Database reset error: {e}")
        return False


def _column_exists(cursor, table_name: str, column_name: str) -> bool:
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]
    return column_name in columns


def _ensure_schema_compatibility(cursor):
    """Ensure tables/columns used by the app exist (idempotent)."""
    # EAs: ensure strategy_tag and risk_config columns exist
    try:
        if not _column_exists(cursor, 'eas', 'strategy_tag'):
            cursor.execute("ALTER TABLE eas ADD COLUMN strategy_tag TEXT DEFAULT 'Default'")
        if not _column_exists(cursor, 'eas', 'risk_config'):
            cursor.execute("ALTER TABLE eas ADD COLUMN risk_config REAL DEFAULT 1.0")
        # Helpful index
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_eas_strategy_tag ON eas(strategy_tag)")
    except Exception as e:
        logger.warning(f"Schema adjust for 'eas' failed or unnecessary: {e}")
    
    # News events table required by models
    try:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS news_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_time TIMESTAMP NOT NULL,
                currency TEXT NOT NULL,
                impact_level TEXT NOT NULL CHECK (impact_level IN ('high', 'medium', 'low')),
                description TEXT NOT NULL,
                pre_minutes INTEGER DEFAULT 30,
                post_minutes INTEGER DEFAULT 30
            )
            """
        )
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_news_events_time ON news_events(event_time)")
    except Exception as e:
        logger.warning(f"Schema adjust for 'news_events' failed or unnecessary: {e}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Database Management")
    parser.add_argument("--init", action="store_true", help="Initialize database")
    parser.add_argument("--verify", action="store_true", help="Verify database integrity")
    parser.add_argument("--stats", action="store_true", help="Show database statistics")
    parser.add_argument("--reset", action="store_true", help="Reset database (WARNING: destroys all data)")
    
    args = parser.parse_args()
    
    if args.init:
        success = init_database()
        print(f"Database initialization: {'SUCCESS' if success else 'FAILED'}")
    
    elif args.verify:
        valid = verify_database_integrity()
        print(f"Database integrity: {'VALID' if valid else 'INVALID'}")
    
    elif args.stats:
        stats = get_database_stats()
        print("Database Statistics:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
    
    elif args.reset:
        confirm = input("Are you sure you want to reset the database? This will destroy all data. (yes/no): ")
        if confirm.lower() == 'yes':
            success = reset_database()
            print(f"Database reset: {'SUCCESS' if success else 'FAILED'}")
        else:
            print("Database reset cancelled")
    
    else:
        print("No action specified. Use --help for options.")