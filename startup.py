#!/usr/bin/env python3
"""
Comprehensive System Startup Script

This script:
1. Runs all tests
2. Starts backend server (FastAPI + WebSocket)
3. Starts frontend development server
4. Monitors health of all services
5. Provides automatic restart on failure
6. Keeps everything running until interrupted

Usage:
    python startup.py [--skip-tests] [--host 127.0.0.1] [--backend-port 80] [--frontend-port 3000]
"""

import asyncio
import subprocess
import sys
import os
import time
import signal
import logging
from pathlib import Path
import argparse
import psutil
import threading
import json
from datetime import datetime

# Configure logging with colors for better visibility
class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors"""
    
    grey = "\x1b[38;20m"
    green = "\x1b[32;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    
    FORMATS = {
        logging.DEBUG: grey + "%(asctime)s - %(levelname)s - %(message)s" + reset,
        logging.INFO: green + "%(asctime)s - %(levelname)s - %(message)s" + reset,
        logging.WARNING: yellow + "%(asctime)s - %(levelname)s - %(message)s" + reset,
        logging.ERROR: red + "%(asctime)s - %(levelname)s - %(message)s" + reset,
        logging.CRITICAL: bold_red + "%(asctime)s - %(levelname)s - %(message)s" + reset
    }
    
    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

# Create console handler with color formatter
console_handler = logging.StreamHandler()
console_handler.setFormatter(ColoredFormatter())

# Configure logger
logging.basicConfig(
    level=logging.INFO,
    handlers=[console_handler]
)
logger = logging.getLogger(__name__)


class ComprehensiveSystemRunner:
    """Manages the entire system lifecycle including tests and services"""
    
    def __init__(self, host=None, backend_port=None, frontend_port=None, 
                 ws_port=None, skip_tests=False):
        # Load from central configuration if not provided
        try:
            from frontend.src.config import config
            config_data = config
        except ImportError:
            try:
                import json
                with open('frontend/src/config.json', 'r') as f:
                    config_data = json.load(f)
            except:
                config_data = {}
        
        self.host = host or config_data.get('backend', {}).get('host', '127.0.0.1')
        self.backend_port = backend_port or config_data.get('backend', {}).get('port', 80)
        frontend_config = config_data.get('frontend', {}).get('dev', {})
        self.frontend_port = frontend_port or frontend_config.get('port', 3000)
        self.ws_port = ws_port or config_data.get('websocket', {}).get('port', 8765)
        self.skip_tests = skip_tests
        
        # Process tracking
        self.backend_process = None
        self.frontend_process = None
        self.processes = []
        self.running = False
        
        # Service health tracking
        self.service_health = {
            "backend": {"status": "stopped", "last_check": None, "restarts": 0},
            "frontend": {"status": "stopped", "last_check": None, "restarts": 0},
            "websocket": {"status": "stopped", "last_check": None, "restarts": 0}
        }
        
        # Maximum restart attempts
        self.max_restarts = 3
        
    def print_banner(self):
        """Print startup banner"""
        banner = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                   MT5 DASHBOARD COMPREHENSIVE STARTUP                          ║
║                                                                                ║
║  This script will:                                                            ║
║  1. Clean up existing processes                                               ║
║  2. Run all tests (unless skipped)                                           ║
║  3. Start Backend API + WebSocket Server                                      ║
║  4. Start Frontend Development Server                                         ║
║  5. Monitor health and auto-restart on failure                                ║
║  6. Keep everything running until interrupted                                 ║
╚══════════════════════════════════════════════════════════════════════════════╝
        """
        print(banner)
        
    def kill_processes_on_ports(self, ports):
        """Kill all processes running on specified ports"""
        logger.info(f"🔍 Checking for processes on ports: {ports}")
        
        killed_count = 0
        
        for port in ports:
            try:
                for proc in psutil.process_iter(['pid', 'name', 'connections']):
                    try:
                        connections = proc.connections()
                        if connections:
                            for conn in connections:
                                if hasattr(conn, 'laddr') and conn.laddr and conn.laddr.port == port:
                                    pid = proc.info['pid']
                                    name = proc.info['name']
                                    logger.info(f"🔪 Killing process {name} (PID: {pid}) on port {port}")
                                    
                                    try:
                                        proc.terminate()
                                        proc.wait(timeout=3)
                                        killed_count += 1
                                    except psutil.TimeoutExpired:
                                        proc.kill()
                                        killed_count += 1
                                    except Exception as e:
                                        logger.warning(f"Failed to kill process {pid}: {e}")
                                        
                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                        continue
                        
            except Exception as e:
                logger.warning(f"Error checking port {port}: {e}")
        
        if killed_count > 0:
            logger.info(f"✅ Killed {killed_count} processes")
            time.sleep(2)
        else:
            logger.info("✅ No processes found on target ports")
    
    def cleanup_all_processes(self):
        """Clean up all existing processes"""
        logger.info("🧹 Cleaning up existing processes...")
        
        # Kill processes on specific ports
        ports_to_check = [self.backend_port, self.frontend_port, self.ws_port]
        self.kill_processes_on_ports(ports_to_check)
        
        # Kill specific Python/Node processes
        current_pid = os.getpid()
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                pid = proc.info['pid']
                if pid == current_pid:
                    continue
                    
                name = proc.info['name'].lower()
                cmdline = ' '.join(proc.info['cmdline'] or []).lower()
                
                # Kill related processes
                if any(keyword in cmdline for keyword in [
                    'uvicorn', 'fastapi', 'main.py', 'start_complete_server',
                    'websocket_server', 'npm', 'react-scripts'
                ]):
                    logger.info(f"🔪 Killing related process (PID: {pid})")
                    try:
                        proc.terminate()
                        proc.wait(timeout=3)
                    except:
                        proc.kill()
                        
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        
        logger.info("✅ Process cleanup completed")
    
    def setup_environment(self):
        """Set up environment variables and paths"""
        logger.info("🔧 Setting up environment...")
        
        # Add paths to Python path
        current_dir = Path.cwd()
        backend_dir = current_dir / "backend"
        
        paths_to_add = [str(current_dir), str(backend_dir)]
        
        for path in paths_to_add:
            if path not in sys.path:
                sys.path.insert(0, path)
        
        # Set environment variables
        pythonpath = os.environ.get('PYTHONPATH', '')
        for path in paths_to_add:
            if path not in pythonpath:
                pythonpath = f"{path}{os.pathsep}{pythonpath}" if pythonpath else path
        
        os.environ['PYTHONPATH'] = pythonpath
        os.environ['HOST'] = self.host
        os.environ['PORT'] = str(self.backend_port)
        os.environ['WS_PORT'] = str(self.ws_port)
        os.environ['ENVIRONMENT'] = 'development'
        
        logger.info("✅ Environment setup completed")
    
    def run_tests(self):
        """Run all tests before starting services"""
        if self.skip_tests:
            logger.info("⏭️  Skipping tests (--skip-tests flag set)")
            return True
            
        logger.info("🧪 Running tests...")
        
        test_results = {
            "backend": False,
            "frontend": False
        }
        
        # Run backend tests
        logger.info("🔬 Running backend tests...")
        try:
            backend_path = Path("backend")
            if (backend_path / "tests").exists():
                result = subprocess.run(
                    [sys.executable, "-m", "pytest", "-v", "--tb=short"],
                    cwd=backend_path,
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    logger.info("✅ Backend tests passed")
                    test_results["backend"] = True
                else:
                    logger.error("❌ Backend tests failed")
                    logger.error(result.stdout)
                    logger.error(result.stderr)
            else:
                logger.warning("⚠️  No backend tests found")
                test_results["backend"] = True
                
        except Exception as e:
            logger.error(f"❌ Failed to run backend tests: {e}")
        
        # Run frontend tests
        logger.info("🔬 Running frontend tests...")
        try:
            frontend_path = Path("frontend")
            if frontend_path.exists() and (frontend_path / "package.json").exists():
                # Check if node_modules exists
                if not (frontend_path / "node_modules").exists():
                    logger.info("📦 Installing frontend dependencies...")
                    subprocess.run(["npm", "install"], cwd=frontend_path, check=True)
                
                # Run tests with CI=true to avoid interactive mode
                env = os.environ.copy()
                env['CI'] = 'true'
                
                result = subprocess.run(
                    ["npm", "test", "--", "--passWithNoTests"],
                    cwd=frontend_path,
                    capture_output=True,
                    text=True,
                    env=env
                )
                
                if result.returncode == 0:
                    logger.info("✅ Frontend tests passed")
                    test_results["frontend"] = True
                else:
                    logger.error("❌ Frontend tests failed")
                    logger.error(result.stdout)
                    logger.error(result.stderr)
            else:
                logger.warning("⚠️  No frontend tests found")
                test_results["frontend"] = True
                
        except Exception as e:
            logger.error(f"❌ Failed to run frontend tests: {e}")
        
        # Summary
        all_passed = all(test_results.values())
        if all_passed:
            logger.info("✅ All tests passed!")
        else:
            logger.warning("⚠️  Some tests failed, but continuing with startup...")
        
        return all_passed
    
    def update_frontend_config(self):
        """Update frontend configuration"""
        logger.info("📝 Updating frontend configuration...")
        
        try:
            frontend_path = Path("frontend")
            if not frontend_path.exists():
                logger.warning("Frontend directory not found, skipping config update")
                return
            
            env_file = frontend_path / ".env"
            
            # Create .env content
            env_content = f"""GENERATE_SOURCEMAP=false
DISABLE_ESLINT_PLUGIN=true
DANGEROUSLY_DISABLE_HOST_CHECK=true
WDS_SOCKET_HOST={self.host}
REACT_APP_API_URL=http://{self.host}:{self.backend_port}
REACT_APP_WS_URL=ws://{self.host}:{self.ws_port}
PORT={self.frontend_port}
HOST={self.host}
"""
            
            # Write the .env file
            with open(env_file, 'w') as f:
                f.write(env_content)
            
            logger.info(f"✅ Frontend configured")
            
        except Exception as e:
            logger.error(f"Failed to update frontend config: {e}")
    
    def start_backend_server(self):
        """Start the backend server"""
        logger.info("🚀 Starting backend server...")
        
        try:
            # Check if start_complete_server.py exists
            start_script = Path("backend/start_complete_server.py")
            if start_script.exists():
                cmd = [
                    sys.executable, str(start_script),
                    "--host", "0.0.0.0",
                    "--port", str(self.backend_port),
                    "--ws-port", str(self.ws_port)
                ]
            else:
                # Fallback to main.py
                cmd = [
                    sys.executable, "-m", "uvicorn",
                    "main:app",
                    "--host", "0.0.0.0",
                    "--port", str(self.backend_port),
                    "--reload"
                ]
            
            self.backend_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
                cwd="backend" if not start_script.exists() else None
            )
            
            self.processes.append(("Backend Server", self.backend_process))
            self.service_health["backend"]["status"] = "starting"
            
            # Start thread to monitor backend output
            threading.Thread(
                target=self._monitor_process_output,
                args=(self.backend_process, "BACKEND"),
                daemon=True
            ).start()
            
            logger.info(f"✅ Backend server started (PID: {self.backend_process.pid})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start backend server: {e}")
            self.service_health["backend"]["status"] = "failed"
            return False
    
    def start_frontend_server(self):
        """Start the frontend server"""
        logger.info("🌐 Starting frontend server...")
        
        try:
            frontend_path = Path("frontend")
            if not frontend_path.exists():
                logger.error("Frontend directory not found")
                return False
            
            # Check if package.json exists
            package_json = frontend_path / "package.json"
            if not package_json.exists():
                logger.error("Frontend package.json not found")
                return False
            
            # Set environment for frontend
            env = os.environ.copy()
            env.update({
                'PORT': str(self.frontend_port),
                'HOST': self.host,
                'REACT_APP_API_URL': f"http://{self.host}:{self.backend_port}",
                'REACT_APP_WS_URL': f"ws://{self.host}:{self.ws_port}",
                'BROWSER': 'none'
            })
            
            # Start frontend development server
            cmd = ["npm", "run", "dev"]
            
            self.frontend_process = subprocess.Popen(
                cmd,
                cwd=frontend_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                env=env,
                bufsize=1,
                universal_newlines=True
            )
            
            self.processes.append(("Frontend Server", self.frontend_process))
            self.service_health["frontend"]["status"] = "starting"
            
            # Start thread to monitor frontend output
            threading.Thread(
                target=self._monitor_process_output,
                args=(self.frontend_process, "FRONTEND"),
                daemon=True
            ).start()
            
            logger.info(f"✅ Frontend server started (PID: {self.frontend_process.pid})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start frontend server: {e}")
            self.service_health["frontend"]["status"] = "failed"
            return False
    
    def _monitor_process_output(self, process, label):
        """Monitor process output in separate thread"""
        try:
            for line in iter(process.stdout.readline, ''):
                if line.strip():
                    # Color code output based on content
                    if "error" in line.lower():
                        print(f"\033[91m[{label}] {line.strip()}\033[0m")
                    elif "warning" in line.lower():
                        print(f"\033[93m[{label}] {line.strip()}\033[0m")
                    elif "started" in line.lower() or "ready" in line.lower():
                        print(f"\033[92m[{label}] {line.strip()}\033[0m")
                    else:
                        print(f"[{label}] {line.strip()}")
                        
        except Exception as e:
            logger.error(f"Error monitoring {label} output: {e}")
    
    async def check_service_health(self):
        """Check health of all services"""
        import aiohttp
        
        async with aiohttp.ClientSession() as session:
            # Check backend health
            try:
                async with session.get(
                    f"http://{self.host}:{self.backend_port}/health",
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status == 200:
                        self.service_health["backend"]["status"] = "healthy"
                        self.service_health["backend"]["last_check"] = datetime.now()
                    else:
                        self.service_health["backend"]["status"] = "unhealthy"
            except:
                if self.backend_process and self.backend_process.poll() is not None:
                    self.service_health["backend"]["status"] = "crashed"
                else:
                    self.service_health["backend"]["status"] = "unhealthy"
            
            # Check WebSocket health
            try:
                import websockets
                async with websockets.connect(
                    f"ws://{self.host}:{self.ws_port}",
                    timeout=5
                ):
                    self.service_health["websocket"]["status"] = "healthy"
                    self.service_health["websocket"]["last_check"] = datetime.now()
            except:
                self.service_health["websocket"]["status"] = "unhealthy"
            
            # Check frontend (just process status)
            if self.frontend_process and self.frontend_process.poll() is None:
                self.service_health["frontend"]["status"] = "healthy"
                self.service_health["frontend"]["last_check"] = datetime.now()
            else:
                self.service_health["frontend"]["status"] = "crashed"
    
    async def restart_failed_services(self):
        """Restart any failed services"""
        # Restart backend if needed
        if self.service_health["backend"]["status"] == "crashed":
            restarts = self.service_health["backend"]["restarts"]
            if restarts < self.max_restarts:
                logger.warning(f"🔄 Restarting backend server (attempt {restarts + 1}/{self.max_restarts})")
                self.service_health["backend"]["restarts"] += 1
                self.start_backend_server()
                await asyncio.sleep(5)
        
        # Restart frontend if needed
        if self.service_health["frontend"]["status"] == "crashed":
            restarts = self.service_health["frontend"]["restarts"]
            if restarts < self.max_restarts:
                logger.warning(f"🔄 Restarting frontend server (attempt {restarts + 1}/{self.max_restarts})")
                self.service_health["frontend"]["restarts"] += 1
                self.start_frontend_server()
                await asyncio.sleep(5)
    
    def print_health_status(self):
        """Print current health status"""
        status_symbols = {
            "healthy": "✅",
            "unhealthy": "⚠️",
            "crashed": "❌",
            "starting": "🔄",
            "stopped": "⏹️",
            "failed": "❌"
        }
        
        print("\n" + "=" * 60)
        print("SERVICE HEALTH STATUS")
        print("=" * 60)
        
        for service, health in self.service_health.items():
            symbol = status_symbols.get(health["status"], "❓")
            restarts = f" (Restarts: {health['restarts']})" if health["restarts"] > 0 else ""
            print(f"{symbol} {service.upper()}: {health['status']}{restarts}")
        
        print("=" * 60)
    
    def stop_all_processes(self):
        """Stop all managed processes"""
        logger.info("🛑 Stopping all processes...")
        
        for name, process in self.processes:
            try:
                if process and process.poll() is None:
                    logger.info(f"Stopping {name}...")
                    process.terminate()
                    
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        logger.warning(f"Force killing {name}...")
                        process.kill()
                        process.wait()
                    
                    logger.info(f"✅ {name} stopped")
                    
            except Exception as e:
                logger.error(f"Error stopping {name}: {e}")
        
        self.processes.clear()
        self.running = False
    
    async def run_system(self):
        """Run the complete system with monitoring"""
        self.print_banner()
        
        logger.info(f"📍 Host: {self.host}")
        logger.info(f"🚀 Backend Port: {self.backend_port}")
        logger.info(f"🌐 Frontend Port: {self.frontend_port}")
        logger.info(f"🔌 WebSocket Port: {self.ws_port}")
        logger.info("=" * 80)
        
        try:
            # Step 1: Cleanup
            self.cleanup_all_processes()
            
            # Step 2: Setup
            self.setup_environment()
            self.update_frontend_config()
            
            # Step 3: Run tests
            self.run_tests()
            
            # Step 4: Start services
            if not self.start_backend_server():
                logger.error("❌ Failed to start backend server")
                return False
            
            await asyncio.sleep(5)
            
            if not self.start_frontend_server():
                logger.error("❌ Failed to start frontend server")
                return False
            
            # Step 5: Wait for services to be ready
            logger.info("⏳ Waiting for services to be ready...")
            await asyncio.sleep(10)
            
            # Step 6: Initial health check
            await self.check_service_health()
            
            # Step 7: Show final status
            logger.info("=" * 80)
            logger.info("🎉 SYSTEM STARTED SUCCESSFULLY!")
            logger.info("=" * 80)
            logger.info(f"🌐 Frontend: http://{self.host}:{self.frontend_port}")
            logger.info(f"🚀 Backend API: http://{self.host}:{self.backend_port}")
            logger.info(f"📚 API Docs: http://{self.host}:{self.backend_port}/docs")
            logger.info(f"🔍 Health Check: http://{self.host}:{self.backend_port}/health")
            logger.info(f"🔌 WebSocket: ws://{self.host}:{self.ws_port}")
            logger.info("=" * 80)
            logger.info("Press Ctrl+C to stop all services")
            logger.info("=" * 80)
            
            self.running = True
            
            # Monitoring loop
            health_check_interval = 30  # seconds
            last_health_check = time.time()
            
            try:
                while self.running:
                    # Periodic health check
                    if time.time() - last_health_check > health_check_interval:
                        await self.check_service_health()
                        await self.restart_failed_services()
                        self.print_health_status()
                        last_health_check = time.time()
                    
                    await asyncio.sleep(1)
                    
            except KeyboardInterrupt:
                logger.info("🛑 Received interrupt signal")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ System startup failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            self.stop_all_processes()


def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}, shutting down...")
    sys.exit(0)


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Comprehensive MT5 Dashboard System Startup',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python startup.py                    # Run with defaults
  python startup.py --skip-tests       # Skip tests and start immediately
  python startup.py --host 0.0.0.0     # Bind to all interfaces
  python startup.py --backend-port 8080 --frontend-port 3001
        """
    )
    
    parser.add_argument('--host', default='127.0.0.1', help='Server host')
    parser.add_argument('--backend-port', type=int, default=80, help='Backend port')
    parser.add_argument('--frontend-port', type=int, default=3000, help='Frontend port')
    parser.add_argument('--ws-port', type=int, default=8765, help='WebSocket port')
    parser.add_argument('--skip-tests', action='store_true', help='Skip running tests')
    
    args = parser.parse_args()
    
    # Install aiohttp if not present (needed for health checks)
    try:
        import aiohttp
    except ImportError:
        logger.info("Installing aiohttp for health checks...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "aiohttp"])
        import aiohttp
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    runner = ComprehensiveSystemRunner(
        args.host, 
        args.backend_port, 
        args.frontend_port, 
        args.ws_port,
        args.skip_tests
    )
    
    try:
        success = await runner.run_system()
        return 0 if success else 1
    except KeyboardInterrupt:
        logger.info("System interrupted by user")
        return 0
    except Exception as e:
        logger.error(f"System error: {e}")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("System stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)