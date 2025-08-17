#!/usr/bin/env python3
"""
MT5 Dashboard Startup Script
============================

This script starts the entire MT5 Dashboard system including:
- Database initialization and migrations
- Backend API server
- Frontend development server
- Environment setup and dependency checks
- Process management and graceful shutdown

Usage:
    python3 start.py [options]

Options:
    --dev           Start in development mode (default)
    --prod          Start in production mode
    --backend-only  Start only the backend server
    --frontend-only Start only the frontend server
    --port PORT     Specify backend port (default: 8000)
    --frontend-port PORT  Specify frontend port (default: 3000)
    --host HOST     Specify backend host (default: 127.0.0.1)
    --no-browser    Don't open browser automatically
    --help          Show this help message
"""

import os
import sys
import time
import signal
import subprocess
import threading
import argparse
import sqlite3
from pathlib import Path
from typing import Optional, List, Dict

class Colors:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

class MT5DashboardStarter:
    """Main class for managing the MT5 Dashboard startup process"""
    
    def __init__(self):
        self.processes: List[subprocess.Popen] = []
        self.shutdown_event = threading.Event()
        self.backend_process: Optional[subprocess.Popen] = None
        self.frontend_process: Optional[subprocess.Popen] = None
        
        # Default configuration
        self.config = {
            'mode': 'dev',
            'backend_port': 8000,
            'frontend_port': 3000,
            'host': '127.0.0.1',
            'backend_only': False,
            'frontend_only': False,
            'no_browser': False
        }
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        print(f"\n{Colors.WARNING}🛑 Shutdown signal received. Stopping services...{Colors.ENDC}")
        self.shutdown()
        sys.exit(0)
    
    def print_header(self):
        """Print startup header"""
        print(f"""
{Colors.HEADER}{Colors.BOLD}
╔═══════════════════════════════════════════════════════════════╗
║                    MT5 Dashboard Startup                     ║
║              Commander-in-Chief Trading System               ║
╚═══════════════════════════════════════════════════════════════╝
{Colors.ENDC}""")
    
    def log(self, message: str, level: str = "INFO"):
        """Log message with timestamp and color"""
        timestamp = time.strftime("%H:%M:%S")
        colors = {
            "INFO": Colors.CYAN,
            "SUCCESS": Colors.GREEN,
            "WARNING": Colors.WARNING,
            "ERROR": Colors.FAIL
        }
        color = colors.get(level, Colors.CYAN)
        print(f"{color}[{timestamp}] {message}{Colors.ENDC}")
    
    def check_dependencies(self) -> bool:
        """Check if all required dependencies are available"""
        self.log("🔍 Checking dependencies...")
        
        dependencies = {
            'python3': 'python3 --version',
            'node': 'node --version',
            'npm': 'npm --version'
        }
        
        missing = []
        
        for dep, cmd in dependencies.items():
            try:
                result = subprocess.run(cmd.split(), capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    version = result.stdout.strip()
                    self.log(f"✅ {dep}: {version}", "SUCCESS")
                else:
                    missing.append(dep)
            except (subprocess.TimeoutExpired, FileNotFoundError):
                missing.append(dep)
        
        if missing:
            self.log(f"❌ Missing dependencies: {', '.join(missing)}", "ERROR")
            return False
        
        return True
    
    def setup_environment(self):
        """Setup environment variables"""
        self.log("🔧 Setting up environment...")
        
        # Set environment variables
        env_vars = {
            'ENVIRONMENT': self.config['mode'],
            'MT5_API_PORT': str(self.config['backend_port']),
            'MT5_HOST': self.config['host'],
            'DATABASE_PATH': 'data/mt5_dashboard.db',
            'PYTHONPATH': os.getcwd(),
            'NODE_ENV': 'development' if self.config['mode'] == 'dev' else 'production'
        }
        
        for key, value in env_vars.items():
            os.environ[key] = value
            self.log(f"  {key}={value}")
    
    def init_database(self) -> bool:
        """Initialize database and run migrations"""
        self.log("🗄️ Initializing database...")
        
        try:
            # Ensure data directory exists
            data_dir = Path("data")
            data_dir.mkdir(exist_ok=True)
            
            # Create database with schema
            db_path = "data/mt5_dashboard.db"
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Apply main schema
            schema_file = Path("backend/database/schema.sql")
            if schema_file.exists():
                with open(schema_file, 'r') as f:
                    cursor.executescript(f.read())
                self.log("✅ Main schema applied", "SUCCESS")
            
            # Apply migrations
            migrations_dir = Path("backend/database/migrations")
            if migrations_dir.exists():
                migration_files = sorted(migrations_dir.glob("*.sql"))
                for migration_file in migration_files:
                    with open(migration_file, 'r') as f:
                        cursor.executescript(f.read())
                    self.log(f"✅ Applied migration: {migration_file.name}", "SUCCESS")
            
            conn.commit()
            conn.close()
            
            self.log("✅ Database initialization completed", "SUCCESS")
            return True
            
        except Exception as e:
            self.log(f"❌ Database initialization failed: {e}", "ERROR")
            return False
    
    def install_python_dependencies(self) -> bool:
        """Install Python dependencies"""
        self.log("📦 Installing Python dependencies...")
        
        try:
            # Install backend dependencies
            cmd = [
                sys.executable, '-m', 'pip', 'install', '--break-system-packages',
                'fastapi', 'uvicorn', 'sqlalchemy', 'python-multipart', 
                'beautifulsoup4', 'requests', 'pandas', 'numpy'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if result.returncode == 0:
                self.log("✅ Python dependencies installed", "SUCCESS")
                return True
            else:
                self.log(f"❌ Failed to install Python dependencies: {result.stderr}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Error installing Python dependencies: {e}", "ERROR")
            return False
    
    def install_node_dependencies(self) -> bool:
        """Install Node.js dependencies"""
        if self.config['backend_only']:
            return True
            
        self.log("📦 Installing Node.js dependencies...")
        
        try:
            # Change to frontend directory
            frontend_dir = Path("frontend")
            if not frontend_dir.exists():
                self.log("❌ Frontend directory not found", "ERROR")
                return False
            
            # Install dependencies
            cmd = ['npm', 'install', '--legacy-peer-deps']
            result = subprocess.run(
                cmd, 
                cwd=frontend_dir, 
                capture_output=True, 
                text=True, 
                timeout=300
            )
            
            if result.returncode == 0:
                self.log("✅ Node.js dependencies installed", "SUCCESS")
                return True
            else:
                self.log(f"❌ Failed to install Node.js dependencies", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Error installing Node.js dependencies: {e}", "ERROR")
            return False
    
    def start_backend(self) -> bool:
        """Start the backend server"""
        if self.config['frontend_only']:
            return True
            
        self.log("🚀 Starting backend server...")
        
        try:
            # Change to backend directory and start server
            backend_dir = Path("backend")
            
            cmd = [
                sys.executable, 'main.py'
            ]
            
            # Set environment variables for the backend process
            env = os.environ.copy()
            env.update({
                'PORT': str(self.config['backend_port']),
                'HOST': self.config['host'],
                'ENVIRONMENT': self.config['mode']
            })
            
            self.backend_process = subprocess.Popen(
                cmd,
                cwd=backend_dir,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            self.processes.append(self.backend_process)
            
            # Start thread to monitor backend output
            threading.Thread(
                target=self._monitor_process,
                args=(self.backend_process, "BACKEND"),
                daemon=True
            ).start()
            
            # Wait a moment for server to start
            time.sleep(2)
            
            if self.backend_process.poll() is None:
                self.log(f"✅ Backend server started on {self.config['host']}:{self.config['backend_port']}", "SUCCESS")
                return True
            else:
                self.log("❌ Backend server failed to start", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Error starting backend: {e}", "ERROR")
            return False
    
    def start_frontend(self) -> bool:
        """Start the frontend development server"""
        if self.config['backend_only']:
            return True
            
        self.log("🌐 Starting frontend server...")
        
        try:
            frontend_dir = Path("frontend")
            
            if self.config['mode'] == 'dev':
                # Development mode - use react-scripts
                cmd = ['npm', 'run', 'dev']
            else:
                # Production mode - build and serve
                self.log("📦 Building frontend for production...")
                build_result = subprocess.run(
                    ['npm', 'run', 'build'],
                    cwd=frontend_dir,
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                
                if build_result.returncode != 0:
                    self.log("❌ Frontend build failed", "ERROR")
                    return False
                
                cmd = ['npx', 'serve', '-s', 'build', '-l', str(self.config['frontend_port'])]
            
            # Set environment variables
            env = os.environ.copy()
            env.update({
                'PORT': str(self.config['frontend_port']),
                'REACT_APP_API_URL': f"http://{self.config['host']}:{self.config['backend_port']}",
                'BROWSER': 'none' if self.config['no_browser'] else 'default'
            })
            
            self.frontend_process = subprocess.Popen(
                cmd,
                cwd=frontend_dir,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            self.processes.append(self.frontend_process)
            
            # Start thread to monitor frontend output
            threading.Thread(
                target=self._monitor_process,
                args=(self.frontend_process, "FRONTEND"),
                daemon=True
            ).start()
            
            # Wait for frontend to start
            time.sleep(5)
            
            if self.frontend_process.poll() is None:
                self.log(f"✅ Frontend server started on http://localhost:{self.config['frontend_port']}", "SUCCESS")
                return True
            else:
                self.log("❌ Frontend server failed to start", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Error starting frontend: {e}", "ERROR")
            return False
    
    def _monitor_process(self, process: subprocess.Popen, name: str):
        """Monitor process output and log it"""
        while process.poll() is None and not self.shutdown_event.is_set():
            try:
                line = process.stdout.readline()
                if line:
                    # Filter out verbose logs but show important ones
                    if any(keyword in line.lower() for keyword in ['error', 'warning', 'started', 'listening', 'running']):
                        self.log(f"[{name}] {line.strip()}")
            except:
                break
    
    def open_browser(self):
        """Open browser to the frontend URL"""
        if self.config['no_browser'] or self.config['backend_only']:
            return
            
        frontend_url = f"http://localhost:{self.config['frontend_port']}"
        
        try:
            import webbrowser
            time.sleep(3)  # Wait for servers to be ready
            webbrowser.open(frontend_url)
            self.log(f"🌐 Opened browser to {frontend_url}", "SUCCESS")
        except:
            self.log(f"🌐 Please open your browser to {frontend_url}", "INFO")
    
    def print_status(self):
        """Print current status and URLs"""
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 MT5 Dashboard is running!{Colors.ENDC}\n")
        
        if not self.config['frontend_only']:
            backend_url = f"http://{self.config['host']}:{self.config['backend_port']}"
            print(f"  🔧 Backend API: {Colors.CYAN}{backend_url}{Colors.ENDC}")
            print(f"  📊 API Docs: {Colors.CYAN}{backend_url}/docs{Colors.ENDC}")
        
        if not self.config['backend_only']:
            frontend_url = f"http://localhost:{self.config['frontend_port']}"
            print(f"  🌐 Frontend: {Colors.CYAN}{frontend_url}{Colors.ENDC}")
        
        print(f"\n{Colors.WARNING}Press Ctrl+C to stop all services{Colors.ENDC}\n")
    
    def wait_for_shutdown(self):
        """Wait for shutdown signal"""
        try:
            while not self.shutdown_event.is_set():
                time.sleep(1)
                
                # Check if processes are still running
                if self.backend_process and self.backend_process.poll() is not None:
                    self.log("❌ Backend process stopped unexpectedly", "ERROR")
                    break
                    
                if self.frontend_process and self.frontend_process.poll() is not None:
                    self.log("❌ Frontend process stopped unexpectedly", "ERROR")
                    break
                    
        except KeyboardInterrupt:
            pass
    
    def shutdown(self):
        """Shutdown all services gracefully"""
        self.shutdown_event.set()
        
        self.log("🛑 Shutting down services...", "WARNING")
        
        for process in self.processes:
            if process and process.poll() is None:
                try:
                    process.terminate()
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                except:
                    pass
        
        self.log("✅ All services stopped", "SUCCESS")
    
    def run(self, args):
        """Main run method"""
        # Update config from arguments
        self.config.update({
            'mode': 'prod' if args.prod else 'dev',
            'backend_port': args.port,
            'frontend_port': args.frontend_port,
            'host': args.host,
            'backend_only': args.backend_only,
            'frontend_only': args.frontend_only,
            'no_browser': args.no_browser
        })
        
        self.print_header()
        
        # Dependency checks
        if not self.check_dependencies():
            return False
        
        # Environment setup
        self.setup_environment()
        
        # Database initialization
        if not self.init_database():
            return False
        
        # Install dependencies
        if not self.install_python_dependencies():
            return False
            
        if not self.install_node_dependencies():
            return False
        
        # Start services
        if not self.start_backend():
            return False
            
        if not self.start_frontend():
            return False
        
        # Open browser
        if not self.config['no_browser']:
            threading.Thread(target=self.open_browser, daemon=True).start()
        
        # Print status
        self.print_status()
        
        # Wait for shutdown
        self.wait_for_shutdown()
        
        return True

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="MT5 Dashboard Startup Script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument('--dev', action='store_true', help='Start in development mode (default)')
    parser.add_argument('--prod', action='store_true', help='Start in production mode')
    parser.add_argument('--backend-only', action='store_true', help='Start only the backend server')
    parser.add_argument('--frontend-only', action='store_true', help='Start only the frontend server')
    parser.add_argument('--port', type=int, default=8000, help='Backend port (default: 8000)')
    parser.add_argument('--frontend-port', type=int, default=3000, help='Frontend port (default: 3000)')
    parser.add_argument('--host', default='127.0.0.1', help='Backend host (default: 127.0.0.1)')
    parser.add_argument('--no-browser', action='store_true', help="Don't open browser automatically")
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.backend_only and args.frontend_only:
        print("❌ Cannot specify both --backend-only and --frontend-only")
        return 1
    
    starter = MT5DashboardStarter()
    
    try:
        success = starter.run(args)
        return 0 if success else 1
    except KeyboardInterrupt:
        starter.shutdown()
        return 0
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        starter.shutdown()
        return 1

if __name__ == "__main__":
    sys.exit(main())