"""
MT5 Trade Tracking API Routes

API endpoints for MetaTrader5 trade tracking, positions, orders, and deals monitoring
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

from backend.services.mt5_trade_tracker import get_mt5_trade_tracker

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/mt5", tags=["MT5 Trade Tracking"])


# Pydantic models for request/response
class EATrackingRequest(BaseModel):
    """Request to add/remove EA tracking"""
    magic_number: int
    action: str  # "add" or "remove"


class MT5StatusResponse(BaseModel):
    """MT5 connection and tracking status"""
    mt5_connected: bool
    running: bool
    tracked_eas: List[int]
    positions_count: int
    orders_count: int
    deals_count: int
    last_update: str


@router.get("/status")
async def get_mt5_status():
    """Get MT5 connection and tracking status"""
    try:
        tracker = get_mt5_trade_tracker()
        status = tracker.get_tracking_status()
        
        return {
            "success": True,
            "status": status,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting MT5 status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get MT5 status: {str(e)}")


@router.post("/initialize")
async def initialize_mt5_tracker(background_tasks: BackgroundTasks):
    """Initialize MT5 connection and start tracking"""
    try:
        tracker = get_mt5_trade_tracker()
        
        # Initialize connection
        success = await tracker.initialize()
        
        if success:
            # Start tracking in background
            background_tasks.add_task(tracker.start_tracking)
            
            return {
                "success": True,
                "message": "MT5 tracker initialized and started successfully",
                "mt5_connected": tracker.mt5_connected,
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to initialize MT5 tracker")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error initializing MT5 tracker: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to initialize MT5 tracker: {str(e)}")


@router.post("/shutdown")
async def shutdown_mt5_tracker():
    """Shutdown MT5 connection and stop tracking"""
    try:
        tracker = get_mt5_trade_tracker()
        await tracker.shutdown()
        
        return {
            "success": True,
            "message": "MT5 tracker shutdown successfully",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error shutting down MT5 tracker: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to shutdown MT5 tracker: {str(e)}")


@router.post("/tracking")
async def manage_ea_tracking(request: EATrackingRequest):
    """Add or remove EA from tracking list"""
    try:
        tracker = get_mt5_trade_tracker()
        
        if request.action.lower() == "add":
            tracker.add_ea_tracking(request.magic_number)
            message = f"EA {request.magic_number} added to tracking"
        elif request.action.lower() == "remove":
            tracker.remove_ea_tracking(request.magic_number)
            message = f"EA {request.magic_number} removed from tracking"
        else:
            raise HTTPException(status_code=400, detail="Action must be 'add' or 'remove'")
        
        return {
            "success": True,
            "message": message,
            "magic_number": request.magic_number,
            "action": request.action,
            "tracked_eas": list(tracker.tracked_eas),
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error managing EA tracking: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to manage EA tracking: {str(e)}")


@router.get("/positions")
async def get_mt5_positions(magic_number: Optional[int] = None):
    """Get current MT5 positions"""
    try:
        tracker = get_mt5_trade_tracker()
        positions = tracker.get_positions(magic_number)
        
        return {
            "success": True,
            "positions": positions,
            "count": len(positions),
            "magic_number": magic_number,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting MT5 positions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get MT5 positions: {str(e)}")


@router.get("/orders")
async def get_mt5_orders(magic_number: Optional[int] = None):
    """Get current MT5 orders"""
    try:
        tracker = get_mt5_trade_tracker()
        orders = tracker.get_orders(magic_number)
        
        return {
            "success": True,
            "orders": orders,
            "count": len(orders),
            "magic_number": magic_number,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting MT5 orders: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get MT5 orders: {str(e)}")


@router.get("/deals")
async def get_mt5_deals(magic_number: Optional[int] = None, limit: int = 50):
    """Get recent MT5 deals"""
    try:
        tracker = get_mt5_trade_tracker()
        deals = tracker.get_recent_deals(magic_number, limit)
        
        return {
            "success": True,
            "deals": deals,
            "count": len(deals),
            "magic_number": magic_number,
            "limit": limit,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting MT5 deals: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get MT5 deals: {str(e)}")


@router.get("/account")
async def get_mt5_account_info():
    """Get MT5 account information"""
    try:
        tracker = get_mt5_trade_tracker()
        account_info = tracker.get_account_info()
        
        if account_info is None:
            raise HTTPException(status_code=404, detail="Account information not available")
        
        return {
            "success": True,
            "account": account_info,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting MT5 account info: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get MT5 account info: {str(e)}")


@router.get("/positions/{magic_number}")
async def get_ea_positions(magic_number: int):
    """Get positions for specific EA"""
    try:
        tracker = get_mt5_trade_tracker()
        positions = tracker.get_positions(magic_number)
        
        return {
            "success": True,
            "magic_number": magic_number,
            "positions": positions,
            "count": len(positions),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting EA positions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get EA positions: {str(e)}")


@router.get("/orders/{magic_number}")
async def get_ea_orders(magic_number: int):
    """Get orders for specific EA"""
    try:
        tracker = get_mt5_trade_tracker()
        orders = tracker.get_orders(magic_number)
        
        return {
            "success": True,
            "magic_number": magic_number,
            "orders": orders,
            "count": len(orders),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting EA orders: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get EA orders: {str(e)}")


@router.get("/deals/{magic_number}")
async def get_ea_deals(magic_number: int, limit: int = 50):
    """Get deals for specific EA"""
    try:
        tracker = get_mt5_trade_tracker()
        deals = tracker.get_recent_deals(magic_number, limit)
        
        return {
            "success": True,
            "magic_number": magic_number,
            "deals": deals,
            "count": len(deals),
            "limit": limit,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting EA deals: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get EA deals: {str(e)}")


@router.get("/summary/{magic_number}")
async def get_ea_trading_summary(magic_number: int):
    """Get comprehensive trading summary for specific EA"""
    try:
        tracker = get_mt5_trade_tracker()
        
        # Get all data for the EA
        positions = tracker.get_positions(magic_number)
        orders = tracker.get_orders(magic_number)
        deals = tracker.get_recent_deals(magic_number, 100)
        
        # Calculate summary statistics
        total_volume = sum(pos['volume'] for pos in positions)
        total_profit = sum(pos['profit'] for pos in positions)
        total_swap = sum(pos['swap'] for pos in positions)
        
        # Count deal types
        buy_deals = len([d for d in deals if d['type_name'] == 'BUY'])
        sell_deals = len([d for d in deals if d['type_name'] == 'SELL'])
        
        # Calculate profit from closed deals
        closed_profit = sum(d['profit'] for d in deals if d['entry_name'] == 'ENTRY_OUT')
        
        summary = {
            "magic_number": magic_number,
            "positions": {
                "count": len(positions),
                "total_volume": round(total_volume, 2),
                "total_profit": round(total_profit, 2),
                "total_swap": round(total_swap, 2),
                "positions": positions
            },
            "orders": {
                "count": len(orders),
                "orders": orders
            },
            "deals": {
                "total_count": len(deals),
                "buy_count": buy_deals,
                "sell_count": sell_deals,
                "closed_profit": round(closed_profit, 2),
                "recent_deals": deals[:20]  # Show only recent 20 deals
            },
            "performance": {
                "unrealized_profit": round(total_profit, 2),
                "realized_profit": round(closed_profit, 2),
                "total_profit": round(total_profit + closed_profit, 2),
                "total_swap": round(total_swap, 2)
            }
        }
        
        return {
            "success": True,
            "summary": summary,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting EA trading summary: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get EA trading summary: {str(e)}")


@router.get("/dashboard")
async def get_mt5_dashboard():
    """Get comprehensive MT5 dashboard data"""
    try:
        tracker = get_mt5_trade_tracker()
        
        # Get tracking status
        status = tracker.get_tracking_status()
        
        # Get account info
        account_info = tracker.get_account_info()
        
        # Get all positions and orders
        all_positions = tracker.get_positions()
        all_orders = tracker.get_orders()
        all_deals = tracker.get_recent_deals(limit=50)
        
        # Group by EA
        ea_data = {}
        for magic_number in status['tracked_eas']:
            ea_positions = [p for p in all_positions if p['magic'] == magic_number]
            ea_orders = [o for o in all_orders if o['magic'] == magic_number]
            ea_deals = [d for d in all_deals if d['magic'] == magic_number]
            
            ea_data[magic_number] = {
                "positions": ea_positions,
                "orders": ea_orders,
                "recent_deals": ea_deals[:10],
                "summary": {
                    "positions_count": len(ea_positions),
                    "orders_count": len(ea_orders),
                    "total_profit": sum(p['profit'] for p in ea_positions),
                    "total_volume": sum(p['volume'] for p in ea_positions)
                }
            }
        
        # Overall statistics
        overall_stats = {
            "total_positions": len(all_positions),
            "total_orders": len(all_orders),
            "total_deals": len(all_deals),
            "total_profit": sum(p['profit'] for p in all_positions),
            "total_volume": sum(p['volume'] for p in all_positions),
            "tracked_eas_count": len(status['tracked_eas'])
        }
        
        return {
            "success": True,
            "status": status,
            "account": account_info,
            "overall_stats": overall_stats,
            "ea_data": ea_data,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting MT5 dashboard: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get MT5 dashboard: {str(e)}")


@router.post("/start-tracking")
async def start_mt5_tracking(background_tasks: BackgroundTasks):
    """Start MT5 tracking (if not already running)"""
    try:
        tracker = get_mt5_trade_tracker()
        
        if not tracker.running:
            background_tasks.add_task(tracker.start_tracking)
            message = "MT5 tracking started"
        else:
            message = "MT5 tracking already running"
        
        return {
            "success": True,
            "message": message,
            "running": tracker.running,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error starting MT5 tracking: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start MT5 tracking: {str(e)}")


@router.post("/stop-tracking")
async def stop_mt5_tracking():
    """Stop MT5 tracking"""
    try:
        tracker = get_mt5_trade_tracker()
        tracker.running = False
        
        return {
            "success": True,
            "message": "MT5 tracking stopped",
            "running": tracker.running,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error stopping MT5 tracking: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to stop MT5 tracking: {str(e)}")


@router.get("/health")
async def mt5_health_check():
    """Health check for MT5 tracking system"""
    try:
        tracker = get_mt5_trade_tracker()
        status = tracker.get_tracking_status()
        
        # Determine health status
        health_status = "healthy"
        issues = []
        
        if not status['mt5_connected']:
            health_status = "unhealthy"
            issues.append("MT5 not connected")
        
        if not status['running']:
            health_status = "warning"
            issues.append("Tracking not running")
        
        if len(status['tracked_eas']) == 0:
            health_status = "warning"
            issues.append("No EAs being tracked")
        
        return {
            "success": True,
            "health_status": health_status,
            "issues": issues,
            "status": status,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in MT5 health check: {e}")
        return {
            "success": False,
            "health_status": "error",
            "issues": [f"Health check failed: {str(e)}"],
            "timestamp": datetime.now().isoformat()
        }