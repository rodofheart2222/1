#!/usr/bin/env python3
"""
Fixed System Starter - Uses development server for frontend
"""

import subprocess
import sys
import os
import time
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def start_backend():
    """Start backend server"""
    logger.info("🚀 Starting backend server...")
    
    cmd = [sys.executable, "backend/start_complete_server.py", "--host", "0.0.0.0", "--port", "8000"]
    
    backend_process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    
    return backend_process

def start_frontend():
    """Start frontend development server"""
    logger.info("🌐 Starting frontend development server...")
    
    # Set environment variables for frontend
    env = os.environ.copy()
    env.update({
        'PORT': '3000',
        'REACT_APP_API_URL': 'http://155.138.174.196:8000',
        'REACT_APP_WS_URL': 'ws://155.138.174.196:8765',
        'BROWSER': 'none'
    })
    
    cmd = ["npm", "run", "dev"]
    
    frontend_process = subprocess.Popen(
        cmd,
        cwd="frontend",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env=env
    )
    
    return frontend_process

def main():
    logger.info("=" * 60)
    logger.info("🎯 Starting MT5 Dashboard System")
    logger.info("=" * 60)
    
    try:
        # Start backend
        backend_process = start_backend()
        logger.info(f"✅ Backend started (PID: {backend_process.pid})")
        
        # Wait for backend to initialize
        time.sleep(8)
        
        # Start frontend
        frontend_process = start_frontend()
        logger.info(f"✅ Frontend started (PID: {frontend_process.pid})")
        
        logger.info("=" * 60)
        logger.info("🎉 System started successfully!")
        logger.info("🌐 Frontend: http://155.138.174.196:3000")
        logger.info("🚀 Backend: http://155.138.174.196:8000")
        logger.info("📚 API Docs: http://155.138.174.196:8000/docs")
        logger.info("=" * 60)
        logger.info("Press Ctrl+C to stop")
        
        # Monitor processes
        while True:
            if backend_process.poll() is not None:
                logger.error("❌ Backend process died")
                break
            if frontend_process.poll() is not None:
                logger.error("❌ Frontend process died")
                break
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("🛑 Shutting down...")
        try:
            backend_process.terminate()
            frontend_process.terminate()
        except:
            pass
    except Exception as e:
        logger.error(f"❌ Error: {e}")

if __name__ == "__main__":
    main()