#!/usr/bin/env python3
"""
MT5 COC Dashboard System Runner

This script provides a unified way to start the entire MT5 COC Dashboard system
with proper error handling, logging, and service coordination.

Features:
- Automatic dependency checking
- Database initialization
- Service startup coordination  
- Health monitoring
- Graceful shutdown

Usage:
    python run_system.py [options]
"""

import asyncio
import argparse
import logging
import signal
import sys
import subprocess
import time
import os
from pathlib import Path
from typing import Optional, List
import json

# Add backend to Python path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/system.log') if Path('logs').exists() else logging.NullHandler()
    ]
)
logger = logging.getLogger(__name__)


class SystemRunner:
    """Manages the entire MT5 COC Dashboard system"""
    
    def __init__(self, config: dict):
        self.config = config
        self.processes = {}
        self.running = False
        self.health_check_interval = 30  # seconds
        
    def check_dependencies(self) -> bool:
        """Check if all required dependencies are available"""
        logger.info("Checking system dependencies...")
        
        required_packages = [
            'fastapi', 'uvicorn', 'websockets', 'sqlalchemy',
            'pandas', 'numpy', 'requests', 'beautifulsoup4', 'pydantic_settings'
        ]
        
        missing_packages = []
        for package in required_packages:
            try:
                __import__(package.replace('-', '_'))
                logger.debug(f" {package}")
            except ImportError:
                logger.error(f" {package}")
                missing_packages.append(package)
        
        if missing_packages:
            logger.error(f"Missing packages: {missing_packages}")
            logger.error("Please install them with: pip install -r requirements.txt")
            return False
        
        logger.info(" All dependencies satisfied")
        return True
    
    def setup_directories(self) -> bool:
        """Create necessary directories"""
        logger.info("Setting up directory structure...")
        
        directories = [
            'data',
            'logs', 
            'data/mt5_fallback',
            'data/mt5_fallback/commands',
            'data/mt5_fallback/ea_data',
            'data/mt5_fallback/heartbeat',
            'data/mt5_globals'
        ]
        
        try:
            for directory in directories:
                Path(directory).mkdir(parents=True, exist_ok=True)
                logger.debug(f" Created/verified: {directory}")
            
            logger.info(" Directory structure ready")
            return True
            
        except Exception as e:
            logger.error(f" Failed to create directories: {e}")
            return False
    
    def initialize_database(self) -> bool:
        """Initialize the database"""
        logger.info("Initializing database...")
        
        try:
            from database.init_db import init_database
            init_database()
            logger.info(" Database initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f" Database initialization failed: {e}")
            logger.warning("️ System will continue with limited functionality")
            return False
    
    async def start_fastapi_server(self) -> Optional[subprocess.Popen]:
        """Start the FastAPI server"""
        logger.info("Starting FastAPI server...")
        
        try:
            cmd = [
                sys.executable, 'main.py'
            ]
            
            process = subprocess.Popen(
                cmd,
                cwd=backend_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Give it time to start
            await asyncio.sleep(3)
            
            if process.poll() is None:
                logger.info(f" FastAPI server started (PID: {process.pid})")
                return process
            else:
                stdout, stderr = process.communicate()
                logger.error(f" FastAPI server failed to start: {stderr}")
                return None
                
        except Exception as e:
            logger.error(f" Failed to start FastAPI server: {e}")
            return None
    
    async def start_websocket_server(self) -> Optional[subprocess.Popen]:
        """Start the WebSocket server"""
        logger.info("Starting WebSocket server...")
        
        try:
            cmd = [
                sys.executable, 'start_websocket.py'
            ]
            
            process = subprocess.Popen(
                cmd,
                cwd=backend_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Give it time to start
            await asyncio.sleep(2)
            
            if process.poll() is None:
                logger.info(f" WebSocket server started (PID: {process.pid})")
                return process
            else:
                stdout, stderr = process.communicate()
                logger.error(f" WebSocket server failed to start: {stderr}")
                return None
                
        except Exception as e:
            logger.error(f" Failed to start WebSocket server: {e}")
            return None
    
    async def health_check(self) -> dict:
        """Perform system health check"""
        health_status = {
            'fastapi': False,
            'websocket': False,
            'database': False,
            'overall': False
        }
        
        # Check FastAPI server
        try:
            import requests
            response = requests.get(f"http://{self.config['host']}:{self.config['port']}/health", timeout=5)
            health_status['fastapi'] = response.status_code == 200
        except:
            health_status['fastapi'] = False
        
        # Check WebSocket server
        try:
            import websockets
            uri = f"ws://{self.config['host']}:{self.config['ws_port']}"
            async with websockets.connect(uri, timeout=5) as websocket:
                health_status['websocket'] = True
        except:
            health_status['websocket'] = False
        
        # Check database
        try:
            from database.connection import test_database_connection
            health_status['database'] = test_database_connection()
        except:
            health_status['database'] = False
        
        health_status['overall'] = all([
            health_status['fastapi'],
            health_status['websocket']
        ])
        
        return health_status
    
    async def monitor_services(self):
        """Monitor running services and restart if needed"""
        while self.running:
            try:
                # Check if processes are still alive
                for service_name, process in self.processes.items():
                    if process and process.poll() is not None:
                        logger.warning(f"️ {service_name} process died, attempting restart...")
                        
                        if service_name == 'fastapi':
                            self.processes['fastapi'] = await self.start_fastapi_server()
                        elif service_name == 'websocket':
                            self.processes['websocket'] = await self.start_websocket_server()
                
                # Perform health check
                health = await self.health_check()
                logger.debug(f"Health status: {health}")
                
                if not health['overall']:
                    logger.warning("️ System health check failed")
                
                await asyncio.sleep(self.health_check_interval)
                
            except Exception as e:
                logger.error(f"Error in service monitoring: {e}")
                await asyncio.sleep(5)
    
    async def start(self):
        """Start the entire system"""
        logger.info(" Starting MT5 COC Dashboard System...")
        
        # Pre-flight checks
        if not self.check_dependencies():
            logger.error(" Dependency check failed")
            return False
        
        if not self.setup_directories():
            logger.error(" Directory setup failed")
            return False
        
        self.initialize_database()  # Continue even if this fails
        
        # Start services
        self.running = True
        
        # Start FastAPI server
        fastapi_process = await self.start_fastapi_server()
        if fastapi_process:
            self.processes['fastapi'] = fastapi_process
        
        # Start WebSocket server
        websocket_process = await self.start_websocket_server()
        if websocket_process:
            self.processes['websocket'] = websocket_process
        
        # Check if at least one server started
        if not any(self.processes.values()):
            logger.error(" Failed to start any services")
            return False
        
        # Display status
        logger.info("=" * 60)
        logger.info(" MT5 COC Dashboard System Started!")
        logger.info("=" * 60)
        logger.info(f" FastAPI Server: http://{self.config['host']}:{self.config['port']}")
        logger.info(f" WebSocket Server: ws://{self.config['host']}:{self.config['ws_port']}")
        logger.info(f" API Documentation: http://{self.config['host']}:{self.config['port']}/docs")
        logger.info("=" * 60)
        
        # Start monitoring
        monitor_task = asyncio.create_task(self.monitor_services())
        
        try:
            # Keep running until interrupted
            while self.running:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        finally:
            monitor_task.cancel()
            await self.stop()
        
        return True
    
    async def stop(self):
        """Stop all services gracefully"""
        logger.info("Stopping MT5 COC Dashboard System...")
        self.running = False
        
        for service_name, process in self.processes.items():
            if process and process.poll() is None:
                logger.info(f"Stopping {service_name}...")
                process.terminate()
                
                # Wait for graceful shutdown
                try:
                    process.wait(timeout=10)
                    logger.info(f" {service_name} stopped gracefully")
                except subprocess.TimeoutExpired:
                    logger.warning(f"️ Force killing {service_name}")
                    process.kill()
        
        logger.info(" System stopped")


def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}")
    # The main loop will handle the actual shutdown


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='MT5 COC Dashboard System')
    parser.add_argument('--host', default='155.138.174.196', help='Host to bind to')
    parser.add_argument('--port', type=int, default=80, help='FastAPI server port')
    parser.add_argument('--ws-port', type=int, default=8765, help='WebSocket server port')
    parser.add_argument('--dev', action='store_true', help='Development mode')
    parser.add_argument('--log-level', default='INFO', help='Logging level')
    
    args = parser.parse_args()
    
    # Configure logging level
    logging.getLogger().setLevel(getattr(logging, args.log_level.upper()))
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create system configuration
    config = {
        'host': args.host,
        'port': args.port,
        'ws_port': args.ws_port,
        'dev_mode': args.dev
    }
    
    # Create and start system
    system = SystemRunner(config)
    success = await system.start()
    
    if not success:
        logger.error(" System startup failed")
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("System stopped by user")
    except Exception as e:
        logger.error(f"System error: {e}")
        sys.exit(1)


