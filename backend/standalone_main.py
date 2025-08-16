
import sys
import os
import asyncio
import threading
import time
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def start_backend_server():
    """Start the FastAPI backend server"""
    try:
        import uvicorn
        from main import app
        
        # Create data directories
        Path("data").mkdir(exist_ok=True)
        Path("logs").mkdir(exist_ok=True)
        
        print(" Starting FastAPI backend on port 8000...")
        uvicorn.run(app, host="155.138.174.196", port=8000, log_level="info")
    except Exception as e:
        print(f" Backend server error: {e}")

def start_websocket_server():
    """Start the WebSocket server"""
    try:
        # Import your websocket server
        from start_websocket_simple import main as websocket_main
        print(" Starting WebSocket server on port 8765...")
        asyncio.run(websocket_main())
    except Exception as e:
        print(f" WebSocket server error: {e}")

if __name__ == "__main__":
    print(" Starting MT5 Dashboard Backend Services...")
    
    # Start WebSocket server in a separate thread
    websocket_thread = threading.Thread(target=start_websocket_server, daemon=True)
    websocket_thread.start()
    
    # Give WebSocket server time to start
    time.sleep(2)
    
    # Start FastAPI server (this will block)
    start_backend_server()
