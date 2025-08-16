#!/usr/bin/env python3
"""
Simple Backend Starter

Starts the backend server with proper path handling
"""

import sys
import os
from pathlib import Path

# Add both current directory and backend directory to Python path
current_dir = Path.cwd()
backend_dir = current_dir / "backend"

# Add to sys.path
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# Set PYTHONPATH environment variable
pythonpath = os.environ.get('PYTHONPATH', '')
paths_to_add = [str(current_dir), str(backend_dir)]

for path in paths_to_add:
    if path not in pythonpath:
        pythonpath = f"{path}{os.pathsep}{pythonpath}" if pythonpath else path

os.environ['PYTHONPATH'] = pythonpath

# Change to backend directory
os.chdir(backend_dir)

# Now import and run the main app
if __name__ == "__main__":
    import uvicorn
    from main import app
    
    # Get configuration
    host = os.getenv("HOST", "155.138.174.196")
    port = int(os.getenv("PORT", 80))
    
    print(f"Starting FastAPI server on {host}:{port}")
    print(f"API Documentation: http://{host}:{port}/docs")
    print(f"Health Check: http://{host}:{port}/health")
    
    # Run the server
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )