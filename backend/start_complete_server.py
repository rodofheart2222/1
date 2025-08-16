#!/usr/bin/env python3
"""
Complete MT5 Dashboard Server Startup

This script starts the complete backend system including:
- FastAPI server
- WebSocket server
- MT5 trade tracker
- Database initialization

Usage:
    python start_complete_server.py [--host HOST] [--port PORT] [--ws-port WS_PORT]
    
Environment variables can be set in .env file or system environment.
"""

# Load environment variables first
import sys
from pathlib import Path
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

try:
    import load_env  # This will auto-load .env file
except ImportError:
    pass  # Continue without .env loading

import asyncio
import uvicorn
import threading
import signal
import sys
import os
import logging
from pathlib import Path
from datetime import datetime
import argparse

# Add backend to Python path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CompleteServerManager:
    """Manages all backend services"""
    
    def __init__(self, host: str = None, port: int = None, ws_port: int = None):
        # Import config here to avoid circular imports
        from config.environment import Config
        
        self.host = host or Config.get_host()
        self.port = port or Config.get_api_port()
        self.ws_port = ws_port or Config.get_ws_port()
        self.running = False
        
        # Service instances
        self.fastapi_server = None
        self.websocket_server = None
        self.mt5_tracker = None
        
        # Background tasks
        self.websocket_task = None
        self.mt5_task = None
    
    async def initialize_services(self):
        """Initialize all services"""
        logger.info("🔧 Initializing backend services...")
        
        try:
            # Initialize database
            from database.init_db import init_database, verify_database_integrity
            
            if not init_database():
                logger.warning("Database initialization failed, continuing with in-memory storage")
            else:
                logger.info("✅ Database initialized successfully")
            
            # Initialize WebSocket server (bind to all interfaces)
            from services.websocket_server import initialize_websocket_server
            from config.environment import Config
            
            self.websocket_server = initialize_websocket_server(
                self.host, 
                self.ws_port, 
                Config.get_auth_token()
            )
            logger.info("✅ WebSocket server initialized")
            
            # Initialize MT5 trade tracker
            from services.mt5_trade_tracker import get_mt5_trade_tracker
            self.mt5_tracker = get_mt5_trade_tracker()
            
            # Try to initialize MT5 connection
            try:
                mt5_success = await self.mt5_tracker.initialize()
                if mt5_success:
                    logger.info("✅ MT5 trade tracker initialized")
                else:
                    logger.warning("⚠️ MT5 not available, using mock data")
            except Exception as e:
                logger.warning(f"⚠️ MT5 initialization failed: {e}, using mock data")
            
            # Initialize trade recording service
            from services.trade_recording_service import get_trade_recording_service
            trade_service = get_trade_recording_service()
            logger.info("✅ Trade recording service initialized")
            
            # Initialize real-time EA updater
            from services.real_time_ea_updater import get_ea_updater
            self.ea_updater = get_ea_updater()
            try:
                ea_updater_success = await self.ea_updater.initialize()
                if ea_updater_success:
                    logger.info("✅ Real-time EA updater initialized")
                    
                    # Do initial EA sync on startup
                    logger.info("🔄 Performing initial EA sync with MT5...")
                    initial_sync_success = await self.ea_updater.force_sync_with_mt5()
                    if initial_sync_success:
                        logger.info("✅ Initial EA sync completed")
                    else:
                        logger.warning("⚠️ Initial EA sync failed")
                else:
                    logger.warning("⚠️ EA updater initialization failed")
            except Exception as e:
                logger.warning(f"⚠️ EA updater initialization failed: {e}")
            
            logger.info("🎯 All services initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Service initialization failed: {e}")
            return False
    
    async def start_websocket_server(self):
        """Start WebSocket server in background"""
        try:
            logger.info(f"🔌 Starting WebSocket server on {self.host}:{self.ws_port}")
            await self.websocket_server.start_server()
        except Exception as e:
            logger.error(f"WebSocket server error: {e}")
    
    async def start_mt5_tracking(self):
        """Start MT5 tracking in background"""
        try:
            if self.mt5_tracker and self.mt5_tracker.mt5_connected:
                logger.info("📊 Starting MT5 trade tracking")
                await self.mt5_tracker.start_tracking()
            else:
                logger.info("📊 MT5 not connected, skipping trade tracking")
                # Keep the task alive
                while self.running:
                    await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"MT5 tracking error: {e}")
    
    async def start_ea_updates(self):
        """Start EA updates in background"""
        try:
            if hasattr(self, 'ea_updater'):
                logger.info("🔄 Starting real-time EA updates")
                await self.ea_updater.start_updates()
            else:
                logger.info("🔄 EA updater not available, skipping updates")
                # Keep the task alive
                while self.running:
                    await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"EA updater error: {e}")
            # Keep the task alive even if there's an error
            while self.running:
                await asyncio.sleep(5)
    
    def start_fastapi_server(self):
        """Start FastAPI server in separate thread"""
        try:
            logger.info(f"🚀 Starting FastAPI server on {self.host}:{self.port}")
            
            # Set environment variables
            os.environ['HOST'] = self.host
            os.environ['PORT'] = str(self.port)
            os.environ['WS_PORT'] = str(self.ws_port)
            os.environ['ENVIRONMENT'] = 'production'
            
            # Import the FastAPI app
            from main import app
            
            # Configure uvicorn
            config = uvicorn.Config(
                app,
                host=self.host,
                port=self.port,
                log_level="info",
                access_log=True
            )
            
            server = uvicorn.Server(config)
            server.run()
            
        except Exception as e:
            logger.error(f"FastAPI server error: {e}")
    
    async def start_all_services(self):
        """Start all services"""
        logger.info("=" * 80)
        logger.info("🎯 MT5 DASHBOARD COMPLETE SERVER STARTUP")
        logger.info("=" * 80)
        logger.info(f"📍 Host: {self.host}")
        logger.info(f"🚀 FastAPI: http://{self.host}:{self.port}")
        logger.info(f"📚 API Docs: http://{self.host}:{self.port}/docs")
        logger.info(f"🔌 WebSocket: ws://{self.host}:{self.ws_port}")
        logger.info("=" * 80)
        
        # Initialize services
        if not await self.initialize_services():
            logger.error("❌ Failed to initialize services")
            return False
        
        self.running = True
        
        try:
            # Start FastAPI server in thread
            fastapi_thread = threading.Thread(
                target=self.start_fastapi_server,
                daemon=True
            )
            fastapi_thread.start()
            
            # Give FastAPI time to start
            await asyncio.sleep(2)
            logger.info("✅ FastAPI server started")
            
            # Start background services
            tasks = []
            
            # WebSocket server
            self.websocket_task = asyncio.create_task(self.start_websocket_server())
            tasks.append(self.websocket_task)
            
            # MT5 tracking
            self.mt5_task = asyncio.create_task(self.start_mt5_tracking())
            tasks.append(self.mt5_task)
            
            # EA updater (always start, it will handle connection issues)
            if hasattr(self, 'ea_updater'):
                self.ea_updater_task = asyncio.create_task(self.start_ea_updates())
                tasks.append(self.ea_updater_task)
                logger.info("✅ Real-time EA updater started")
            
            logger.info("✅ All services started successfully")
            logger.info("🎉 Server is ready to accept connections!")
            logger.info("=" * 80)
            
            # Wait for all tasks
            await asyncio.gather(*tasks, return_exceptions=True)
            
        except Exception as e:
            logger.error(f"❌ Error starting services: {e}")
            return False
        finally:
            await self.stop_all_services()
    
    async def stop_all_services(self):
        """Stop all services"""
        logger.info("🛑 Stopping all services...")
        self.running = False
        
        try:
            # Stop WebSocket server
            if self.websocket_server:
                await self.websocket_server.stop_server()
                logger.info("✅ WebSocket server stopped")
            
            # Stop MT5 tracker
            if self.mt5_tracker:
                await self.mt5_tracker.shutdown()
                logger.info("✅ MT5 tracker stopped")
            
            # Stop EA updater
            if hasattr(self, 'ea_updater'):
                await self.ea_updater.stop_updates()
                logger.info("✅ EA updater stopped")
            
            # Cancel background tasks
            if self.websocket_task and not self.websocket_task.done():
                self.websocket_task.cancel()
            
            if self.mt5_task and not self.mt5_task.done():
                self.mt5_task.cancel()
            
            if hasattr(self, 'ea_updater_task') and not self.ea_updater_task.done():
                self.ea_updater_task.cancel()
            
            logger.info("✅ All services stopped")
            
        except Exception as e:
            logger.error(f"Error stopping services: {e}")


# Global server manager
server_manager = None


def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}, shutting down...")
    if server_manager:
        asyncio.create_task(server_manager.stop_all_services())
    sys.exit(0)


async def main():
    """Main entry point"""
    global server_manager
    
    # Import config for defaults
    from config.environment import Config
    
    parser = argparse.ArgumentParser(description='Complete MT5 Dashboard Server')
    parser.add_argument('--host', default=Config.get_host(), help='Server host')
    parser.add_argument('--port', type=int, default=Config.get_api_port(), help='FastAPI port')
    parser.add_argument('--ws-port', type=int, default=Config.get_ws_port(), help='WebSocket port')
    
    args = parser.parse_args()
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    server_manager = CompleteServerManager(args.host, args.port, args.ws_port)
    
    try:
        await server_manager.start_all_services()
    except KeyboardInterrupt:
        logger.info("Server interrupted by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)