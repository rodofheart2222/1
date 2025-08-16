#!/usr/bin/env python3
"""
Sync EAs with MT5
Force sync the database EA list with current MT5 EAs
"""

import sys
import asyncio
import logging
from pathlib import Path

# Add backend to path
sys.path.append('backend')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def sync_eas_with_mt5():
    """Sync EAs with MT5"""
    try:
        from services.real_time_ea_updater import get_ea_updater
        
        logger.info("Initializing EA updater...")
        ea_updater = get_ea_updater()
        
        # Initialize connection
        success = await ea_updater.initialize()
        if not success:
            logger.error("Failed to initialize EA updater")
            return False
        
        logger.info("Forcing sync with MT5...")
        
        # Force sync
        sync_success = await ea_updater.force_sync_with_mt5()
        
        if sync_success:
            logger.info("✅ Sync completed successfully")
            
            # Show current status
            status = ea_updater.get_status()
            logger.info(f"Current status: {status['tracked_eas']} EAs tracked")
            
        else:
            logger.error("❌ Sync failed")
        
        # Cleanup
        await ea_updater.stop_updates()
        
        return sync_success
        
    except Exception as e:
        logger.error(f"Error syncing EAs: {e}")
        return False

async def check_current_eas():
    """Check current EAs in MT5 and database"""
    try:
        import sqlite3
        import os
        
        # Check MT5 EAs
        try:
            import MetaTrader5 as mt5
            
            if not mt5.initialize():
                logger.error("Failed to connect to MT5")
                return
            
            positions = mt5.positions_get()
            orders = mt5.orders_get()
            
            if positions is None:
                positions = []
            if orders is None:
                orders = []
            
            mt5_magics = set()
            for pos in positions:
                if pos.magic != 0:
                    mt5_magics.add(pos.magic)
            for order in orders:
                if order.magic != 0:
                    mt5_magics.add(order.magic)
            
            logger.info(f"MT5 EAs found: {sorted(list(mt5_magics))}")
            
            mt5.shutdown()
            
        except Exception as e:
            logger.error(f"Error checking MT5: {e}")
            return
        
        # Check database EAs
        try:
            db_path = os.getenv("DATABASE_PATH", "data/mt5_dashboard.db")
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT magic_number FROM eas ORDER BY magic_number")
            db_magics = [row[0] for row in cursor.fetchall()]
            
            logger.info(f"Database EAs found: {db_magics}")
            
            conn.close()
            
        except Exception as e:
            logger.error(f"Error checking database: {e}")
            return
        
        # Compare
        mt5_set = set(mt5_magics)
        db_set = set(db_magics)
        
        if mt5_set == db_set:
            logger.info("✅ MT5 and database are in sync")
        else:
            logger.warning("⚠️ MT5 and database are NOT in sync")
            logger.info(f"Only in MT5: {mt5_set - db_set}")
            logger.info(f"Only in database: {db_set - mt5_set}")
        
    except Exception as e:
        logger.error(f"Error checking EAs: {e}")

async def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Sync EAs with MT5")
    parser.add_argument("--sync", action="store_true", help="Force sync with MT5")
    parser.add_argument("--check", action="store_true", help="Check current EAs")
    
    args = parser.parse_args()
    
    if args.sync:
        logger.info("🔄 Starting EA sync with MT5...")
        success = await sync_eas_with_mt5()
        print(f"EA sync: {'SUCCESS' if success else 'FAILED'}")
    elif args.check:
        logger.info("🔍 Checking current EAs...")
        await check_current_eas()
    else:
        print("Use --sync to force sync with MT5 or --check to compare current EAs")

if __name__ == "__main__":
    asyncio.run(main())