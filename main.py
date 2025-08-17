#!/usr/bin/env python3
"""
Complete MT5 COC Dashboard Startup
Usage: python main.py [URL]
Example: python main.py http://155.38.174.196:3000
"""

import sys
import os
import asyncio
import threading
import time
import signal
import subprocess
from pathlib import Path
from urllib.parse import urlparse

def parse_url(url):
    """Parse URL and extract host and port"""
    if not url.startswith(('http://', 'https://')):
        url = 'http://' + url
    
    parsed = urlparse(url)
    host = parsed.hostname or '155.38.174.196'
    frontend_port = parsed.port or 3000
    
    return host, frontend_port

def update_frontend_config(host, api_port, ws_port, frontend_port):
    """Update frontend .env file with backend URLs"""
    try:
        frontend_path = Path(__file__).parent / "frontend"
        env_file = frontend_path / ".env"
        
        # Create new .env content
        env_content = f"""GENERATE_SOURCEMAP=false
DISABLE_ESLINT_PLUGIN=true
DANGEROUSLY_DISABLE_HOST_CHECK=true
WDS_SOCKET_HOST={host}
REACT_APP_API_URL=http://{host}:{api_port}
REACT_APP_WS_URL=ws://{host}:{ws_port}
PORT={frontend_port}
"""
        
        # Write the .env file
        with open(env_file, 'w') as f:
            f.write(env_content)
        
        print(f"✅ Frontend configured to connect to backend at http://{host}:{api_port}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to update frontend config: {e}")
        return False

class MT5DashboardManager:
    """Manages all MT5 Dashboard services"""
    
    def __init__(self, host=None, api_port=None, ws_port=None, frontend_port=None):
        # Try to use environment config
        try:
            backend_path = Path(__file__).parent / "backend"
            sys.path.insert(0, str(backend_path))
            from config.environment import Config
            
            self.host = host or Config.get_host()
            self.api_port = api_port or Config.get_api_port()
            self.ws_port = ws_port or Config.get_ws_port()
            self.frontend_port = frontend_port or Config.get_frontend_port()
        except ImportError:
            # Fallback to defaults
            self.host = host or "127.0.0.1"
            self.api_port = api_port or 8000
            self.ws_port = ws_port or 8765
            self.frontend_port = frontend_port or 3000
        
        # Thread safety
        self._lock = threading.Lock()
        self.running = False
        self.fastapi_thread = None
        self.frontend_thread = None
        self.fastapi_process = None
        self.frontend_process = None
        
    def _set_running(self, value):
        """Thread-safe way to set running state"""
        with self._lock:
            self.running = value
    
    def _get_running(self):
        """Thread-safe way to get running state"""
        with self._lock:
            return self.running
        
    def start_fastapi_server(self):
        """Start FastAPI server in separate thread"""
        try:
            print(f"🚀 Starting FastAPI server on {self.host}:{self.api_port}")
            
            # Change to backend directory
            backend_path = Path(__file__).parent / "backend"
            os.chdir(backend_path)
            
            # Add backend to Python path
            sys.path.insert(0, str(backend_path))
            
            # Set environment variables
            os.environ['HOST'] = self.host
            os.environ['PORT'] = str(self.api_port)
            os.environ['ENVIRONMENT'] = 'production'
            
            # Import and run the backend
            import uvicorn
            from main import app
            
            uvicorn.run(
                app,
                host=self.host,
                port=self.api_port,
                log_level="info"
            )
            
        except Exception as e:
            print(f"❌ FastAPI server error: {e}")
            self._set_running(False)
    
    def start_frontend_server(self):
        """Start frontend React server in separate thread"""
        try:
            print(f"🌐 Starting frontend server on {self.host}:{self.frontend_port}")
            
            # Change to frontend directory
            frontend_path = Path(__file__).parent / "frontend"
            
            # Check if frontend directory exists
            if not frontend_path.exists():
                print("⚠️  Frontend directory not found, skipping frontend server")
                return
            
            # Check if package.json exists
            package_json = frontend_path / "package.json"
            if not package_json.exists():
                print("⚠️  Frontend package.json not found, skipping frontend server")
                return
            
            # Check if npm is available
            try:
                subprocess.run(["npm", "--version"], capture_output=True, check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                print("⚠️  npm not found. Please install Node.js to run the frontend server")
                print(f"   Backend API will still work at http://{self.host}:{self.api_port}")
                print("   You can run the frontend separately with: cd frontend && npm run dev")
                return
            
            # Set environment variables
            env = os.environ.copy()
            env['PORT'] = str(self.frontend_port)
            env['HOST'] = self.host if self.host != "0.0.0.0" else "127.0.0.1"
            env['REACT_APP_API_URL'] = f"http://{env['HOST']}:{self.api_port}"
            env['REACT_APP_WS_URL'] = f"ws://{env['HOST']}:{self.ws_port}"
            
            # Start the development server
            subprocess.run([
                "npm", "run", "dev"
            ], cwd=frontend_path, env=env)
            
        except Exception as e:
            print(f"⚠️  Failed to start frontend server: {e}")
            print(f"   Backend API is still available at http://{self.host}:{self.api_port}")
            print(f"   You can run the frontend manually: cd frontend && npm run dev")
    
    async def start_websocket_server(self):
        """Start WebSocket server"""
        try:
            print(f"🔌 Starting WebSocket server on {self.host}:{self.ws_port}")
            
            # Change to backend directory
            backend_path = Path(__file__).parent / "backend"
            os.chdir(backend_path)
            
            # Add backend to Python path
            sys.path.insert(0, str(backend_path))
            
            # Set environment variables for WebSocket
            os.environ['WS_HOST'] = self.host
            os.environ['WS_PORT'] = str(self.ws_port)
            os.environ['WS_AUTH_TOKEN'] = 'dashboard_token_2024'
            
            # Import WebSocket services
            try:
                from services.start_websocket_server import start_integrated_system
                await start_integrated_system(self.host, self.ws_port, "dashboard_token_2024")
            except ImportError:
                print("⚠️  WebSocket service not available, continuing without it")
                # Keep running without WebSocket
                while self._get_running():
                    await asyncio.sleep(1)
                    
        except Exception as e:
            print(f"❌ WebSocket server error: {e}")
            self._set_running(False)
    
    async def start_all_services(self):
        """Start all services"""
        try:
            print("🎯 MT5 COC Dashboard Complete Startup")
            print(f"📍 Host: {self.host}")
            print(f"🌐 Frontend: http://{self.host}:{self.frontend_port}")
            print(f"🚀 Backend API: http://{self.host}:{self.api_port}")
            print(f"📚 API Docs: http://{self.host}:{self.api_port}/docs")
            print(f"🔌 WebSocket: ws://{self.host}:{self.ws_port}")
            print("-" * 50)
            
            # Update frontend configuration
            update_frontend_config(self.host, self.api_port, self.ws_port, self.frontend_port)
            
            self._set_running(True)
            
            # Start FastAPI server in thread
            self.fastapi_thread = threading.Thread(
                target=self.start_fastapi_server,
                daemon=True
            )
            self.fastapi_thread.start()
            
            # Give FastAPI time to start
            print("⏳ Starting FastAPI server...")
            time.sleep(3)
            
            # Start frontend server in thread
            self.frontend_thread = threading.Thread(
                target=self.start_frontend_server,
                daemon=True
            )
            self.frontend_thread.start()
            
            # Give frontend time to start
            print("⏳ Starting frontend server...")
            time.sleep(2)
            
            # Start WebSocket server in current async context
            print("⏳ Starting WebSocket server...")
            await self.start_websocket_server()
            
        except Exception as e:
            print(f"❌ Failed to start services: {e}")
            await self.stop()
            raise
    
    async def stop(self):
        """Stop all services"""
        print("🛑 Stopping all services...")
        self._set_running(False)
        
        try:
            # WebSocket server will stop when running becomes False
            print("✅ Services stopped")
        except Exception as e:
            print(f"❌ Error stopping services: {e}")

# Global manager
dashboard_manager = None

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print(f"\n🛑 Received signal {signum}, shutting down...")
    if dashboard_manager:
        asyncio.create_task(dashboard_manager.stop())

async def main():
    """Main entry point"""
    global dashboard_manager
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        url = sys.argv[1]
        host, frontend_port = parse_url(url)
    else:
        host = '155.38.174.196'
        frontend_port = 3000
    
    # Backend API port (usually 80 or 8000)
    api_port = 80
    # WebSocket port
    ws_port = 8765
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    dashboard_manager = MT5DashboardManager(
        host=host,
        api_port=api_port,
        ws_port=ws_port,
        frontend_port=frontend_port
    )
    
    try:
        await dashboard_manager.start_all_services()
    except KeyboardInterrupt:
        print("\n🛑 Received keyboard interrupt, shutting down...")
    except Exception as e:
        print(f"❌ Startup failed: {e}")
        sys.exit(1)
    finally:
        if dashboard_manager:
            await dashboard_manager.stop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Failed to start: {e}")
        sys.exit(1)