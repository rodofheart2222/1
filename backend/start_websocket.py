#!/usr/bin/env python3
"""
WebSocket Server Startup Script

Starts the WebSocket server with proper configuration and integration
with the main MT5 COC Dashboard backend.
"""

import asyncio
import logging
import signal
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from config.settings import settings
from services.websocket_server import start_websocket_server, stop_websocket_server

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class WebSocketServerManager:
    """Manages WebSocket server lifecycle"""
    
    def __init__(self):
        self.websocket_server = None
        self.running = False
    
    async def start(self):
        """Start WebSocket server"""
        try:
            logger.info(f"Starting WebSocket server on {settings.WS_HOST}:{settings.WS_PORT}")
            
            # Start WebSocket server
            self.websocket_server = await start_websocket_server(
                host=settings.WS_HOST,
                port=settings.WS_PORT,
                auth_token="dashboard_token"
            )
            
            self.running = True
            logger.info("WebSocket server started successfully")
            logger.info(f" WebSocket server listening on ws://{settings.WS_HOST}:{settings.WS_PORT}")
            
            # Keep running until stopped
            while self.running:
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"Failed to start WebSocket server: {e}")
            raise
    
    async def stop(self):
        """Stop WebSocket server"""
        logger.info("Stopping WebSocket server...")
        self.running = False
        
        try:
            if self.websocket_server:
                await stop_websocket_server()
                
            logger.info("WebSocket server stopped successfully")
            
        except Exception as e:
            logger.error(f"Error stopping WebSocket server: {e}")

# Global server manager instance
server_manager = WebSocketServerManager()

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}, shutting down gracefully...")
    asyncio.create_task(server_manager.stop())

async def main():
    """Main entry point"""
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        await server_manager.start()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)
    finally:
        await server_manager.stop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        sys.exit(1)
