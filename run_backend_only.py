#!/usr/bin/env python3
"""
Backend Only Runner

Starts just the backend server (FastAPI + WebSocket) without frontend
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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BackendRunner:
    """Runs just the backend server"""
    
    def __init__(self, host=None, backend_port=None, ws_port=None):
        # Try to use environment config
        try:
            backend_path = Path(__file__).parent / "backend"
            sys.path.insert(0, str(backend_path))
            from config.environment import Config
            
            self.host = host or Config.get_host()
            self.backend_port = backend_port or Config.get_api_port()
            self.ws_port = ws_port or Config.get_ws_port()
        except ImportError:
            # Fallback to defaults
            self.host = host or "127.0.0.1"
            self.backend_port = backend_port or 8000
            self.ws_port = ws_port or 8765
        self.backend_process = None
        self.running = False
    
    def kill_ports_simple(self):
        """Kill processes on ports using simple method"""
        logger.info("🔍 Cleaning up ports...")
        
        ports = [self.backend_port, self.ws_port, 80, 8080]
        
        for port in ports:
            try:
                # Windows netstat command
                result = subprocess.run(['netstat', '-ano'], capture_output=True, text=True)
                lines = result.stdout.split('\n')
                
                for line in lines:
                    if f':{port}' in line and 'LISTENING' in line:
                        parts = line.split()
                        if len(parts) >= 5:
                            pid = parts[-1]
                            logger.info(f"🔪 Killing process on port {port} (PID: {pid})")
                            
                            try:
                                subprocess.run(['taskkill', '/F', '/PID', pid], 
                                             capture_output=True, check=True)
                            except subprocess.CalledProcessError:
                                pass
                            
            except Exception as e:
                logger.debug(f"Error checking port {port}: {e}")
        
        time.sleep(2)
        logger.info("✅ Port cleanup completed")
    
    def setup_environment(self):
        """Set up environment"""
        logger.info("🔧 Setting up environment...")
        
        # Add paths
        current_dir = Path.cwd()
        backend_dir = current_dir / "backend"
        
        paths = [str(current_dir), str(backend_dir)]
        
        for path in paths:
            if path not in sys.path:
                sys.path.insert(0, path)
        
        # Environment variables
        pythonpath = os.environ.get('PYTHONPATH', '')
        for path in paths:
            if path not in pythonpath:
                pythonpath = f"{path}{os.pathsep}{pythonpath}" if pythonpath else path
        
        os.environ['PYTHONPATH'] = pythonpath
        os.environ['HOST'] = "0.0.0.0"  # Bind to all interfaces
        os.environ['PORT'] = str(self.backend_port)
        os.environ['WS_PORT'] = str(self.ws_port)
        
        logger.info("✅ Environment ready")
    
    def start_backend(self):
        """Start backend server"""
        logger.info("🚀 Starting backend server...")
        
        try:
            cmd = [
                sys.executable, "backend/start_complete_server.py",
                "--host", "0.0.0.0",
                "--port", str(self.backend_port),
                "--ws-port", str(self.ws_port)
            ]
            
            self.backend_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            logger.info(f"✅ Backend started (PID: {self.backend_process.pid})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start backend: {e}")
            return False
    
    def monitor_backend(self):
        """Monitor backend output"""
        try:
            for line in iter(self.backend_process.stdout.readline, ''):
                if line.strip():
                    print(f"[BACKEND] {line.strip()}")
        except Exception as e:
            logger.error(f"Error monitoring backend: {e}")
    
    def stop_backend(self):
        """Stop backend process"""
        if self.backend_process:
            logger.info("🛑 Stopping backend...")
            try:
                self.backend_process.terminate()
                self.backend_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.backend_process.kill()
                self.backend_process.wait()
            except Exception as e:
                logger.error(f"Error stopping backend: {e}")
    
    async def run_backend_only(self):
        """Run just the backend server"""
        logger.info("=" * 80)
        logger.info("🎯 MT5 DASHBOARD BACKEND STARTUP")
        logger.info("=" * 80)
        logger.info(f"📍 Host: {self.host}")
        logger.info(f"🚀 Backend: http://{self.host}:{self.backend_port}")
        logger.info(f"📚 API Docs: http://{self.host}:{self.backend_port}/docs")
        logger.info(f"🔌 WebSocket: ws://{self.host}:{self.ws_port}")
        logger.info("=" * 80)
        
        try:
            # Cleanup
            self.kill_ports_simple()
            
            # Setup
            self.setup_environment()
            
            # Start backend
            if not self.start_backend():
                return False
            
            # Wait for backend to start
            time.sleep(5)
            
            # Test backend
            try:
                import requests
                response = requests.get(f"http://{self.host}:{self.backend_port}/health", timeout=5)
                if response.status_code == 200:
                    logger.info("✅ Backend health check passed")
                else:
                    logger.warning(f"⚠️ Backend health check returned {response.status_code}")
            except Exception as e:
                logger.warning(f"⚠️ Backend health check failed: {e}")
            
            # Show URLs
            logger.info("=" * 80)
            logger.info("🎉 BACKEND READY!")
            logger.info("=" * 80)
            logger.info(f"🚀 Backend API: http://{self.host}:{self.backend_port}")
            logger.info(f"📚 API Documentation: http://{self.host}:{self.backend_port}/docs")
            logger.info(f"🔍 Health Check: http://{self.host}:{self.backend_port}/health")
            logger.info(f"🔌 WebSocket: ws://{self.host}:{self.ws_port}")
            logger.info("=" * 80)
            logger.info("💡 To test WebSocket: python test_websocket.py")
            logger.info("💡 To test API: python quick_test_8000.py")
            logger.info("Press Ctrl+C to stop")
            logger.info("=" * 80)
            
            self.running = True
            
            # Monitor backend output
            import threading
            monitor_thread = threading.Thread(target=self.monitor_backend, daemon=True)
            monitor_thread.start()
            
            # Keep running
            while self.running:
                if self.backend_process and self.backend_process.poll() is not None:
                    logger.error("❌ Backend stopped unexpectedly")
                    break
                await asyncio.sleep(1)
            
            return True
            
        except KeyboardInterrupt:
            logger.info("🛑 Interrupted by user")
            return True
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            return False
        finally:
            self.stop_backend()


async def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Backend Only Runner')
    parser.add_argument('--host', default='155.138.174.196', help='Host')
    parser.add_argument('--backend-port', type=int, default=8000, help='Backend port')
    parser.add_argument('--ws-port', type=int, default=8765, help='WebSocket port')
    
    args = parser.parse_args()
    
    runner = BackendRunner(args.host, args.backend_port, args.ws_port)
    
    try:
        success = await runner.run_backend_only()
        return 0 if success else 1
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        sys.exit(0)