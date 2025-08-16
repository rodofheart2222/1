#!/usr/bin/env python3
"""
Complete System Runner

This script:
1. Terminates all existing processes (backend, frontend, WebSocket)
2. Starts backend server
3. Starts frontend development server
4. Manages both processes together

Usage:
    python run_full_system.py [--host 155.138.174.196] [--backend-port 8000] [--frontend-port 3000]
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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FullSystemRunner:
    """Manages complete system startup and shutdown"""
    
    def __init__(self, host="155.138.174.196", backend_port=8000, frontend_port=3000, ws_port=8765):
        self.host = host
        self.backend_port = backend_port
        self.frontend_port = frontend_port
        self.ws_port = ws_port
        
        # Process tracking
        self.backend_process = None
        self.frontend_process = None
        self.processes = []
        self.running = False
        
    def kill_processes_on_ports(self, ports):
        """Kill all processes running on specified ports"""
        logger.info(f"🔍 Checking for processes on ports: {ports}")
        
        killed_count = 0
        
        for port in ports:
            try:
                # Find processes using the port
                for proc in psutil.process_iter(['pid', 'name', 'connections']):
                    try:
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
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            continue
                                    
                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                        continue
                        
            except Exception as e:
                logger.warning(f"Error checking port {port}: {e}")
        
        if killed_count > 0:
            logger.info(f"✅ Killed {killed_count} processes")
            time.sleep(2)  # Wait for processes to fully terminate
        else:
            logger.info("✅ No processes found on target ports")
    
    def kill_node_processes(self):
        """Kill all Node.js processes (frontend servers)"""
        logger.info("🔍 Checking for Node.js processes...")
        
        killed_count = 0
        
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    name = proc.info['name'].lower()
                    cmdline = ' '.join(proc.info['cmdline'] or []).lower()
                    
                    # Kill Node.js processes that might be frontend servers
                    if ('node' in name or 'npm' in name) and any(keyword in cmdline for keyword in ['start', 'dev', 'serve', 'react']):
                        pid = proc.info['pid']
                        logger.info(f"🔪 Killing Node.js process (PID: {pid}): {' '.join(proc.info['cmdline'][:3])}")
                        
                        try:
                            proc.terminate()
                            proc.wait(timeout=3)
                            killed_count += 1
                        except psutil.TimeoutExpired:
                            proc.kill()
                            killed_count += 1
                        except Exception as e:
                            logger.warning(f"Failed to kill Node.js process {pid}: {e}")
                            
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
                    
        except Exception as e:
            logger.warning(f"Error checking Node.js processes: {e}")
        
        if killed_count > 0:
            logger.info(f"✅ Killed {killed_count} Node.js processes")
            time.sleep(2)
        else:
            logger.info("✅ No Node.js processes found")
    
    def kill_python_servers(self):
        """Kill Python server processes"""
        logger.info("🔍 Checking for Python server processes...")
        
        killed_count = 0
        current_pid = os.getpid()
        
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    pid = proc.info['pid']
                    if pid == current_pid:  # Don't kill ourselves
                        continue
                        
                    name = proc.info['name'].lower()
                    cmdline = ' '.join(proc.info['cmdline'] or []).lower()
                    
                    # Kill Python processes that might be servers
                    if 'python' in name and any(keyword in cmdline for keyword in [
                        'uvicorn', 'fastapi', 'main.py', 'start_complete_server', 'websocket_server'
                    ]):
                        logger.info(f"🔪 Killing Python server (PID: {pid}): {' '.join(proc.info['cmdline'][:3])}")
                        
                        try:
                            proc.terminate()
                            proc.wait(timeout=3)
                            killed_count += 1
                        except psutil.TimeoutExpired:
                            proc.kill()
                            killed_count += 1
                        except Exception as e:
                            logger.warning(f"Failed to kill Python process {pid}: {e}")
                            
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
                    
        except Exception as e:
            logger.warning(f"Error checking Python processes: {e}")
        
        if killed_count > 0:
            logger.info(f"✅ Killed {killed_count} Python server processes")
            time.sleep(2)
        else:
            logger.info("✅ No Python server processes found")
    
    def cleanup_all_processes(self):
        """Clean up all existing processes"""
        logger.info("🧹 Cleaning up existing processes...")
        
        # Kill processes on specific ports
        ports_to_check = [self.backend_port, self.frontend_port, self.ws_port, 80, 8080]
        self.kill_processes_on_ports(ports_to_check)
        
        # Kill Node.js processes
        self.kill_node_processes()
        
        # Kill Python server processes
        self.kill_python_servers()
        
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
            
            logger.info(f"✅ Frontend configured - API: http://{self.host}:{self.backend_port}, WS: ws://{self.host}:{self.ws_port}")
            
        except Exception as e:
            logger.error(f"Failed to update frontend config: {e}")
    
    def start_backend_server(self):
        """Start the backend server"""
        logger.info("🚀 Starting backend server...")
        
        try:
            # Use the complete server startup script
            cmd = [
                sys.executable, "backend/start_complete_server.py",
                "--host", "0.0.0.0",  # Bind to all interfaces
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
            
            self.processes.append(("Backend Server", self.backend_process))
            
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
                'BROWSER': 'none'  # Don't auto-open browser
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
            return False
    
    def _monitor_process_output(self, process, label):
        """Monitor process output in separate thread"""
        try:
            for line in iter(process.stdout.readline, ''):
                if line.strip():
                    print(f"[{label}] {line.strip()}")
        except Exception as e:
            logger.error(f"Error monitoring {label} output: {e}")
    
    def wait_for_servers(self):
        """Wait for servers to be ready"""
        logger.info("⏳ Waiting for servers to start...")
        
        # Wait for backend
        backend_ready = False
        for i in range(30):  # 30 second timeout
            try:
                import requests
                response = requests.get(f"http://{self.host}:{self.backend_port}/health", timeout=2)
                if response.status_code == 200:
                    backend_ready = True
                    logger.info("✅ Backend server is ready")
                    break
            except:
                pass
            time.sleep(1)
        
        if not backend_ready:
            logger.warning("⚠️ Backend server may not be ready")
        
        # Wait a bit more for frontend
        time.sleep(5)
        logger.info("✅ Frontend server should be ready")
    
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
    
    async def run_full_system(self):
        """Run the complete system"""
        logger.info("=" * 80)
        logger.info("🎯 MT5 DASHBOARD FULL SYSTEM STARTUP")
        logger.info("=" * 80)
        logger.info(f"📍 Host: {self.host}")
        logger.info(f"🚀 Backend: http://{self.host}:{self.backend_port}")
        logger.info(f"📚 API Docs: http://{self.host}:{self.backend_port}/docs")
        logger.info(f"🌐 Frontend: http://{self.host}:{self.frontend_port}")
        logger.info(f"🔌 WebSocket: ws://{self.host}:{self.ws_port}")
        logger.info("=" * 80)
        
        try:
            # Step 1: Cleanup existing processes
            self.cleanup_all_processes()
            
            # Step 2: Setup environment
            self.setup_environment()
            
            # Step 3: Update frontend config
            self.update_frontend_config()
            
            # Step 4: Start backend server
            if not self.start_backend_server():
                logger.error("❌ Failed to start backend server")
                return False
            
            # Step 5: Wait for backend to be ready
            time.sleep(5)
            
            # Step 6: Start frontend server
            if not self.start_frontend_server():
                logger.error("❌ Failed to start frontend server")
                return False
            
            # Step 7: Wait for servers to be ready
            self.wait_for_servers()
            
            # Step 8: Show status
            logger.info("=" * 80)
            logger.info("🎉 FULL SYSTEM STARTED SUCCESSFULLY!")
            logger.info("=" * 80)
            logger.info(f"🌐 Frontend: http://{self.host}:{self.frontend_port}")
            logger.info(f"🚀 Backend API: http://{self.host}:{self.backend_port}")
            logger.info(f"📚 API Docs: http://{self.host}:{self.backend_port}/docs")
            logger.info(f"🔍 Health Check: http://{self.host}:{self.backend_port}/health")
            logger.info(f"🔌 WebSocket: ws://{self.host}:{self.ws_port}")
            logger.info("=" * 80)
            logger.info("Press Ctrl+C to stop all servers")
            logger.info("=" * 80)
            
            self.running = True
            
            # Keep running until interrupted
            try:
                while self.running:
                    # Check if processes are still running
                    if self.backend_process and self.backend_process.poll() is not None:
                        logger.error("❌ Backend server stopped unexpectedly")
                        break
                    
                    if self.frontend_process and self.frontend_process.poll() is not None:
                        logger.error("❌ Frontend server stopped unexpectedly")
                        break
                    
                    await asyncio.sleep(1)
                    
            except KeyboardInterrupt:
                logger.info("🛑 Received interrupt signal")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ System startup failed: {e}")
            return False
        finally:
            self.stop_all_processes()


def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}, shutting down...")
    sys.exit(0)


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Complete MT5 Dashboard System Runner')
    parser.add_argument('--host', default='155.138.174.196', help='Server host')
    parser.add_argument('--backend-port', type=int, default=8000, help='Backend port')
    parser.add_argument('--frontend-port', type=int, default=3000, help='Frontend port')
    parser.add_argument('--ws-port', type=int, default=8765, help='WebSocket port')
    
    args = parser.parse_args()
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    runner = FullSystemRunner(args.host, args.backend_port, args.frontend_port, args.ws_port)
    
    try:
        success = await runner.run_full_system()
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