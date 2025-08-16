#!/usr/bin/env python3
"""
Simple Backend Server Runner

Run this from the backend directory to start just the FastAPI server
"""

import sys
import os
from pathlib import Path

# Add current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Also add parent directory for backend imports
parent_dir = current_dir.parent
sys.path.insert(0, str(parent_dir))

if __name__ == "__main__":
    import uvicorn
    from main import app
    
    # Get configuration
    host = os.getenv("HOST", "155.138.174.196")
    port = int(os.getenv("PORT", 80))
    
    print(f"Starting FastAPI server on {host}:{port}")
    print(f"API Documentation: http://{host}:{port}/docs")
    
    # Run the server
    uvicorn.run(
        app,
        host=host,
        port=port,
        reload=False,
        log_level="info"
    )