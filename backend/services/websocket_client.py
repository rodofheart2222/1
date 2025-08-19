"""
WebSocket Client Helper

This module provides a WebSocket client for testing and integration purposes.
It can be used to test the WebSocket server functionality and as a reference
for frontend implementation.
"""

import asyncio
import json
import logging
from typing import Dict, List, Callable, Optional
import websockets
from websockets.client import WebSocketClientProtocol
from websockets.exceptions import ConnectionClosed, WebSocketException


logger = logging.getLogger(__name__)


class WebSocketClient:
    """WebSocket client for testing and integration"""
    
    def __init__(self, uri: str, auth_token: str = "dashboard_token"):
        self.uri = uri
        self.auth_token = auth_token
        self.websocket: Optional[WebSocketClientProtocol] = None
        self.authenticated = False
        self.subscriptions = set()
        self.message_handlers: Dict[str, Callable] = {}
        self.running = False
        
    async def connect(self):
        """Connect to WebSocket server"""
        try:
            self.websocket = await websockets.connect(self.uri)
            self.running = True
            logger.info(f"Connected to WebSocket server at {self.uri}")
            
            # Start message handling task
            asyncio.create_task(self.message_handler())
            
            # Start heartbeat task
            asyncio.create_task(self.heartbeat_task())
            
        except Exception as e:
            logger.error(f"Failed to connect to WebSocket server: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from WebSocket server"""
        if self.websocket:
            self.running = False
            await self.websocket.close()
            logger.info("Disconnected from WebSocket server")
    
    async def authenticate(self):
        """Authenticate with the server"""
        if not self.websocket:
            raise RuntimeError("Not connected to server")
        
        auth_message = {
            "type": "auth",
            "data": {"token": self.auth_token}
        }
        
        await self.websocket.send(json.dumps(auth_message))
        logger.info("Authentication request sent")
    
    async def subscribe(self, channels: List[str]):
        """Subscribe to message channels"""
        if not self.websocket or not self.authenticated:
            raise RuntimeError("Not connected or not authenticated")
        
        subscribe_message = {
            "type": "subscribe",
            "data": {"channels": channels}
        }
        
        await self.websocket.send(json.dumps(subscribe_message))
        self.subscriptions.update(channels)
        logger.info(f"Subscribed to channels: {channels}")
    
    async def unsubscribe(self, channels: List[str]):
        """Unsubscribe from message channels"""
        if not self.websocket:
            raise RuntimeError("Not connected to server")
        
        unsubscribe_message = {
            "type": "unsubscribe",
            "data": {"channels": channels}
        }
        
        await self.websocket.send(json.dumps(unsubscribe_message))
        for channel in channels:
            self.subscriptions.discard(channel)
        logger.info(f"Unsubscribed from channels: {channels}")
    
    async def send_heartbeat(self):
        """Send heartbeat to server"""
        if not self.websocket:
            return
        
        heartbeat_message = {
            "type": "heartbeat",
            "data": {}
        }
        
        await self.websocket.send(json.dumps(heartbeat_message))
    
    async def message_handler(self):
        """Handle incoming messages from server"""
        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    message_type = data.get("type")
                    payload = data.get("data", {})
                    
                    # Handle authentication response
                    if message_type == "auth_response":
                        if payload.get("status") == "authenticated":
                            self.authenticated = True
                            logger.info("Authentication successful")
                        else:
                            logger.error(f"Authentication failed: {payload.get('message')}")
                    
                    # Call registered message handler
                    if message_type in self.message_handlers:
                        await self.message_handlers[message_type](payload)
                    
                    logger.debug(f"Received message: {message_type}")
                    
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON received: {message}")
                except Exception as e:
                    logger.error(f"Error handling message: {e}")
                    
        except ConnectionClosed:
            logger.info("Connection closed by server")
        except WebSocketException as e:
            logger.error(f"WebSocket error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in message handler: {e}")
        finally:
            self.running = False
    
    async def heartbeat_task(self):
        """Send periodic heartbeats to server"""
        while self.running:
            try:
                await self.send_heartbeat()
                await asyncio.sleep(25)  # Send heartbeat every 25 seconds
            except Exception as e:
                logger.error(f"Error sending heartbeat: {e}")
                break
    
    def register_message_handler(self, message_type: str, handler: Callable):
        """Register a handler for specific message type"""
        self.message_handlers[message_type] = handler
        logger.info(f"Registered handler for message type: {message_type}")
    
    def unregister_message_handler(self, message_type: str):
        """Unregister a message handler"""
        if message_type in self.message_handlers:
            del self.message_handlers[message_type]
            logger.info(f"Unregistered handler for message type: {message_type}")


# Example usage and testing functions

async def test_client_connection():
    """Test basic client connection and authentication"""
    try:
        from backend.config.urls import WS_URL
    except ImportError:
        from config.urls import WS_URL
    client = WebSocketClient(WS_URL)
    
    try:
        await client.connect()
        await client.authenticate()
        
        # Wait for authentication
        await asyncio.sleep(1)
        
        if client.authenticated:
            # Subscribe to channels
            await client.subscribe(["ea_updates", "portfolio_updates"])
            
            # Keep connection alive for testing
            await asyncio.sleep(10)
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
    finally:
        await client.disconnect()


async def test_message_handling():
    """Test message handling with custom handlers"""
    try:
        from backend.config.urls import WS_URL
    except ImportError:
        from config.urls import WS_URL
    client = WebSocketClient(WS_URL)
    
    # Register message handlers
    async def handle_ea_update(data):
        print(f"EA Update received: {data}")
    
    async def handle_portfolio_update(data):
        print(f"Portfolio Update received: {data}")
    
    client.register_message_handler("ea_update", handle_ea_update)
    client.register_message_handler("portfolio_update", handle_portfolio_update)
    
    try:
        await client.connect()
        await client.authenticate()
        await asyncio.sleep(1)
        
        if client.authenticated:
            await client.subscribe(["ea_updates", "portfolio_updates"])
            
            # Keep connection alive to receive messages
            await asyncio.sleep(30)
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
    finally:
        await client.disconnect()


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Run test
    asyncio.run(test_client_connection())