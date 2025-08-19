#!/usr/bin/env python3
"""
EA Response Simulator

This script simulates an EA (Expert Advisor) responding to dashboard commands.
It polls for commands and sends appropriate responses to test the complete workflow.

Usage:
    python simulate_ea_responses.py [--magic 12345] [--symbol EURUSD] [--host 127.0.0.1]
"""

import asyncio
import aiohttp
import json
import time
import random
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EASimulator:
    """Simulates an EA responding to dashboard commands"""
    
    def __init__(self, magic_number: int, symbol: str, host: str = "127.0.0.1", port: int = 80):
        self.magic_number = magic_number
        self.symbol = symbol
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"
        
        self.session: Optional[aiohttp.ClientSession] = None
        self.running = False
        
        # EA state
        self.current_profit = 0.0
        self.open_positions = 0
        self.sl_value = 0.0
        self.tp_value = 0.0
        self.trailing_active = False
        self.is_paused = False
        
        # Orders and positions
        self.pending_orders: List[Dict] = []
        self.open_positions_list: List[Dict] = []
        self.trade_history: List[Dict] = []
        
        # Performance metrics
        self.total_profit = 0.0
        self.trade_count = 0
        self.win_count = 0
        self.profit_factor = 1.0
        
        # Current market price (simulated)
        self.current_price = self._get_base_price()
        
    def _get_base_price(self) -> float:
        """Get base price for symbol"""
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
        return base_prices.get(self.symbol, 1.0000)
    
    def _simulate_price_movement(self):
        """Simulate realistic price movement"""
        # Small random price movement
        if self.symbol == 'XAUUSD':
            movement = random.uniform(-2.0, 2.0)
        elif 'JPY' in self.symbol:
            movement = random.uniform(-0.05, 0.05)
        else:
            movement = random.uniform(-0.0010, 0.0010)
        
        self.current_price += movement
        self.current_price = round(self.current_price, 5 if 'JPY' not in self.symbol else 3)
    
    async def start(self):
        """Start the EA simulator"""
        self.session = aiohttp.ClientSession()
        self.running = True
        
        logger.info(f"🤖 Starting EA Simulator - Magic: {self.magic_number}, Symbol: {self.symbol}")
        
        # Start background tasks
        tasks = [
            asyncio.create_task(self._status_update_loop()),
            asyncio.create_task(self._command_polling_loop()),
            asyncio.create_task(self._price_simulation_loop()),
            asyncio.create_task(self._order_monitoring_loop())
        ]
        
        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            logger.error(f"EA Simulator error: {e}")
        finally:
            await self.stop()
    
    async def stop(self):
        """Stop the EA simulator"""
        self.running = False
        if self.session:
            await self.session.close()
        logger.info("🛑 EA Simulator stopped")
    
    async def _api_request(self, method: str, endpoint: str, data: Dict = None) -> Dict:
        """Make API request"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == "GET":
                async with self.session.get(url) as response:
                    return await response.json()
            elif method.upper() == "POST":
                async with self.session.post(url, json=data) as response:
                    return await response.json()
            else:
                raise ValueError(f"Unsupported method: {method}")
        except Exception as e:
            logger.error(f"API request failed: {e}")
            return {"error": str(e)}
    
    async def _status_update_loop(self):
        """Send periodic status updates"""
        while self.running:
            try:
                # Update performance metrics
                self._update_performance_metrics()
                
                # Prepare status update
                status_update = {
                    "magic_number": self.magic_number,
                    "symbol": self.symbol,
                    "strategy_tag": "EX BOC V24",
                    "current_profit": round(self.current_profit, 2),
                    "open_positions": len(self.open_positions_list),
                    "sl_value": self.sl_value,
                    "tp_value": self.tp_value,
                    "trailing_active": self.trailing_active,
                    "module_status": {
                        "connection": "connected",
                        "trading": "active" if not self.is_paused else "paused",
                        "risk_management": "active",
                        "news_filter": "active"
                    },
                    "performance_metrics": {
                        "total_profit": round(self.total_profit, 2),
                        "profit_factor": round(self.profit_factor, 2),
                        "expected_payoff": round(self.total_profit / max(self.trade_count, 1), 2),
                        "drawdown": round(abs(min(0, self.total_profit)), 2),
                        "z_score": round(random.uniform(-2.0, 2.0), 2),
                        "trade_count": self.trade_count
                    },
                    "last_trades": self.trade_history[-5:],  # Last 5 trades
                    "coc_override": False,
                    "is_paused": self.is_paused,
                    "timestamp": datetime.now().isoformat()
                }
                
                # Send status update
                result = await self._api_request("POST", "/api/ea/status", status_update)
                logger.debug(f"Status update sent: {result.get('status', 'unknown')}")
                
                # Wait before next update
                await asyncio.sleep(5)  # Update every 5 seconds
                
            except Exception as e:
                logger.error(f"Status update error: {e}")
                await asyncio.sleep(5)
    
    async def _command_polling_loop(self):
        """Poll for pending commands"""
        while self.running:
            try:
                # Check for pending commands
                result = await self._api_request("GET", f"/api/ea/commands/{self.magic_number}")
                
                if "command" in result:
                    await self._process_command(result)
                
                # Wait before next poll
                await asyncio.sleep(1)  # Poll every second
                
            except Exception as e:
                if "404" not in str(e):  # Ignore "no commands" errors
                    logger.debug(f"Command polling: {e}")
                await asyncio.sleep(1)
    
    async def _price_simulation_loop(self):
        """Simulate price movements"""
        while self.running:
            try:
                self._simulate_price_movement()
                await asyncio.sleep(0.5)  # Update price every 500ms
            except Exception as e:
                logger.error(f"Price simulation error: {e}")
                await asyncio.sleep(1)
    
    async def _order_monitoring_loop(self):
        """Monitor orders for fills"""
        while self.running:
            try:
                # Check pending orders for fills
                filled_orders = []
                
                for order in self.pending_orders:
                    if self._should_order_fill(order):
                        filled_orders.append(order)
                
                # Process fills
                for order in filled_orders:
                    await self._fill_order(order)
                    self.pending_orders.remove(order)
                
                await asyncio.sleep(0.1)  # Check every 100ms
                
            except Exception as e:
                logger.error(f"Order monitoring error: {e}")
                await asyncio.sleep(1)
    
    def _should_order_fill(self, order: Dict) -> bool:
        """Determine if an order should fill based on current price"""
        order_price = order["price"]
        order_type = order["order_type"]
        
        if order_type == "BUY_LIMIT":
            return self.current_price <= order_price
        elif order_type == "SELL_LIMIT":
            return self.current_price >= order_price
        elif order_type == "BUY_STOP":
            return self.current_price >= order_price
        elif order_type == "SELL_STOP":
            return self.current_price <= order_price
        
        return False
    
    async def _fill_order(self, order: Dict):
        """Fill an order and create position"""
        logger.info(f"[ENTRY] Order filled: {order['order_type']} {order['volume']} {self.symbol} @ {order['price']}")
        
        # Create position
        position = {
            "position_id": f"pos_{int(time.time())}_{random.randint(1000, 9999)}",
            "symbol": self.symbol,
            "order_type": order["order_type"].replace("_LIMIT", "").replace("_STOP", ""),
            "volume": order["volume"],
            "open_price": order["price"],
            "sl": order.get("sl"),
            "tp": order.get("tp"),
            "profit": 0.0,
            "open_time": datetime.now().isoformat(),
            "comment": order.get("comment", "")
        }
        
        self.open_positions_list.append(position)
        
        # Update SL/TP values
        if order.get("sl"):
            self.sl_value = order["sl"]
            logger.info(f"[SL] clamp activated at {self.sl_value}")
        
        if order.get("tp"):
            self.tp_value = order["tp"]
            logger.info(f"[TP] placed at {self.tp_value}")
        
        # Calculate and log RR
        if order.get("sl") and order.get("tp"):
            risk_pips = abs(order["price"] - order["sl"]) / (0.0001 if "JPY" not in self.symbol else 0.01)
            reward_pips = abs(order["tp"] - order["price"]) / (0.0001 if "JPY" not in self.symbol else 0.01)
            rr_ratio = reward_pips / risk_pips if risk_pips > 0 else 0
            logger.info(f"[RR] Risk/Reward ratio: 1:{rr_ratio:.1f}")
        
        # Send trade fill to trade recording service
        await self._send_trade_fill_update(position)
        
        # Send acknowledgment
        await self._send_command_ack("PLACE_ORDER", "success", f"Order filled at {order['price']}")
    
    async def _process_command(self, command: Dict):
        """Process a command from the dashboard"""
        command_type = command.get("command")
        parameters = command.get("parameters", {})
        
        logger.info(f"📨 Received command: {command_type} with parameters: {parameters}")
        
        try:
            if command_type == "PLACE_ORDER":
                await self._handle_place_order(parameters)
            elif command_type == "MODIFY_ORDER":
                await self._handle_modify_order(parameters)
            elif command_type == "CANCEL_ORDER":
                await self._handle_cancel_order(parameters)
            elif command_type == "CLOSE_POSITION":
                await self._handle_close_position(parameters)
            elif command_type == "PAUSE_TRADING":
                await self._handle_pause_trading(parameters)
            elif command_type == "RESUME_TRADING":
                await self._handle_resume_trading(parameters)
            elif command_type in ["PING", "LATENCY_TEST"]:
                await self._handle_ping(parameters)
            else:
                logger.warning(f"Unknown command: {command_type}")
                await self._send_command_ack(command_type, "error", f"Unknown command: {command_type}")
                
        except Exception as e:
            logger.error(f"Command processing error: {e}")
            await self._send_command_ack(command_type, "error", str(e))
    
    async def _handle_place_order(self, params: Dict):
        """Handle place order command"""
        order = {
            "order_id": f"order_{int(time.time())}_{random.randint(1000, 9999)}",
            "order_type": params.get("order_type", "BUY_LIMIT"),
            "symbol": params.get("symbol", self.symbol),
            "volume": params.get("volume", 0.01),
            "price": params.get("price", self.current_price),
            "sl": params.get("sl"),
            "tp": params.get("tp"),
            "comment": params.get("comment", ""),
            "timestamp": datetime.now().isoformat()
        }
        
        self.pending_orders.append(order)
        
        logger.info(f"[ENTRY] Order placed: {order['order_type']} {order['volume']} {order['symbol']} @ {order['price']}")
        
        await self._send_command_ack("PLACE_ORDER", "success", f"Order placed: {order['order_id']}")
    
    async def _handle_modify_order(self, params: Dict):
        """Handle modify order command"""
        order_id = params.get("order_id")
        
        # Find order to modify
        order_found = False
        for order in self.pending_orders:
            if order["order_id"] == order_id:
                # Update order parameters
                if "new_price" in params:
                    order["price"] = params["new_price"]
                if "new_sl" in params:
                    order["sl"] = params["new_sl"]
                if "new_tp" in params:
                    order["tp"] = params["new_tp"]
                
                order_found = True
                logger.info(f"[MODIFY] Order {order_id} modified")
                break
        
        if order_found:
            await self._send_command_ack("MODIFY_ORDER", "success", f"Order {order_id} modified")
        else:
            await self._send_command_ack("MODIFY_ORDER", "error", f"Order {order_id} not found")
    
    async def _handle_cancel_order(self, params: Dict):
        """Handle cancel order command"""
        order_id = params.get("order_id")
        
        # Find and remove order
        order_found = False
        for order in self.pending_orders[:]:  # Copy list to avoid modification during iteration
            if order["order_id"] == order_id:
                self.pending_orders.remove(order)
                order_found = True
                logger.info(f"[CANCEL] Order {order_id} cancelled")
                break
        
        if order_found:
            await self._send_command_ack("CANCEL_ORDER", "success", f"Order {order_id} cancelled")
        else:
            await self._send_command_ack("CANCEL_ORDER", "error", f"Order {order_id} not found")
    
    async def _handle_close_position(self, params: Dict):
        """Handle close position command"""
        position_id = params.get("position_id")
        
        # Find and close position
        position_found = False
        closed_position = None
        for position in self.open_positions_list[:]:
            if position["position_id"] == position_id:
                # Calculate profit
                if position["order_type"] == "BUY":
                    profit = (self.current_price - position["open_price"]) * position["volume"] * 100000
                else:  # SELL
                    profit = (position["open_price"] - self.current_price) * position["volume"] * 100000
                
                # Close position
                position["close_price"] = self.current_price
                position["close_time"] = datetime.now().isoformat()
                position["profit"] = round(profit, 2)
                
                # Store for trade recording
                closed_position = position.copy()
                
                # Move to trade history
                self.trade_history.append(position)
                self.open_positions_list.remove(position)
                
                # Update totals
                self.current_profit -= profit  # Remove from current profit
                self.total_profit += profit
                self.trade_count += 1
                if profit > 0:
                    self.win_count += 1
                
                position_found = True
                logger.info(f"[CLOSE] Position {position_id} closed with profit: {profit:.2f}")
                break
        
        if position_found and closed_position:
            # Send trade close to trade recording service
            await self._send_trade_close_update(closed_position)
            await self._send_command_ack("CLOSE_POSITION", "success", f"Position {position_id} closed")
        else:
            await self._send_command_ack("CLOSE_POSITION", "error", f"Position {position_id} not found")
    
    async def _handle_pause_trading(self, params: Dict):
        """Handle pause trading command"""
        self.is_paused = True
        logger.info("[PAUSE] Trading paused")
        await self._send_command_ack("PAUSE_TRADING", "success", "Trading paused")
    
    async def _handle_resume_trading(self, params: Dict):
        """Handle resume trading command"""
        self.is_paused = False
        logger.info("[RESUME] Trading resumed")
        await self._send_command_ack("RESUME_TRADING", "success", "Trading resumed")
    
    async def _handle_ping(self, params: Dict):
        """Handle ping/latency test command"""
        test_id = params.get("test_id", "ping")
        logger.info(f"[PING] Responding to {test_id}")
        await self._send_command_ack("LATENCY_TEST", "success", f"Pong: {test_id}")
    
    async def _send_command_ack(self, command: str, status: str, message: str = ""):
        """Send command acknowledgment"""
        ack = {
            "magic_number": self.magic_number,
            "command": command,
            "status": status,
            "timestamp": datetime.now().isoformat()
        }
        
        if message:
            ack["message"] = message
        
        result = await self._api_request("POST", "/api/ea/command-ack", ack)
        logger.debug(f"Command ack sent: {result.get('status', 'unknown')}")
    
    async def _send_trade_fill_update(self, position: Dict):
        """Send trade fill update to trade recording service"""
        try:
            fill_data = {
                "magic_number": self.magic_number,
                "event_type": "FILL",
                "trade_data": {
                    "magic_number": self.magic_number,
                    "ticket": random.randint(100000, 999999),  # Mock MT5 ticket
                    "symbol": position["symbol"],
                    "order_type": position["order_type"],
                    "volume": position["volume"],
                    "price": position["open_price"],
                    "sl": position.get("sl"),
                    "tp": position.get("tp"),
                    "comment": position.get("comment", ""),
                    "commission": 0.0,
                    "swap": 0.0
                },
                "timestamp": datetime.now().isoformat()
            }
            
            result = await self._api_request("POST", "/api/trades/mt5-update", fill_data)
            logger.debug(f"Trade fill update sent: {result.get('success', False)}")
            
        except Exception as e:
            logger.error(f"Failed to send trade fill update: {e}")
    
    async def _send_trade_close_update(self, position: Dict):
        """Send trade close update to trade recording service"""
        try:
            close_data = {
                "magic_number": self.magic_number,
                "event_type": "CLOSE",
                "trade_data": {
                    "magic_number": self.magic_number,
                    "ticket": random.randint(100000, 999999),  # Mock MT5 ticket
                    "symbol": position["symbol"],
                    "close_price": position.get("close_price", self.current_price),
                    "profit": position.get("profit", 0.0),
                    "commission": 0.0,
                    "swap": 0.0
                },
                "timestamp": datetime.now().isoformat()
            }
            
            result = await self._api_request("POST", "/api/trades/mt5-update", close_data)
            logger.debug(f"Trade close update sent: {result.get('success', False)}")
            
        except Exception as e:
            logger.error(f"Failed to send trade close update: {e}")
    
    def _update_performance_metrics(self):
        """Update performance metrics"""
        # Update current profit from open positions
        total_current_profit = 0.0
        
        for position in self.open_positions_list:
            if position["order_type"] == "BUY":
                profit = (self.current_price - position["open_price"]) * position["volume"] * 100000
            else:  # SELL
                profit = (position["open_price"] - self.current_price) * position["volume"] * 100000
            
            position["profit"] = round(profit, 2)
            total_current_profit += profit
        
        self.current_profit = round(total_current_profit, 2)
        
        # Update profit factor
        if self.trade_count > 0:
            win_rate = self.win_count / self.trade_count
            avg_win = sum(t["profit"] for t in self.trade_history if t["profit"] > 0) / max(self.win_count, 1)
            avg_loss = abs(sum(t["profit"] for t in self.trade_history if t["profit"] < 0)) / max(self.trade_count - self.win_count, 1)
            
            if avg_loss > 0:
                self.profit_factor = (win_rate * avg_win) / ((1 - win_rate) * avg_loss)
            else:
                self.profit_factor = 2.0  # Default if no losses


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='EA Response Simulator')
    parser.add_argument('--magic', type=int, default=12345, help='EA Magic Number')
    parser.add_argument('--symbol', default='EURUSD', help='Trading Symbol')
    parser.add_argument('--host', default='127.0.0.1', help='Server Host')
    parser.add_argument('--port', type=int, default=80, help='Server Port')
    
    args = parser.parse_args()
    
    simulator = EASimulator(args.magic, args.symbol, args.host, args.port)
    
    try:
        await simulator.start()
    except KeyboardInterrupt:
        logger.info("Simulator stopped by user")
    except Exception as e:
        logger.error(f"Simulator error: {e}")
    finally:
        await simulator.stop()


if __name__ == "__main__":
    asyncio.run(main())