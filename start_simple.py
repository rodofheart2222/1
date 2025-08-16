#!/usr/bin/env python3
"""
Simple Starter - Just Backend

The simplest way to start the backend server
"""

import sys
import os
from pathlib import Path

# Add paths
current_dir = Path.cwd()
backend_dir = current_dir / "backend"
sys.path.insert(0, str(current_dir))
sys.path.insert(0, str(backend_dir))

# Set environment
os.environ['PYTHONPATH'] = f"{current_dir}{os.pathsep}{backend_dir}"
os.environ['HOST'] = '0.0.0.0'
os.environ['PORT'] = '8000'
os.environ['WS_PORT'] = '8765'

print("🚀 Starting MT5 Dashboard Backend...")
print("📍 Host: 155.138.174.196:8000")
print("📚 API Docs: http://155.138.174.196:8000/docs")
print("🔌 WebSocket: ws://155.138.174.196:8765")
print("=" * 50)

# Change to backend directory and run
os.chdir(backend_dir)

if __name__ == "__main__":
    import uvicorn
    from main import app
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )