#!/usr/bin/env python3
"""
MT5 Dashboard Startup Script
===========================

This script handles the complete startup process for the MT5 Dashboard system.
It manages dependencies, environment setup, and process launching.

Usage:
    python3 startup.py [options]

Options:
    --skip-deps     Skip dependency installation
    --backend-only  Start only the backend server
    --frontend-only Start only the frontend server
    --port PORT     Backend port (default: 8000)
    --host HOST     Backend host (default: 0.0.0.0)
    --help          Show this help message
"""

import os
import sys
import subprocess
import signal
import time
import argparse
from pathlib import Path

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

def print_colored(message, color=Colors.ENDC):
    """Print colored message to console"""
    print(f"{color}{message}{Colors.ENDC}")

def run_command(command, shell=True, check=True):
    """Run a shell command and return the result"""
    try:
        result = subprocess.run(command, shell=shell, check=check, 
                              capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        return False, e.stdout, e.stderr

class MT5DashboardStartup:
    def __init__(self):
        self.root_dir = Path(__file__).parent.absolute()
        self.backend_dir = self.root_dir / "backend"
        self.frontend_dir = self.root_dir / "frontend"
        self.processes = []
        
    def check_python(self):
        """Check if Python is installed and version is appropriate"""
        print_colored("Checking Python installation...", Colors.BLUE)
        success, stdout, _ = run_command("python3 --version")
        if success:
            print_colored(f"✓ {stdout.strip()}", Colors.GREEN)
            return True
        else:
            print_colored("✗ Python 3 not found!", Colors.FAIL)
            return False
            
    def check_node(self):
        """Check if Node.js is installed"""
        print_colored("Checking Node.js installation...", Colors.BLUE)
        success, stdout, _ = run_command("node --version")
        if success:
            print_colored(f"✓ Node.js {stdout.strip()}", Colors.GREEN)
            return True
        else:
            print_colored("✗ Node.js not found!", Colors.FAIL)
            return False
            
    def install_python_deps(self):
        """Install Python dependencies"""
        print_colored("\nInstalling Python dependencies...", Colors.HEADER)
        
        # Check if pip is available
        success, _, _ = run_command("pip3 --version", check=False)
        if not success:
            print_colored("pip3 not found, trying pip...", Colors.WARNING)
            success, _, _ = run_command("pip --version", check=False)
            if not success:
                print_colored("✗ pip not found! Please install pip first.", Colors.FAIL)
                return False
                
        # Try to install dependencies
        req_file = self.backend_dir / "requirements.txt"
        if not req_file.exists():
            print_colored("✗ requirements.txt not found!", Colors.FAIL)
            return False
            
        # First try with user installation
        print_colored("Installing Python packages...", Colors.BLUE)
        cmd = f"pip3 install --user -r {req_file} 2>/dev/null || pip3 install --break-system-packages -r {req_file}"
        success, stdout, stderr = run_command(cmd, check=False)
        
        if not success:
            # Try to install essential packages only
            print_colored("Full installation failed, installing essential packages...", Colors.WARNING)
            essential_packages = [
                "fastapi==0.115.13",
                "uvicorn==0.34.3",
                "websockets==13.1",
                "sqlalchemy==2.0.42",
                "pandas==2.3.0",
                "numpy==2.1.3",
                "requests==2.31.0",
                "python-dotenv==1.1.0",
                "pydantic==2.11.7",
                "pydantic-settings==2.8.0",
                "aiofiles==23.2.1",
                "python-multipart==0.0.6"
            ]
            
            for package in essential_packages:
                cmd = f"pip3 install --user {package} 2>/dev/null || pip3 install --break-system-packages {package}"
                success, _, _ = run_command(cmd, check=False)
                if success:
                    print_colored(f"  ✓ Installed {package.split('==')[0]}", Colors.GREEN)
                else:
                    print_colored(f"  ✗ Failed to install {package}", Colors.WARNING)
                    
        print_colored("✓ Python dependencies installed", Colors.GREEN)
        return True
        
    def install_node_deps(self):
        """Install Node.js dependencies"""
        print_colored("\nInstalling Node.js dependencies...", Colors.HEADER)
        
        # Check if package.json exists
        package_json = self.frontend_dir / "package.json"
        if not package_json.exists():
            print_colored("✗ package.json not found!", Colors.FAIL)
            return False
            
        # Install dependencies
        os.chdir(self.frontend_dir)
        success, _, _ = run_command("npm install", check=False)
        os.chdir(self.root_dir)
        
        if success:
            print_colored("✓ Node.js dependencies installed", Colors.GREEN)
        else:
            print_colored("⚠ Some Node.js dependencies may have failed", Colors.WARNING)
            
        return True
        
    def setup_database(self):
        """Initialize the database"""
        print_colored("\nSetting up database...", Colors.HEADER)
        
        # Create data directory if it doesn't exist
        data_dir = self.root_dir / "data"
        data_dir.mkdir(exist_ok=True)
        
        # Run database setup scripts if they exist
        setup_scripts = [
            "fix_database_schema.py",
            "populate_ea_database.py",
            "setup_mt5_communication.py"
        ]
        
        for script in setup_scripts:
            script_path = self.root_dir / script
            if script_path.exists():
                print_colored(f"Running {script}...", Colors.BLUE)
                success, _, _ = run_command(f"python3 {script_path}", check=False)
                if success:
                    print_colored(f"  ✓ {script} completed", Colors.GREEN)
                else:
                    print_colored(f"  ⚠ {script} had warnings", Colors.WARNING)
                    
        print_colored("✓ Database setup complete", Colors.GREEN)
        return True
        
    def start_backend(self, host="0.0.0.0", port=8000):
        """Start the backend server"""
        print_colored(f"\nStarting backend server on {host}:{port}...", Colors.HEADER)
        
        # Check if backend main.py exists
        backend_main = self.backend_dir / "main.py"
        if not backend_main.exists():
            print_colored("✗ Backend main.py not found!", Colors.FAIL)
            return None
            
        # Start the backend process
        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"
        
        process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "backend.main:app", 
             "--host", host, "--port", str(port), "--reload"],
            cwd=self.root_dir,
            env=env
        )
        
        # Wait a bit for the server to start
        time.sleep(3)
        
        if process.poll() is None:
            print_colored(f"✓ Backend server started on http://{host}:{port}", Colors.GREEN)
            return process
        else:
            print_colored("✗ Backend server failed to start", Colors.FAIL)
            return None
            
    def start_frontend(self, port=3000):
        """Start the frontend server"""
        print_colored(f"\nStarting frontend server on port {port}...", Colors.HEADER)
        
        # Update frontend .env file
        env_file = self.frontend_dir / ".env"
        env_content = f"""GENERATE_SOURCEMAP=false
DISABLE_ESLINT_PLUGIN=true
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8001
PORT={port}
"""
        with open(env_file, 'w') as f:
            f.write(env_content)
            
        # Start the frontend process
        env = os.environ.copy()
        env["PORT"] = str(port)
        
        process = subprocess.Popen(
            ["npm", "start"],
            cwd=self.frontend_dir,
            env=env
        )
        
        # Wait a bit for the server to start
        time.sleep(5)
        
        if process.poll() is None:
            print_colored(f"✓ Frontend server started on http://localhost:{port}", Colors.GREEN)
            return process
        else:
            print_colored("✗ Frontend server failed to start", Colors.FAIL)
            return None
            
    def cleanup(self):
        """Clean up all processes on exit"""
        print_colored("\n\nShutting down services...", Colors.WARNING)
        for process in self.processes:
            if process and process.poll() is None:
                process.terminate()
                process.wait()
        print_colored("✓ All services stopped", Colors.GREEN)
        
    def run(self, args):
        """Main execution function"""
        print_colored("MT5 Dashboard Startup", Colors.HEADER + Colors.BOLD)
        print_colored("=" * 50, Colors.HEADER)
        
        # Check prerequisites
        if not self.check_python():
            return 1
            
        if not args.backend_only and not self.check_node():
            print_colored("Node.js is required for the frontend. Install it or use --backend-only", Colors.WARNING)
            return 1
            
        # Install dependencies if not skipped
        if not args.skip_deps:
            if not self.install_python_deps():
                print_colored("Failed to install Python dependencies", Colors.FAIL)
                return 1
                
            if not args.backend_only:
                if not self.install_node_deps():
                    print_colored("Failed to install Node.js dependencies", Colors.WARNING)
                    
        # Setup database
        self.setup_database()
        
        # Start services
        if not args.frontend_only:
            backend_process = self.start_backend(args.host, args.port)
            if backend_process:
                self.processes.append(backend_process)
            else:
                return 1
                
        if not args.backend_only:
            frontend_process = self.start_frontend(3000)
            if frontend_process:
                self.processes.append(frontend_process)
                
        if not self.processes:
            print_colored("No services started!", Colors.FAIL)
            return 1
            
        # Setup signal handlers
        def signal_handler(sig, frame):
            self.cleanup()
            sys.exit(0)
            
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        print_colored("\n✓ All services started successfully!", Colors.GREEN + Colors.BOLD)
        print_colored(f"\nAccess the dashboard at: http://localhost:3000", Colors.CYAN)
        print_colored("\nPress Ctrl+C to stop all services", Colors.WARNING)
        
        # Keep the script running
        try:
            while True:
                time.sleep(1)
                # Check if processes are still running
                for process in self.processes:
                    if process.poll() is not None:
                        print_colored(f"\n⚠ A service has stopped unexpectedly", Colors.WARNING)
                        self.cleanup()
                        return 1
        except KeyboardInterrupt:
            self.cleanup()
            
        return 0

def main():
    parser = argparse.ArgumentParser(description="MT5 Dashboard Startup Script")
    parser.add_argument("--skip-deps", action="store_true", help="Skip dependency installation")
    parser.add_argument("--backend-only", action="store_true", help="Start only the backend server")
    parser.add_argument("--frontend-only", action="store_true", help="Start only the frontend server")
    parser.add_argument("--port", type=int, default=8000, help="Backend port (default: 8000)")
    parser.add_argument("--host", default="0.0.0.0", help="Backend host (default: 0.0.0.0)")
    
    args = parser.parse_args()
    
    if args.backend_only and args.frontend_only:
        print_colored("Cannot use --backend-only and --frontend-only together", Colors.FAIL)
        return 1
        
    starter = MT5DashboardStartup()
    return starter.run(args)

if __name__ == "__main__":
    sys.exit(main())