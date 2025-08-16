"""
EA Communication Routes
Handles communication between Soldier EAs and COC Dashboard
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks, Query, UploadFile, File, Form
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import sqlite3
import os
import tempfile
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Import WebSocket server for real-time updates
try:
    from backend.services.websocket_server import get_websocket_server
    WEBSOCKET_AVAILABLE = True
except ImportError:
    try:
        from services.websocket_server import get_websocket_server
        WEBSOCKET_AVAILABLE = True
    except ImportError:
        WEBSOCKET_AVAILABLE = False
        print("️ WebSocket server not available - real-time updates disabled")

# Import price service for chart data
try:
    from backend.services.mt5_price_service import mt5_price_service
    PRICE_SERVICE_AVAILABLE = True
except ImportError:
    try:
        from services.mt5_price_service import mt5_price_service
        PRICE_SERVICE_AVAILABLE = True
    except ImportError:
        PRICE_SERVICE_AVAILABLE = False
        print("️ Price service not available - chart data disabled")

# Import backtest services
try:
    from backend.services.backtest_parser import BacktestHTMLParser
    from backend.services.backtest_comparison import BacktestComparison
    BACKTEST_SERVICE_AVAILABLE = True
    backtest_parser = BacktestHTMLParser()
    backtest_comparison = BacktestComparison()
except ImportError:
    try:
        from services.backtest_parser import BacktestHTMLParser
        from services.backtest_comparison import BacktestComparison
        BACKTEST_SERVICE_AVAILABLE = True
        backtest_parser = BacktestHTMLParser()
        backtest_comparison = BacktestComparison()
    except ImportError:
        BACKTEST_SERVICE_AVAILABLE = False
        print("️ Backtest service not available - backtest comparison disabled")

router = APIRouter(prefix="/api/ea", tags=["EA Communication"])


def get_db_connection():
    """Get database connection"""
    db_path = os.getenv("DATABASE_PATH", "data/mt5_dashboard.db")
    # Enable row factory if needed later
    return sqlite3.connect(db_path)


def _get_or_create_ea(cursor: sqlite3.Cursor, magic_number: int, symbol: str, strategy_tag: str) -> int:
    """Return ea.id for a given magic_number; create if missing."""
    cursor.execute("SELECT id FROM eas WHERE magic_number = ?", (magic_number,))
    row = cursor.fetchone()
    if row:
        ea_id = row[0]
        # Update symbol/strategy if changed and last_seen
        cursor.execute(
            """
            UPDATE eas
            SET symbol = ?, strategy_tag = ?, last_seen = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (symbol, strategy_tag, ea_id),
        )
        return ea_id

    # Create new EA entry
    cursor.execute(
        """
        INSERT INTO eas (magic_number, symbol, strategy_tag)
        VALUES (?, ?, ?)
        """,
        (magic_number, symbol, strategy_tag),
    )
    cursor.execute("SELECT id FROM eas WHERE magic_number = ?", (magic_number,))
    row = cursor.fetchone()
    return row[0]


# Pydantic models for request/response
class EAStatusUpdate(BaseModel):
    magic_number: int
    symbol: str
    strategy_tag: str
    current_profit: float
    open_positions: int
    sl_value: float
    tp_value: float
    trailing_active: bool
    module_status: Dict[str, str]
    performance_metrics: Dict[str, float]
    last_trades: List[Dict[str, Any]]
    coc_override: bool
    is_paused: bool
    timestamp: str


class CommandAcknowledgment(BaseModel):
    magic_number: int
    command: str
    status: str
    timestamp: str


class EACommand(BaseModel):
    command: str
    parameters: Optional[Dict[str, Any]] = {}
    target_eas: Optional[List[int]] = []
    execution_time: Optional[str] = None


# In-memory storage for pending commands (in production, use Redis or database)
pending_commands: Dict[int, List[EACommand]] = {}
ea_status_cache: Dict[int, EAStatusUpdate] = {}


@router.post("/status")
async def receive_ea_status(status: EAStatusUpdate):
    """Receive status update from Soldier EA"""
    try:
        # Store in cache for real-time dashboard updates
        ea_status_cache[status.magic_number] = status

        # Store in database
        conn = get_db_connection()
        cursor = conn.cursor()

        # Ensure EA exists and get ea_id
        ea_id = _get_or_create_ea(cursor, status.magic_number, status.symbol, status.strategy_tag)

        # Update EA paused/active status and last_seen
        cursor.execute(
            """
            UPDATE eas
            SET status = ?, last_seen = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            ("paused" if status.is_paused else "active", ea_id),
        )

        # Insert EA status snapshot (schema: ea_id, timestamp, current_profit, open_positions, sl_value, tp_value, trailing_active, module_status)
        cursor.execute(
            """
            INSERT INTO ea_status (
                ea_id, current_profit, open_positions, sl_value, tp_value, trailing_active, module_status
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                ea_id,
                status.current_profit,
                status.open_positions,
                status.sl_value,
                status.tp_value,
                1 if status.trailing_active else 0,
                json.dumps(status.module_status),
            ),
        )

        # Insert performance metrics (schema: ea_id, date, total_profit, profit_factor, expected_payoff, drawdown, z_score, trade_count)
        trade_count = status.performance_metrics.get("trade_count")
        if trade_count is None:
            trade_count = len(status.last_trades or [])

        cursor.execute(
            """
            INSERT INTO performance_history (
                ea_id, total_profit, profit_factor, expected_payoff, drawdown, z_score, trade_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                ea_id,
                float(status.performance_metrics.get("total_profit", 0.0)),
                float(status.performance_metrics.get("profit_factor", 0.0)),
                float(status.performance_metrics.get("expected_payoff", 0.0)),
                float(status.performance_metrics.get("drawdown", 0.0)),
                float(status.performance_metrics.get("z_score", 0.0)),
                int(trade_count),
            ),
        )

        # Store recent trades (map to schema: order_type, open_price, close_price, open_time, close_time)
        for trade in (status.last_trades or [])[-5:]:
            cursor.execute(
                """
                INSERT INTO trades (
                    ea_id, symbol, order_type, volume, open_price, close_price, profit, open_time, close_time
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    ea_id,
                    trade.get("symbol", status.symbol),
                    trade.get("type", "UNKNOWN"),
                    float(trade.get("volume", 0.0)),
                    float(trade.get("price", 0.0)),
                    None,
                    float(trade.get("profit", 0.0)),
                    trade.get("timestamp", datetime.now().isoformat()),
                    None,
                ),
            )

        conn.commit()
        conn.close()

        # Broadcast real-time update to WebSocket clients with portfolio analytics theme
        if WEBSOCKET_AVAILABLE:
            try:
                websocket_server = get_websocket_server()
                
                # Apply portfolio analytics theme styling to EA data
                theme_status = _apply_portfolio_theme_to_ea_status(status)
                
                ea_data = {
                    "eaId": status.magic_number,  # Use camelCase for frontend consistency
                    "ea_id": status.magic_number,  # Keep snake_case for backward compatibility
                    "magicNumber": status.magic_number,  # Use camelCase for frontend consistency
                    "magic_number": status.magic_number,  # Keep snake_case for backward compatibility
                    "symbol": status.symbol,
                    "strategyTag": status.strategy_tag,  # Use camelCase for frontend consistency
                    "strategy_tag": status.strategy_tag,  # Keep snake_case for backward compatibility
                    "status": "paused" if status.is_paused else "active",
                    "currentProfit": status.current_profit,  # Use camelCase for frontend consistency
                    "current_profit": status.current_profit,  # Keep snake_case for backward compatibility
                    "openPositions": status.open_positions,  # Use camelCase for frontend consistency
                    "open_positions": status.open_positions,  # Keep snake_case for backward compatibility
                    "slValue": status.sl_value,  # Use camelCase for frontend consistency
                    "sl_value": status.sl_value,  # Keep snake_case for backward compatibility
                    "tpValue": status.tp_value,  # Use camelCase for frontend consistency
                    "tp_value": status.tp_value,  # Keep snake_case for backward compatibility
                    "trailingActive": status.trailing_active,  # Use camelCase for frontend consistency
                    "trailing_active": status.trailing_active,  # Keep snake_case for backward compatibility
                    "moduleStatus": status.module_status,  # Use camelCase for frontend consistency
                    "module_status": status.module_status,  # Keep snake_case for backward compatibility
                    "performanceMetrics": status.performance_metrics,  # Use camelCase for frontend consistency
                    "performance_metrics": status.performance_metrics,  # Keep snake_case for backward compatibility
                    "lastTrades": status.last_trades,  # Use camelCase for frontend consistency
                    "last_trades": status.last_trades,  # Keep snake_case for backward compatibility
                    "cocOverride": status.coc_override,  # Use camelCase for frontend consistency
                    "coc_override": status.coc_override,  # Keep snake_case for backward compatibility
                    "lastUpdate": status.timestamp,  # Use camelCase for frontend consistency
                    "last_update": status.timestamp,  # Keep snake_case for backward compatibility
                    # Portfolio analytics theme data
                    "themeData": theme_status
                }
                
                # Use asyncio to broadcast without blocking the API response
                import asyncio
                asyncio.create_task(websocket_server.broadcast_ea_update(ea_data))
            except Exception as e:
                print(f"️ WebSocket broadcast failed: {e}")

        return {"status": "success", "message": "Status received"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process status: {str(e)}")


@router.get("/commands/{magic_number}")
async def get_pending_commands(magic_number: int):
    """Get pending commands for specific EA"""
    if magic_number in pending_commands and pending_commands[magic_number]:
        # Return first pending command
        command = pending_commands[magic_number].pop(0)
        return command.dict()
    else:
        raise HTTPException(status_code=404, detail="No pending commands")


@router.post("/command-ack")
async def acknowledge_command(ack: CommandAcknowledgment):
    """Acknowledge command execution by EA"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Map magic_number to ea_id
        cursor.execute("SELECT id FROM eas WHERE magic_number = ?", (ack.magic_number,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="EA not found")
        ea_id = row[0]

        command_data = {
            "acknowledged": True,
            "ack_status": ack.status,
            "ack_timestamp": ack.timestamp,
        }
        executed = 1 if str(ack.status).lower() in {"ok", "success", "executed", "done"} else 0

        cursor.execute(
            """
            INSERT INTO command_queue (ea_id, command_type, command_data, executed, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (ea_id, ack.command, json.dumps(command_data), executed, datetime.now()),
        )

        conn.commit()
        conn.close()

        # Broadcast command acknowledgment to WebSocket clients
        if WEBSOCKET_AVAILABLE:
            try:
                websocket_server = get_websocket_server()
                command_data = {
                    "eaId": ack.magic_number,  # Use camelCase for frontend consistency
                    "ea_id": ack.magic_number,  # Keep snake_case for backward compatibility
                    "magicNumber": ack.magic_number,  # Use camelCase for frontend consistency
                    "magic_number": ack.magic_number,  # Keep snake_case for backward compatibility
                    "command": ack.command,
                    "status": ack.status,
                    "timestamp": ack.timestamp
                }
                
                import asyncio
                asyncio.create_task(websocket_server.broadcast_command_update(command_data))
            except Exception as e:
                print(f"️ WebSocket broadcast failed: {e}")

        return {"status": "acknowledged"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to acknowledge command: {str(e)}")


@router.post("/command")
async def send_command_to_ea(magic_number: int, command: EACommand):
    """Send command to specific EA"""
    try:
        # Add command to pending queue
        if magic_number not in pending_commands:
            pending_commands[magic_number] = []

        pending_commands[magic_number].append(command)

        conn = get_db_connection()
        cursor = conn.cursor()

        # Map magic_number to ea_id
        cursor.execute("SELECT id FROM eas WHERE magic_number = ?", (magic_number,))
        row = cursor.fetchone()
        if row:
            ea_id = row[0]
        else:
            # If EA hasn't reported yet, create minimal record
            ea_id = _get_or_create_ea(cursor, magic_number, "UNKNOWN", "UNKNOWN")

        command_data = {
            "parameters": command.parameters or {},
            "status": "pending",
            "execution_time": command.execution_time,
        }

        cursor.execute(
            """
            INSERT INTO command_queue (ea_id, command_type, command_data, executed, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (ea_id, command.command, json.dumps(command_data), 0, datetime.now()),
        )

        conn.commit()
        conn.close()

        # Record trade command if it's a trading command
        if command.command in ["PLACE_ORDER", "MODIFY_ORDER", "CANCEL_ORDER", "CLOSE_POSITION"]:
            try:
                from services.trade_recording_service import get_trade_recording_service
                trade_service = get_trade_recording_service()
                
                command_data_for_trade = {
                    'magic_number': magic_number,
                    'command': command.command,
                    'parameters': command.parameters or {},
                    'command_id': f"cmd_{int(datetime.now().timestamp())}_{magic_number}",
                    'timestamp': datetime.now().isoformat()
                }
                
                trade_id = await trade_service.record_dashboard_command(command_data_for_trade)
                logger.info(f"Trade command recorded with ID: {trade_id}")
                
            except Exception as trade_error:
                logger.error(f"Failed to record trade command: {trade_error}")
                # Don't fail the main command, just log the error

        return {"status": "command_queued", "message": f"Command sent to EA {magic_number}"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send command: {str(e)}")


@router.post("/commands/batch")
async def send_batch_commands(command: EACommand):
    """Send command to multiple EAs"""
    try:
        results = []

        conn = get_db_connection()
        cursor = conn.cursor()

        for magic_number in command.target_eas:
            # Add command to pending queue
            if magic_number not in pending_commands:
                pending_commands[magic_number] = []

            pending_commands[magic_number].append(command)
            results.append({"ea_id": magic_number, "status": "queued"})

            # Map magic_number to ea_id
            cursor.execute("SELECT id FROM eas WHERE magic_number = ?", (magic_number,))
            row = cursor.fetchone()
            if row:
                ea_id = row[0]
            else:
                ea_id = _get_or_create_ea(cursor, magic_number, "UNKNOWN", "UNKNOWN")

            command_data = {
                "parameters": command.parameters or {},
                "status": "pending",
                "execution_time": command.execution_time,
            }

            cursor.execute(
                """
                INSERT INTO command_queue (ea_id, command_type, command_data, executed, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (ea_id, command.command, json.dumps(command_data), 0, datetime.now()),
            )

        conn.commit()
        conn.close()

        return {"status": "batch_commands_queued", "results": results}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send batch commands: {str(e)}")


@router.get("/status/all")
async def get_all_ea_status():
    """Get status of all EAs (latest snapshot per EA)"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Join eas with the latest status per ea_id
        cursor.execute(
            """
            SELECT e.magic_number, e.symbol, e.strategy_tag, e.status,
                   s.current_profit, s.open_positions, s.sl_value, s.tp_value,
                   s.trailing_active, s.module_status, s.timestamp
            FROM eas e
            LEFT JOIN (
              SELECT x.* FROM ea_status x
              JOIN (
                SELECT ea_id, MAX(timestamp) AS max_ts
                FROM ea_status
                GROUP BY ea_id
              ) y ON x.ea_id = y.ea_id AND x.timestamp = y.max_ts
            ) s ON s.ea_id = e.id
            ORDER BY COALESCE(s.timestamp, e.last_seen) DESC
            """
        )

        eas: List[Dict[str, Any]] = []
        for row in cursor.fetchall():
            # Create mock EA status for theme application
            mock_status = EAStatusUpdate(
                magic_number=row[0],
                symbol=row[1],
                strategy_tag=row[2],
                current_profit=row[4] or 0.0,
                open_positions=row[5] or 0,
                sl_value=row[6] or 0.0,
                tp_value=row[7] or 0.0,
                trailing_active=bool(row[8]) if row[8] is not None else False,
                module_status={},
                performance_metrics={"profit_factor": 1.0 + (row[4] or 0.0) * 0.1},
                last_trades=[],
                coc_override=False,
                is_paused=(row[3] == "paused"),
                timestamp=row[10] or ""
            )
            
            # Apply portfolio theme
            theme_data = _apply_portfolio_theme_to_ea_status(mock_status)
            
            eas.append(
                {
                    "magicNumber": row[0],  # Use camelCase for frontend consistency
                    "magic_number": row[0],  # Keep snake_case for backward compatibility
                    "symbol": row[1],
                    "strategyTag": row[2],  # Use camelCase for frontend consistency
                    "strategy_tag": row[2],  # Keep snake_case for backward compatibility
                    "currentProfit": row[4] or 0.0,  # Use camelCase for frontend consistency
                    "current_profit": row[4] or 0.0,  # Keep snake_case for backward compatibility
                    "openPositions": row[5] or 0,  # Use camelCase for frontend consistency
                    "open_positions": row[5] or 0,  # Keep snake_case for backward compatibility
                    "slValue": row[6],  # Use camelCase for frontend consistency
                    "sl_value": row[6],  # Keep snake_case for backward compatibility
                    "tpValue": row[7],  # Use camelCase for frontend consistency
                    "tp_value": row[7],  # Keep snake_case for backward compatibility
                    "trailingActive": bool(row[8]) if row[8] is not None else False,  # Use camelCase for frontend consistency
                    "trailing_active": bool(row[8]) if row[8] is not None else False,  # Keep snake_case for backward compatibility
                    "cocOverride": False,  # Use camelCase for frontend consistency
                    "coc_override": False,  # Keep snake_case for backward compatibility
                    "isPaused": (row[3] == "paused"),  # Use camelCase for frontend consistency
                    "is_paused": (row[3] == "paused"),  # Keep snake_case for backward compatibility
                    "lastUpdate": row[10] or None,  # Use camelCase for frontend consistency
                    "last_update": row[10] or None,  # Keep snake_case for backward compatibility
                    "themeData": theme_data  # Portfolio analytics theme data
                }
            )

        conn.close()
        return {"eas": eas, "count": len(eas)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get EA status: {str(e)}")


@router.get("/status/{magic_number}")
async def get_ea_status(magic_number: int):
    """Get status of specific EA (latest snapshot)"""
    try:
        # First check cache for real-time data
        if magic_number in ea_status_cache:
            return ea_status_cache[magic_number].dict()

        conn = get_db_connection()
        cursor = conn.cursor()

        # Get ea_id
        cursor.execute("SELECT id, symbol, strategy_tag, status FROM eas WHERE magic_number = ?", (magic_number,))
        ea_row = cursor.fetchone()
        if not ea_row:
            raise HTTPException(status_code=404, detail="EA not found")
        ea_id, symbol, strategy_tag, ea_status_val = ea_row

        # Latest status
        cursor.execute(
            """
            SELECT current_profit, open_positions, sl_value, tp_value, trailing_active, module_status, timestamp
            FROM ea_status
            WHERE ea_id = ?
            ORDER BY timestamp DESC
            LIMIT 1
            """,
            (ea_id,),
        )
        row = cursor.fetchone()

        if not row:
            # No status yet; return basic info
            conn.close()
            return {
                "magicNumber": magic_number,  # Use camelCase for frontend consistency
                "magic_number": magic_number,  # Keep snake_case for backward compatibility
                "symbol": symbol,
                "strategyTag": strategy_tag,  # Use camelCase for frontend consistency
                "strategy_tag": strategy_tag,  # Keep snake_case for backward compatibility
                "currentProfit": 0.0,  # Use camelCase for frontend consistency
                "current_profit": 0.0,  # Keep snake_case for backward compatibility
                "openPositions": 0,  # Use camelCase for frontend consistency
                "open_positions": 0,  # Keep snake_case for backward compatibility
                "slValue": None,  # Use camelCase for frontend consistency
                "sl_value": None,  # Keep snake_case for backward compatibility
                "tpValue": None,  # Use camelCase for frontend consistency
                "tp_value": None,  # Keep snake_case for backward compatibility
                "trailingActive": False,  # Use camelCase for frontend consistency
                "trailing_active": False,  # Keep snake_case for backward compatibility
                "cocOverride": False,  # Use camelCase for frontend consistency
                "coc_override": False,  # Keep snake_case for backward compatibility
                "isPaused": (ea_status_val == "paused"),  # Use camelCase for frontend consistency
                "is_paused": (ea_status_val == "paused"),  # Keep snake_case for backward compatibility
                "lastUpdate": None,  # Use camelCase for frontend consistency
                "last_update": None,  # Keep snake_case for backward compatibility
            }

        # Create mock EA status for theme application
        mock_status = EAStatusUpdate(
            magic_number=magic_number,
            symbol=symbol,
            strategy_tag=strategy_tag,
            current_profit=row[0],
            open_positions=row[1],
            sl_value=row[2] or 0.0,
            tp_value=row[3] or 0.0,
            trailing_active=bool(row[4]) if row[4] is not None else False,
            module_status={},
            performance_metrics={"profit_factor": 1.0 + (row[0] or 0.0) * 0.1},
            last_trades=[],
            coc_override=False,
            is_paused=(ea_status_val == "paused"),
            timestamp=row[6] or ""
        )
        
        # Apply portfolio theme
        theme_data = _apply_portfolio_theme_to_ea_status(mock_status)

        ea_data = {
            "magicNumber": magic_number,  # Use camelCase for frontend consistency
            "magic_number": magic_number,  # Keep snake_case for backward compatibility
            "symbol": symbol,
            "strategyTag": strategy_tag,  # Use camelCase for frontend consistency
            "strategy_tag": strategy_tag,  # Keep snake_case for backward compatibility
            "currentProfit": row[0],  # Use camelCase for frontend consistency
            "current_profit": row[0],  # Keep snake_case for backward compatibility
            "openPositions": row[1],  # Use camelCase for frontend consistency
            "open_positions": row[1],  # Keep snake_case for backward compatibility
            "slValue": row[2],  # Use camelCase for frontend consistency
            "sl_value": row[2],  # Keep snake_case for backward compatibility
            "tpValue": row[3],  # Use camelCase for frontend consistency
            "tp_value": row[3],  # Keep snake_case for backward compatibility
            "trailingActive": bool(row[4]) if row[4] is not None else False,  # Use camelCase for frontend consistency
            "trailing_active": bool(row[4]) if row[4] is not None else False,  # Keep snake_case for backward compatibility
            "cocOverride": False,  # Use camelCase for frontend consistency
            "coc_override": False,  # Keep snake_case for backward compatibility
            "isPaused": (ea_status_val == "paused"),  # Use camelCase for frontend consistency
            "is_paused": (ea_status_val == "paused"),  # Keep snake_case for backward compatibility
            "lastUpdate": row[6],  # Use camelCase for frontend consistency
            "last_update": row[6],  # Keep snake_case for backward compatibility
            "themeData": theme_data  # Portfolio analytics theme data
        }

        conn.close()
        return ea_data

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get EA status: {str(e)}")


@router.get("/performance/{magic_number}")
async def get_ea_performance(magic_number: int):
    """Get performance history for specific EA"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Map magic_number to ea_id
        cursor.execute("SELECT id FROM eas WHERE magic_number = ?", (magic_number,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="EA not found")
        ea_id = row[0]

        cursor.execute(
            """
            SELECT date, total_profit, profit_factor, expected_payoff, drawdown, z_score, trade_count
            FROM performance_history
            WHERE ea_id = ?
            ORDER BY date DESC
            LIMIT 100
            """,
            (ea_id,),
        )

        performance_data = []
        for row in cursor.fetchall():
            performance_data.append(
                {
                    "timestamp": row[0],
                    "total_profit": row[1],
                    "profit_factor": row[2],
                    "expected_payoff": row[3],
                    "drawdown": row[4],
                    "z_score": row[5],
                    "trade_count": row[6],
                }
            )

        conn.close()
        return {"performance_history": performance_data}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get performance data: {str(e)}")


@router.get("/trades/{magic_number}")
async def get_ea_trades(magic_number: int, limit: int = 50):
    """Get recent trades for specific EA"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Map magic_number to ea_id
        cursor.execute("SELECT id FROM eas WHERE magic_number = ?", (magic_number,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="EA not found")
        ea_id = row[0]

        cursor.execute(
            """
            SELECT symbol, order_type, volume, open_price, profit, open_time
            FROM trades
            WHERE ea_id = ?
            ORDER BY open_time DESC
            LIMIT ?
            """,
            (ea_id, limit),
        )

        trades = []
        for row in cursor.fetchall():
            trades.append(
                {
                    "symbol": row[0],
                    "type": row[1],
                    "volume": row[2],
                    "price": row[3],
                    "profit": row[4],
                    "timestamp": row[5],
                }
            )

        conn.close()
        return {"trades": trades}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get trades: {str(e)}")


@router.delete("/status/{magic_number}")
async def remove_ea(magic_number: int):
    """Remove EA from system"""
    try:
        # Remove from cache
        if magic_number in ea_status_cache:
            del ea_status_cache[magic_number]

        # Remove pending commands
        if magic_number in pending_commands:
            del pending_commands[magic_number]

        conn = get_db_connection()
        cursor = conn.cursor()

        # Map magic_number to ea_id
        cursor.execute("SELECT id FROM eas WHERE magic_number = ?", (magic_number,))
        row = cursor.fetchone()
        if not row:
            # Nothing to remove in DB, return success for idempotency
            return {"status": "removed", "message": f"EA {magic_number} removed from system"}
        ea_id = row[0]

        cursor.execute("DELETE FROM ea_status WHERE ea_id = ?", (ea_id,))
        cursor.execute("DELETE FROM performance_history WHERE ea_id = ?", (ea_id,))
        cursor.execute("DELETE FROM trades WHERE ea_id = ?", (ea_id,))
        cursor.execute("DELETE FROM command_queue WHERE ea_id = ?", (ea_id,))
        cursor.execute("DELETE FROM eas WHERE id = ?", (ea_id,))

        conn.commit()
        conn.close()

        return {"status": "removed", "message": f"EA {magic_number} removed from system"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to remove EA: {str(e)}")


@router.post("/backtest/upload")
async def upload_backtest_report(
    magic_number: int = Form(...),
    file: UploadFile = File(...)
):
    """Upload backtest HTML report for an EA"""
    print(f"🔄 Starting backtest upload for EA {magic_number}")
    
    try:
        # Validate file type
        if not file.filename.endswith(('.html', '.htm')):
            raise HTTPException(
                status_code=400, 
                detail="File must be an HTML backtest report"
            )
        
        print(f"📁 File validation passed: {file.filename}")
        
        # Read file content
        content = await file.read()
        html_content = content.decode('utf-8', errors='ignore')
        print(f"📖 File read successfully: {len(html_content)} characters")
        
        # Simple parsing without external dependencies
        import re
        from bs4 import BeautifulSoup
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            text_content = soup.get_text()
            
            # Extract metrics using regex
            patterns = {
                'profit_factor': r'Profit\s+factor\s*[:\-]?\s*([\d\.]+)',
                'expected_payoff': r'Expected\s+payoff\s*[:\-]?\s*([\d\.\-]+)',
                'drawdown': r'([\d\.]+)\s*\(([\d\.]+)%\)</b></td>',
                'win_rate': r'Profit\s+trades\s+\([^)]*\)\s*[:\-]?\s*\d+\s*\(\s*([\d\.]+)\s*%\s*\)',
                'trade_count': r'Total\s+deals\s*[:\-]?\s*(\d+)'
            }
            
            metrics = {}
            for metric_name, pattern in patterns.items():
                match = re.search(pattern, text_content, re.IGNORECASE)
                if match:
                    try:
                        if metric_name == 'drawdown':
                            value = float(match.group(2))  # Get percentage value
                        else:
                            value = float(match.group(1))
                        metrics[metric_name] = value
                    except (ValueError, IndexError):
                        continue
            
            if len(metrics) < 4:  # Need at least 4 metrics
                raise HTTPException(
                    status_code=400,
                    detail="Could not extract required metrics from backtest report"
                )
            
            print(f"✅ Parsing successful: {metrics}")
            
        except Exception as parse_error:
            print(f"❌ Parsing error: {parse_error}")
            raise HTTPException(
                status_code=400,
                detail=f"Failed to parse backtest report: {str(parse_error)}"
            )
        
        # Get database connection and find EA
        print("🗄️ Connecting to database...")
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Map magic_number to ea_id
        cursor.execute("SELECT id FROM eas WHERE magic_number = ?", (magic_number,))
        row = cursor.fetchone()
        if not row:
            print(f"🆕 Creating new EA entry for magic number {magic_number}")
            ea_id = _get_or_create_ea(cursor, magic_number, "UNKNOWN", "UNKNOWN")
        else:
            ea_id = row[0]
            print(f"✅ Found existing EA: ea_id={ea_id}")
        
        # Store backtest benchmark
        try:
            print("📊 Creating/updating backtest_benchmarks table...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS backtest_benchmarks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ea_id INTEGER NOT NULL,
                    profit_factor REAL NOT NULL,
                    expected_payoff REAL NOT NULL,
                    drawdown REAL NOT NULL,
                    win_rate REAL NOT NULL,
                    trade_count INTEGER NOT NULL,
                    upload_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (ea_id) REFERENCES eas (id)
                )
            """)
            
            print("💾 Inserting backtest benchmark data...")
            cursor.execute("""
                INSERT OR REPLACE INTO backtest_benchmarks 
                (ea_id, profit_factor, expected_payoff, drawdown, win_rate, trade_count)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                ea_id,
                metrics.get('profit_factor', 0.0),
                metrics.get('expected_payoff', 0.0),
                metrics.get('drawdown', 0.0),
                metrics.get('win_rate', 0.0),
                int(metrics.get('trade_count', 0))
            ))
            
            conn.commit()
            print(f"✅ Backtest benchmark stored for EA {magic_number} (ea_id: {ea_id})")
            
        except Exception as db_error:
            print(f"❌ Database error: {db_error}")
            conn.rollback()
            raise HTTPException(status_code=500, detail=f"Database error: {str(db_error)}")
        finally:
            conn.close()
        
        return {
            "success": True,
            "message": f"Backtest report uploaded successfully for EA {magic_number}",
            "ea_id": ea_id,
            "magic_number": magic_number,
            "metrics": metrics
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Upload error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/backtest/compare/{magic_number}")
async def compare_ea_with_backtest(magic_number: int):
    """Compare EA's current performance with its backtest benchmark"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get EA info
        cursor.execute("SELECT id FROM eas WHERE magic_number = ?", (magic_number,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            raise HTTPException(status_code=404, detail="EA not found")
        ea_id = row[0]
        
        # Get backtest benchmark
        cursor.execute("""
            SELECT profit_factor, expected_payoff, drawdown, win_rate, trade_count
            FROM backtest_benchmarks 
            WHERE ea_id = ? 
            ORDER BY upload_date DESC 
            LIMIT 1
        """, (ea_id,))
        
        benchmark_row = cursor.fetchone()
        if not benchmark_row:
            conn.close()
            raise HTTPException(
                status_code=404, 
                detail=f"No backtest benchmark found for EA {magic_number}"
            )
        
        # Get latest live performance
        cursor.execute("""
            SELECT total_profit, profit_factor, expected_payoff, drawdown, z_score, trade_count
            FROM performance_history 
            WHERE ea_id = ? 
            ORDER BY date DESC 
            LIMIT 1
        """, (ea_id,))
        
        live_row = cursor.fetchone()
        conn.close()
        
        if not live_row:
            raise HTTPException(
                status_code=404,
                detail=f"No live performance data found for EA {magic_number}"
            )
        
        # Calculate deviations manually (simplified comparison)
        backtest_pf = benchmark_row[0]
        live_pf = live_row[1]
        
        pf_deviation = ((live_pf - backtest_pf) / backtest_pf * 100) if backtest_pf != 0 else 0
        
        backtest_ep = benchmark_row[1]
        live_ep = live_row[2]
        ep_deviation = ((live_ep - backtest_ep) / backtest_ep * 100) if backtest_ep != 0 else 0
        
        backtest_dd = benchmark_row[2]
        live_dd = live_row[3]
        dd_deviation = ((live_dd - backtest_dd) / backtest_dd * 100) if backtest_dd != 0 else 0
        
        # Determine overall status
        overall_status = "good"
        if abs(pf_deviation) > 20 or abs(ep_deviation) > 25 or dd_deviation > 50:
            overall_status = "critical"
        elif abs(pf_deviation) > 10 or abs(ep_deviation) > 15 or dd_deviation > 25:
            overall_status = "warning"
        
        return {
            "success": True,
            "magic_number": magic_number,
            "ea_id": ea_id,
            "comparison": {
                "overall_status": overall_status,
                "profit_factor_deviation": round(pf_deviation, 2),
                "expected_payoff_deviation": round(ep_deviation, 2),
                "drawdown_deviation": round(dd_deviation, 2),
                "alerts": [
                    {
                        "metric": "profit_factor",
                        "deviation": round(pf_deviation, 2),
                        "status": "critical" if abs(pf_deviation) > 20 else "warning" if abs(pf_deviation) > 10 else "good"
                    },
                    {
                        "metric": "expected_payoff", 
                        "deviation": round(ep_deviation, 2),
                        "status": "critical" if abs(ep_deviation) > 25 else "warning" if abs(ep_deviation) > 15 else "good"
                    },
                    {
                        "metric": "drawdown",
                        "deviation": round(dd_deviation, 2),
                        "status": "critical" if dd_deviation > 50 else "warning" if dd_deviation > 25 else "good"
                    }
                ]
            },
            "backtest_benchmark": {
                "profit_factor": benchmark_row[0],
                "expected_payoff": benchmark_row[1],
                "drawdown": benchmark_row[2],
                "win_rate": benchmark_row[3],
                "trade_count": benchmark_row[4]
            },
            "live_performance": {
                "total_profit": live_row[0],
                "profit_factor": live_row[1],
                "expected_payoff": live_row[2],
                "drawdown": live_row[3],
                "trade_count": live_row[5]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Comparison error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Comparison failed: {str(e)}")


@router.get("/backtest/benchmark/{magic_number}")
async def get_ea_backtest_benchmark(magic_number: int):
    """Get backtest benchmark for specific EA"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get EA info and benchmark
        cursor.execute("""
            SELECT b.profit_factor, b.expected_payoff, b.drawdown, b.win_rate, 
                   b.trade_count, b.upload_date, e.symbol, e.strategy_tag
            FROM backtest_benchmarks b
            JOIN eas e ON b.ea_id = e.id
            WHERE e.magic_number = ?
            ORDER BY b.upload_date DESC
            LIMIT 1
        """, (magic_number,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            raise HTTPException(
                status_code=404,
                detail=f"No backtest benchmark found for EA {magic_number}"
            )
        
        return {
            "success": True,
            "magic_number": magic_number,
            "symbol": row[6],
            "strategy_tag": row[7],
            "benchmark": {
                "profit_factor": row[0],
                "expected_payoff": row[1],
                "drawdown": row[2],
                "win_rate": row[3],
                "trade_count": row[4],
                "upload_date": row[5]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Benchmark retrieval error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get benchmark: {str(e)}")





@router.get("/chart-data/{symbol}")
async def get_chart_data(
    symbol: str,
    timeframe: str = Query(default="1H", description="Chart timeframe (1M, 5M, 15M, 1H, 4H, 1D)"),
    points: int = Query(default=50, description="Number of data points")
):
    """Get chart data for a symbol"""
    try:
        if not PRICE_SERVICE_AVAILABLE:
            # Return mock data if price service is not available
            return _generate_mock_chart_data(symbol, timeframe, points)
        
        # Get chart data from price service
        chart_data = await mt5_price_service.get_chart_data(symbol, timeframe, points)
        
        if chart_data:
            return chart_data.to_dict()
        else:
            # Fallback to mock data
            return _generate_mock_chart_data(symbol, timeframe, points)
            
    except Exception as e:
        # Fallback to mock data on error
        return _generate_mock_chart_data(symbol, timeframe, points)


@router.post("/ticker-data")
async def get_ticker_data(request: Dict[str, List[str]]):
    """Get real-time ticker data for multiple symbols"""
    try:
        symbols = request.get("symbols", [])
        if not symbols:
            raise HTTPException(status_code=400, detail="No symbols provided")
        
        if not PRICE_SERVICE_AVAILABLE:
            # Return mock ticker data if price service is not available
            mock_response = _generate_mock_ticker_data(symbols)
            return mock_response if isinstance(mock_response, dict) else {"data": mock_response}
        
        # Get real ticker data from price service
        ticker_data = []
        for symbol in symbols:
            price_data = mt5_price_service.get_current_price(symbol)
            if price_data:
                # Calculate change from previous price (simplified)
                change = 0.0  # Would need historical data for real change
                change_percent = 0.0
                
                ticker_data.append({
                    "symbol": symbol,
                    "price": (price_data.bid + price_data.ask) / 2,
                    "bid": price_data.bid,
                    "ask": price_data.ask,
                    "spread": price_data.spread,
                    "change": change,
                    "changePercent": change_percent,
                    "volume": price_data.volume,
                    "timestamp": price_data.timestamp.isoformat(),
                    "source": "mt5_real"
                })
            else:
                # Fallback for this symbol
                mock_response = _generate_mock_ticker_data([symbol])
                if isinstance(mock_response, dict) and 'data' in mock_response:
                    ticker_data.extend(mock_response['data'])
                else:
                    ticker_data.append(mock_response[0] if isinstance(mock_response, list) else mock_response)
        
        # Apply portfolio theme to real ticker data response
        portfolio_theme = {
            "tickerTheme": {
                "backgroundColor": "rgba(0, 0, 0, 0.95)",
                "glassEffect": {
                    "backdropFilter": "blur(25px)",
                    "border": "1px solid rgba(255, 255, 255, 0.08)",
                    "boxShadow": "0 4px 20px rgba(0, 0, 0, 0.8)"
                },
                "itemTheme": {
                    "background": "rgba(10, 10, 10, 0.9)",
                    "hoverBackground": "rgba(15, 15, 15, 0.95)",
                    "border": "1px solid rgba(255, 255, 255, 0.08)",
                    "borderRadius": "6px"
                },
                "colors": {
                    "positive": "#00ffaa",
                    "negative": "#ff4d99",
                    "neutral": "#00d4ff",
                    "text": "#ffffff",
                    "textSecondary": "#a6a6a6"
                },
                "animations": {
                    "scrollSpeed": "30s",
                    "glowPulse": True,
                    "hoverEffects": True
                }
            }
        }
        
        return {
            "success": True,
            "data": ticker_data,
            "count": len(ticker_data),
            "source": "mt5_real",
            "themeConfig": portfolio_theme
        }
        
    except Exception as e:
        # Fallback to mock data on error
        symbols = request.get("symbols", [])
        return _generate_mock_ticker_data(symbols)


@router.get("/current-prices")
async def get_current_prices():
    """Get current prices for all available symbols"""
    try:
        if not PRICE_SERVICE_AVAILABLE:
            # Return mock prices if price service is not available
            return {
                "prices": {
                    'EURUSD': 1.0847,
                    'GBPUSD': 1.2634,
                    'USDJPY': 149.82,
                    'USDCHF': 0.8756,
                    'AUDUSD': 0.6523,
                    'USDCAD': 1.3789,
                    'NZDUSD': 0.5987,
                    'XAUUSD': 2034.67
                },
                "source": "mock_fallback"
            }
        
        # Get real prices from price service
        price_cache = mt5_price_service.get_price_cache()
        prices = {}
        
        for symbol, price_data in price_cache.items():
            prices[symbol] = price_data.get('price', 0.0)
        
        return {
            "prices": prices,
            "source": "mt5_real"
        }
        
    except Exception as e:
        # Fallback to mock prices
        return {
            "prices": {
                'EURUSD': 1.0847,
                'GBPUSD': 1.2634,
                'USDJPY': 149.82,
                'USDCHF': 0.8756,
                'AUDUSD': 0.6523,
                'USDCAD': 1.3789,
                'NZDUSD': 0.5987,
                'XAUUSD': 2034.67
            },
            "source": "error_fallback"
        }


def _generate_mock_ticker_data(symbols: List[str]) -> List[Dict[str, Any]]:
    """Generate mock ticker data for symbols"""
    import random
    import math
    from datetime import datetime
    
    base_prices = {
        'EURUSD': 1.0847,
        'GBPUSD': 1.2634,
        'USDJPY': 149.82,
        'USDCHF': 0.8756,
        'AUDUSD': 0.6523,
        'USDCAD': 1.3789,
        'NZDUSD': 0.5987,
        'XAUUSD': 2034.67
    }
    
    ticker_data = []
    current_time = datetime.now()
    
    for symbol in symbols:
        base_price = base_prices.get(symbol.upper(), 1.0000)
        
        # Generate realistic price movement
        symbol_seed = sum(ord(c) for c in symbol)
        time_factor = math.sin(current_time.timestamp() / 300)  # 5-minute cycles
        
        # Price variation
        variation = (math.sin(symbol_seed / 100) * 0.8 + time_factor * 0.3) / 100
        current_price = base_price * (1 + variation)
        
        # Calculate spread
        if symbol.upper() == 'XAUUSD':
            spread = 0.5
            decimal_places = 2
        elif symbol.upper() in ['USDJPY', 'EURJPY', 'GBPJPY']:
            spread = 0.002
            decimal_places = 3
        else:
            spread = 0.00002
            decimal_places = 5
        
        bid = round(current_price - spread/2, decimal_places)
        ask = round(current_price + spread/2, decimal_places)
        
        # Calculate change
        change = base_price * variation
        change_percent = variation * 100
        
        # Generate volume
        volume = random.randint(50000, 200000)
        
        # Apply portfolio theme colors based on performance
        theme_color = "#00ffaa" if change >= 0 else "#ff4d99"
        
        ticker_data.append({
            "symbol": symbol,
            "price": round(current_price, decimal_places),
            "bid": bid,
            "ask": ask,
            "spread": round(spread, decimal_places),
            "change": round(change, decimal_places),
            "changePercent": round(change_percent, 2),
            "volume": volume,
            "timestamp": current_time.isoformat(),
            "source": "mock_fallback",
            # Portfolio analytics theme data
            "themeColor": theme_color,
            "glowEffect": f"0 0 8px {theme_color}50",
            "trendIndicator": 'up' if change >= 0 else 'down',
            "portfolioTheme": {
                "background": "rgba(10, 10, 10, 0.9)",
                "hoverBackground": "rgba(15, 15, 15, 0.95)",
                "border": "1px solid rgba(255, 255, 255, 0.08)",
                "textColor": "#ffffff",
                "accentColor": theme_color
            }
        })
    
    # Apply overall portfolio theme to ticker response
    portfolio_theme = {
        "tickerTheme": {
            "backgroundColor": "rgba(0, 0, 0, 0.95)",
            "glassEffect": {
                "backdropFilter": "blur(25px)",
                "border": "1px solid rgba(255, 255, 255, 0.08)",
                "boxShadow": "0 4px 20px rgba(0, 0, 0, 0.8)"
            },
            "itemTheme": {
                "background": "rgba(10, 10, 10, 0.9)",
                "hoverBackground": "rgba(15, 15, 15, 0.95)",
                "border": "1px solid rgba(255, 255, 255, 0.08)",
                "borderRadius": "6px"
            },
            "colors": {
                "positive": "#00ffaa",
                "negative": "#ff4d99",
                "neutral": "#00d4ff",
                "text": "#ffffff",
                "textSecondary": "#a6a6a6"
            },
            "animations": {
                "scrollSpeed": "30s",
                "glowPulse": True,
                "hoverEffects": True
            }
        }
    }
    
    return {
        "data": ticker_data,
        "count": len(ticker_data),
        "source": "mock_fallback",
        "themeConfig": portfolio_theme
    }


def _generate_mock_chart_data(symbol: str, timeframe: str, points: int) -> Dict[str, Any]:
    """Generate realistic mock chart data as fallback"""
    import time
    import random
    import math
    from datetime import datetime, timedelta
    
    base_prices = {
        'EURUSD': 1.0847,
        'GBPUSD': 1.2634,
        'USDJPY': 149.82,
        'USDCHF': 0.8756,
        'AUDUSD': 0.6523,
        'USDCAD': 1.3789,
        'NZDUSD': 0.5987,
        'XAUUSD': 2034.67
    }
    
    base_price = base_prices.get(symbol.upper(), 1.0000)
    data = []
    price = base_price
    now = datetime.now()
    
    # Timeframe intervals in minutes
    intervals = {
        '1M': 1,
        '5M': 5,
        '15M': 15,
        '1H': 60,
        '4H': 240,
        '1D': 1440
    }
    
    interval_minutes = intervals.get(timeframe, 60)
    
    # Symbol-specific parameters
    if symbol.upper() == 'XAUUSD':
        volatility = 3.0
        decimal_places = 2
        max_deviation = base_price * 0.05
    elif symbol.upper() in ['USDJPY', 'EURJPY', 'GBPJPY']:
        volatility = 0.08
        decimal_places = 3
        max_deviation = base_price * 0.02
    else:
        volatility = 0.0012
        decimal_places = 5
        max_deviation = base_price * 0.02
    
    # Use symbol hash for consistent randomness per symbol
    random.seed(hash(symbol.upper()) % 10000)
    
    for i in range(points):
        timestamp = now - timedelta(minutes=(points - i - 1) * interval_minutes)
        
        # Generate realistic price movement
        time_factor = (i + time.time()) / 100
        
        # Random walk with mean reversion
        random_change = random.gauss(0, volatility * 0.3)
        mean_reversion = (base_price - price) * 0.05
        trend = math.sin(time_factor / 50) * volatility * 0.2
        
        # Combine factors
        price_change = random_change + mean_reversion + trend
        
        # Apply change but keep within bounds
        new_price = price + price_change
        if abs(new_price - base_price) > max_deviation:
            new_price = base_price + (new_price - base_price) * 0.7
        
        # Generate OHLC for this candle
        open_price = price
        close_price = new_price
        
        # Generate high and low with realistic behavior
        candle_range = abs(close_price - open_price) + volatility * random.uniform(0.2, 0.8)
        
        high = max(open_price, close_price) + candle_range * random.uniform(0.1, 0.6)
        low = min(open_price, close_price) - candle_range * random.uniform(0.1, 0.6)
        
        # Ensure proper OHLC relationships
        high = max(high, open_price, close_price)
        low = min(low, open_price, close_price)
        
        # Round to appropriate decimal places
        open_price = round(open_price, decimal_places)
        high = round(high, decimal_places)
        low = round(low, decimal_places)
        close_price = round(close_price, decimal_places)
        
        # Generate realistic volume
        base_volume = 50000
        volatility_factor = abs(close_price - open_price) / (volatility * 2) + 0.5
        time_factor_vol = 1 + 0.3 * math.sin(time_factor / 10)
        volume = int(base_volume * volatility_factor * time_factor_vol * random.uniform(0.7, 1.5))
        
        data.append({
            'timestamp': timestamp.isoformat(),
            'open': open_price,
            'high': high,
            'low': low,
            'close': close_price,
            'volume': volume
        })
        
        # Update price for next iteration
        price = close_price
    
    # Reset random seed to avoid affecting other operations
    random.seed()
    
    price_change = data[-1]['close'] - data[0]['close'] if len(data) > 1 else 0.0
    
    # Apply portfolio analytics theme to chart data
    theme_config = _get_portfolio_chart_theme(symbol, price_change)
    
    return {
        'symbol': symbol.upper(),
        'timeframe': timeframe,
        'data': data,
        'currentPrice': data[-1]['close'],  # Use camelCase for frontend consistency
        'current_price': data[-1]['close'],  # Keep snake_case for backward compatibility
        'priceChange': round(price_change, decimal_places),  # Use camelCase for frontend consistency
        'price_change': round(price_change, decimal_places),  # Keep snake_case for backward compatibility
        'lastUpdate': now.isoformat(),  # Use camelCase for frontend consistency
        'last_update': now.isoformat(),  # Keep snake_case for backward compatibility
        'source': 'mock_data',
        'themeConfig': theme_config  # Portfolio analytics theme configuration
    }


def _apply_portfolio_theme_to_ea_status(status: EAStatusUpdate) -> Dict[str, Any]:
    """Apply portfolio analytics theme styling to EA status data"""
    
    # Determine theme colors based on EA performance
    profit_color = "#00ffaa" if status.current_profit >= 0 else "#ff4d99"  # Success/Error colors from theme
    status_color = "#00d4ff" if not status.is_paused else "#faad14"  # Primary/Warning colors
    
    # Calculate performance indicators for theme
    performance_score = 0
    if status.performance_metrics:
        profit_factor = status.performance_metrics.get("profit_factor", 0)
        if profit_factor > 1.5:
            performance_score = 3  # Excellent
        elif profit_factor > 1.2:
            performance_score = 2  # Good
        elif profit_factor > 1.0:
            performance_score = 1  # Fair
        else:
            performance_score = 0  # Poor
    
    # Theme-specific styling data
    theme_data = {
        "glassEffect": {
            "background": "rgba(17, 17, 17, 0.88)",
            "backdropFilter": "blur(18px)",
            "border": f"1px solid {status_color}40",  # 40 = 25% opacity
            "borderRadius": "14px",
            "boxShadow": f"0 10px 35px rgba(0, 0, 0, 0.65), inset 0 1px 0 rgba(255, 255, 255, 0.1), 0 0 20px {status_color}20"
        },
        "statusIndicator": {
            "color": status_color,
            "glowEffect": f"0 0 8px {status_color}50",
            "pulseAnimation": not status.is_paused
        },
        "profitIndicator": {
            "color": profit_color,
            "glowEffect": f"0 0 8px {profit_color}50",
            "gradient": f"linear-gradient(135deg, {profit_color} 0%, rgba(255, 255, 255, 0.2) 50%, {profit_color}cc 100%)"
        },
        "performanceTheme": {
            "score": performance_score,
            "badgeColor": ["#ff4d99", "#faad14", "#00d4ff", "#00ffaa"][performance_score],
            "backgroundGradient": f"linear-gradient(135deg, rgba(20, 20, 20, 0.9) 0%, rgba({_hex_to_rgb(status_color)}, 0.05) 100%)"
        },
        "moduleStatusTheme": {
            "activeColor": "#00ffaa",
            "inactiveColor": "#666666",
            "warningColor": "#faad14",
            "errorColor": "#ff4d99",
            "glassBackground": "rgba(38, 38, 38, 0.8)"
        },
        "chartTheme": {
            "primaryColor": "#00d4ff",
            "secondaryColor": "#4de0ff",
            "gridColor": "rgba(255, 255, 255, 0.1)",
            "backgroundColor": "rgba(20, 20, 20, 0.6)"
        }
    }
    
    return theme_data


def _get_portfolio_chart_theme(symbol: str, price_change: float) -> Dict[str, Any]:
    """Get portfolio analytics theme configuration for charts"""
    
    # Determine trend color based on price change
    trend_color = "#00ffaa" if price_change >= 0 else "#ff4d99"
    
    return {
        "chartTheme": {
            "backgroundColor": "rgba(20, 20, 20, 0.6)",
            "gridColor": "rgba(255, 255, 255, 0.1)",
            "candleColors": {
                "up": "#00ffaa",  # Success green from theme
                "down": "#ff4d99",  # Error red from theme
                "wick": "#ffffff",
                "border": "rgba(255, 255, 255, 0.3)"
            },
            "volumeColor": "#00d4ff40",  # Primary cyan with transparency
            "trendColor": trend_color,
            "glassEffect": {
                "background": "rgba(20, 20, 20, 0.6)",
                "backdropFilter": "blur(15px)",
                "border": "1px solid rgba(255, 255, 255, 0.08)",
                "borderRadius": "12px",
                "boxShadow": "0 8px 32px rgba(0, 0, 0, 0.7), inset 0 1px 0 rgba(255, 255, 255, 0.08)"
            },
            "indicators": {
                "ma": "#00d4ff",  # Primary cyan
                "ema": "#4de0ff",  # Light cyan
                "bollinger": "#faad14",  # Warning yellow
                "rsi": "#ff8c00"  # Orange accent
            },
            "axes": {
                "color": "rgba(255, 255, 255, 0.6)",
                "gridColor": "rgba(255, 255, 255, 0.1)",
                "labelColor": "#a6a6a6"
            }
        },
        "animations": {
            "enabled": True,
            "duration": 300,
            "easing": "cubic-bezier(0.4, 0, 0.2, 1)",
            "glowPulse": True
        },
        "interactivity": {
            "hoverEffects": True,
            "glowOnHover": True,
            "tooltipTheme": {
                "background": "rgba(15, 15, 15, 0.95)",
                "border": "1px solid rgba(255, 255, 255, 0.12)",
                "color": "#ffffff",
                "backdropFilter": "blur(20px)"
            }
        }
    }


def _hex_to_rgb(hex_color: str) -> str:
    """Convert hex color to RGB values for CSS rgba"""
    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 6:
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return f"{r}, {g}, {b}"
    return "0, 212, 255"  # Default to primary cyan