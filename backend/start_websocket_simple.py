#!/usr/bin/env python3
"""
Simple WebSocket Server Startup Script

This is a simplified version that avoids complex dependencies
and just starts the WebSocket server for real-time communication.
"""

import asyncio
import logging
import signal
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Simple WebSocket server without complex dependencies
class SimpleWebSocketServer:
    """Simple WebSocket server manager"""
    
    def __init__(self, host="155.138.174.196", port=8765):
        self.host = host
        self.port = port
        self.server = None
        self.running = False
        
    async def start(self):
        """Start the WebSocket server"""
        try:
            import websockets
            
            async def handle_client(websocket, path):
                """Handle WebSocket client connections"""
                client_id = f"client_{id(websocket)}"
                logger.info(f"New client connected: {client_id}")
                
                try:
                    # Send welcome message
                    welcome_msg = {
                        "type": "connection",
                        "data": {
                            "status": "connected",
                            "client_id": client_id,
                            "message": "Connected to MT5 COC Dashboard WebSocket Server"
                        }
                    }
                    await websocket.send(str(welcome_msg).replace("'", '"'))
                    
                    # Handle incoming messages
                    async for message in websocket:
                        try:
                            logger.debug(f"Received message from {client_id}: {message}")
                            
                            # Echo back for now - can be extended later
                            response = {
                                "type": "echo",
                                "data": {"received": True, "original": message}
                            }
                            await websocket.send(str(response).replace("'", '"'))
                            
                        except Exception as e:
                            logger.error(f"Error handling message from {client_id}: {e}")
                            
                except websockets.exceptions.ConnectionClosed:
                    logger.info(f"Client {client_id} disconnected")
                except Exception as e:
                    logger.error(f"Error handling client {client_id}: {e}")
                finally:
                    logger.info(f"Cleaned up client {client_id}")
            
            # Start the server
            self.server = await websockets.serve(
                handle_client,
                self.host,
                self.port,
                ping_interval=20,
                ping_timeout=10
            )
            
            self.running = True
            logger.info(f" WebSocket server started on ws://{self.host}:{self.port}")
            logger.info(" Ready to accept client connections")
            
            # Keep running
            while self.running:
                await asyncio.sleep(1)
                
        except ImportError:
            logger.error(" websockets package not found. Install with: pip install websockets")
            raise
        except Exception as e:
            logger.error(f" Failed to start WebSocket server: {e}")
            raise
    
    async def stop(self):
        """Stop the WebSocket server"""
        logger.info("Stopping WebSocket server...")
        self.running = False
        
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            logger.info(" WebSocket server stopped")

# Global server instance
websocket_server = SimpleWebSocketServer()

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}, shutting down...")
    asyncio.create_task(websocket_server.stop())

async def main():
    """Main entry point"""
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        logger.info(" Starting MT5 COC Dashboard WebSocket Server...")
        await websocket_server.start()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)
    finally:
        await websocket_server.stop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        sys.exit(1)


