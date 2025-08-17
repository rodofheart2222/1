#!/usr/bin/env python3
"""
Complete Backend Server Startup Script

This script starts both the FastAPI backend server and the WebSocket server
together in a single process, making it easier to manage.

Usage:
    python start_complete_server.py [--host 0.0.0.0] [--port 8000] [--ws-port 8765]
"""

import asyncio
import sys
import os
import argparse
import logging
import signal
from pathlib import Path
from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import services
from backend.services.websocket_server import WebSocketServer
from backend.database.base import init_db
from backend.api import ea_api, backtest_api, news_api, trade_api

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CompleteServer:
    """Manages both FastAPI and WebSocket server"""
    
    def __init__(self, host="0.0.0.0", port=8000, ws_port=8765):
        self.host = host
        self.port = port
        self.ws_port = ws_port
        self.websocket_server = None
        self.app = None
        self.running = False
        
    def create_app(self):
        """Create and configure FastAPI application"""
        
        @asynccontextmanager
        async def lifespan(app: FastAPI):
            """Manage application lifecycle"""
            # Startup
            logger.info("🚀 Starting complete backend server...")
            
            # Initialize database
            init_db()
            logger.info("✅ Database initialized")
            
            # Start WebSocket server
            self.websocket_server = WebSocketServer(port=self.ws_port)
            asyncio.create_task(self.websocket_server.start())
            logger.info(f"✅ WebSocket server started on port {self.ws_port}")
            
            yield
            
            # Shutdown
            logger.info("🛑 Shutting down complete backend server...")
            if self.websocket_server:
                await self.websocket_server.stop()
            logger.info("✅ Server shutdown complete")
        
        # Create FastAPI app with lifespan
        app = FastAPI(
            title="MT5 Dashboard API",
            description="Complete API for MT5 Dashboard System",
            version="1.0.0",
            lifespan=lifespan
        )
        
        # Configure CORS
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # In production, specify actual origins
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Include routers
        app.include_router(ea_api.router, prefix="/api/eas", tags=["EAs"])
        app.include_router(backtest_api.router, prefix="/api/backtest", tags=["Backtest"])
        app.include_router(news_api.router, prefix="/api/news", tags=["News"])
        app.include_router(trade_api.router, prefix="/api/trades", tags=["Trades"])
        
        # Health check endpoint
        @app.get("/health")
        async def health_check():
            """Health check endpoint"""
            ws_status = "healthy" if self.websocket_server and self.websocket_server.running else "unhealthy"
            return {
                "status": "healthy",
                "api": "healthy",
                "websocket": ws_status,
                "host": self.host,
                "port": self.port,
                "ws_port": self.ws_port
            }
        
        # Root endpoint
        @app.get("/")
        async def root():
            """Root endpoint"""
            return {
                "message": "MT5 Dashboard API",
                "docs": f"http://{self.host}:{self.port}/docs",
                "health": f"http://{self.host}:{self.port}/health",
                "websocket": f"ws://{self.host}:{self.ws_port}"
            }
        
        self.app = app
        return app
    
    async def run(self):
        """Run the complete server"""
        try:
            # Create app
            app = self.create_app()
            
            # Configure uvicorn
            config = uvicorn.Config(
                app=app,
                host=self.host,
                port=self.port,
                loop="asyncio",
                log_level="info",
                access_log=True,
                use_colors=True
            )
            
            server = uvicorn.Server(config)
            
            logger.info("=" * 80)
            logger.info("🚀 COMPLETE BACKEND SERVER STARTING")
            logger.info("=" * 80)
            logger.info(f"📡 API Server: http://{self.host}:{self.port}")
            logger.info(f"📚 API Docs: http://{self.host}:{self.port}/docs")
            logger.info(f"🔍 Health Check: http://{self.host}:{self.port}/health")
            logger.info(f"🔌 WebSocket: ws://{self.host}:{self.ws_port}")
            logger.info("=" * 80)
            
            self.running = True
            
            # Run server
            await server.serve()
            
        except Exception as e:
            logger.error(f"Server error: {e}")
            raise
        finally:
            self.running = False


def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}, shutting down...")
    sys.exit(0)


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Complete MT5 Dashboard Backend Server')
    parser.add_argument('--host', default='0.0.0.0', help='Server host')
    parser.add_argument('--port', type=int, default=8000, help='API server port')
    parser.add_argument('--ws-port', type=int, default=8765, help='WebSocket server port')
    
    args = parser.parse_args()
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create and run server
    server = CompleteServer(args.host, args.port, args.ws_port)
    
    try:
        await server.run()
    except KeyboardInterrupt:
        logger.info("Server interrupted by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)