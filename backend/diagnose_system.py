#!/usr/bin/env python3
"""
MT5 COC Dashboard System Diagnostic Tool

This script checks the system health and helps diagnose common issues.
"""

import requests
import socket
import subprocess
import sys
import time
from pathlib import Path

def check_port(host, port):
    """Check if a port is open"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except:
        return False

def check_process_running(process_name):
    """Check if a process is running (basic check)"""
    try:
        if sys.platform == "win32":
            cmd = f'tasklist /FI "IMAGENAME eq python.exe"'
        else:
            cmd = "ps aux | grep python"
        
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return process_name in result.stdout.lower()
    except:
        return False

def check_api_endpoint(url):
    """Check if an API endpoint responds"""
    try:
        response = requests.get(url, timeout=5)
        return response.status_code == 200
    except:
        return False

def check_dependencies():
    """Check if required Python packages are installed"""
    required_packages = [
        'fastapi', 'uvicorn', 'websockets', 'sqlalchemy',
        'pandas', 'numpy', 'requests', 'beautifulsoup4', 'pydantic_settings'
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing.append(package)
    
    return missing

def check_files():
    """Check if required files exist"""
    required_files = [
        'main.py',
        'requirements.txt',
        'database/init_db.py',
        'start_websocket.py',
        'config/settings.py'
    ]
    
    missing = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing.append(file_path)
    
    return missing

def main():
    """Run system diagnostics"""
    print(" MT5 COC Dashboard System Diagnostics")
    print("=" * 50)
    
    # Check dependencies
    print("\n Checking Python Dependencies...")
    missing_deps = check_dependencies()
    if missing_deps:
        print(f" Missing packages: {', '.join(missing_deps)}")
        print(f" Install with: pip install {' '.join(missing_deps)}")
    else:
        print(" All required packages are installed")
    
    # Check files
    print("\n Checking Required Files...")
    missing_files = check_files()
    if missing_files:
        print(f" Missing files: {', '.join(missing_files)}")
    else:
        print(" All required files found")
    
    # Check ports
    print("\n Checking Network Ports...")
    
    # FastAPI port (80)
    if check_port('155.138.174.196', 80):
        print(" Port 80 (FastAPI) is open")
        
        # Check API endpoint
        if check_api_endpoint('http://155.138.174.196:80/health'):
            print(" FastAPI server is responding")
        else:
            print("️ Port 80 is open but API not responding")
    else:
        print(" Port 80 (FastAPI) is not available")
        print(" Start with: cd backend && python main.py")
    
    # WebSocket port (8765)
    if check_port('155.138.174.196', 8765):
        print(" Port 8765 (WebSocket) is open")
    else:
        print(" Port 8765 (WebSocket) is not available")
        print(" Start with: cd backend && python start_websocket.py")
    
    # Frontend port (3000)
    if check_port('155.138.174.196', 3000):
        print(" Port 3000 (Frontend) is open")
    else:
        print("️ Port 3000 (Frontend) is not available")
        print(" Start with: cd frontend && npm run dev")
    
    # Check database
    print("\n️ Checking Database...")
    db_path = Path('data/mt5_dashboard.db')
    if db_path.exists():
        print(f" Database file exists ({db_path.stat().st_size} bytes)")
    else:
        print(" Database file not found")
        print(" Initialize with: python database/init_db.py")
    
    # Directory structure
    print("\n Checking Directory Structure...")
    required_dirs = ['data', 'logs', 'data/mt5_fallback', 'data/mt5_globals']
    for dir_path in required_dirs:
        if Path(dir_path).exists():
            print(f" {dir_path}/")
        else:
            print(f"️ {dir_path}/ missing (will be created automatically)")
    
    # System summary
    print("\n System Status Summary")
    print("=" * 30)
    
    issues = []
    if missing_deps:
        issues.append("Missing Python dependencies")
    if missing_files:
        issues.append("Missing required files")
    if not check_port('155.138.174.196', 80):
        issues.append("FastAPI server not running")
    if not check_port('155.138.174.196', 8765):
        issues.append("WebSocket server not running")
    if not db_path.exists():
        issues.append("Database not initialized")
    
    if not issues:
        print(" System appears to be healthy!")
        print(" Try accessing: http://155.138.174.196:3000")
    else:
        print("️ Issues found:")
        for issue in issues:
            print(f"   • {issue}")
        print("\n See SYSTEM_STARTUP_GUIDE.md for detailed troubleshooting")
    
    print("\n Quick Links:")
    print("   • Backend API: http://155.138.174.196:80")
    print("   • API Docs: http://155.138.174.196:80/docs")
    print("   • Frontend: http://155.138.174.196:3000")
    print("   • Health Check: http://155.138.174.196:80/health")

if __name__ == "__main__":
    main()


