"""
MT5 Trade Tracker Service

This service tracks trades directly from MetaTrader5 using the metatrader5 module.
It monitors positions, orders, and deals in real-time and integrates with the 
trade recording service for comprehensive trade lifecycle management.
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import threading
from concurrent.futures import ThreadPoolExecutor

try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False
    logging.warning("MetaTrader5 module not available. Trade tracker will use mock data.")

# Handle imports for both running from root and from backend directory
try:
    from backend.services.trade_recording_service import get_trade_recording_service, TradeStatus, TradeType
except ImportError:
    from services.trade_recording_service import get_trade_recording_service, TradeStatus, TradeType

# Configure logging
logger = logging.getLogger(__name__)


class MT5OrderType(Enum):
    """MT5 Order types"""
    ORDER_TYPE_BUY = 0
    ORDER_TYPE_SELL = 1
    ORDER_TYPE_BUY_LIMIT = 2
    ORDER_TYPE_SELL_LIMIT = 3
    ORDER_TYPE_BUY_STOP = 4
    ORDER_TYPE_SELL_STOP = 5
    ORDER_TYPE_BUY_STOP_LIMIT = 6
    ORDER_TYPE_SELL_STOP_LIMIT = 7


class MT5DealType(Enum):
    """MT5 Deal types"""
    DEAL_TYPE_BUY = 0
    DEAL_TYPE_SELL = 1
    DEAL_TYPE_BALANCE = 2
    DEAL_TYPE_CREDIT = 3
    DEAL_TYPE_CHARGE = 4
    DEAL_TYPE_CORRECTION = 5
    DEAL_TYPE_BONUS = 6
    DEAL_TYPE_COMMISSION = 7
    DEAL_TYPE_COMMISSION_DAILY = 8
    DEAL_TYPE_COMMISSION_MONTHLY = 9
    DEAL_TYPE_COMMISSION_AGENT_DAILY = 10
    DEAL_TYPE_COMMISSION_AGENT_MONTHLY = 11
    DEAL_TYPE_INTEREST = 12
    DEAL_TYPE_BUY_CANCELED = 13
    DEAL_TYPE_SELL_CANCELED = 14
    DEAL_TYPE_DIVIDEND = 15
    DEAL_TYPE_DIVIDEND_FRANKED = 16
    DEAL_TYPE_TAX = 17


@dataclass
class MT5Position:
    """MT5 Position data structure"""
    ticket: int
    time: datetime
    time_msc: int
    time_update: datetime
    time_update_msc: int
    type: int
    magic: int
    identifier: int
    reason: int
    volume: float
    price_open: float
    sl: float
    tp: float
    price_current: float
    swap: float
    profit: float
    symbol: str
    comment: str
    external_id: str
    
    @classmethod
    def from_mt5_position(cls, pos):
        """Create from MT5 position structure"""
        return cls(
            ticket=pos.ticket,
            time=datetime.fromtimestamp(pos.time),
            time_msc=pos.time_msc,
            time_update=datetime.fromtimestamp(pos.time_update),
            time_update_msc=pos.time_update_msc,
            type=pos.type,
            magic=pos.magic,
            identifier=pos.identifier,
            reason=pos.reason,
            volume=pos.volume,
            price_open=pos.price_open,
            sl=pos.sl,
            tp=pos.tp,
            price_current=pos.price_current,
            swap=pos.swap,
            profit=pos.profit,
            symbol=pos.symbol,
            comment=pos.comment,
            external_id=pos.external_id
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'ticket': self.ticket,
            'time': self.time.isoformat(),
            'time_msc': self.time_msc,
            'time_update': self.time_update.isoformat(),
            'time_update_msc': self.time_update_msc,
            'type': self.type,
            'type_name': 'BUY' if self.type == 0 else 'SELL',
            'magic': self.magic,
            'identifier': self.identifier,
            'reason': self.reason,
            'volume': self.volume,
            'price_open': self.price_open,
            'sl': self.sl,
            'tp': self.tp,
            'price_current': self.price_current,
            'swap': self.swap,
            'profit': self.profit,
            'symbol': self.symbol,
            'comment': self.comment,
            'external_id': self.external_id
        }


@dataclass
class MT5Order:
    """MT5 Order data structure"""
    ticket: int
    time_setup: datetime
    time_setup_msc: int
    time_expiration: datetime
    type: int
    state: int
    magic: int
    position_id: int
    position_by_id: int
    reason: int
    volume_initial: float
    volume_current: float
    price_open: float
    sl: float
    tp: float
    price_current: float
    price_stoplimit: float
    symbol: str
    comment: str
    external_id: str
    
    @classmethod
    def from_mt5_order(cls, order):
        """Create from MT5 order structure"""
        return cls(
            ticket=order.ticket,
            time_setup=datetime.fromtimestamp(order.time_setup),
            time_setup_msc=order.time_setup_msc,
            time_expiration=datetime.fromtimestamp(order.time_expiration) if order.time_expiration > 0 else None,
            type=order.type,
            state=order.state,
            magic=order.magic,
            position_id=order.position_id,
            position_by_id=order.position_by_id,
            reason=order.reason,
            volume_initial=order.volume_initial,
            volume_current=order.volume_current,
            price_open=order.price_open,
            sl=order.sl,
            tp=order.tp,
            price_current=order.price_current,
            price_stoplimit=order.price_stoplimit,
            symbol=order.symbol,
            comment=order.comment,
            external_id=order.external_id
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        order_type_names = {
            0: 'BUY',
            1: 'SELL',
            2: 'BUY_LIMIT',
            3: 'SELL_LIMIT',
            4: 'BUY_STOP',
            5: 'SELL_STOP',
            6: 'BUY_STOP_LIMIT',
            7: 'SELL_STOP_LIMIT'
        }
        
        return {
            'ticket': self.ticket,
            'time_setup': self.time_setup.isoformat(),
            'time_setup_msc': self.time_setup_msc,
            'time_expiration': self.time_expiration.isoformat() if self.time_expiration else None,
            'type': self.type,
            'type_name': order_type_names.get(self.type, f'TYPE_{self.type}'),
            'state': self.state,
            'magic': self.magic,
            'position_id': self.position_id,
            'position_by_id': self.position_by_id,
            'reason': self.reason,
            'volume_initial': self.volume_initial,
            'volume_current': self.volume_current,
            'price_open': self.price_open,
            'sl': self.sl,
            'tp': self.tp,
            'price_current': self.price_current,
            'price_stoplimit': self.price_stoplimit,
            'symbol': self.symbol,
            'comment': self.comment,
            'external_id': self.external_id
        }


@dataclass
class MT5Deal:
    """MT5 Deal data structure"""
    ticket: int
    order: int
    time: datetime
    time_msc: int
    type: int
    entry: int
    magic: int
    position_id: int
    reason: int
    volume: float
    price: float
    commission: float
    swap: float
    profit: float
    symbol: str
    comment: str
    external_id: str
    
    @classmethod
    def from_mt5_deal(cls, deal):
        """Create from MT5 deal structure"""
        return cls(
            ticket=deal.ticket,
            order=deal.order,
            time=datetime.fromtimestamp(deal.time),
            time_msc=deal.time_msc,
            type=deal.type,
            entry=deal.entry,
            magic=deal.magic,
            position_id=deal.position_id,
            reason=deal.reason,
            volume=deal.volume,
            price=deal.price,
            commission=deal.commission,
            swap=deal.swap,
            profit=deal.profit,
            symbol=deal.symbol,
            comment=deal.comment,
            external_id=deal.external_id
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        deal_type_names = {
            0: 'BUY',
            1: 'SELL',
            2: 'BALANCE',
            3: 'CREDIT',
            4: 'CHARGE',
            5: 'CORRECTION',
            6: 'BONUS',
            7: 'COMMISSION',
            8: 'COMMISSION_DAILY',
            9: 'COMMISSION_MONTHLY',
            10: 'COMMISSION_AGENT_DAILY',
            11: 'COMMISSION_AGENT_MONTHLY',
            12: 'INTEREST',
            13: 'BUY_CANCELED',
            14: 'SELL_CANCELED',
            15: 'DIVIDEND',
            16: 'DIVIDEND_FRANKED',
            17: 'TAX'
        }
        
        entry_names = {
            0: 'ENTRY_IN',
            1: 'ENTRY_OUT',
            2: 'ENTRY_INOUT',
            3: 'ENTRY_OUT_BY'
        }
        
        return {
            'ticket': self.ticket,
            'order': self.order,
            'time': self.time.isoformat(),
            'time_msc': self.time_msc,
            'type': self.type,
            'type_name': deal_type_names.get(self.type, f'TYPE_{self.type}'),
            'entry': self.entry,
            'entry_name': entry_names.get(self.entry, f'ENTRY_{self.entry}'),
            'magic': self.magic,
            'position_id': self.position_id,
            'reason': self.reason,
            'volume': self.volume,
            'price': self.price,
            'commission': self.commission,
            'swap': self.swap,
            'profit': self.profit,
            'symbol': self.symbol,
            'comment': self.comment,
            'external_id': self.external_id
        }


class MT5TradeTracker:
    """
    Service for tracking trades directly from MetaTrader5
    """
    
    def __init__(self):
        self.mt5_connected = False
        self.running = False
        self.executor = ThreadPoolExecutor(max_workers=3)
        self.update_interval = 1.0  # seconds
        
        # Tracking data
        self.tracked_eas: Set[int] = set()  # Magic numbers to track
        self.positions_cache: Dict[int, MT5Position] = {}  # ticket -> position
        self.orders_cache: Dict[int, MT5Order] = {}  # ticket -> order
        self.deals_cache: Dict[int, MT5Deal] = {}  # ticket -> deal
        
        # Last update timestamps for change detection
        self.last_positions_update = 0
        self.last_orders_update = 0
        self.last_deals_update = 0
        
        # Integration with trade recording service
        self.trade_recording_service = None
        
        # Account info cache
        self.account_info = None
        self.last_account_update = 0
        
    async def initialize(self) -> bool:
        """Initialize MT5 connection and trade tracking"""
        if not MT5_AVAILABLE:
            logger.warning("MT5 not available, trade tracking disabled")
            return False
            
        try:
            # Initialize MT5 connection
            loop = asyncio.get_event_loop()
            success = await loop.run_in_executor(
                self.executor, 
                self._initialize_mt5
            )
            
            if success:
                logger.info("MT5 Trade Tracker initialized successfully")
                self.mt5_connected = True
                
                # Get trade recording service
                self.trade_recording_service = get_trade_recording_service()
                
                # Load initial data
                await self._load_initial_data()
                
                return True
            else:
                logger.error("Failed to initialize MT5 Trade Tracker")
                return False
                
        except Exception as e:
            logger.error(f"Error initializing MT5 Trade Tracker: {e}")
            return False
    
    def _initialize_mt5(self) -> bool:
        """Initialize MT5 in thread (blocking operation)"""
        try:
            if not mt5.initialize():
                logger.error(f"MT5 initialization failed: {mt5.last_error()}")
                return False
                
            # Get account info
            account_info = mt5.account_info()
            if account_info is None:
                logger.error("Failed to get account info")
                return False
                
            self.account_info = account_info
            logger.info(f"Connected to MT5 account: {account_info.login} ({account_info.server})")
            return True
            
        except Exception as e:
            logger.error(f"MT5 initialization error: {e}")
            return False
    
    async def shutdown(self):
        """Shutdown the trade tracker"""
        self.running = False
        
        if MT5_AVAILABLE and self.mt5_connected:
            try:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(self.executor, mt5.shutdown)
                logger.info("MT5 Trade Tracker connection closed")
            except Exception as e:
                logger.error(f"Error shutting down MT5 Trade Tracker: {e}")
        
        self.executor.shutdown(wait=True)
    
    def add_ea_tracking(self, magic_number: int):
        """Add EA magic number to tracking list"""
        self.tracked_eas.add(magic_number)
        logger.info(f"Added EA {magic_number} to trade tracking")
    
    def remove_ea_tracking(self, magic_number: int):
        """Remove EA magic number from tracking list"""
        self.tracked_eas.discard(magic_number)
        logger.info(f"Removed EA {magic_number} from trade tracking")
    
    async def start_tracking(self):
        """Start the trade tracking loop"""
        if not self.mt5_connected:
            logger.error("MT5 not connected, cannot start tracking")
            return
            
        if self.running:
            return
            
        self.running = True
        logger.info("Starting MT5 trade tracking")
        
        while self.running:
            try:
                # Update all tracking data
                await self._update_positions()
                await self._update_orders()
                await self._update_deals()
                await self._update_account_info()
                
                await asyncio.sleep(self.update_interval)
                
            except Exception as e:
                logger.error(f"Error in trade tracking loop: {e}")
                await asyncio.sleep(5)  # Wait longer on error
    
    async def _load_initial_data(self):
        """Load initial positions, orders, and recent deals"""
        try:
            await self._update_positions()
            await self._update_orders()
            await self._update_deals()
            await self._update_account_info()
            logger.info("Initial MT5 data loaded successfully")
        except Exception as e:
            logger.error(f"Error loading initial MT5 data: {e}")
    
    async def _update_positions(self):
        """Update positions from MT5"""
        try:
            if not self.mt5_connected:
                return
                
            loop = asyncio.get_event_loop()
            positions = await loop.run_in_executor(
                self.executor,
                mt5.positions_get
            )
            
            if positions is None:
                return
            
            current_positions = {}
            new_positions = []
            closed_positions = []
            
            # Process current positions
            for pos in positions:
                # Only track positions for our EAs
                if pos.magic in self.tracked_eas or not self.tracked_eas:
                    mt5_pos = MT5Position.from_mt5_position(pos)
                    current_positions[pos.ticket] = mt5_pos
                    
                    # Check if this is a new position
                    if pos.ticket not in self.positions_cache:
                        new_positions.append(mt5_pos)
                        logger.info(f"[ENTRY] New position detected: {pos.symbol} {mt5_pos.to_dict()['type_name']} {pos.volume} @ {pos.price_open}")
            
            # Check for closed positions
            for ticket, old_pos in self.positions_cache.items():
                if ticket not in current_positions:
                    closed_positions.append(old_pos)
                    logger.info(f"[CLOSE] Position closed: {old_pos.symbol} ticket {ticket}")
            
            # Update cache
            self.positions_cache = current_positions
            
            # Notify trade recording service
            if self.trade_recording_service:
                for pos in new_positions:
                    await self._record_position_open(pos)
                
                for pos in closed_positions:
                    await self._record_position_close(pos)
            
        except Exception as e:
            logger.error(f"Error updating positions: {e}")
    
    async def _update_orders(self):
        """Update orders from MT5"""
        try:
            if not self.mt5_connected:
                return
                
            loop = asyncio.get_event_loop()
            orders = await loop.run_in_executor(
                self.executor,
                mt5.orders_get
            )
            
            if orders is None:
                return
            
            current_orders = {}
            new_orders = []
            cancelled_orders = []
            
            # Process current orders
            for order in orders:
                # Only track orders for our EAs
                if order.magic in self.tracked_eas or not self.tracked_eas:
                    mt5_order = MT5Order.from_mt5_order(order)
                    current_orders[order.ticket] = mt5_order
                    
                    # Check if this is a new order
                    if order.ticket not in self.orders_cache:
                        new_orders.append(mt5_order)
                        logger.info(f"[ENTRY] New order placed: {order.symbol} {mt5_order.to_dict()['type_name']} {order.volume_current} @ {order.price_open}")
            
            # Check for cancelled orders
            for ticket, old_order in self.orders_cache.items():
                if ticket not in current_orders:
                    cancelled_orders.append(old_order)
                    logger.info(f"[CANCEL] Order cancelled: {old_order.symbol} ticket {ticket}")
            
            # Update cache
            self.orders_cache = current_orders
            
            # Notify trade recording service
            if self.trade_recording_service:
                for order in new_orders:
                    await self._record_order_placed(order)
                
                for order in cancelled_orders:
                    await self._record_order_cancelled(order)
            
        except Exception as e:
            logger.error(f"Error updating orders: {e}")
    
    async def _update_deals(self):
        """Update recent deals from MT5"""
        try:
            if not self.mt5_connected:
                return
            
            # Get deals from the last hour
            from_date = datetime.now() - timedelta(hours=1)
            to_date = datetime.now()
            
            loop = asyncio.get_event_loop()
            deals = await loop.run_in_executor(
                self.executor,
                mt5.history_deals_get,
                from_date,
                to_date
            )
            
            if deals is None:
                return
            
            new_deals = []
            
            # Process deals
            for deal in deals:
                # Only track deals for our EAs and trading deals
                if ((deal.magic in self.tracked_eas or not self.tracked_eas) and 
                    deal.type in [0, 1]):  # BUY or SELL deals only
                    
                    if deal.ticket not in self.deals_cache:
                        mt5_deal = MT5Deal.from_mt5_deal(deal)
                        self.deals_cache[deal.ticket] = mt5_deal
                        new_deals.append(mt5_deal)
                        
                        deal_type = "BUY" if deal.type == 0 else "SELL"
                        if deal.entry == 0:  # Entry in
                            logger.info(f"[ENTRY] Deal executed: {deal.symbol} {deal_type} {deal.volume} @ {deal.price}")
                        elif deal.entry == 1:  # Entry out
                            logger.info(f"[CLOSE] Deal closed: {deal.symbol} {deal_type} {deal.volume} @ {deal.price} (P/L: {deal.profit:.2f})")
            
            # Notify trade recording service
            if self.trade_recording_service:
                for deal in new_deals:
                    await self._record_deal(deal)
            
        except Exception as e:
            logger.error(f"Error updating deals: {e}")
    
    async def _update_account_info(self):
        """Update account information"""
        try:
            if not self.mt5_connected:
                return
            
            current_time = time.time()
            if current_time - self.last_account_update < 5:  # Update every 5 seconds
                return
            
            loop = asyncio.get_event_loop()
            account_info = await loop.run_in_executor(
                self.executor,
                mt5.account_info
            )
            
            if account_info is not None:
                self.account_info = account_info
                self.last_account_update = current_time
                
                # Update EA heartbeats with account info
                if self.trade_recording_service:
                    for magic_number in self.tracked_eas:
                        await self.trade_recording_service.update_ea_heartbeat(
                            magic_number,
                            {
                                'balance': float(account_info.balance),
                                'equity': float(account_info.equity),
                                'margin': float(account_info.margin),
                                'free_margin': float(account_info.margin_free),
                                'margin_level': float(account_info.margin_level)
                            }
                        )
            
        except Exception as e:
            logger.error(f"Error updating account info: {e}")
    
    async def _record_position_open(self, position: MT5Position):
        """Record position opening in trade recording service"""
        try:
            fill_data = {
                'magic_number': position.magic,
                'ticket': position.ticket,
                'symbol': position.symbol,
                'order_type': 'BUY' if position.type == 0 else 'SELL',
                'volume': position.volume,
                'price': position.price_open,
                'sl': position.sl if position.sl > 0 else None,
                'tp': position.tp if position.tp > 0 else None,
                'comment': position.comment,
                'commission': 0.0,  # Will be updated when position closes
                'swap': position.swap,
                'account_balance': float(self.account_info.balance) if self.account_info else 0.0,
                'account_equity': float(self.account_info.equity) if self.account_info else 0.0
            }
            
            await self.trade_recording_service.record_mt5_fill(fill_data)
            
        except Exception as e:
            logger.error(f"Error recording position open: {e}")
    
    async def _record_position_close(self, position: MT5Position):
        """Record position closing in trade recording service"""
        try:
            close_data = {
                'magic_number': position.magic,
                'ticket': position.ticket,
                'symbol': position.symbol,
                'close_price': position.price_current,
                'profit': position.profit,
                'commission': 0.0,  # Commission is usually in deals
                'swap': position.swap
            }
            
            await self.trade_recording_service.record_trade_close(close_data)
            
        except Exception as e:
            logger.error(f"Error recording position close: {e}")
    
    async def _record_order_placed(self, order: MT5Order):
        """Record order placement in trade recording service"""
        try:
            # Convert MT5 order type to our trade type
            order_type_map = {
                0: 'BUY',
                1: 'SELL',
                2: 'BUY_LIMIT',
                3: 'SELL_LIMIT',
                4: 'BUY_STOP',
                5: 'SELL_STOP'
            }
            
            command_data = {
                'magic_number': order.magic,
                'command': 'PLACE_ORDER',
                'parameters': {
                    'symbol': order.symbol,
                    'order_type': order_type_map.get(order.type, 'BUY'),
                    'volume': order.volume_current,
                    'price': order.price_open,
                    'sl': order.sl if order.sl > 0 else None,
                    'tp': order.tp if order.tp > 0 else None,
                    'comment': order.comment,
                    'account_balance': float(self.account_info.balance) if self.account_info else 0.0
                },
                'command_id': f'mt5_order_{order.ticket}',
                'timestamp': order.time_setup.isoformat()
            }
            
            await self.trade_recording_service.record_dashboard_command(command_data)
            
        except Exception as e:
            logger.error(f"Error recording order placement: {e}")
    
    async def _record_order_cancelled(self, order: MT5Order):
        """Record order cancellation in trade recording service"""
        try:
            cancel_data = {
                'magic_number': order.magic,
                'order_id': f'mt5_order_{order.ticket}',
                'symbol': order.symbol
            }
            
            await self.trade_recording_service.record_trade_cancellation(cancel_data)
            
        except Exception as e:
            logger.error(f"Error recording order cancellation: {e}")
    
    async def _record_deal(self, deal: MT5Deal):
        """Record deal in trade recording service"""
        try:
            if deal.entry == 0:  # Entry in - position opening
                fill_data = {
                    'magic_number': deal.magic,
                    'ticket': deal.position_id,
                    'symbol': deal.symbol,
                    'order_type': 'BUY' if deal.type == 0 else 'SELL',
                    'volume': deal.volume,
                    'price': deal.price,
                    'commission': deal.commission,
                    'swap': deal.swap,
                    'comment': deal.comment,
                    'account_balance': float(self.account_info.balance) if self.account_info else 0.0,
                    'account_equity': float(self.account_info.equity) if self.account_info else 0.0
                }
                
                await self.trade_recording_service.record_mt5_fill(fill_data)
                
            elif deal.entry == 1:  # Entry out - position closing
                close_data = {
                    'magic_number': deal.magic,
                    'ticket': deal.position_id,
                    'symbol': deal.symbol,
                    'close_price': deal.price,
                    'profit': deal.profit,
                    'commission': deal.commission,
                    'swap': deal.swap
                }
                
                await self.trade_recording_service.record_trade_close(close_data)
            
        except Exception as e:
            logger.error(f"Error recording deal: {e}")
    
    # Public API methods
    
    def get_positions(self, magic_number: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get current positions"""
        positions = []
        for pos in self.positions_cache.values():
            if magic_number is None or pos.magic == magic_number:
                positions.append(pos.to_dict())
        return positions
    
    def get_orders(self, magic_number: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get current orders"""
        orders = []
        for order in self.orders_cache.values():
            if magic_number is None or order.magic == magic_number:
                orders.append(order.to_dict())
        return orders
    
    def get_recent_deals(self, magic_number: Optional[int] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent deals"""
        deals = []
        sorted_deals = sorted(self.deals_cache.values(), key=lambda x: x.time, reverse=True)
        
        for deal in sorted_deals[:limit]:
            if magic_number is None or deal.magic == magic_number:
                deals.append(deal.to_dict())
        
        return deals
    
    def get_account_info(self) -> Optional[Dict[str, Any]]:
        """Get current account information"""
        if not self.account_info:
            return None
        
        return {
            'login': self.account_info.login,
            'trade_mode': self.account_info.trade_mode,
            'leverage': self.account_info.leverage,
            'limit_orders': self.account_info.limit_orders,
            'margin_so_mode': self.account_info.margin_so_mode,
            'trade_allowed': self.account_info.trade_allowed,
            'trade_expert': self.account_info.trade_expert,
            'margin_mode': self.account_info.margin_mode,
            'currency_digits': self.account_info.currency_digits,
            'fifo_close': self.account_info.fifo_close,
            'balance': self.account_info.balance,
            'credit': self.account_info.credit,
            'profit': self.account_info.profit,
            'equity': self.account_info.equity,
            'margin': self.account_info.margin,
            'margin_free': self.account_info.margin_free,
            'margin_level': self.account_info.margin_level,
            'margin_so_call': self.account_info.margin_so_call,
            'margin_so_so': self.account_info.margin_so_so,
            'margin_initial': self.account_info.margin_initial,
            'margin_maintenance': self.account_info.margin_maintenance,
            'assets': self.account_info.assets,
            'liabilities': self.account_info.liabilities,
            'commission_blocked': self.account_info.commission_blocked,
            'name': self.account_info.name,
            'server': self.account_info.server,
            'currency': self.account_info.currency,
            'company': self.account_info.company
        }
    
    def get_tracking_status(self) -> Dict[str, Any]:
        """Get tracking status information"""
        return {
            'mt5_connected': self.mt5_connected,
            'running': self.running,
            'tracked_eas': list(self.tracked_eas),
            'positions_count': len(self.positions_cache),
            'orders_count': len(self.orders_cache),
            'deals_count': len(self.deals_cache),
            'last_update': datetime.now().isoformat()
        }


# Global instance
_mt5_trade_tracker = None

def get_mt5_trade_tracker() -> MT5TradeTracker:
    """Get global MT5 trade tracker instance"""
    global _mt5_trade_tracker
    if _mt5_trade_tracker is None:
        _mt5_trade_tracker = MT5TradeTracker()
    return _mt5_trade_tracker