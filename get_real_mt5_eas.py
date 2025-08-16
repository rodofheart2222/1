#!/usr/bin/env python3
"""
Get Real MT5 EAs
Connect to MT5 terminal and get actual running EAs
"""

import sys
import logging
from datetime import datetime
from pathlib import Path

# Add backend to path
sys.path.append('backend')

try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False
    print("MetaTrader5 module not available")
    sys.exit(1)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def connect_to_mt5():
    """Connect to MT5 terminal"""
    try:
        logger.info("Connecting to MT5 terminal...")
        
        # Initialize MT5 connection
        if not mt5.initialize():
            logger.error("Failed to initialize MT5")
            logger.error(f"MT5 error: {mt5.last_error()}")
            return False
        
        # Get terminal info
        terminal_info = mt5.terminal_info()
        if terminal_info is None:
            logger.error("Failed to get terminal info")
            return False
        
        logger.info(f"Connected to MT5 terminal:")
        logger.info(f"  Company: {terminal_info.company}")
        logger.info(f"  Name: {terminal_info.name}")
        logger.info(f"  Path: {terminal_info.path}")
        logger.info(f"  Data Path: {terminal_info.data_path}")
        logger.info(f"  Connected: {terminal_info.connected}")
        
        # Get account info
        account_info = mt5.account_info()
        if account_info is None:
            logger.error("Failed to get account info")
            return False
        
        logger.info(f"Account info:")
        logger.info(f"  Login: {account_info.login}")
        logger.info(f"  Server: {account_info.server}")
        logger.info(f"  Balance: {account_info.balance}")
        logger.info(f"  Equity: {account_info.equity}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error connecting to MT5: {e}")
        return False

def get_running_eas():
    """Get list of running EAs from MT5"""
    try:
        logger.info("Getting running EAs from MT5...")
        
        # Get all open positions (these indicate EAs are trading)
        positions = mt5.positions_get()
        if positions is None:
            logger.warning("No positions found or error getting positions")
            positions = []
        
        # Get all pending orders (these also indicate EA activity)
        orders = mt5.orders_get()
        if orders is None:
            logger.warning("No orders found or error getting orders")
            orders = []
        
        # Extract unique magic numbers (EA identifiers)
        magic_numbers = set()
        
        # From positions
        for position in positions:
            if position.magic != 0:  # 0 means manual trade
                magic_numbers.add(position.magic)
        
        # From orders
        for order in orders:
            if order.magic != 0:  # 0 means manual order
                magic_numbers.add(order.magic)
        
        logger.info(f"Found {len(magic_numbers)} unique magic numbers from positions/orders")
        
        # Get EA details
        ea_list = []
        for magic in magic_numbers:
            ea_info = get_ea_info(magic, positions, orders)
            if ea_info:
                ea_list.append(ea_info)
        
        # Also check for EAs that might be running but not currently trading
        # This is harder to detect, but we can look at recent history
        recent_deals = get_recent_ea_activity()
        for magic, ea_info in recent_deals.items():
            if magic not in magic_numbers:
                logger.info(f"Found EA {magic} from recent activity (not currently trading)")
                ea_list.append(ea_info)
        
        return ea_list
        
    except Exception as e:
        logger.error(f"Error getting running EAs: {e}")
        return []

def get_ea_info(magic_number, positions, orders):
    """Get detailed info for a specific EA"""
    try:
        # Find positions and orders for this EA
        ea_positions = [p for p in positions if p.magic == magic_number]
        ea_orders = [o for o in orders if o.magic == magic_number]
        
        if not ea_positions and not ea_orders:
            return None
        
        # Get symbol from positions or orders
        symbol = None
        if ea_positions:
            symbol = ea_positions[0].symbol
        elif ea_orders:
            symbol = ea_orders[0].symbol
        
        # Calculate current profit
        current_profit = sum(p.profit + p.swap for p in ea_positions)
        
        # Count open positions
        open_positions = len(ea_positions)
        
        # Get symbol info for additional details
        symbol_info = mt5.symbol_info(symbol) if symbol else None
        
        ea_info = {
            'magic_number': magic_number,
            'symbol': symbol,
            'strategy_tag': f'EA_{magic_number}',  # We can't get the actual EA name from MT5 API
            'current_profit': round(current_profit, 2),
            'open_positions': open_positions,
            'pending_orders': len(ea_orders),
            'status': 'active',
            'last_update': datetime.now().isoformat(),
            'positions': [
                {
                    'ticket': p.ticket,
                    'symbol': p.symbol,
                    'type': 'buy' if p.type == 0 else 'sell',
                    'volume': p.volume,
                    'price_open': p.price_open,
                    'price_current': p.price_current,
                    'profit': p.profit,
                    'swap': p.swap
                } for p in ea_positions
            ],
            'orders': [
                {
                    'ticket': o.ticket,
                    'symbol': o.symbol,
                    'type': o.type,
                    'volume': o.volume_initial,
                    'price_open': o.price_open,
                    'sl': o.sl,
                    'tp': o.tp
                } for o in ea_orders
            ]
        }
        
        if symbol_info:
            ea_info['symbol_info'] = {
                'digits': symbol_info.digits,
                'point': symbol_info.point,
                'spread': symbol_info.spread,
                'bid': symbol_info.bid,
                'ask': symbol_info.ask
            }
        
        return ea_info
        
    except Exception as e:
        logger.error(f"Error getting EA info for magic {magic_number}: {e}")
        return None

def get_recent_ea_activity():
    """Get recent EA activity from deal history"""
    try:
        # Get deals from last 24 hours
        from datetime import datetime, timedelta
        
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=24)
        
        deals = mt5.history_deals_get(start_time, end_time)
        if deals is None:
            return {}
        
        # Group deals by magic number
        ea_activity = {}
        for deal in deals:
            if deal.magic != 0:  # Skip manual trades
                magic = deal.magic
                if magic not in ea_activity:
                    ea_activity[magic] = {
                        'magic_number': magic,
                        'symbol': deal.symbol,
                        'strategy_tag': f'EA_{magic}',
                        'current_profit': 0.0,  # We can't get current profit from history
                        'open_positions': 0,    # We can't get current positions from history
                        'status': 'recently_active',
                        'last_update': datetime.now().isoformat(),
                        'recent_deals': []
                    }
                
                # Add deal info
                ea_activity[magic]['recent_deals'].append({
                    'ticket': deal.ticket,
                    'symbol': deal.symbol,
                    'type': deal.type,
                    'volume': deal.volume,
                    'price': deal.price,
                    'profit': deal.profit,
                    'time': deal.time.isoformat() if hasattr(deal.time, 'isoformat') else str(deal.time)
                })
        
        return ea_activity
        
    except Exception as e:
        logger.error(f"Error getting recent EA activity: {e}")
        return {}

def populate_database_with_real_eas(ea_list):
    """Populate database with real EA data from MT5"""
    try:
        import sqlite3
        import os
        
        logger.info(f"Populating database with {len(ea_list)} real EAs...")
        
        # Get database connection
        db_path = os.getenv("DATABASE_PATH", "data/mt5_dashboard.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        for ea_info in ea_list:
            try:
                magic_number = ea_info['magic_number']
                
                # Insert or update EA in database
                cursor.execute("""
                    INSERT OR REPLACE INTO eas (
                        magic_number, ea_name, symbol, timeframe, status,
                        last_heartbeat, strategy_tag, last_seen, risk_config
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    magic_number,
                    f"EA_{magic_number}",
                    ea_info['symbol'],
                    "M1",  # Default timeframe
                    ea_info['status'],
                    datetime.now(),
                    ea_info['strategy_tag'],
                    datetime.now(),
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
                        datetime.now(),
                        ea_info['current_profit'],
                        ea_info['open_positions'],
                        0.0,  # We don't have SL/TP info from MT5 API
                        0.0,
                        False,  # We don't have trailing info
                        "{}"  # Empty JSON for module status
                    ))
                
                logger.info(f"Updated real EA {magic_number} ({ea_info['symbol']}) - Profit: {ea_info['current_profit']}, Positions: {ea_info['open_positions']}")
                
            except Exception as e:
                logger.error(f"Error processing EA {ea_info.get('magic_number', 'unknown')}: {e}")
                continue
        
        # Commit changes
        conn.commit()
        conn.close()
        
        logger.info(f"Successfully populated database with {len(ea_list)} real EAs from MT5")
        return True
        
    except Exception as e:
        logger.error(f"Error populating database with real EAs: {e}")
        return False

def main():
    """Main function"""
    try:
        logger.info("Starting real MT5 EA detection...")
        
        # Connect to MT5
        if not connect_to_mt5():
            logger.error("Failed to connect to MT5")
            return False
        
        # Get running EAs
        ea_list = get_running_eas()
        
        if not ea_list:
            logger.warning("No EAs found in MT5 terminal")
            logger.info("This could mean:")
            logger.info("  1. No EAs are currently running")
            logger.info("  2. EAs are running but have no open positions/orders")
            logger.info("  3. All trades are manual (magic number = 0)")
            return False
        
        logger.info(f"Found {len(ea_list)} EAs in MT5:")
        for ea in ea_list:
            logger.info(f"  EA {ea['magic_number']}: {ea['symbol']} - Profit: {ea['current_profit']}, Positions: {ea['open_positions']}")
        
        # Populate database
        success = populate_database_with_real_eas(ea_list)
        
        # Shutdown MT5
        mt5.shutdown()
        
        return success
        
    except Exception as e:
        logger.error(f"Error in main: {e}")
        return False
    finally:
        # Always shutdown MT5
        try:
            mt5.shutdown()
        except:
            pass

if __name__ == "__main__":
    success = main()
    print(f"Real MT5 EA detection: {'SUCCESS' if success else 'FAILED'}")