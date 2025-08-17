#!/usr/bin/env python3
"""
Simple System Runner

Simplified version that starts both backend and frontend without advanced process management
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
import threading

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SimpleSystemRunner:
    """Simple system runner"""
    
    def __init__(self, host="155.138.174.196", backend_port=8000, frontend_port=3000, ws_port=8765):
        self.host = host
        self.backend_port = backend_port
        self.frontend_port = frontend_port
        self.ws_port = ws_port
        
        self.backend_process = None
        self.frontend_process = None
        self.running = False
    
    def kill_ports_windows(self):
        """Kill processes on ports using Windows commands"""
        logger.info("🔍 Checking for processes on target ports...")
        
        ports = [self.backend_port, self.frontend_port, self.ws_port, 80, 8080]
        
        for port in ports:
            try:
                # Find processes using netstat
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
                logger.warning(f"Error checking port {port}: {e}")
        
        time.sleep(2)  # Wait for processes to terminate
    
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
        os.environ['HOST'] = self.host
        os.environ['PORT'] = str(self.backend_port)
        os.environ['WS_PORT'] = str(self.ws_port)
        
        logger.info("✅ Environment ready")
    
    def update_frontend_config(self):
        """Update frontend .env file"""
        logger.info("📝 Updating frontend config...")
        
        try:
            frontend_path = Path("frontend")
            if frontend_path.exists():
                env_file = frontend_path / ".env"
                
                env_content = f"""GENERATE_SOURCEMAP=false
DISABLE_ESLINT_PLUGIN=true
DANGEROUSLY_DISABLE_HOST_CHECK=true
WDS_SOCKET_HOST={self.host}
REACT_APP_API_URL=http://{self.host}:{self.backend_port}
REACT_APP_WS_URL=ws://{self.host}:{self.ws_port}
PORT={self.frontend_port}
HOST={self.host}
BROWSER=none
"""
                
                with open(env_file, 'w') as f:
                    f.write(env_content)
                
                logger.info("✅ Frontend config updated")
            else:
                logger.warning("Frontend directory not found")
                
        except Exception as e:
            logger.error(f"Failed to update frontend config: {e}")
    
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
                text=True
            )
            
            # Monitor backend output in thread
            threading.Thread(
                target=self._monitor_output,
                args=(self.backend_process, "BACKEND"),
                daemon=True
            ).start()
            
            logger.info(f"✅ Backend started (PID: {self.backend_process.pid})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start backend: {e}")
            return False
    
    def start_frontend(self):
        """Start frontend server"""
        logger.info("🌐 Starting frontend server...")
        
        try:
            frontend_path = Path("frontend")
            if not frontend_path.exists():
                logger.error("Frontend directory not found")
                return False
            
            env = os.environ.copy()
            env.update({
                'PORT': str(self.frontend_port),
                'HOST': self.host,
                'REACT_APP_API_URL': f"http://{self.host}:{self.backend_port}",
                'REACT_APP_WS_URL': f"ws://{self.host}:{self.ws_port}",
                'BROWSER': 'none'
            })
            
            self.frontend_process = subprocess.Popen(
                ["npm", "start"],
                cwd=frontend_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                env=env
            )
            
            # Monitor frontend output in thread
            threading.Thread(
                target=self._monitor_output,
                args=(self.frontend_process, "FRONTEND"),
                daemon=True
            ).start()
            
            logger.info(f"✅ Frontend started (PID: {self.frontend_process.pid})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start frontend: {e}")
            return False
    
    def _monitor_output(self, process, label):
        """Monitor process output"""
        try:
            for line in iter(process.stdout.readline, ''):
                if line.strip():
                    print(f"[{label}] {line.strip()}")
        except (IOError, OSError) as e:
            # Process may have terminated, which is expected
            logger.debug(f"Process output monitoring ended for {label}: {e}")
        except Exception as e:
            logger.warning(f"Unexpected error monitoring {label} output: {e}")
    
    def stop_processes(self):
        """Stop all processes"""
        logger.info("🛑 Stopping processes...")
        
        if self.backend_process:
            try:
                self.backend_process.terminate()
                self.backend_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                logger.warning("Backend process termination timed out, force killing")
                try:
                    self.backend_process.kill()
                    self.backend_process.wait()
                except (OSError, subprocess.TimeoutExpired) as e:
                    logger.error(f"Failed to force kill backend process: {e}")
            except (OSError, ValueError) as e:
                logger.error(f"Error terminating backend process: {e}")
        
        if self.frontend_process:
            try:
                self.frontend_process.terminate()
                self.frontend_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                logger.warning("Frontend process termination timed out, force killing")
                try:
                    self.frontend_process.kill()
                    self.frontend_process.wait()
                except (OSError, subprocess.TimeoutExpired) as e:
                    logger.error(f"Failed to force kill frontend process: {e}")
            except (OSError, ValueError) as e:
                logger.error(f"Error terminating frontend process: {e}")
        
        logger.info("✅ Processes stopped")
    
    async def run_system(self):
        """Run the complete system"""
        logger.info("=" * 80)
        logger.info("🎯 MT5 DASHBOARD SYSTEM STARTUP")
        logger.info("=" * 80)
        logger.info(f"📍 Host: {self.host}")
        logger.info(f"🚀 Backend: http://{self.host}:{self.backend_port}")
        logger.info(f"🌐 Frontend: http://{self.host}:{self.frontend_port}")
        logger.info(f"🔌 WebSocket: ws://{self.host}:{self.ws_port}")
        logger.info("=" * 80)
        
        try:
            # Cleanup
            self.kill_ports_windows()
            
            # Setup
            self.setup_environment()
            self.update_frontend_config()
            
            # Start backend
            if not self.start_backend():
                return False
            
            # Wait for backend
            time.sleep(8)
            
            # Start frontend
            if not self.start_frontend():
                return False
            
            # Wait for frontend
            time.sleep(10)
            
            # Show URLs
            logger.info("=" * 80)
            logger.info("🎉 SYSTEM READY!")
            logger.info("=" * 80)
            logger.info(f"🌐 Frontend: http://{self.host}:{self.frontend_port}")
            logger.info(f"🚀 Backend: http://{self.host}:{self.backend_port}")
            logger.info(f"📚 API Docs: http://{self.host}:{self.backend_port}/docs")
            logger.info("=" * 80)
            logger.info("Press Ctrl+C to stop")
            
            self.running = True
            
            # Keep running
            while self.running:
                if self.backend_process and self.backend_process.poll() is not None:
                    logger.error("Backend stopped")
                    break
                if self.frontend_process and self.frontend_process.poll() is not None:
                    logger.error("Frontend stopped")
                    break
                await asyncio.sleep(1)
            
            return True
            
        except KeyboardInterrupt:
            logger.info("Interrupted by user")
            return True
        except Exception as e:
            logger.error(f"Error: {e}")
            return False
        finally:
            self.stop_processes()


async def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Simple System Runner')
    parser.add_argument('--host', default='155.138.174.196', help='Host')
    parser.add_argument('--backend-port', type=int, default=8000, help='Backend port')
    parser.add_argument('--frontend-port', type=int, default=3000, help='Frontend port')
    parser.add_argument('--ws-port', type=int, default=8765, help='WebSocket port')
    
    args = parser.parse_args()
    
    runner = SimpleSystemRunner(args.host, args.backend_port, args.frontend_port, args.ws_port)
    
    try:
        success = await runner.run_system()
        return 0 if success else 1
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        sys.exit(0)