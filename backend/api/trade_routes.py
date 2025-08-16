"""
Trade Recording API Routes

API endpoints for comprehensive trade recording, tracking, and display
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

import sqlite3
import os

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/trades", tags=["Trade Recording"])

# Import the trade recording service
# Handle imports for both running from root and from backend directory
try:
    from backend.services.trade_recording_service import get_trade_recording_service, TradeStatus
except ImportError:
    from services.trade_recording_service import get_trade_recording_service, TradeStatus


# Pydantic models for request/response
class DashboardTradeCommand(BaseModel):
    """Trade command from dashboard"""
    magic_number: int
    command: str  # PLACE_ORDER, MODIFY_ORDER, CANCEL_ORDER, CLOSE_POSITION
    parameters: Dict[str, Any]
    command_id: Optional[str] = None


class MT5TradeUpdate(BaseModel):
    """Trade update from MT5 EA"""
    magic_number: int
    event_type: str  # FILL, CLOSE, CANCEL, MODIFY
    trade_data: Dict[str, Any]
    timestamp: str


class TradeQuery(BaseModel):
    """Query parameters for trade retrieval"""
    magic_number: Optional[int] = None
    symbol: Optional[str] = None
    status: Optional[str] = None
    limit: int = 50


@router.post("/command")
async def record_dashboard_command(command: DashboardTradeCommand, background_tasks: BackgroundTasks):
    """Record a trade command from the dashboard"""
    try:
        trade_service = get_trade_recording_service()
        
        # Prepare command data
        command_data = {
            'magic_number': command.magic_number,
            'command': command.command,
            'parameters': command.parameters,
            'command_id': command.command_id,
            'timestamp': datetime.now().isoformat()
        }
        
        # Record the command
        trade_id = await trade_service.record_dashboard_command(command_data)
        
        logger.info(f"Dashboard command recorded: {command.command} for EA {command.magic_number}")
        
        return {
            "success": True,
            "trade_id": trade_id,
            "message": f"Trade command recorded successfully",
            "command": command.command,
            "magic_number": command.magic_number
        }
        
    except Exception as e:
        logger.error(f"Error recording dashboard command: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to record command: {str(e)}")


@router.post("/mt5-update")
async def record_mt5_update(update: MT5TradeUpdate, background_tasks: BackgroundTasks):
    """Record a trade update from MT5 EA"""
    try:
        trade_service = get_trade_recording_service()
        
        success = False
        
        if update.event_type == "FILL":
            success = await trade_service.record_mt5_fill(update.trade_data)
        elif update.event_type == "CLOSE":
            success = await trade_service.record_trade_close(update.trade_data)
        elif update.event_type == "CANCEL":
            success = await trade_service.record_trade_cancellation(update.trade_data)
        else:
            raise HTTPException(status_code=400, detail=f"Unknown event type: {update.event_type}")
        
        if success:
            logger.info(f"MT5 update recorded: {update.event_type} for EA {update.magic_number}")
            return {
                "success": True,
                "message": f"MT5 {update.event_type.lower()} update recorded successfully",
                "event_type": update.event_type,
                "magic_number": update.magic_number
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to process MT5 update")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recording MT5 update: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to record MT5 update: {str(e)}")


@router.get("/active")
async def get_active_trades(magic_number: Optional[int] = None):
    """Get active trades"""
    try:
        trade_service = get_trade_recording_service()
        active_trades = trade_service.get_active_trades(magic_number)
        
        return {
            "success": True,
            "trades": [trade.to_dict() for trade in active_trades],
            "count": len(active_trades),
            "magic_number": magic_number
        }
        
    except Exception as e:
        logger.error(f"Error getting active trades: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get active trades: {str(e)}")


@router.get("/history")
async def get_trade_history(magic_number: Optional[int] = None, limit: int = 50):
    """Get trade history"""
    try:
        trade_service = get_trade_recording_service()
        trade_history = trade_service.get_trade_history(magic_number, limit)
        
        return {
            "success": True,
            "trades": [trade.to_dict() for trade in trade_history],
            "count": len(trade_history),
            "magic_number": magic_number,
            "limit": limit
        }
        
    except Exception as e:
        logger.error(f"Error getting trade history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get trade history: {str(e)}")


@router.get("/journal")
async def get_trade_journal(magic_number: Optional[int] = None, limit: int = 20):
    """Get formatted trade journal entries"""
    try:
        trade_service = get_trade_recording_service()
        journal_entries = trade_service.get_trade_journal(magic_number, limit)
        
        return {
            "success": True,
            "journal_entries": journal_entries,
            "count": len(journal_entries),
            "magic_number": magic_number,
            "format": "Tagged journal format with [ENTRY], [SL], [TP], [RR], [CLOSE], [CANCEL] tags"
        }
        
    except Exception as e:
        logger.error(f"Error getting trade journal: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get trade journal: {str(e)}")


@router.get("/performance/{magic_number}")
async def get_ea_performance(magic_number: int):
    """Get performance summary for an EA based on recorded trades"""
    try:
        trade_service = get_trade_recording_service()
        performance = trade_service.get_ea_performance_summary(magic_number)
        
        return {
            "success": True,
            "magic_number": magic_number,
            "performance": performance,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting EA performance: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get EA performance: {str(e)}")


@router.get("/{trade_id}")
async def get_trade_details(trade_id: str):
    """Get detailed information about a specific trade"""
    try:
        trade_service = get_trade_recording_service()
        trade = trade_service.get_trade_by_id(trade_id)
        
        if not trade:
            raise HTTPException(status_code=404, detail="Trade not found")
        
        return {
            "success": True,
            "trade": trade.to_dict(),
            "journal_format": trade.to_journal_format()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting trade details: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get trade details: {str(e)}")


@router.get("/dashboard/{magic_number}")
async def get_dashboard_trade_data(magic_number: int):
    """Get comprehensive trade data for dashboard display"""
    try:
        trade_service = get_trade_recording_service()
        
        # Get active trades
        active_trades = trade_service.get_active_trades(magic_number)
        
        # Get recent trade history
        trade_history = trade_service.get_trade_history(magic_number, 10)
        
        # Get performance summary
        performance = trade_service.get_ea_performance_summary(magic_number)
        
        # Get journal entries
        journal_entries = trade_service.get_trade_journal(magic_number, 15)
        
        return {
            "success": True,
            "magic_number": magic_number,
            "active_trades": {
                "count": len(active_trades),
                "trades": [trade.to_dict() for trade in active_trades]
            },
            "recent_history": {
                "count": len(trade_history),
                "trades": [trade.to_dict() for trade in trade_history]
            },
            "performance_summary": performance,
            "journal_entries": journal_entries,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting dashboard trade data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard trade data: {str(e)}")


@router.post("/simulate-fill")
async def simulate_trade_fill(magic_number: int, trade_data: Dict[str, Any]):
    """Simulate a trade fill for testing purposes"""
    try:
        trade_service = get_trade_recording_service()
        
        # Add magic number to trade data
        trade_data['magic_number'] = magic_number
        
        # Record the fill
        success = await trade_service.record_mt5_fill(trade_data)
        
        if success:
            return {
                "success": True,
                "message": "Trade fill simulated successfully",
                "magic_number": magic_number,
                "trade_data": trade_data
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to simulate trade fill")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error simulating trade fill: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to simulate trade fill: {str(e)}")


@router.post("/simulate-close")
async def simulate_trade_close(magic_number: int, close_data: Dict[str, Any]):
    """Simulate a trade close for testing purposes"""
    try:
        trade_service = get_trade_recording_service()
        
        # Add magic number to close data
        close_data['magic_number'] = magic_number
        
        # Record the close
        success = await trade_service.record_trade_close(close_data)
        
        if success:
            return {
                "success": True,
                "message": "Trade close simulated successfully",
                "magic_number": magic_number,
                "close_data": close_data
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to simulate trade close")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error simulating trade close: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to simulate trade close: {str(e)}")


@router.delete("/clear/{magic_number}")
async def clear_ea_trades(magic_number: int):
    """Clear all trades for an EA (for testing purposes)"""
    try:
        trade_service = get_trade_recording_service()
        
        # Remove from active trades
        trades_to_remove = []
        for trade_id, trade in trade_service.active_trades.items():
            if trade.magic_number == magic_number:
                trades_to_remove.append(trade_id)
        
        for trade_id in trades_to_remove:
            del trade_service.active_trades[trade_id]
        
        # Remove from history
        trade_service.trade_history = [
            trade for trade in trade_service.trade_history 
            if trade.magic_number != magic_number
        ]
        
        logger.info(f"Cleared all trades for EA {magic_number}")
        
        return {
            "success": True,
            "message": f"All trades cleared for EA {magic_number}",
            "magic_number": magic_number,
            "cleared_active": len(trades_to_remove)
        }
        
    except Exception as e:
        logger.error(f"Error clearing EA trades: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear EA trades: {str(e)}")


# EA Management Routes
class EARegistration(BaseModel):
    """EA registration data"""
    magic_number: int
    ea_name: str
    symbol: str
    timeframe: str = "M1"
    account_number: Optional[str] = None
    broker: Optional[str] = None
    balance: float = 0.0
    equity: float = 0.0
    margin: float = 0.0
    free_margin: float = 0.0
    margin_level: float = 0.0


class EAHeartbeat(BaseModel):
    """EA heartbeat data"""
    magic_number: int
    balance: Optional[float] = None
    equity: Optional[float] = None
    margin: Optional[float] = None
    free_margin: Optional[float] = None
    margin_level: Optional[float] = None


@router.post("/ea/register")
async def register_ea(ea_data: EARegistration):
    """Register a new EA or update existing EA information"""
    try:
        trade_service = get_trade_recording_service()
        
        success = await trade_service.register_ea(ea_data.dict())
        
        if success:
            return {
                "success": True,
                "message": f"EA {ea_data.ea_name} registered successfully",
                "magic_number": ea_data.magic_number,
                "ea_name": ea_data.ea_name
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to register EA")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error registering EA: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to register EA: {str(e)}")


@router.post("/ea/heartbeat")
async def ea_heartbeat(heartbeat: EAHeartbeat):
    """Update EA heartbeat and account information"""
    try:
        trade_service = get_trade_recording_service()
        
        account_data = {}
        if heartbeat.balance is not None:
            account_data['balance'] = heartbeat.balance
        if heartbeat.equity is not None:
            account_data['equity'] = heartbeat.equity
        if heartbeat.margin is not None:
            account_data['margin'] = heartbeat.margin
        if heartbeat.free_margin is not None:
            account_data['free_margin'] = heartbeat.free_margin
        if heartbeat.margin_level is not None:
            account_data['margin_level'] = heartbeat.margin_level
        
        success = await trade_service.update_ea_heartbeat(
            heartbeat.magic_number, 
            account_data if account_data else None
        )
        
        if success:
            return {
                "success": True,
                "message": "EA heartbeat updated",
                "magic_number": heartbeat.magic_number
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to update EA heartbeat")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating EA heartbeat: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update EA heartbeat: {str(e)}")


@router.get("/ea/all")
async def get_all_eas():
    """Get all registered EAs"""
    try:
        trade_service = get_trade_recording_service()
        all_eas = trade_service.get_all_eas()
        
        return {
            "success": True,
            "eas": [ea.to_dict() for ea in all_eas],
            "count": len(all_eas),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting all EAs: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get EAs: {str(e)}")


@router.get("/ea/active")
async def get_active_eas():
    """Get only active EAs (with recent heartbeat)"""
    try:
        trade_service = get_trade_recording_service()
        active_eas = trade_service.get_active_eas()
        
        return {
            "success": True,
            "eas": [ea.to_dict() for ea in active_eas],
            "count": len(active_eas),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting active EAs: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get active EAs: {str(e)}")


@router.get("/ea/{magic_number}")
async def get_ea_details(magic_number: int):
    """Get detailed information about a specific EA"""
    try:
        trade_service = get_trade_recording_service()
        ea = trade_service.get_ea_by_magic(magic_number)
        
        if not ea:
            raise HTTPException(status_code=404, detail="EA not found")
        
        # Get EA's trades
        active_trades = trade_service.get_active_trades(magic_number)
        trade_history = trade_service.get_trade_history(magic_number, 20)
        performance = trade_service.get_ea_performance_summary(magic_number)
        
        return {
            "success": True,
            "ea": ea.to_dict(),
            "active_trades": [trade.to_dict() for trade in active_trades],
            "recent_history": [trade.to_dict() for trade in trade_history],
            "performance": performance,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting EA details: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get EA details: {str(e)}")


@router.get("/account/overview")
async def get_account_overview():
    """Get comprehensive account overview with all EAs and trading activity"""
    try:
        trade_service = get_trade_recording_service()
        overview = trade_service.get_account_overview()
        
        return {
            "success": True,
            **overview
        }
        
    except Exception as e:
        logger.error(f"Error getting account overview: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get account overview: {str(e)}")


@router.get("/stats/summary")
async def get_trade_statistics():
    """Get overall trade statistics across all EAs"""
    try:
        trade_service = get_trade_recording_service()
        
        # Get all trades
        all_active = list(trade_service.active_trades.values())
        all_history = trade_service.trade_history
        
        # Calculate statistics
        total_active = len(all_active)
        total_closed = len([t for t in all_history if t.status == TradeStatus.CLOSED])
        total_cancelled = len([t for t in all_history if t.status == TradeStatus.CANCELLED])
        
        # Group by EA
        ea_stats = {}
        for trade in all_active + all_history:
            magic = trade.magic_number
            if magic not in ea_stats:
                ea_stats[magic] = {
                    'active': 0,
                    'closed': 0,
                    'cancelled': 0,
                    'total_profit': 0.0
                }
            
            if trade.status == TradeStatus.FILLED or trade.status == TradeStatus.PENDING:
                ea_stats[magic]['active'] += 1
            elif trade.status == TradeStatus.CLOSED:
                ea_stats[magic]['closed'] += 1
                ea_stats[magic]['total_profit'] += trade.profit
            elif trade.status == TradeStatus.CANCELLED:
                ea_stats[magic]['cancelled'] += 1
        
        # Get EA information
        registered_eas = trade_service.get_all_eas()
        active_eas = trade_service.get_active_eas()
        
        return {
            "success": True,
            "overall_stats": {
                "total_active_trades": total_active,
                "total_closed_trades": total_closed,
                "total_cancelled_trades": total_cancelled,
                "total_eas_registered": len(registered_eas),
                "total_eas_active": len(active_eas)
            },
            "ea_breakdown": ea_stats,
            "registered_eas": [ea.to_dict() for ea in registered_eas],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting trade statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get trade statistics: {str(e)}")