"""
WebSocket Server for Real-time Updates

Provides WebSocket communication for real-time updates between dashboard and backend
"""

import asyncio
import json
import logging
import websockets
from datetime import datetime
from typing import Dict, Set, Any, Optional, List
from websockets.server import WebSocketServerProtocol
import threading

logger = logging.getLogger(__name__)


class WebSocketServer:
    """WebSocket server for real-time communication"""
    
    def __init__(self, host: str = None, port: int = None, auth_token: str = None):
        # Import config here to avoid circular imports
        try:
            from config.environment import Config
            self.host = host or Config.get_host()
            self.port = port or Config.get_ws_port()
            self.auth_token = auth_token or Config.get_auth_token()
        except ImportError:
            # Fallback if config not available
            self.host = host or "0.0.0.0"
            try:
                from backend.config.urls import WS_PORT
            except ImportError:
                from config.urls import WS_PORT
            self.port = port or WS_PORT
            self.auth_token = auth_token or "dashboard_token_2024"
        
        # Connected clients
        self.clients: Set[WebSocketServerProtocol] = set()
        self.authenticated_clients: Set[WebSocketServerProtocol] = set()
        
        # Server instance
        self.server = None
        self.running = False
        
    async def start_server(self):
        """Start the WebSocket server"""
        try:
            logger.info(f"Starting WebSocket server on {self.host}:{self.port}")
            
            self.server = await websockets.serve(
                self.handle_client,
                self.host,
                self.port,
                ping_interval=30,
                ping_timeout=10
            )
            
            self.running = True
            logger.info(f"✅ WebSocket server started on ws://{self.host}:{self.port}")
            
            # Start price updates in background
            price_task = asyncio.create_task(self.start_price_updates())
            
            # Keep server running
            try:
                await self.server.wait_closed()
            finally:
                price_task.cancel()
            
        except Exception as e:
            logger.error(f"WebSocket server error: {e}")
            raise
    
    async def stop_server(self):
        """Stop the WebSocket server"""
        self.running = False
        
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            
        # Close all client connections
        if self.clients:
            await asyncio.gather(
                *[client.close() for client in self.clients],
                return_exceptions=True
            )
        
        self.clients.clear()
        self.authenticated_clients.clear()
        
        logger.info("WebSocket server stopped")
    
    async def handle_client(self, websocket: WebSocketServerProtocol, path: str):
        """Handle new client connection"""
        client_addr = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
        logger.info(f"New WebSocket connection from {client_addr}")
        
        self.clients.add(websocket)
        
        try:
            async for message in websocket:
                await self.process_message(websocket, message)
                
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"WebSocket connection closed: {client_addr}")
        except Exception as e:
            logger.error(f"WebSocket client error: {e}")
        finally:
            self.clients.discard(websocket)
            self.authenticated_clients.discard(websocket)
    
    async def process_message(self, websocket: WebSocketServerProtocol, message: str):
        """Process incoming message from client"""
        try:
            data = json.loads(message)
            message_type = data.get("type")
            
            if message_type == "auth":
                await self.handle_auth(websocket, data)
            elif message_type == "subscribe":
                await self.handle_subscribe(websocket, data)
            elif message_type == "subscribe_prices":
                await self.handle_subscribe_prices(websocket, data)
            elif message_type == "unsubscribe_prices":
                await self.handle_unsubscribe_prices(websocket, data)
            elif message_type == "heartbeat":
                await self.handle_heartbeat(websocket, data)
            elif message_type == "ping":
                await self.handle_ping(websocket, data)
            else:
                logger.debug(f"Unknown message type: {message_type}")
                # Send error response for unknown message types
                await self.send_error(websocket, f"Unknown message type: {message_type}")
                
        except json.JSONDecodeError:
            logger.error("Invalid JSON received from client")
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    async def handle_auth(self, websocket: WebSocketServerProtocol, data: Dict[str, Any]):
        """Handle authentication request"""
        auth_data = data.get("data", {})
        token = auth_data.get("token")
        
        if token == self.auth_token:
            self.authenticated_clients.add(websocket)
            response = {
                "type": "auth_response",
                "data": {
                    "status": "authenticated",
                    "timestamp": datetime.now().isoformat()
                }
            }
            logger.info(f"Client authenticated: {websocket.remote_address}")
        else:
            response = {
                "type": "auth_response",
                "data": {
                    "status": "failed",
                    "error": "Invalid token",
                    "timestamp": datetime.now().isoformat()
                }
            }
            logger.warning(f"Authentication failed for client: {websocket.remote_address}")
        
        await websocket.send(json.dumps(response))
    
    async def handle_subscribe(self, websocket: WebSocketServerProtocol, data: Dict[str, Any]):
        """Handle subscription request"""
        if websocket not in self.authenticated_clients:
            await websocket.send(json.dumps({
                "type": "error",
                "data": {"message": "Not authenticated"}
            }))
            return
        
        subscribe_data = data.get("data", {})
        channels = subscribe_data.get("channels", [])
        
        response = {
            "type": "subscribe_response",
            "data": {
                "status": "subscribed",
                "channels": channels,
                "timestamp": datetime.now().isoformat()
            }
        }
        
        await websocket.send(json.dumps(response))
        logger.info(f"Client subscribed to channels: {channels}")
    
    async def handle_heartbeat(self, websocket: WebSocketServerProtocol, data: Dict[str, Any]):
        """Handle heartbeat request"""
        response = {
            "type": "heartbeat_response",
            "data": {
                "timestamp": datetime.now().isoformat(),
                "server_time": datetime.now().isoformat()
            }
        }
        
        await websocket.send(json.dumps(response))
    
    async def handle_subscribe_prices(self, websocket: WebSocketServerProtocol, data: Dict[str, Any]):
        """Handle price subscription request"""
        if websocket not in self.authenticated_clients:
            await self.send_error(websocket, "Not authenticated")
            return
        
        subscribe_data = data.get("data", {})
        symbols = subscribe_data.get("symbols", [])
        
        # For now, just acknowledge the subscription
        # In a real implementation, you would start sending price updates
        response = {
            "type": "price_subscription_response",
            "data": {
                "status": "subscribed",
                "symbols": symbols,
                "message": "Price subscription acknowledged (mock data will be sent)",
                "timestamp": datetime.now().isoformat()
            }
        }
        
        await websocket.send(json.dumps(response))
        logger.debug(f"Client subscribed to price updates for symbols: {symbols}")
        
        # Send mock price data immediately
        await self.send_mock_prices(websocket, symbols)
    
    async def handle_unsubscribe_prices(self, websocket: WebSocketServerProtocol, data: Dict[str, Any]):
        """Handle price unsubscription request"""
        if websocket not in self.authenticated_clients:
            await self.send_error(websocket, "Not authenticated")
            return
        
        subscribe_data = data.get("data", {})
        symbols = subscribe_data.get("symbols", [])
        
        response = {
            "type": "price_unsubscription_response",
            "data": {
                "status": "unsubscribed",
                "symbols": symbols,
                "timestamp": datetime.now().isoformat()
            }
        }
        
        await websocket.send(json.dumps(response))
        logger.debug(f"Client unsubscribed from price updates for symbols: {symbols}")
    
    async def handle_ping(self, websocket: WebSocketServerProtocol, data: Dict[str, Any]):
        """Handle ping request"""
        response = {
            "type": "pong",
            "data": {
                "timestamp": datetime.now().isoformat(),
                "original_data": data.get("data", {})
            }
        }
        
        await websocket.send(json.dumps(response))
    
    async def send_error(self, websocket: WebSocketServerProtocol, error_message: str):
        """Send error response to client"""
        error_response = {
            "type": "error",
            "data": {
                "message": error_message,
                "timestamp": datetime.now().isoformat()
            }
        }
        
        try:
            await websocket.send(json.dumps(error_response))
        except Exception as e:
            logger.error(f"Failed to send error response: {e}")
    
    async def send_mock_prices(self, websocket: WebSocketServerProtocol, symbols: list):
        """Send current price data to client"""
        try:
            # Try to use price service
            from services.mt5_price_service import get_mt5_price_service
            price_service = get_mt5_price_service()
            
            if not symbols:
                symbols = price_service.get_all_symbols()[:8]  # Limit to first 8 symbols
            
            # Get current prices from service
            prices = price_service.get_prices(symbols)
            
            # Convert to format expected by frontend
            price_data = {}
            for symbol, price in prices.items():
                price_data[symbol] = {
                    "bid": price.bid,
                    "ask": price.ask,
                    "spread": price.spread
                }
            
        except ImportError:
            # Fallback to static mock data
            if not symbols:
                symbols = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD"]
            
            mock_prices = {
                "EURUSD": {"bid": 1.0847, "ask": 1.0849, "spread": 0.0002},
                "GBPUSD": {"bid": 1.2634, "ask": 1.2636, "spread": 0.0002},
                "USDJPY": {"bid": 149.82, "ask": 149.84, "spread": 0.02},
                "AUDUSD": {"bid": 0.6523, "ask": 0.6525, "spread": 0.0002}
            }
            
            price_data = {symbol: mock_prices.get(symbol, {"bid": 1.0000, "ask": 1.0002, "spread": 0.0002}) 
                         for symbol in symbols}
        
        price_update = {
            "type": "price_update",
            "data": {
                "prices": price_data,
                "timestamp": datetime.now().isoformat()
            }
        }
        
        try:
            await websocket.send(json.dumps(price_update))
        except Exception as e:
            logger.error(f"Failed to send prices: {e}")
    
    async def send_mock_prices(self, websocket: WebSocketServerProtocol, symbols: List[str]):
        """Send mock price data to client"""
        import random
        
        # Mock price data for common symbols
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
        
        price_data = {}
        
        for symbol in symbols:
            base_price = base_prices.get(symbol, 1.0000)
            
            # Add small random variation
            if symbol == 'XAUUSD':
                variation = random.uniform(-5.0, 5.0)
            elif 'JPY' in symbol:
                variation = random.uniform(-0.1, 0.1)
            else:
                variation = random.uniform(-0.002, 0.002)
            
            current_price = base_price + variation
            
            price_data[symbol] = {
                'symbol': symbol,
                'bid': round(current_price - 0.0001, 5),
                'ask': round(current_price + 0.0001, 5),
                'timestamp': datetime.now().isoformat(),
                'change': round(variation, 5),
                'change_percent': round((variation / base_price) * 100, 3)
            }
        
        response = {
            "type": "price_update",
            "data": {
                "prices": price_data,
                "timestamp": datetime.now().isoformat()
            }
        }
        
        try:
            await websocket.send(json.dumps(response))
        except Exception as e:
            logger.error(f"Failed to send mock prices: {e}")
    
    async def broadcast_to_authenticated(self, message: Dict[str, Any]):
        """Broadcast message to all authenticated clients"""
        if not self.authenticated_clients:
            return
        
        message_str = json.dumps(message)
        
        # Send to all authenticated clients
        disconnected_clients = set()
        
        for client in self.authenticated_clients:
            try:
                await client.send(message_str)
            except websockets.exceptions.ConnectionClosed:
                disconnected_clients.add(client)
            except Exception as e:
                logger.error(f"Error sending message to client: {e}")
                disconnected_clients.add(client)
        
        # Remove disconnected clients
        for client in disconnected_clients:
            self.clients.discard(client)
            self.authenticated_clients.discard(client)
    
    async def broadcast_trade_update(self, trade_data: Dict[str, Any]):
        """Broadcast trade update to clients"""
        message = {
            "type": "trade_update",
            "data": trade_data,
            "timestamp": datetime.now().isoformat()
        }
        
        await self.broadcast_to_authenticated(message)
    
    async def broadcast_ea_update(self, ea_data: Dict[str, Any]):
        """Broadcast EA update to clients"""
        message = {
            "type": "ea_update",
            "data": ea_data,
            "timestamp": datetime.now().isoformat()
        }
        
        await self.broadcast_to_authenticated(message)
    
    async def broadcast_command_update(self, command_data: Dict[str, Any]):
        """Broadcast command update to clients"""
        message = {
            "type": "command_update",
            "data": command_data,
            "timestamp": datetime.now().isoformat()
        }
        
        await self.broadcast_to_authenticated(message)
    
    async def broadcast_price_update(self, price_data: Dict[str, Any]):
        """Broadcast price update to clients"""
        message = {
            "type": "price_update",
            "data": price_data,
            "timestamp": datetime.now().isoformat()
        }
        
        await self.broadcast_to_authenticated(message)
    
    async def start_price_updates(self):
        """Start periodic price updates using price service"""
        try:
            # Import price service
            from services.mt5_price_service import get_mt5_price_service
            price_service = get_mt5_price_service()
            
            # Start price simulation
            simulation_task = asyncio.create_task(price_service.start_price_simulation())
            
            while self.running:
                try:
                    # Get current prices from service
                    prices = price_service.get_prices()
                    
                    # Convert to format expected by frontend
                    price_data = {}
                    for symbol, price in prices.items():
                        price_data[symbol] = {
                            "bid": price.bid,
                            "ask": price.ask,
                            "spread": price.spread
                        }
                    
                    # Broadcast price update to all authenticated clients
                    if self.authenticated_clients:
                        await self.broadcast_price_update({
                            "prices": price_data,
                            "timestamp": datetime.now().isoformat()
                        })
                    
                    # Wait before next update
                    await asyncio.sleep(2)  # Update every 2 seconds
                    
                except Exception as e:
                    logger.error(f"Error in price updates: {e}")
                    await asyncio.sleep(5)
            
            # Stop price simulation when done
            price_service.stop_price_simulation()
            simulation_task.cancel()
            
        except ImportError:
            logger.warning("Price service not available, using basic mock data")
            await self._basic_price_updates()
        except Exception as e:
            logger.error(f"Error starting price updates: {e}")
    
    async def _basic_price_updates(self):
        """Basic price updates without price service"""
        import random
        
        base_prices = {
            "EURUSD": 1.0847,
            "GBPUSD": 1.2634,
            "USDJPY": 149.82,
            "AUDUSD": 0.6523
        }
        
        while self.running:
            try:
                updated_prices = {}
                
                for symbol, base_price in base_prices.items():
                    movement = random.uniform(-0.0010, 0.0010)
                    spread = 0.0002
                    
                    new_price = base_price + movement
                    base_prices[symbol] = new_price
                    
                    updated_prices[symbol] = {
                        "bid": round(new_price, 5),
                        "ask": round(new_price + spread, 5),
                        "spread": spread
                    }
                
                if self.authenticated_clients:
                    await self.broadcast_price_update({
                        "prices": updated_prices,
                        "timestamp": datetime.now().isoformat()
                    })
                
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"Error in basic price updates: {e}")
                await asyncio.sleep(5)
    
    def get_status(self) -> Dict[str, Any]:
        """Get server status"""
        return {
            "running": self.running,
            "host": self.host,
            "port": self.port,
            "total_clients": len(self.clients),
            "authenticated_clients": len(self.authenticated_clients),
            "timestamp": datetime.now().isoformat()
        }


# Global WebSocket server instance
_websocket_server: Optional[WebSocketServer] = None


def get_websocket_server() -> WebSocketServer:
    """Get global WebSocket server instance"""
    global _websocket_server
    if _websocket_server is None:
        _websocket_server = WebSocketServer()
    return _websocket_server


def initialize_websocket_server(host: str = None, port: int = None, auth_token: str = None) -> WebSocketServer:
    """Initialize global WebSocket server with custom parameters"""
    global _websocket_server
    _websocket_server = WebSocketServer(host, port, auth_token)
    return _websocket_server


async def start_websocket_server_standalone(host: str = None, port: int = None, auth_token: str = None):
    """Start WebSocket server as standalone service"""
    server = initialize_websocket_server(host, port, auth_token)
    
    try:
        await server.start_server()
    except KeyboardInterrupt:
        logger.info("WebSocket server interrupted by user")
    except Exception as e:
        logger.error(f"WebSocket server error: {e}")
    finally:
        await server.stop_server()


if __name__ == "__main__":
    import argparse
    
    # Import config for defaults
    try:
        from config.environment import Config
        default_host = Config.get_host()
        default_port = Config.get_ws_port()
        default_token = Config.get_auth_token()
    except ImportError:
        default_host = "0.0.0.0"
        try:
            from backend.config.urls import WS_PORT
        except ImportError:
            from config.urls import WS_PORT
        default_port = WS_PORT
        default_token = "dashboard_token_2024"
    
    parser = argparse.ArgumentParser(description="WebSocket Server for MT5 Dashboard")
    parser.add_argument("--host", default=default_host, help="Server host")
    parser.add_argument("--port", type=int, default=default_port, help="Server port")
    parser.add_argument("--auth-token", default=default_token, help="Authentication token")
    
    args = parser.parse_args()
    
    asyncio.run(start_websocket_server_standalone(args.host, args.port, args.auth_token))