#!/usr/bin/env python3
"""
Populate EA Database from MT5
Get list of EAs from MT5 and populate the database
"""

import os
import sys
import sqlite3
import logging
from datetime import datetime
from pathlib import Path

# Add backend to path
sys.path.append('backend')

from services.mt5_communication import MT5CommunicationInterface
from database.connection import get_database_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def populate_ea_database():
    """Populate database with EAs from MT5"""
    try:
        logger.info("Starting EA database population...")
        
        # Initialize MT5 interface
        mt5_interface = MT5CommunicationInterface()
        
        # Get EA data from MT5
        logger.info("Collecting EA data from MT5...")
        ea_reports = mt5_interface.collect_ea_data()
        
        if not ea_reports:
            logger.warning("No EA data found from MT5. Creating sample data...")
            return create_sample_ea_data()
        
        logger.info(f"Found {len(ea_reports)} EAs from MT5")
        
        # Get database connection
        db_path = os.getenv("DATABASE_PATH", "data/mt5_dashboard.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Process each EA
        for magic_number, report in ea_reports.items():
            try:
                # Insert or update EA in database
                cursor.execute("""
                    INSERT OR REPLACE INTO eas (
                        magic_number, ea_name, symbol, timeframe, status,
                        last_heartbeat, strategy_tag, last_seen, risk_config
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    magic_number,
                    f"EA_{magic_number}",  # Default EA name
                    report.symbol,
                    "M1",  # Default timeframe
                    "active",
                    report.last_update,
                    getattr(report, 'strategy_tag', f'Strategy_{magic_number}'),
                    report.last_update,
                    1.0  # Default risk config
                ))
                
                # Get the EA ID
                cursor.execute("SELECT id FROM eas WHERE magic_number = ?", (magic_number,))
                ea_row = cursor.fetchone()
                if ea_row:
                    ea_id = ea_row[0]
                    
                    # Insert EA status
                    cursor.execute("""
                        INSERT OR REPLACE INTO ea_status (
                            ea_id, timestamp, current_profit, open_positions,
                            sl_value, tp_value, trailing_active, module_status
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        ea_id,
                        report.last_update,
                        report.current_profit,
                        report.open_positions,
                        getattr(report, 'sl_value', 0.0),
                        getattr(report, 'tp_value', 0.0),
                        getattr(report, 'trailing_active', False),
                        "{}"  # Empty JSON for module status
                    ))
                
                logger.info(f"Updated EA {magic_number} ({report.symbol})")
                
            except Exception as e:
                logger.error(f"Error processing EA {magic_number}: {e}")
                continue
        
        # Commit changes
        conn.commit()
        conn.close()
        
        logger.info(f"Successfully populated database with {len(ea_reports)} EAs")
        return True
        
    except Exception as e:
        logger.error(f"Error populating EA database: {e}")
        return False

def create_sample_ea_data():
    """Create sample EA data if no MT5 data is available"""
    try:
        logger.info("Creating sample EA data...")
        
        # Sample EA data
        sample_eas = [
            {
                'magic_number': 12345,
                'ea_name': 'Compression_EA_v1',
                'symbol': 'EURUSD',
                'strategy_tag': 'Compression_v1',
                'current_profit': 150.75,
                'open_positions': 2
            },
            {
                'magic_number': 67890,
                'ea_name': 'Scalper_EA_v2',
                'symbol': 'GBPUSD',
                'strategy_tag': 'Scalper_v2',
                'current_profit': -25.30,
                'open_positions': 1
            },
            {
                'magic_number': 11111,
                'ea_name': 'Trend_EA_v1',
                'symbol': 'USDJPY',
                'strategy_tag': 'Trend_v1',
                'current_profit': 89.45,
                'open_positions': 0
            }
        ]
        
        # Get database connection
        db_path = os.getenv("DATABASE_PATH", "data/mt5_dashboard.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        current_time = datetime.now()
        
        for ea_data in sample_eas:
            try:
                # Insert EA
                cursor.execute("""
                    INSERT OR REPLACE INTO eas (
                        magic_number, ea_name, symbol, timeframe, status,
                        last_heartbeat, strategy_tag, last_seen, risk_config
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    ea_data['magic_number'],
                    ea_data['ea_name'],
                    ea_data['symbol'],
                    "M1",
                    "active",
                    current_time,
                    ea_data['strategy_tag'],
                    current_time,
                    1.0
                ))
                
                # Get EA ID
                cursor.execute("SELECT id FROM eas WHERE magic_number = ?", (ea_data['magic_number'],))
                ea_row = cursor.fetchone()
                if ea_row:
                    ea_id = ea_row[0]
                    
                    # Insert EA status
                    cursor.execute("""
                        INSERT OR REPLACE INTO ea_status (
                            ea_id, timestamp, current_profit, open_positions,
                            sl_value, tp_value, trailing_active, module_status
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        ea_id,
                        current_time,
                        ea_data['current_profit'],
                        ea_data['open_positions'],
                        0.0,
                        0.0,
                        False,
                        "{}"
                    ))
                
                logger.info(f"Created sample EA {ea_data['magic_number']} ({ea_data['symbol']})")
                
            except Exception as e:
                logger.error(f"Error creating sample EA {ea_data['magic_number']}: {e}")
                continue
        
        # Commit changes
        conn.commit()
        conn.close()
        
        logger.info(f"Successfully created {len(sample_eas)} sample EAs")
        return True
        
    except Exception as e:
        logger.error(f"Error creating sample EA data: {e}")
        return False

def verify_ea_data():
    """Verify EA data in database"""
    try:
        db_path = os.getenv("DATABASE_PATH", "data/mt5_dashboard.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Count EAs
        cursor.execute("SELECT COUNT(*) FROM eas")
        ea_count = cursor.fetchone()[0]
        
        # Count EA status records
        cursor.execute("SELECT COUNT(*) FROM ea_status")
        status_count = cursor.fetchone()[0]
        
        # Get sample data
        cursor.execute("""
            SELECT e.magic_number, e.symbol, e.strategy_tag, e.status,
                   s.current_profit, s.open_positions
            FROM eas e
            LEFT JOIN ea_status s ON s.ea_id = e.id
            ORDER BY e.magic_number
            LIMIT 5
        """)
        
        sample_data = cursor.fetchall()
        
        conn.close()
        
        logger.info(f"Database verification:")
        logger.info(f"  Total EAs: {ea_count}")
        logger.info(f"  Total status records: {status_count}")
        logger.info(f"  Sample EAs:")
        
        for row in sample_data:
            magic, symbol, strategy, status, profit, positions = row
            logger.info(f"    EA {magic}: {symbol} ({strategy}) - Profit: {profit}, Positions: {positions}")
        
        return ea_count > 0
        
    except Exception as e:
        logger.error(f"Error verifying EA data: {e}")
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Populate EA Database")
    parser.add_argument("--populate", action="store_true", help="Populate database with EA data")
    parser.add_argument("--verify", action="store_true", help="Verify EA data in database")
    parser.add_argument("--sample", action="store_true", help="Create sample EA data only")
    
    args = parser.parse_args()
    
    if args.populate:
        success = populate_ea_database()
        print(f"EA database population: {'SUCCESS' if success else 'FAILED'}")
    elif args.sample:
        success = create_sample_ea_data()
        print(f"Sample EA data creation: {'SUCCESS' if success else 'FAILED'}")
    elif args.verify:
        valid = verify_ea_data()
        print(f"EA data verification: {'PASSED' if valid else 'FAILED'}")
    else:
        print("Use --populate to populate from MT5, --sample for sample data, or --verify to check data")