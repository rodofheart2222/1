#!/usr/bin/env python3
"""
Simple MT5 COC Dashboard System Starter

This script starts the system with minimal dependencies to avoid import issues.
"""

import asyncio
import subprocess
import sys
import time
import os
from pathlib import Path

def check_dependencies():
    """Check basic dependencies"""
    required = ['fastapi', 'uvicorn', 'websockets']
    missing = []
    
    for package in required:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    if missing:
        print(f" Missing packages: {missing}")
        print(f" Install with: pip install {' '.join(missing)}")
        return False
    
    print(" Basic dependencies satisfied")
    return True

def start_fastapi():
    """Start FastAPI server"""
    print(" Starting FastAPI server...")
    
    try:
        # Change to backend directory
        os.chdir(Path(__file__).parent)
        
        # Start FastAPI server
        process = subprocess.Popen([
            sys.executable, 'main.py'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        return process
    except Exception as e:
        print(f" Failed to start FastAPI: {e}")
        return None

def start_websocket():
    """Start WebSocket server"""
    print(" Starting WebSocket server...")
    
    try:
        # Start simple WebSocket server
        process = subprocess.Popen([
            sys.executable, 'start_websocket_simple.py'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        return process
    except Exception as e:
        print(f" Failed to start WebSocket server: {e}")
        return None

def main():
    """Main startup function"""
    print(" MT5 COC Dashboard - Simple System Startup")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        print("\n Install missing packages and try again")
        return
    
    # Create required directories
    directories = ['data', 'logs', 'data/mt5_fallback', 'data/mt5_globals']
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    print(" Directory structure ready")
    
    # Initialize database
    print("️ Initializing database...")
    try:
        subprocess.run([sys.executable, 'database/init_db.py'], check=True)
        print(" Database initialized")
    except Exception as e:
        print(f"️ Database initialization failed: {e}")
        print(" Continuing anyway...")
    
    # Start services
    fastapi_process = start_fastapi()
    if not fastapi_process:
        print(" Failed to start FastAPI server")
        return
    
    # Wait a moment for FastAPI to start
    time.sleep(3)
    
    websocket_process = start_websocket()
    if not websocket_process:
        print(" Failed to start WebSocket server")
        if fastapi_process:
            fastapi_process.terminate()
        return
    
    print("\n System started successfully!")
    print("=" * 50)
    print(" FastAPI Server: http://155.138.174.196:80")
    print(" WebSocket Server: ws://155.138.174.196:8765")
    print(" API Documentation: http://155.138.174.196:80/docs")
    print("=" * 50)
    print("\n Next steps:")
    print("1. Open another terminal and run:")
    print("   cd frontend && npm run dev")
    print("2. Access dashboard at: http://155.138.174.196:3000")
    print("\n️ Press Ctrl+C to stop all services")
    
    try:
        # Monitor processes
        while True:
            # Check if processes are still running
            if fastapi_process.poll() is not None:
                print("️ FastAPI server stopped unexpectedly")
                break
            
            if websocket_process.poll() is not None:
                print("️ WebSocket server stopped unexpectedly")
                break
            
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n Stopping services...")
        
        # Stop processes gracefully
        if fastapi_process:
            fastapi_process.terminate()
            try:
                fastapi_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                fastapi_process.kill()
        
        if websocket_process:
            websocket_process.terminate()
            try:
                websocket_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                websocket_process.kill()
        
        print(" All services stopped")

if __name__ == "__main__":
    main()


