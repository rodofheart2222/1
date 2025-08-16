#!/usr/bin/env python3
"""
WebSocket Server Startup for Railway Deployment
"""

import asyncio
import os
import logging
from services.start_websocket_server import start_integrated_system

async def main():
    """Start WebSocket server for Railway"""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Get configuration from environment
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8765))
    auth_token = os.getenv("WS_AUTH_TOKEN", "railway_dashboard_token_2024")
    
    print(f" Starting WebSocket server on {host}:{port}")
    print(f" Auth token: {auth_token}")
    
    # Start the integrated system
    await start_integrated_system(host, port, auth_token)

if __name__ == "__main__":
    asyncio.run(main())