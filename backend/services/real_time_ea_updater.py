"""
Real-time EA Updater Service
Continuously updates EA data from MT5 and broadcasts via WebSocket
"""

import asyncio
import logging
import sqlite3
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json

try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False

# Handle imports for both running from root and from backend directory
try:
    from services.websocket_server import get_websocket_server
    WEBSOCKET_AVAILABLE = True
except ImportError:
    try:
        from backend.services.websocket_server import get_websocket_server
        WEBSOCKET_AVAILABLE = True
    except ImportError:
        WEBSOCKET_AVAILABLE = False

logger = logging.getLogger(__name__)

class RealTimeEAUpdater:
    """Service for real-time EA data updates from MT5"""
    
    def __init__(self, update_interval: int = 2):
        """
        Initialize the real-time EA updater
        
        Args:
            update_interval: Update interval in seconds (default 2 seconds for fast sync)
        """
        self.update_interval = update_interval
        self.running = False
        self.mt5_connected = False
        self.websocket_server = None
        self.last_ea_data = {}
        
        if WEBSOCKET_AVAILABLE:
            self.websocket_server = get_websocket_server()
    
    async def initialize(self) -> bool:
        """Initialize MT5 connection"""
        try:
            if not MT5_AVAILABLE:
                logger.warning("MetaTrader5 not available")
                return False
            
            # Initialize MT5 connection
            if not mt5.initialize():
                logger.error(f"Failed to initialize MT5: {mt5.last_error()}")
                return False
            
            self.mt5_connected = True
            logger.info("Real-time EA updater initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing EA updater: {e}")
            return False
    
    async def start_updates(self):
        """Start the real-time update loop"""
        if not self.mt5_connected:
            logger.error("MT5 not connected, cannot start updates")
            return
        
        self.running = True
        logger.info(f"Starting real-time EA updates (interval: {self.update_interval}s)")
        
        try:
            while self.running:
                await self.update_ea_data()
                await asyncio.sleep(self.update_interval)
        except Exception as e:
            logger.error(f"Error in update loop: {e}")
        finally:
            self.running = False
    
    async def stop_updates(self):
        """Stop the update loop"""
        self.running = False
        
        if self.mt5_connected:
            try:
                mt5.shutdown()
                self.mt5_connected = False
                logger.info("MT5 connection closed")
            except Exception as e:
                logger.error(f"Error shutting down MT5: {e}")
    
    async def update_ea_data(self):
        """Update EA data from MT5 and broadcast changes"""
        try:
            # Get current EA data from MT5
            ea_data = await self.get_mt5_ea_data()
            
            logger.debug(f"EA update cycle: found {len(ea_data)} EAs")
            
            # Sync database with MT5 (remove inactive EAs, add new ones)
            await self.sync_database_with_mt5(ea_data)
            
            # Update database with current data
            await self.update_database(ea_data)
            
            # Check for changes and broadcast
            await self.broadcast_changes(ea_data)
            
            # Update last known data
            self.last_ea_data = ea_data
            
        except Exception as e:
            logger.error(f"Error updating EA data: {e}")
    
    async def get_mt5_ea_data(self) -> Dict[int, Dict]:
        """Get current EA data from MT5"""
        try:
            if not self.mt5_connected:
                return {}
            
            # Get all positions and orders
            positions = mt5.positions_get()
            orders = mt5.orders_get()
            
            if positions is None:
                positions = []
            if orders is None:
                orders = []
            
            # Group by magic number
            ea_data = {}
            
            # Process positions
            for position in positions:
                if position.magic != 0:  # Skip manual trades
                    magic = position.magic
                    if magic not in ea_data:
                        ea_data[magic] = {
                            'magic_number': magic,
                            'symbol': position.symbol,
                            'current_profit': 0.0,
                            'open_positions': 0,
                            'pending_orders': 0,
                            'positions': [],
                            'orders': [],
                            'last_update': datetime.now().isoformat(),
                            'detection_method': 'active_position'
                        }
                    
                    ea_data[magic]['current_profit'] += position.profit + position.swap
                    ea_data[magic]['open_positions'] += 1
                    ea_data[magic]['positions'].append({
                        'ticket': position.ticket,
                        'type': 'buy' if position.type == 0 else 'sell',
                        'volume': position.volume,
                        'price_open': position.price_open,
                        'price_current': position.price_current,
                        'profit': position.profit,
                        'swap': position.swap
                    })
            
            # Process orders
            for order in orders:
                if order.magic != 0:  # Skip manual orders
                    magic = order.magic
                    if magic not in ea_data:
                        ea_data[magic] = {
                            'magic_number': magic,
                            'symbol': order.symbol,
                            'current_profit': 0.0,
                            'open_positions': 0,
                            'pending_orders': 0,
                            'positions': [],
                            'orders': [],
                            'last_update': datetime.now().isoformat(),
                            'detection_method': 'pending_order'
                        }
                    
                    ea_data[magic]['pending_orders'] += 1
                    ea_data[magic]['orders'].append({
                        'ticket': order.ticket,
                        'type': order.type,
                        'volume': order.volume_initial,
                        'price_open': order.price_open,
                        'sl': order.sl,
                        'tp': order.tp
                    })
            
            # Check recent deals to find EAs that might be running but not currently trading
            await self.check_recent_ea_activity(ea_data)
            
            # Check for EAs attached to charts (extended detection)
            await self.check_chart_attached_eas(ea_data)
            
            # Check for EAs using file-based communication (fallback method)
            await self.check_file_based_eas(ea_data)
            
            # Log current detection
            if ea_data:
                logger.debug(f"Detected {len(ea_data)} EAs: {list(ea_data.keys())}")
                for magic, data in ea_data.items():
                    logger.debug(f"  EA {magic}: {data['symbol']} ({data.get('detection_method', 'unknown')})")
            else:
                logger.debug("No EAs detected from any method")
            
            # Round profit values
            for magic in ea_data:
                ea_data[magic]['current_profit'] = round(ea_data[magic]['current_profit'], 2)
            
            return ea_data
            
        except Exception as e:
            logger.error(f"Error getting MT5 EA data: {e}")
            return {}
    
    async def check_recent_ea_activity(self, ea_data: Dict[int, Dict]):
        """Check recent deals to find EAs that might be running but not currently trading"""
        try:
            from datetime import timedelta
            
            # Get deals from last 1 hour to find recently active EAs
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=1)
            
            deals = mt5.history_deals_get(start_time, end_time)
            if deals is None:
                return
            
            # Find EAs from recent deals that aren't already in ea_data
            for deal in deals:
                if deal.magic != 0 and deal.magic not in ea_data:
                    # This EA was recently active but has no current positions/orders
                    ea_data[deal.magic] = {
                        'magic_number': deal.magic,
                        'symbol': deal.symbol,
                        'current_profit': 0.0,
                        'open_positions': 0,
                        'pending_orders': 0,
                        'positions': [],
                        'orders': [],
                        'last_update': datetime.now().isoformat(),
                        'status': 'recently_active'  # Mark as recently active
                    }
                    
                    logger.info(f"Found recently active EA {deal.magic} on {deal.symbol}")
        
        except Exception as e:
            logger.error(f"Error checking recent EA activity: {e}")
    
    async def check_chart_attached_eas(self, ea_data: Dict[int, Dict]):
        """Check for EAs that might be attached to charts but not trading"""
        try:
            # Method 1: Check all available symbols for potential EA activity
            # This is a heuristic approach since MT5 API doesn't directly expose running EAs
            
            # Get all symbols that have charts open (we can't directly get this, but we can check popular symbols)
            common_symbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'USDCAD', 'USDCHF', 'NZDUSD', 
                            'EURJPY', 'GBPJPY', 'AUDJPY', 'XAUUSD', 'US30', 'NAS100', 'SPX500']
            
            # Method 2: Check for any global variables that might indicate EA presence
            # Some EAs create global variables for communication
            await self.check_ea_global_variables(ea_data)
            
            # Method 3: Check extended deal history (last 24 hours) for dormant EAs
            await self.check_extended_ea_history(ea_data)
            
            # Method 4: Check account statistics for potential EA signatures
            await self.check_account_ea_signatures(ea_data)
            
        except Exception as e:
            logger.error(f"Error checking chart attached EAs: {e}")
    
    async def check_ea_global_variables(self, ea_data: Dict[int, Dict]):
        """Check for EA-related global variables"""
        try:
            # This is a placeholder - MT5 Python API doesn't expose global variables directly
            # But if EAs use specific naming conventions, we could detect them
            # For now, we'll use a different approach
            pass
        except Exception as e:
            logger.error(f"Error checking EA global variables: {e}")
    
    async def check_extended_ea_history(self, ea_data: Dict[int, Dict]):
        """Check extended deal history for dormant EAs"""
        try:
            from datetime import timedelta
            
            # Check last 24 hours for any EA activity
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=24)
            
            deals = mt5.history_deals_get(start_time, end_time)
            if deals is None:
                return
            
            # Find EAs that traded in the last 24 hours but aren't currently active
            for deal in deals:
                if deal.magic != 0 and deal.magic not in ea_data:
                    # This EA was active in the last 24 hours but has no current activity
                    ea_data[deal.magic] = {
                        'magic_number': deal.magic,
                        'symbol': deal.symbol,
                        'current_profit': 0.0,
                        'open_positions': 0,
                        'pending_orders': 0,
                        'positions': [],
                        'orders': [],
                        'last_update': datetime.now().isoformat(),
                        'detection_method': 'recent_history_24h',
                        'status': 'dormant',
                        'last_trade_time': deal.time.isoformat() if hasattr(deal.time, 'isoformat') else str(deal.time)
                    }
                    
                    logger.info(f"Found dormant EA {deal.magic} on {deal.symbol} (last trade: {deal.time})")
        
        except Exception as e:
            logger.error(f"Error checking extended EA history: {e}")
    
    async def check_account_ea_signatures(self, ea_data: Dict[int, Dict]):
        """Check account for EA signatures"""
        try:
            # Get account info
            account_info = mt5.account_info()
            if account_info is None:
                return
            
            # Check if there are any patterns that suggest EA activity
            # This is heuristic and may not be 100% accurate
            
            # Method: Check for symbols with recent price requests (indicates chart activity)
            symbols = mt5.symbols_get()
            if symbols:
                for symbol in symbols:
                    symbol_info = mt5.symbol_info(symbol.name)
                    if symbol_info and symbol_info.select:  # Symbol is selected in Market Watch
                        # Check if this symbol has any recent tick activity
                        ticks = mt5.copy_ticks_from(symbol.name, datetime.now(), 1, mt5.COPY_TICKS_ALL)
                        if ticks is not None and len(ticks) > 0:
                            # This symbol is actively monitored - could indicate EA presence
                            # But we need a magic number to create an EA entry
                            # This is more for logging/debugging purposes
                            logger.debug(f"Active symbol detected: {symbol.name}")
        
        except Exception as e:
            logger.error(f"Error checking account EA signatures: {e}")
    
    async def check_file_based_eas(self, ea_data: Dict[int, Dict]):
        """Check for EAs using file-based communication (MT5 globals/fallback)"""
        try:
            from pathlib import Path
            import json
            
            # Check MT5 globals directory
            globals_dir = Path("data/mt5_globals")
            if globals_dir.exists():
                for file_path in globals_dir.glob("COC_EA_*.txt"):
                    try:
                        # Extract magic number from filename
                        filename = file_path.stem  # COC_EA_12345_DATA
                        parts = filename.split('_')
                        if len(parts) >= 3:
                            magic_str = parts[2]
                            magic = int(magic_str)
                            
                            if magic not in ea_data:
                                # Read EA data from file
                                content = file_path.read_text()
                                ea_file_data = json.loads(content)
                                
                                ea_data[magic] = {
                                    'magic_number': magic,
                                    'symbol': ea_file_data.get('symbol', 'UNKNOWN'),
                                    'current_profit': ea_file_data.get('current_profit', 0.0),
                                    'open_positions': ea_file_data.get('open_positions', 0),
                                    'pending_orders': 0,
                                    'positions': [],
                                    'orders': [],
                                    'last_update': ea_file_data.get('last_update', datetime.now().isoformat()),
                                    'detection_method': 'file_based_globals',
                                    'status': 'file_communication'
                                }
                                
                                logger.info(f"Found file-based EA {magic} on {ea_data[magic]['symbol']}")
                    
                    except Exception as e:
                        logger.warning(f"Error reading EA file {file_path}: {e}")
            
            # Check fallback directory
            fallback_dir = Path("data/mt5_fallback/ea_data")
            if fallback_dir.exists():
                for file_path in fallback_dir.glob("ea_*.json"):
                    try:
                        # Extract magic number from filename
                        filename = file_path.stem  # ea_12345
                        magic_str = filename.replace('ea_', '')
                        magic = int(magic_str)
                        
                        if magic not in ea_data:
                            # Read EA data from file
                            content = file_path.read_text()
                            ea_file_data = json.loads(content)
                            
                            ea_data[magic] = {
                                'magic_number': magic,
                                'symbol': ea_file_data.get('symbol', 'UNKNOWN'),
                                'current_profit': ea_file_data.get('current_profit', 0.0),
                                'open_positions': ea_file_data.get('open_positions', 0),
                                'pending_orders': 0,
                                'positions': [],
                                'orders': [],
                                'last_update': ea_file_data.get('last_update', datetime.now().isoformat()),
                                'detection_method': 'file_based_fallback',
                                'status': 'file_communication'
                            }
                            
                            logger.info(f"Found fallback EA {magic} on {ea_data[magic]['symbol']}")
                    
                    except Exception as e:
                        logger.warning(f"Error reading fallback EA file {file_path}: {e}")
        
        except Exception as e:
            logger.error(f"Error checking file-based EAs: {e}")
    
    async def sync_database_with_mt5(self, current_mt5_eas: Dict[int, Dict]):
        """Sync database EA list with current MT5 EAs"""
        try:
            db_path = os.getenv("DATABASE_PATH", "data/mt5_dashboard.db")
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Get all EAs currently in database
            cursor.execute("SELECT magic_number, id FROM eas")
            db_eas = {row[0]: row[1] for row in cursor.fetchall()}
            
            current_mt5_magics = set(current_mt5_eas.keys())
            db_magics = set(db_eas.keys())
            
            # Find EAs to remove (in database but not in MT5)
            eas_to_remove = db_magics - current_mt5_magics
            
            # Find EAs to add (in MT5 but not in database)
            eas_to_add = current_mt5_magics - db_magics
            
            # Remove inactive EAs
            if eas_to_remove:
                logger.info(f"Removing {len(eas_to_remove)} inactive EAs: {list(eas_to_remove)}")
                
                for magic_number in eas_to_remove:
                    ea_id = db_eas[magic_number]
                    
                    # Remove EA status records
                    cursor.execute("DELETE FROM ea_status WHERE ea_id = ?", (ea_id,))
                    
                    # Remove EA record
                    cursor.execute("DELETE FROM eas WHERE magic_number = ?", (magic_number,))
                    
                    logger.info(f"Removed inactive EA {magic_number}")
            
            # Add new EAs
            if eas_to_add:
                logger.info(f"Adding {len(eas_to_add)} new EAs: {list(eas_to_add)}")
                
                for magic_number in eas_to_add:
                    ea_data = current_mt5_eas[magic_number]
                    logger.info(f"Added new EA {magic_number} ({ea_data['symbol']})")
            
            conn.commit()
            conn.close()
            
            # Broadcast sync changes if any
            if eas_to_remove or eas_to_add:
                await self.broadcast_sync_changes(eas_to_remove, eas_to_add, current_mt5_eas)
            
        except Exception as e:
            logger.error(f"Error syncing database with MT5: {e}")
    
    async def broadcast_sync_changes(self, removed_eas: set, added_eas: set, current_mt5_eas: Dict[int, Dict]):
        """Broadcast EA sync changes"""
        try:
            if not self.websocket_server:
                return
            
            changes = []
            
            # Broadcast removed EAs
            for magic_number in removed_eas:
                changes.append({
                    'type': 'ea_removed',
                    'magic_number': magic_number,
                    'reason': 'no_longer_active_in_mt5'
                })
            
            # Broadcast added EAs
            for magic_number in added_eas:
                ea_data = current_mt5_eas[magic_number]
                changes.append({
                    'type': 'ea_added',
                    'magic_number': magic_number,
                    'symbol': ea_data['symbol'],
                    'current_profit': ea_data['current_profit'],
                    'open_positions': ea_data['open_positions']
                })
            
            if changes:
                await self.websocket_server.broadcast_to_authenticated({
                    'type': 'ea_sync_update',
                    'timestamp': datetime.now().isoformat(),
                    'changes': changes,
                    'total_active_eas': len(current_mt5_eas)
                })
                
                logger.info(f"Broadcasted EA sync changes: {len(changes)} changes")
        
        except Exception as e:
            logger.error(f"Error broadcasting sync changes: {e}")

    async def update_database(self, ea_data: Dict[int, Dict]):
        """Update database with current EA data"""
        try:
            db_path = os.getenv("DATABASE_PATH", "data/mt5_dashboard.db")
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            for magic_number, data in ea_data.items():
                try:
                    # Update EA record
                    cursor.execute("""
                        INSERT OR REPLACE INTO eas (
                            magic_number, ea_name, symbol, timeframe, status,
                            last_heartbeat, strategy_tag, last_seen, risk_config
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        magic_number,
                        f"EA_{magic_number}",
                        data['symbol'],
                        "M1",
                        "active",
                        datetime.now(),
                        f"Strategy_{magic_number}",
                        datetime.now(),
                        1.0
                    ))
                    
                    # Get EA ID
                    cursor.execute("SELECT id FROM eas WHERE magic_number = ?", (magic_number,))
                    ea_row = cursor.fetchone()
                    if ea_row:
                        ea_id = ea_row[0]
                        
                        # Update EA status
                        cursor.execute("""
                            INSERT OR REPLACE INTO ea_status (
                                ea_id, timestamp, current_profit, open_positions,
                                sl_value, tp_value, trailing_active, module_status
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            ea_id,
                            datetime.now(),
                            data['current_profit'],
                            data['open_positions'],
                            0.0,
                            0.0,
                            False,
                            json.dumps({
                                'pending_orders': data['pending_orders'],
                                'last_update': data['last_update']
                            })
                        ))
                
                except Exception as e:
                    logger.error(f"Error updating EA {magic_number} in database: {e}")
                    continue
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error updating database: {e}")
    
    async def broadcast_changes(self, current_data: Dict[int, Dict]):
        """Broadcast EA data changes via WebSocket"""
        try:
            if not self.websocket_server:
                return
            
            # Check for changes
            changes = []
            
            for magic_number, data in current_data.items():
                last_data = self.last_ea_data.get(magic_number, {})
                
                # Check if profit changed
                if data['current_profit'] != last_data.get('current_profit', 0):
                    changes.append({
                        'type': 'ea_profit_update',
                        'magic_number': magic_number,
                        'symbol': data['symbol'],
                        'old_profit': last_data.get('current_profit', 0),
                        'new_profit': data['current_profit'],
                        'change': data['current_profit'] - last_data.get('current_profit', 0)
                    })
                
                # Check if positions changed
                if data['open_positions'] != last_data.get('open_positions', 0):
                    changes.append({
                        'type': 'ea_positions_update',
                        'magic_number': magic_number,
                        'symbol': data['symbol'],
                        'old_positions': last_data.get('open_positions', 0),
                        'new_positions': data['open_positions']
                    })
            
            # Check for new EAs
            for magic_number in current_data:
                if magic_number not in self.last_ea_data:
                    changes.append({
                        'type': 'ea_connected',
                        'magic_number': magic_number,
                        'symbol': current_data[magic_number]['symbol'],
                        'current_profit': current_data[magic_number]['current_profit'],
                        'open_positions': current_data[magic_number]['open_positions']
                    })
            
            # Check for disconnected EAs
            for magic_number in self.last_ea_data:
                if magic_number not in current_data:
                    changes.append({
                        'type': 'ea_disconnected',
                        'magic_number': magic_number,
                        'symbol': self.last_ea_data[magic_number]['symbol']
                    })
            
            # Broadcast changes
            if changes:
                await self.websocket_server.broadcast_to_authenticated({
                    'type': 'ea_updates',
                    'timestamp': datetime.now().isoformat(),
                    'changes': changes
                })
                
                logger.info(f"Broadcasted {len(changes)} EA changes")
            
            # Always broadcast current status
            await self.websocket_server.broadcast_to_authenticated({
                'type': 'ea_status_update',
                'timestamp': datetime.now().isoformat(),
                'eas': list(current_data.values())
            })
            
        except Exception as e:
            logger.error(f"Error broadcasting changes: {e}")
    
    async def force_sync_with_mt5(self):
        """Force a full sync with MT5 (useful for manual cleanup)"""
        try:
            logger.info("Forcing full sync with MT5...")
            
            # Get current MT5 data
            ea_data = await self.get_mt5_ea_data()
            
            # Perform sync
            await self.sync_database_with_mt5(ea_data)
            
            # Update database
            await self.update_database(ea_data)
            
            # Update last known data
            self.last_ea_data = ea_data
            
            logger.info(f"Force sync completed - {len(ea_data)} active EAs")
            return True
            
        except Exception as e:
            logger.error(f"Error in force sync: {e}")
            return False
    
    def get_status(self) -> Dict:
        """Get updater status"""
        return {
            'running': self.running,
            'mt5_connected': self.mt5_connected,
            'update_interval': self.update_interval,
            'tracked_eas': len(self.last_ea_data),
            'websocket_available': WEBSOCKET_AVAILABLE
        }

# Global instance
_ea_updater = None

def get_ea_updater() -> RealTimeEAUpdater:
    """Get the global EA updater instance"""
    global _ea_updater
    if _ea_updater is None:
        _ea_updater = RealTimeEAUpdater()
    return _ea_updater