#!/usr/bin/env python3
"""
Start WebSocket Server Only

Simple script to start just the WebSocket server for testing
"""

import asyncio
import sys
from pathlib import Path

# Add backend to Python path
backend_path = Path.cwd() / "backend"
sys.path.insert(0, str(backend_path))

async def main():
    """Start WebSocket server"""
    try:
        from services.websocket_server import WebSocketServer
        
        # Create server instance
        server = WebSocketServer("0.0.0.0", 8765, "dashboard_token_2024")
        
        print("🔌 Starting WebSocket server...")
        print(f"📍 Binding to: 0.0.0.0:8765")
        print(f"🌐 Connect to: ws://155.138.174.196:8765")
        print(f"🔑 Auth token: dashboard_token_2024")
        print("=" * 50)
        
        # Start server
        await server.start_server()
        
    except KeyboardInterrupt:
        print("\n🛑 WebSocket server stopped by user")
    except Exception as e:
        print(f"❌ WebSocket server error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("Interrupted")
        sys.exit(0)