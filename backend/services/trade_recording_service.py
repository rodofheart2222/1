"""
Trade Recording Service

Comprehensive service for recording trades from dashboard commands through MT5 execution
and back to dashboard display. Handles the complete trade lifecycle with proper logging.
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

# Handle imports for both running from root and from backend directory
try:
    from backend.database.connection import DatabaseManager
except ImportError:
    from database.connection import DatabaseManager
from sqlalchemy import text, desc
from sqlalchemy.orm import Session

# For now, we'll work without the model imports to avoid import issues
# from models.trade import Trade
# from models.ea import EA, EAStatus  
# from models.command import Command

logger = logging.getLogger(__name__)


class TradeStatus(Enum):
    """Trade status enumeration"""
    PENDING = "pending"
    FILLED = "filled"
    CANCELLED = "cancelled"
    CLOSED = "closed"
    REJECTED = "rejected"


class TradeType(Enum):
    """Trade type enumeration"""
    BUY = "BUY"
    SELL = "SELL"
    BUY_LIMIT = "BUY_LIMIT"
    SELL_LIMIT = "SELL_LIMIT"
    BUY_STOP = "BUY_STOP"
    SELL_STOP = "SELL_STOP"


@dataclass
class EARecord:
    """EA tracking record"""
    magic_number: int
    ea_name: str
    symbol: str
    timeframe: str
    status: str = "active"  # active, inactive, error
    last_heartbeat: datetime = None
    account_number: Optional[str] = None
    broker: Optional[str] = None
    balance: float = 0.0
    equity: float = 0.0
    margin: float = 0.0
    free_margin: float = 0.0
    margin_level: float = 0.0
    total_trades: int = 0
    active_trades: int = 0
    total_profit: float = 0.0
    
    def __post_init__(self):
        if self.last_heartbeat is None:
            self.last_heartbeat = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'magic_number': self.magic_number,
            'ea_name': self.ea_name,
            'symbol': self.symbol,
            'timeframe': self.timeframe,
            'status': self.status,
            'last_heartbeat': self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            'account_number': self.account_number,
            'broker': self.broker,
            'balance': self.balance,
            'equity': self.equity,
            'margin': self.margin,
            'free_margin': self.free_margin,
            'margin_level': self.margin_level,
            'total_trades': self.total_trades,
            'active_trades': self.active_trades,
            'total_profit': self.total_profit
        }


@dataclass
class TradeRecord:
    """Complete trade record with all lifecycle information"""
    trade_id: str
    ea_id: int
    magic_number: int
    symbol: str
    trade_type: TradeType
    volume: float
    requested_price: float
    actual_price: Optional[float] = None
    sl: Optional[float] = None
    tp: Optional[float] = None
    status: TradeStatus = TradeStatus.PENDING
    profit: float = 0.0
    commission: float = 0.0
    swap: float = 0.0
    comment: str = ""
    
    # Timestamps
    request_time: datetime = None
    fill_time: Optional[datetime] = None
    close_time: Optional[datetime] = None
    
    # Dashboard tracking
    dashboard_command_id: Optional[str] = None
    mt5_ticket: Optional[int] = None
    
    # Risk management
    risk_percent: float = 0.0
    account_balance: float = 0.0
    position_size_usd: float = 0.0
    
    def __post_init__(self):
        if self.request_time is None:
            self.request_time = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'trade_id': self.trade_id,
            'ea_id': self.ea_id,
            'magic_number': self.magic_number,
            'symbol': self.symbol,
            'trade_type': self.trade_type.value,
            'volume': self.volume,
            'requested_price': self.requested_price,
            'actual_price': self.actual_price,
            'sl': self.sl,
            'tp': self.tp,
            'status': self.status.value,
            'profit': self.profit,
            'commission': self.commission,
            'swap': self.swap,
            'comment': self.comment,
            'request_time': self.request_time.isoformat() if self.request_time else None,
            'fill_time': self.fill_time.isoformat() if self.fill_time else None,
            'close_time': self.close_time.isoformat() if self.close_time else None,
            'dashboard_command_id': self.dashboard_command_id,
            'mt5_ticket': self.mt5_ticket,
            'risk_percent': self.risk_percent,
            'account_balance': self.account_balance,
            'position_size_usd': self.position_size_usd
        }
    
    def to_journal_format(self) -> str:
        """Format trade for journal display"""
        action = "Buy" if "BUY" in self.trade_type.value else "Sell"
        order_type = "[LIMIT]" if "LIMIT" in self.trade_type.value else "[STOP]" if "STOP" in self.trade_type.value else "[MARKET]"
        
        if self.status == TradeStatus.FILLED and self.actual_price:
            price_info = f"@ {self.actual_price}"
        else:
            price_info = f"@ {self.requested_price} (Pending)"
        
        if self.status == TradeStatus.CLOSED and self.profit != 0:
            return f"{order_type} {self.symbol} {action} {self.volume} {price_info} -> Closed (P/L: {self.profit:.2f})"
        else:
            return f"{order_type} {self.symbol} {action} {self.volume} {price_info}"


class TradeRecordingService:
    """Service for comprehensive trade recording and lifecycle management"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.active_trades: Dict[str, TradeRecord] = {}
        self.trade_history: List[TradeRecord] = []
        
        # EA tracking
        self.registered_eas: Dict[int, EARecord] = {}  # magic_number -> EARecord
        self.ea_heartbeat_timeout = 300  # 5 minutes
        
        # WebSocket server for real-time updates
        self.websocket_server = None
        try:
            from backend.services.websocket_server import get_websocket_server
            self.websocket_server = get_websocket_server()
        except ImportError:
            try:
                from services.websocket_server import get_websocket_server
                self.websocket_server = get_websocket_server()
            except ImportError:
                logger.warning("WebSocket server not available - real-time updates disabled")
    
    async def register_ea(self, ea_data: Dict[str, Any]) -> bool:
        """
        Register or update an EA in the system
        
        Args:
            ea_data: EA information including magic_number, name, symbol, etc.
            
        Returns:
            True if successfully registered
        """
        try:
            magic_number = ea_data.get('magic_number')
            if not magic_number:
                raise ValueError("Magic number is required for EA registration")
            
            ea_record = EARecord(
                magic_number=magic_number,
                ea_name=ea_data.get('ea_name', f'EA_{magic_number}'),
                symbol=ea_data.get('symbol', 'UNKNOWN'),
                timeframe=ea_data.get('timeframe', 'M1'),
                account_number=ea_data.get('account_number'),
                broker=ea_data.get('broker'),
                balance=float(ea_data.get('balance', 0.0)),
                equity=float(ea_data.get('equity', 0.0)),
                margin=float(ea_data.get('margin', 0.0)),
                free_margin=float(ea_data.get('free_margin', 0.0)),
                margin_level=float(ea_data.get('margin_level', 0.0))
            )
            
            # Update existing or add new
            if magic_number in self.registered_eas:
                existing = self.registered_eas[magic_number]
                existing.last_heartbeat = datetime.now()
                existing.status = "active"
                existing.balance = ea_record.balance
                existing.equity = ea_record.equity
                existing.margin = ea_record.margin
                existing.free_margin = ea_record.free_margin
                existing.margin_level = ea_record.margin_level
                logger.info(f"EA {magic_number} ({existing.ea_name}) heartbeat updated")
            else:
                self.registered_eas[magic_number] = ea_record
                logger.info(f"EA registered: {ea_record.ea_name} (Magic: {magic_number}) on {ea_record.symbol}")
            
            # Update EA statistics
            await self._update_ea_statistics(magic_number)
            
            # Broadcast EA update
            await self._broadcast_ea_update(self.registered_eas[magic_number], "registered")
            
            return True
            
        except Exception as e:
            logger.error(f"Error registering EA: {e}")
            return False
    
    async def update_ea_heartbeat(self, magic_number: int, account_data: Optional[Dict[str, Any]] = None) -> bool:
        """
        Update EA heartbeat and account information
        
        Args:
            magic_number: EA magic number
            account_data: Optional account information update
            
        Returns:
            True if successfully updated
        """
        try:
            if magic_number not in self.registered_eas:
                logger.warning(f"Heartbeat received for unregistered EA: {magic_number}")
                # Auto-register with minimal info
                await self.register_ea({
                    'magic_number': magic_number,
                    'ea_name': f'EA_{magic_number}',
                    'symbol': 'AUTO_DETECTED'
                })
                return True
            
            ea_record = self.registered_eas[magic_number]
            ea_record.last_heartbeat = datetime.now()
            ea_record.status = "active"
            
            # Update account data if provided
            if account_data:
                ea_record.balance = float(account_data.get('balance', ea_record.balance))
                ea_record.equity = float(account_data.get('equity', ea_record.equity))
                ea_record.margin = float(account_data.get('margin', ea_record.margin))
                ea_record.free_margin = float(account_data.get('free_margin', ea_record.free_margin))
                ea_record.margin_level = float(account_data.get('margin_level', ea_record.margin_level))
            
            # Update statistics
            await self._update_ea_statistics(magic_number)
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating EA heartbeat: {e}")
            return False
    
    def get_all_eas(self) -> List[EARecord]:
        """Get all registered EAs"""
        return list(self.registered_eas.values())
    
    def get_active_eas(self) -> List[EARecord]:
        """Get only active EAs (recent heartbeat)"""
        now = datetime.now()
        active_eas = []
        
        for ea in self.registered_eas.values():
            if ea.last_heartbeat:
                time_diff = (now - ea.last_heartbeat).total_seconds()
                if time_diff <= self.ea_heartbeat_timeout:
                    ea.status = "active"
                    active_eas.append(ea)
                else:
                    ea.status = "inactive"
        
        return active_eas
    
    def get_ea_by_magic(self, magic_number: int) -> Optional[EARecord]:
        """Get EA by magic number"""
        return self.registered_eas.get(magic_number)
    
    async def _update_ea_statistics(self, magic_number: int):
        """Update EA trade statistics"""
        try:
            if magic_number not in self.registered_eas:
                return
            
            ea_record = self.registered_eas[magic_number]
            
            # Count active trades
            active_count = len([t for t in self.active_trades.values() if t.magic_number == magic_number])
            
            # Count total trades and calculate profit
            ea_history = [t for t in self.trade_history if t.magic_number == magic_number]
            total_trades = len(ea_history)
            total_profit = sum(t.profit for t in ea_history if t.status == TradeStatus.CLOSED)
            
            # Update EA record
            ea_record.active_trades = active_count
            ea_record.total_trades = total_trades
            ea_record.total_profit = total_profit
            
        except Exception as e:
            logger.error(f"Error updating EA statistics: {e}")

    async def record_dashboard_command(self, command_data: Dict[str, Any]) -> str:
        """
        Record a trade command from the dashboard
        
        Args:
            command_data: Command data from dashboard
            
        Returns:
            Trade ID for tracking
        """
        try:
            # Generate unique trade ID
            trade_id = f"trade_{int(datetime.now().timestamp())}_{command_data.get('magic_number', 0)}"
            
            # Extract trade information
            params = command_data.get('parameters', {})
            
            trade_record = TradeRecord(
                trade_id=trade_id,
                ea_id=0,  # Will be resolved later
                magic_number=command_data.get('magic_number', 0),
                symbol=params.get('symbol', 'UNKNOWN'),
                trade_type=TradeType(params.get('order_type', 'BUY')),
                volume=float(params.get('volume', 0.01)),
                requested_price=float(params.get('price', 0.0)),
                sl=float(params.get('sl')) if params.get('sl') else None,
                tp=float(params.get('tp')) if params.get('tp') else None,
                comment=params.get('comment', ''),
                dashboard_command_id=command_data.get('command_id'),
                risk_percent=float(params.get('risk_percent', 0.0)),
                account_balance=float(params.get('account_balance', 0.0))
            )
            
            # Store in active trades
            self.active_trades[trade_id] = trade_record
            
            # Log the command
            logger.info(f"[ENTRY] Dashboard command recorded: {trade_record.to_journal_format()}")
            
            # Store in database
            await self._store_trade_record(trade_record)
            
            # Broadcast to dashboard
            await self._broadcast_trade_update(trade_record, "command_recorded")
            
            return trade_id
            
        except Exception as e:
            logger.error(f"Error recording dashboard command: {e}")
            raise
    
    async def record_mt5_fill(self, fill_data: Dict[str, Any]) -> bool:
        """
        Record trade fill from MT5
        
        Args:
            fill_data: Fill data from MT5 EA
            
        Returns:
            True if successfully recorded
        """
        try:
            magic_number = fill_data.get('magic_number')
            mt5_ticket = fill_data.get('ticket')
            symbol = fill_data.get('symbol')
            
            # Auto-register EA if not already registered
            if magic_number not in self.registered_eas:
                await self.register_ea({
                    'magic_number': magic_number,
                    'ea_name': f'EA_{magic_number}',
                    'symbol': symbol,
                    'timeframe': 'AUTO_DETECTED',
                    'balance': float(fill_data.get('account_balance', 0.0)),
                    'equity': float(fill_data.get('account_equity', 0.0))
                })
            else:
                # Update heartbeat
                await self.update_ea_heartbeat(magic_number, {
                    'balance': float(fill_data.get('account_balance', 0.0)),
                    'equity': float(fill_data.get('account_equity', 0.0))
                })
            
            # Find matching trade record
            trade_record = None
            for trade_id, record in self.active_trades.items():
                if (record.magic_number == magic_number and 
                    record.symbol == symbol and 
                    record.status == TradeStatus.PENDING):
                    trade_record = record
                    break
            
            if not trade_record:
                # Create new trade record for fills without dashboard command
                trade_id = f"mt5_fill_{int(datetime.now().timestamp())}_{magic_number}"
                trade_record = TradeRecord(
                    trade_id=trade_id,
                    ea_id=0,  # Will be resolved
                    magic_number=magic_number,
                    symbol=symbol,
                    trade_type=TradeType(fill_data.get('order_type', 'BUY')),
                    volume=float(fill_data.get('volume', 0.0)),
                    requested_price=float(fill_data.get('price', 0.0)),
                    actual_price=float(fill_data.get('price', 0.0)),
                    sl=float(fill_data.get('sl')) if fill_data.get('sl') else None,
                    tp=float(fill_data.get('tp')) if fill_data.get('tp') else None,
                    comment=fill_data.get('comment', ''),
                    mt5_ticket=mt5_ticket
                )
                self.active_trades[trade_id] = trade_record
            
            # Update with fill information
            trade_record.status = TradeStatus.FILLED
            trade_record.actual_price = float(fill_data.get('price', trade_record.requested_price))
            trade_record.fill_time = datetime.now()
            trade_record.mt5_ticket = mt5_ticket
            trade_record.commission = float(fill_data.get('commission', 0.0))
            trade_record.swap = float(fill_data.get('swap', 0.0))
            
            # Calculate position size in USD
            if trade_record.actual_price > 0:
                trade_record.position_size_usd = trade_record.volume * trade_record.actual_price * 100000
            
            # Log the fill
            logger.info(f"[ENTRY] Order filled: {trade_record.to_journal_format()}")
            
            # Log SL/TP placement
            if trade_record.sl:
                logger.info(f"[SL] Stop Loss clamp activated at {trade_record.sl}")
            if trade_record.tp:
                logger.info(f"[TP] Take Profit placed at {trade_record.tp}")
            
            # Calculate and log Risk/Reward ratio
            if trade_record.sl and trade_record.tp and trade_record.actual_price:
                risk_pips = abs(trade_record.actual_price - trade_record.sl)
                reward_pips = abs(trade_record.tp - trade_record.actual_price)
                if risk_pips > 0:
                    rr_ratio = reward_pips / risk_pips
                    logger.info(f"[RR] Risk/Reward ratio: 1:{rr_ratio:.1f}")
            
            # Store in database
            await self._store_trade_record(trade_record)
            
            # Broadcast to dashboard
            await self._broadcast_trade_update(trade_record, "filled")
            
            return True
            
        except Exception as e:
            logger.error(f"Error recording MT5 fill: {e}")
            return False
    
    async def record_trade_close(self, close_data: Dict[str, Any]) -> bool:
        """
        Record trade close from MT5 or dashboard
        
        Args:
            close_data: Close data
            
        Returns:
            True if successfully recorded
        """
        try:
            magic_number = close_data.get('magic_number')
            mt5_ticket = close_data.get('ticket')
            symbol = close_data.get('symbol')
            
            # Find matching trade record
            trade_record = None
            for trade_id, record in self.active_trades.items():
                if ((record.magic_number == magic_number and record.symbol == symbol) or
                    (mt5_ticket and record.mt5_ticket == mt5_ticket)):
                    trade_record = record
                    break
            
            if not trade_record:
                logger.warning(f"No matching trade found for close: magic={magic_number}, ticket={mt5_ticket}")
                return False
            
            # Update with close information
            trade_record.status = TradeStatus.CLOSED
            trade_record.close_time = datetime.now()
            trade_record.profit = float(close_data.get('profit', 0.0))
            trade_record.commission += float(close_data.get('commission', 0.0))
            trade_record.swap += float(close_data.get('swap', 0.0))
            
            # Calculate net profit
            net_profit = trade_record.profit - trade_record.commission - trade_record.swap
            
            # Log the close
            close_price = close_data.get('close_price', 'Market')
            logger.info(f"[CLOSE] Position closed: {trade_record.symbol} @ {close_price} (P/L: {net_profit:.2f})")
            
            # Move to history
            self.trade_history.append(trade_record)
            if trade_record.trade_id in self.active_trades:
                del self.active_trades[trade_record.trade_id]
            
            # Store in database
            await self._store_trade_record(trade_record)
            
            # Broadcast to dashboard
            await self._broadcast_trade_update(trade_record, "closed")
            
            return True
            
        except Exception as e:
            logger.error(f"Error recording trade close: {e}")
            return False
    
    async def record_trade_cancellation(self, cancel_data: Dict[str, Any]) -> bool:
        """
        Record trade cancellation
        
        Args:
            cancel_data: Cancellation data
            
        Returns:
            True if successfully recorded
        """
        try:
            magic_number = cancel_data.get('magic_number')
            order_id = cancel_data.get('order_id')
            
            # Find matching trade record
            trade_record = None
            for trade_id, record in self.active_trades.items():
                if (record.magic_number == magic_number and 
                    (record.trade_id == order_id or record.dashboard_command_id == order_id)):
                    trade_record = record
                    break
            
            if not trade_record:
                logger.warning(f"No matching trade found for cancellation: magic={magic_number}, order={order_id}")
                return False
            
            # Update status
            trade_record.status = TradeStatus.CANCELLED
            trade_record.close_time = datetime.now()
            
            # Log the cancellation
            logger.info(f"[CANCEL] Order cancelled: {trade_record.to_journal_format()}")
            
            # Move to history
            self.trade_history.append(trade_record)
            if trade_record.trade_id in self.active_trades:
                del self.active_trades[trade_record.trade_id]
            
            # Store in database
            await self._store_trade_record(trade_record)
            
            # Broadcast to dashboard
            await self._broadcast_trade_update(trade_record, "cancelled")
            
            return True
            
        except Exception as e:
            logger.error(f"Error recording trade cancellation: {e}")
            return False
    
    def get_active_trades(self, magic_number: Optional[int] = None) -> List[TradeRecord]:
        """Get active trades, optionally filtered by magic number"""
        if magic_number:
            return [trade for trade in self.active_trades.values() if trade.magic_number == magic_number]
        return list(self.active_trades.values())
    
    def get_trade_history(self, magic_number: Optional[int] = None, limit: int = 50) -> List[TradeRecord]:
        """Get trade history, optionally filtered by magic number"""
        history = self.trade_history
        if magic_number:
            history = [trade for trade in history if trade.magic_number == magic_number]
        
        # Sort by close time (most recent first) and limit
        history.sort(key=lambda x: x.close_time or x.request_time, reverse=True)
        return history[:limit]
    
    def get_trade_by_id(self, trade_id: str) -> Optional[TradeRecord]:
        """Get trade by ID from active trades or history"""
        if trade_id in self.active_trades:
            return self.active_trades[trade_id]
        
        for trade in self.trade_history:
            if trade.trade_id == trade_id:
                return trade
        
        return None
    
    def get_ea_performance_summary(self, magic_number: int) -> Dict[str, Any]:
        """Get performance summary for an EA based on recorded trades"""
        try:
            # Get all trades for this EA
            all_trades = []
            all_trades.extend([t for t in self.active_trades.values() if t.magic_number == magic_number])
            all_trades.extend([t for t in self.trade_history if t.magic_number == magic_number])
            
            # Filter closed trades for performance calculation
            closed_trades = [t for t in all_trades if t.status == TradeStatus.CLOSED]
            
            if not closed_trades:
                return {
                    'total_trades': 0,
                    'open_trades': len([t for t in all_trades if t.status == TradeStatus.FILLED]),
                    'pending_trades': len([t for t in all_trades if t.status == TradeStatus.PENDING]),
                    'total_profit': 0.0,
                    'profit_factor': 0.0,
                    'win_rate': 0.0,
                    'expected_payoff': 0.0,
                    'largest_win': 0.0,
                    'largest_loss': 0.0
                }
            
            # Calculate metrics
            total_profit = sum(t.profit for t in closed_trades)
            winning_trades = [t for t in closed_trades if t.profit > 0]
            losing_trades = [t for t in closed_trades if t.profit < 0]
            
            gross_profit = sum(t.profit for t in winning_trades) if winning_trades else 0
            gross_loss = abs(sum(t.profit for t in losing_trades)) if losing_trades else 0
            
            profit_factor = gross_profit / gross_loss if gross_loss > 0 else gross_profit
            win_rate = (len(winning_trades) / len(closed_trades)) * 100 if closed_trades else 0
            expected_payoff = total_profit / len(closed_trades) if closed_trades else 0
            
            largest_win = max((t.profit for t in winning_trades), default=0.0)
            largest_loss = min((t.profit for t in losing_trades), default=0.0)
            
            return {
                'total_trades': len(closed_trades),
                'open_trades': len([t for t in all_trades if t.status == TradeStatus.FILLED]),
                'pending_trades': len([t for t in all_trades if t.status == TradeStatus.PENDING]),
                'total_profit': round(total_profit, 2),
                'profit_factor': round(profit_factor, 2),
                'win_rate': round(win_rate, 2),
                'expected_payoff': round(expected_payoff, 2),
                'largest_win': round(largest_win, 2),
                'largest_loss': round(largest_loss, 2),
                'gross_profit': round(gross_profit, 2),
                'gross_loss': round(gross_loss, 2)
            }
            
        except Exception as e:
            logger.error(f"Error calculating EA performance summary: {e}")
            return {}
    
    def get_trade_journal(self, magic_number: Optional[int] = None, limit: int = 20) -> List[str]:
        """Get formatted trade journal entries"""
        try:
            # Get recent trades
            all_trades = []
            all_trades.extend(self.active_trades.values())
            all_trades.extend(self.trade_history)
            
            if magic_number:
                all_trades = [t for t in all_trades if t.magic_number == magic_number]
            
            # Sort by most recent activity
            all_trades.sort(key=lambda x: x.close_time or x.fill_time or x.request_time, reverse=True)
            
            # Format as journal entries
            journal_entries = []
            for trade in all_trades[:limit]:
                journal_entries.append(trade.to_journal_format())
            
            return journal_entries
            
        except Exception as e:
            logger.error(f"Error generating trade journal: {e}")
            return []
    
    async def _store_trade_record(self, trade_record: TradeRecord):
        """Store trade record in database"""
        try:
            # Store in database using direct SQL for now
            # This avoids model import issues while providing actual persistence
            
            import sqlite3
            from config.environment import Config
            
            db_path = Config.get_db_path()
            
            # Ensure directory exists
            from pathlib import Path
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
            
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                # Create table if it doesn't exist
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS trade_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        trade_id TEXT UNIQUE NOT NULL,
                        ea_id INTEGER,
                        magic_number INTEGER NOT NULL,
                        symbol TEXT NOT NULL,
                        trade_type TEXT NOT NULL,
                        volume REAL NOT NULL,
                        requested_price REAL,
                        actual_price REAL,
                        sl REAL,
                        tp REAL,
                        status TEXT NOT NULL,
                        profit REAL DEFAULT 0.0,
                        commission REAL DEFAULT 0.0,
                        swap REAL DEFAULT 0.0,
                        comment TEXT,
                        request_time TEXT,
                        fill_time TEXT,
                        close_time TEXT,
                        dashboard_command_id TEXT,
                        mt5_ticket INTEGER,
                        risk_percent REAL DEFAULT 0.0,
                        account_balance REAL DEFAULT 0.0,
                        position_size_usd REAL DEFAULT 0.0,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Insert or update trade record
                cursor.execute("""
                    INSERT OR REPLACE INTO trade_records (
                        trade_id, ea_id, magic_number, symbol, trade_type, volume,
                        requested_price, actual_price, sl, tp, status, profit,
                        commission, swap, comment, request_time, fill_time, close_time,
                        dashboard_command_id, mt5_ticket, risk_percent, account_balance,
                        position_size_usd
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    trade_record.trade_id,
                    trade_record.ea_id,
                    trade_record.magic_number,
                    trade_record.symbol,
                    trade_record.trade_type.value,
                    trade_record.volume,
                    trade_record.requested_price,
                    trade_record.actual_price,
                    trade_record.sl,
                    trade_record.tp,
                    trade_record.status.value,
                    trade_record.profit,
                    trade_record.commission,
                    trade_record.swap,
                    trade_record.comment,
                    trade_record.request_time.isoformat() if trade_record.request_time else None,
                    trade_record.fill_time.isoformat() if trade_record.fill_time else None,
                    trade_record.close_time.isoformat() if trade_record.close_time else None,
                    trade_record.dashboard_command_id,
                    trade_record.mt5_ticket,
                    trade_record.risk_percent,
                    trade_record.account_balance,
                    trade_record.position_size_usd
                ))
                
                conn.commit()
                logger.info(f"Trade record stored in database: {trade_record.trade_id}")
                
        except Exception as e:
            logger.error(f"Error storing trade record in database: {e}")
            # Fallback to logging only
            logger.info(f"Trade record (fallback log): {trade_record.trade_id} - {trade_record.symbol} {trade_record.trade_type.value} {trade_record.volume}")
    
    async def _broadcast_trade_update(self, trade_record: TradeRecord, event_type: str):
        """Broadcast trade update to WebSocket clients"""
        try:
            if not self.websocket_server:
                return
            
            update_data = {
                "type": "trade_update",
                "event": event_type,
                "trade": trade_record.to_dict(),
                "timestamp": datetime.now().isoformat()
            }
            
            # Use asyncio to broadcast without blocking
            import asyncio
            asyncio.create_task(self.websocket_server.broadcast_trade_update(update_data))
            
        except Exception as e:
            logger.error(f"Error broadcasting trade update: {e}")
    
    async def _broadcast_ea_update(self, ea_record: EARecord, event_type: str):
        """Broadcast EA update to WebSocket clients"""
        try:
            if not self.websocket_server:
                return
            
            update_data = {
                "type": "ea_update",
                "event": event_type,
                "ea": ea_record.to_dict(),
                "timestamp": datetime.now().isoformat()
            }
            
            # Use asyncio to broadcast without blocking
            import asyncio
            asyncio.create_task(self.websocket_server.broadcast_ea_update(update_data))
            
        except Exception as e:
            logger.error(f"Error broadcasting EA update: {e}")
    
    def get_account_overview(self) -> Dict[str, Any]:
        """Get comprehensive account overview with all EAs"""
        try:
            active_eas = self.get_active_eas()
            
            # Calculate totals
            total_balance = max((ea.balance for ea in active_eas), default=0.0)
            total_equity = max((ea.equity for ea in active_eas), default=0.0)
            total_margin = sum(ea.margin for ea in active_eas)
            total_free_margin = max((ea.free_margin for ea in active_eas), default=0.0)
            
            # Calculate overall statistics
            total_active_trades = sum(ea.active_trades for ea in active_eas)
            total_completed_trades = sum(ea.total_trades for ea in active_eas)
            total_profit = sum(ea.total_profit for ea in active_eas)
            
            # Get account info from first active EA
            account_info = {}
            if active_eas:
                first_ea = active_eas[0]
                account_info = {
                    'account_number': first_ea.account_number,
                    'broker': first_ea.broker
                }
            
            return {
                'account_info': account_info,
                'account_metrics': {
                    'balance': round(total_balance, 2),
                    'equity': round(total_equity, 2),
                    'margin': round(total_margin, 2),
                    'free_margin': round(total_free_margin, 2),
                    'margin_level': round((total_equity / total_margin * 100) if total_margin > 0 else 0, 2)
                },
                'trading_summary': {
                    'active_eas': len(active_eas),
                    'total_eas': len(self.registered_eas),
                    'active_trades': total_active_trades,
                    'completed_trades': total_completed_trades,
                    'total_profit': round(total_profit, 2)
                },
                'ea_list': [ea.to_dict() for ea in active_eas],
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting account overview: {e}")
            return {}


# Global instance
_trade_recording_service = None

def get_trade_recording_service() -> TradeRecordingService:
    """Get global trade recording service instance"""
    global _trade_recording_service
    if _trade_recording_service is None:
        try:
            from backend.database.connection import get_database_manager
        except ImportError:
            from database.connection import get_database_manager
        db_manager = get_database_manager()
        _trade_recording_service = TradeRecordingService(db_manager)
    return _trade_recording_service