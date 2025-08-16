#!/usr/bin/env python3
"""
Fix and Start MT5 Dashboard System

This script fixes common issues and starts the complete system:
1. Fixes import paths
2. Initializes database
3. Starts backend server
4. Runs health checks
5. Provides system status

Usage:
    python fix_and_start_system.py [--host 155.138.174.196] [--port 80]
"""

import asyncio
import subprocess
import sys
import os
import time
import logging
from pathlib import Path
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SystemFixer:
    """Fixes and starts the MT5 Dashboard system"""
    
    def __init__(self, host: str = None, port: int = None):
        # Import config for defaults
        try:
            import sys
            from pathlib import Path
            backend_path = Path(__file__).parent / "backend"
            sys.path.insert(0, str(backend_path))
            from config.environment import Config
            self.host = host or Config.get_host()
            self.port = port or Config.get_api_port()
        except ImportError:
            # Fallback if config not available
            self.host = host or "127.0.0.1"
            self.port = port or 8000
        self.backend_process = None
        
    def fix_python_path(self):
        """Fix Python path issues"""
        logger.info("🔧 Fixing Python path...")
        
        # Add current directory and backend to Python path
        current_dir = Path.cwd()
        backend_dir = current_dir / "backend"
        
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
        
        logger.info("✅ Python path fixed")
    
    def create_directories(self):
        """Create necessary directories"""
        logger.info("📁 Creating directories...")
        
        directories = [
            "data",
            "logs", 
            "data/mt5_fallback",
            "data/mt5_globals",
            "backend/data",
            "backend/logs"
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
        
        logger.info("✅ Directories created")
    
    def initialize_database(self):
        """Initialize database"""
        logger.info("🗄️ Initializing database...")
        
        try:
            # Add backend to path for imports
            backend_path = Path.cwd() / "backend"
            sys.path.insert(0, str(backend_path))
            
            from backend.database.init_db import init_database, verify_database_integrity
            
            # Initialize database
            if init_database():
                logger.info("✅ Database initialized successfully")
                
                # Verify integrity
                if verify_database_integrity():
                    logger.info("✅ Database integrity verified")
                    return True
                else:
                    logger.warning("⚠️ Database integrity check failed")
                    return False
            else:
                logger.error("❌ Database initialization failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ Database setup error: {e}")
            return False
    
    def install_dependencies(self):
        """Install missing dependencies"""
        logger.info("📦 Checking dependencies...")
        
        required_packages = [
            "fastapi",
            "uvicorn",
            "websockets",
            "aiohttp",
            "sqlalchemy",
            "pydantic"
        ]
        
        missing_packages = []
        
        for package in required_packages:
            try:
                __import__(package)
            except ImportError:
                missing_packages.append(package)
        
        if missing_packages:
            logger.info(f"Installing missing packages: {missing_packages}")
            try:
                subprocess.check_call([
                    sys.executable, "-m", "pip", "install"
                ] + missing_packages)
                logger.info("✅ Dependencies installed")
            except subprocess.CalledProcessError as e:
                logger.error(f"❌ Failed to install dependencies: {e}")
                return False
        else:
            logger.info("✅ All dependencies available")
        
        return True
    
    async def start_backend_server(self):
        """Start the backend server"""
        logger.info("🚀 Starting backend server...")
        
        try:
            # Use the complete server startup script
            self.backend_process = subprocess.Popen([
                sys.executable, "backend/start_complete_server.py",
                "--host", self.host,
                "--port", str(self.port),
                "--ws-port", "8765"
            ], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True
            )
            
            # Wait a moment for server to start
            await asyncio.sleep(5)
            
            # Check if process is still running
            if self.backend_process.poll() is None:
                logger.info("✅ Backend server started successfully")
                return True
            else:
                stdout, stderr = self.backend_process.communicate()
                logger.error(f"❌ Backend server failed to start:")
                logger.error(f"STDOUT: {stdout}")
                logger.error(f"STDERR: {stderr}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to start backend server: {e}")
            return False
    
    async def run_health_check(self):
        """Run system health check"""
        logger.info("🔍 Running health check...")
        
        try:
            # First try a quick test
            process = subprocess.Popen([
                sys.executable, "quick_test.py"
            ], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True
            )
            
            stdout, stderr = process.communicate(timeout=10)  # 10 second timeout
            
            if process.returncode == 0:
                logger.info("✅ Quick health check passed")
                logger.info(f"Server response: {stdout.strip()}")
                
                # Now run the full health test
                logger.info("Running full health check...")
                process = subprocess.Popen([
                    sys.executable, "test_system_health.py",
                    "--host", self.host,
                    "--port", str(self.port)
                ], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True
                )
                
                stdout, stderr = process.communicate(timeout=30)  # 30 second timeout
                
                if process.returncode == 0:
                    logger.info("✅ Full health check passed")
                    return True
                else:
                    logger.warning("⚠️ Full health check had issues, but server is responding")
                    return True  # Server is at least responding
            else:
                logger.error("❌ Health check failed")
                logger.error(f"Quick test output: {stdout}")
                logger.error(f"Quick test errors: {stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("❌ Health check timed out")
            return False
        except Exception as e:
            logger.error(f"❌ Health check error: {e}")
            return False
    
    def stop_backend_server(self):
        """Stop the backend server"""
        if self.backend_process:
            logger.info("🛑 Stopping backend server...")
            try:
                self.backend_process.terminate()
                self.backend_process.wait(timeout=10)
                logger.info("✅ Backend server stopped")
            except subprocess.TimeoutExpired:
                logger.warning("⚠️ Force killing backend server...")
                self.backend_process.kill()
                self.backend_process.wait()
            except Exception as e:
                logger.error(f"Error stopping backend server: {e}")
    
    async def fix_and_start_system(self):
        """Fix issues and start the complete system"""
        logger.info("=" * 80)
        logger.info("🔧 MT5 DASHBOARD SYSTEM FIXER AND STARTER")
        logger.info("=" * 80)
        logger.info(f"Host: {self.host}:{self.port}")
        logger.info("=" * 80)
        
        try:
            # Step 1: Fix Python path
            self.fix_python_path()
            
            # Step 2: Create directories
            self.create_directories()
            
            # Step 3: Install dependencies
            if not self.install_dependencies():
                logger.error("❌ Failed to install dependencies")
                return False
            
            # Step 4: Initialize database
            if not self.initialize_database():
                logger.warning("⚠️ Database initialization failed, continuing anyway")
            
            # Step 5: Start backend server
            if not await self.start_backend_server():
                logger.error("❌ Failed to start backend server")
                return False
            
            # Step 6: Run health check
            if not await self.run_health_check():
                logger.warning("⚠️ Health check failed, but server is running")
            
            # Step 7: Show status
            logger.info("=" * 80)
            logger.info("🎉 SYSTEM STARTED SUCCESSFULLY!")
            logger.info("=" * 80)
            logger.info(f"🌐 API Server: http://{self.host}:{self.port}")
            logger.info(f"📚 API Documentation: http://{self.host}:{self.port}/docs")
            logger.info(f"🔌 WebSocket Server: ws://{self.host}:8765")
            logger.info(f"🔍 Health Check: http://{self.host}:{self.port}/health")
            logger.info("=" * 80)
            logger.info("Press Ctrl+C to stop the server")
            
            # Keep running until interrupted
            try:
                while True:
                    await asyncio.sleep(1)
                    
                    # Check if backend process is still running
                    if self.backend_process.poll() is not None:
                        logger.error("❌ Backend server stopped unexpectedly")
                        break
                        
            except KeyboardInterrupt:
                logger.info("🛑 Received interrupt signal")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ System startup failed: {e}")
            return False
        finally:
            self.stop_backend_server()
    
    def show_troubleshooting_info(self):
        """Show troubleshooting information"""
        logger.info("=" * 80)
        logger.info("🔧 TROUBLESHOOTING INFORMATION")
        logger.info("=" * 80)
        logger.info("If the system failed to start, try these steps:")
        logger.info("")
        logger.info("1. Check Python version (requires Python 3.8+):")
        logger.info("   python --version")
        logger.info("")
        logger.info("2. Install dependencies manually:")
        logger.info("   pip install fastapi uvicorn websockets aiohttp sqlalchemy pydantic")
        logger.info("")
        logger.info("3. Check if ports are available:")
        logger.info(f"   netstat -an | grep {self.port}")
        logger.info("   netstat -an | grep 8765")
        logger.info("")
        logger.info("4. Run individual components:")
        logger.info("   python backend/start_complete_server.py")
        logger.info("   python test_system_health.py")
        logger.info("")
        logger.info("5. Check logs in the console output above")
        logger.info("=" * 80)


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Fix and Start MT5 Dashboard System")
    # Try to get defaults from config
    try:
        import sys
        from pathlib import Path
        backend_path = Path(__file__).parent / "backend"
        sys.path.insert(0, str(backend_path))
        from config.environment import Config
        default_host = Config.get_external_host()
        default_port = Config.get_api_port()
    except ImportError:
        default_host = "127.0.0.1"
        default_port = 8000
    
    parser.add_argument("--host", default=default_host, help="Server host")
    parser.add_argument("--port", type=int, default=default_port, help="Server port")
    parser.add_argument("--troubleshoot", action="store_true", help="Show troubleshooting info only")
    
    args = parser.parse_args()
    
    fixer = SystemFixer(args.host, args.port)
    
    if args.troubleshoot:
        fixer.show_troubleshooting_info()
        return 0
    
    try:
        success = await fixer.fix_and_start_system()
        return 0 if success else 1
    except KeyboardInterrupt:
        logger.info("System startup interrupted by user")
        return 0
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        fixer.show_troubleshooting_info()
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("Interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)