#!/usr/bin/env python3
"""
Start WebSocket server with MT5 price service integration

This script starts the WebSocket server and automatically subscribes to
common forex symbols for real-time price updates.
"""

import asyncio
import logging
import signal
import sys
from typing import List

from services.websocket_server import start_websocket_server, stop_websocket_server
from services.mt5_price_service import mt5_price_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Common forex symbols to subscribe to
DEFAULT_SYMBOLS = [
    'EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 
    'AUDUSD', 'USDCAD', 'NZDUSD', 'XAUUSD'
]

class PriceWebSocketServer:
    """WebSocket server with integrated price service"""
    
    def __init__(self, host: str = "155.138.174.196", port: int = 8765):
        self.host = host
        self.port = port
        self.websocket_server = None
        self.running = False
        
    async def start(self, symbols: List[str] = None):
        """Start the server and price service"""
        if symbols is None:
            symbols = DEFAULT_SYMBOLS
            
        try:
            logger.info("Starting WebSocket server with price service...")
            
            # Start WebSocket server
            self.websocket_server = await start_websocket_server(
                host=self.host,
                port=self.port,
                auth_token="dashboard_token"
            )
            
            # Wait a moment for server to fully initialize
            await asyncio.sleep(1)
            
            # Subscribe to symbols for price updates
            logger.info(f"Subscribing to price updates for symbols: {symbols}")
            for symbol in symbols:
                try:
                    await mt5_price_service.subscribe_symbol(symbol)
                    logger.info(f"Subscribed to {symbol}")
                except Exception as e:
                    logger.error(f"Failed to subscribe to {symbol}: {e}")
            
            self.running = True
            logger.info(f"Server started successfully on ws://{self.host}:{self.port}")
            logger.info("Price service is running and streaming data")
            
            # Keep the server running
            while self.running:
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"Failed to start server: {e}")
            raise
    
    async def stop(self):
        """Stop the server and price service"""
        logger.info("Stopping server...")
        self.running = False
        
        try:
            # Stop price service
            await mt5_price_service.shutdown()
            logger.info("Price service stopped")
            
            # Stop WebSocket server
            if self.websocket_server:
                await stop_websocket_server()
                logger.info("WebSocket server stopped")
                
        except Exception as e:
            logger.error(f"Error stopping server: {e}")


async def main():
    """Main function"""
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description='Start WebSocket server with MT5 price service')
    parser.add_argument('--host', default='155.138.174.196', help='Server host (default: 155.138.174.196)')
    parser.add_argument('--port', type=int, default=8765, help='Server port (default: 8765)')
    parser.add_argument('--symbols', nargs='*', help='Symbols to subscribe to (default: common forex pairs)')
    
    args = parser.parse_args()
    
    # Create server instance
    server = PriceWebSocketServer(host=args.host, port=args.port)
    
    # Setup signal handlers for graceful shutdown
    def signal_handler():
        logger.info("Received shutdown signal")
        asyncio.create_task(server.stop())
    
    # Register signal handlers
    if sys.platform != 'win32':
        loop = asyncio.get_event_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, signal_handler)
    
    try:
        # Start server
        symbols = args.symbols if args.symbols else DEFAULT_SYMBOLS
        await server.start(symbols)
        
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Server error: {e}")
    finally:
        await server.stop()
        logger.info("Server shutdown complete")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
    except Exception as e:
        logger.error(f"Application error: {e}")
        sys.exit(1)