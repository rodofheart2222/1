"""
EA Sync Routes
API endpoints for EA synchronization and management
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ea", tags=["EA Sync"])

@router.post("/sync")
async def force_ea_sync():
    """Force synchronization with MT5 EAs"""
    try:
        from services.real_time_ea_updater import get_ea_updater
        
        ea_updater = get_ea_updater()
        
        if not ea_updater.mt5_connected:
            raise HTTPException(status_code=503, detail="MT5 not connected")
        
        # Force sync
        success = await ea_updater.force_sync_with_mt5()
        
        if success:
            status = ea_updater.get_status()
            return {
                "success": True,
                "message": "EA sync completed successfully",
                "tracked_eas": status['tracked_eas'],
                "status": status
            }
        else:
            raise HTTPException(status_code=500, detail="EA sync failed")
    
    except Exception as e:
        logger.error(f"Error in force EA sync: {e}")
        raise HTTPException(status_code=500, detail=f"EA sync error: {str(e)}")

@router.get("/sync/status")
async def get_ea_sync_status():
    """Get EA synchronization status"""
    try:
        from services.real_time_ea_updater import get_ea_updater
        
        ea_updater = get_ea_updater()
        status = ea_updater.get_status()
        
        # Also get current MT5 EAs if connected
        mt5_eas = {}
        if ea_updater.mt5_connected:
            try:
                mt5_eas = await ea_updater.get_mt5_ea_data()
            except Exception as e:
                logger.warning(f"Could not get current MT5 EAs: {e}")
        
        return {
            "updater_status": status,
            "current_mt5_eas": len(mt5_eas),
            "mt5_ea_list": list(mt5_eas.keys()) if mt5_eas else [],
            "last_ea_data": ea_updater.last_ea_data
        }
    
    except Exception as e:
        logger.error(f"Error getting EA sync status: {e}")
        raise HTTPException(status_code=500, detail=f"Status error: {str(e)}")

@router.get("/detection/test")
async def test_ea_detection():
    """Test EA detection methods"""
    try:
        import MetaTrader5 as mt5
        from datetime import datetime, timedelta
        
        if not mt5.initialize():
            raise HTTPException(status_code=503, detail=f"MT5 connection failed: {mt5.last_error()}")
        
        try:
            # Check positions
            positions = mt5.positions_get()
            position_eas = set()
            if positions:
                for pos in positions:
                    if pos.magic != 0:
                        position_eas.add(pos.magic)
            
            # Check orders
            orders = mt5.orders_get()
            order_eas = set()
            if orders:
                for order in orders:
                    if order.magic != 0:
                        order_eas.add(order.magic)
            
            # Check recent deals
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=1)
            deals = mt5.history_deals_get(start_time, end_time)
            deal_eas = set()
            if deals:
                for deal in deals:
                    if deal.magic != 0:
                        deal_eas.add(deal.magic)
            
            all_eas = position_eas | order_eas | deal_eas
            
            return {
                "total_eas_detected": len(all_eas),
                "ea_magic_numbers": sorted(list(all_eas)),
                "detection_methods": {
                    "from_positions": sorted(list(position_eas)),
                    "from_orders": sorted(list(order_eas)),
                    "from_recent_deals": sorted(list(deal_eas))
                },
                "mt5_info": {
                    "positions_count": len(positions) if positions else 0,
                    "orders_count": len(orders) if orders else 0,
                    "recent_deals_count": len(deals) if deals else 0
                }
            }
        
        finally:
            mt5.shutdown()
    
    except Exception as e:
        logger.error(f"Error testing EA detection: {e}")
        raise HTTPException(status_code=500, detail=f"Detection test error: {str(e)}")

@router.post("/database/clean")
async def clean_ea_database():
    """Clean database - remove EAs not found in MT5"""
    try:
        from services.real_time_ea_updater import get_ea_updater
        import sqlite3
        import os
        
        ea_updater = get_ea_updater()
        
        if not ea_updater.mt5_connected:
            raise HTTPException(status_code=503, detail="MT5 not connected")
        
        # Get current MT5 EAs
        mt5_eas = await ea_updater.get_mt5_ea_data()
        mt5_magics = set(mt5_eas.keys())
        
        # Get database EAs
        db_path = os.getenv("DATABASE_PATH", "data/mt5_dashboard.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT magic_number, id FROM eas")
        db_eas = {row[0]: row[1] for row in cursor.fetchall()}
        db_magics = set(db_eas.keys())
        
        # Find EAs to remove
        eas_to_remove = db_magics - mt5_magics
        
        removed_count = 0
        if eas_to_remove:
            for magic_number in eas_to_remove:
                ea_id = db_eas[magic_number]
                
                # Remove EA status records
                cursor.execute("DELETE FROM ea_status WHERE ea_id = ?", (ea_id,))
                
                # Remove EA record
                cursor.execute("DELETE FROM eas WHERE magic_number = ?", (magic_number,))
                
                removed_count += 1
            
            conn.commit()
        
        conn.close()
        
        return {
            "success": True,
            "removed_eas": sorted(list(eas_to_remove)),
            "removed_count": removed_count,
            "remaining_eas": sorted(list(mt5_magics)),
            "remaining_count": len(mt5_magics)
        }
    
    except Exception as e:
        logger.error(f"Error cleaning EA database: {e}")
        raise HTTPException(status_code=500, detail=f"Database clean error: {str(e)}")