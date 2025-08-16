#!/usr/bin/env python3
"""
Frontend Server Starter

This script starts the React frontend development server.
"""

import subprocess
import sys
import os
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_node_installed():
    """Check if Node.js is installed"""
    try:
        result = subprocess.run(['node', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            logger.info(f"✅ Node.js version: {result.stdout.strip()}")
            return True
        else:
            logger.error("❌ Node.js not found")
            return False
    except FileNotFoundError:
        logger.error("❌ Node.js not installed")
        return False


def check_npm_installed():
    """Check if npm is installed"""
    try:
        result = subprocess.run(['npm', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            logger.info(f"✅ npm version: {result.stdout.strip()}")
            return True
        else:
            logger.error("❌ npm not found")
            return False
    except FileNotFoundError:
        logger.error("❌ npm not installed")
        return False


def install_dependencies():
    """Install npm dependencies"""
    frontend_dir = Path("frontend")
    if not frontend_dir.exists():
        logger.error("❌ Frontend directory not found")
        return False
    
    logger.info("📦 Installing npm dependencies...")
    try:
        result = subprocess.run(
            ['npm', 'install'], 
            cwd=frontend_dir, 
            capture_output=True, 
            text=True
        )
        
        if result.returncode == 0:
            logger.info("✅ Dependencies installed successfully")
            return True
        else:
            logger.error(f"❌ Failed to install dependencies: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error installing dependencies: {e}")
        return False


def start_frontend_dev_server():
    """Start the frontend development server"""
    frontend_dir = Path("frontend")
    
    logger.info("🚀 Starting React development server...")
    try:
        # Start the development server
        process = subprocess.Popen(
            ['npm', 'run', 'dev'],
            cwd=frontend_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        logger.info("✅ Frontend development server started")
        logger.info("🌐 Frontend should be available at http://localhost:3000")
        
        # Stream output
        try:
            for line in iter(process.stdout.readline, ''):
                if line:
                    print(f"[Frontend] {line.rstrip()}")
        except KeyboardInterrupt:
            logger.info("🛑 Stopping frontend server...")
            process.terminate()
            process.wait()
            logger.info("✅ Frontend server stopped")
            
    except Exception as e:
        logger.error(f"❌ Failed to start frontend server: {e}")
        return False


def main():
    """Main entry point"""
    logger.info("=" * 60)
    logger.info("🎯 STARTING FRONTEND DEVELOPMENT SERVER")
    logger.info("=" * 60)
    
    # Check prerequisites
    if not check_node_installed():
        logger.error("Please install Node.js from https://nodejs.org/")
        return 1
    
    if not check_npm_installed():
        logger.error("npm should be installed with Node.js")
        return 1
    
    # Check if frontend directory exists
    if not Path("frontend").exists():
        logger.error("❌ Frontend directory not found")
        return 1
    
    # Install dependencies if node_modules doesn't exist
    if not Path("frontend/node_modules").exists():
        if not install_dependencies():
            return 1
    
    # Start the development server
    try:
        start_frontend_dev_server()
        return 0
    except KeyboardInterrupt:
        logger.info("Frontend server stopped by user")
        return 0
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())