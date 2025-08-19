#!/usr/bin/env python3
"""
MT5 Dashboard Setup Verification Script

This script verifies that both backend and frontend are properly configured
and ready to run.
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def check_file_exists(filepath, description):
    """Check if a file exists"""
    exists = Path(filepath).exists()
    print(f"  {description}: {'✅ OK' if exists else '❌ MISSING'}")
    return exists

def check_directory_exists(dirpath, description):
    """Check if a directory exists"""
    exists = Path(dirpath).exists()
    print(f"  {description}: {'✅ OK' if exists else '❌ MISSING'}")
    return exists

def run_command(cmd, description, cwd=None):
    """Run a command and return success status"""
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            capture_output=True, 
            text=True, 
            cwd=cwd,
            timeout=30
        )
        success = result.returncode == 0
        print(f"  {description}: {'✅ OK' if success else '❌ FAILED'}")
        if not success and result.stderr:
            print(f"    Error: {result.stderr.strip()}")
        return success
    except subprocess.TimeoutExpired:
        print(f"  {description}: ❌ TIMEOUT")
        return False
    except Exception as e:
        print(f"  {description}: ❌ ERROR - {e}")
        return False

def verify_backend_setup():
    """Verify backend setup"""
    print("🔧 Backend Setup Verification")
    print("-" * 40)
    
    # Check essential files
    backend_files = [
        ("backend/main.py", "Main backend application"),
        ("backend/requirements.txt", "Python dependencies"),
        ("backend/database/connection.py", "Database connection"),
        ("backend/database/init_db.py", "Database initialization"),
        ("backend/config/environment.py", "Environment configuration"),
        (".env", "Environment variables"),
    ]
    
    all_files_ok = True
    for filepath, description in backend_files:
        if not check_file_exists(filepath, description):
            all_files_ok = False
    
    print()
    
    # Check virtual environment
    venv_ok = check_directory_exists("venv", "Python virtual environment")
    
    # Test backend functionality
    print("\nTesting backend functionality...")
    backend_tests = [
        ("cd backend && bash -c 'source ../venv/bin/activate && python test_backend.py'", "Backend test script"),
    ]
    
    backend_functional = True
    for cmd, description in backend_tests:
        if not run_command(cmd, description):
            backend_functional = False
    
    return all_files_ok and venv_ok and backend_functional

def verify_frontend_setup():
    """Verify frontend setup"""
    print("\n🎨 Frontend Setup Verification")
    print("-" * 40)
    
    # Check essential files
    frontend_files = [
        ("frontend/package.json", "Frontend package configuration"),
        ("frontend/src/App.js", "Main React application"),
        ("frontend/src/services/api.js", "API service"),
        ("frontend/.env", "Frontend environment variables"),
    ]
    
    all_files_ok = True
    for filepath, description in frontend_files:
        if not check_file_exists(filepath, description):
            all_files_ok = False
    
    print()
    
    # Check node_modules
    node_modules_ok = check_directory_exists("frontend/node_modules", "Node.js dependencies")
    
    # Check build directory
    build_ok = check_directory_exists("frontend/build", "Production build")
    
    # Test frontend functionality
    print("\nTesting frontend functionality...")
    frontend_tests = [
        ("cd frontend && npm run build", "Frontend build process"),
    ]
    
    frontend_functional = True
    for cmd, description in frontend_tests:
        if not run_command(cmd, description):
            frontend_functional = False
    
    return all_files_ok and node_modules_ok and build_ok and frontend_functional

def verify_database_setup():
    """Verify database setup"""
    print("\n🗄️  Database Setup Verification")
    print("-" * 40)
    
    # Check database file
    db_file_ok = check_file_exists("backend/data/mt5_dashboard.db", "SQLite database file")
    
    # Test database functionality
    print("\nTesting database functionality...")
    db_tests = [
        ("cd backend && bash -c 'source ../venv/bin/activate && python -m database.init_db --verify'", "Database integrity check"),
        ("cd backend && bash -c 'source ../venv/bin/activate && python -m database.init_db --stats'", "Database statistics"),
    ]
    
    db_functional = True
    for cmd, description in db_tests:
        if not run_command(cmd, description):
            db_functional = False
    
    return db_file_ok and db_functional

def verify_environment_config():
    """Verify environment configuration"""
    print("\n⚙️  Environment Configuration")
    print("-" * 40)
    
    # Check environment files
    env_files = [
        (".env", "Root environment file"),
        ("frontend/.env", "Frontend environment file"),
    ]
    
    all_env_ok = True
    for filepath, description in env_files:
        if not check_file_exists(filepath, description):
            all_env_ok = False
    
    # Check environment variables
    print("\nChecking environment variables...")
    env_vars = [
        ("MT5_API_PORT", "Backend API port"),
        ("MT5_FRONTEND_PORT", "Frontend port"),
        ("MT5_DB_PATH", "Database path"),
    ]
    
    env_vars_ok = True
    for var, description in env_vars:
        value = os.getenv(var)
        if value:
            print(f"  {description}: ✅ OK ({value})")
        else:
            print(f"  {description}: ⚠️  NOT SET (using default)")
    
    return all_env_ok

def generate_startup_instructions():
    """Generate startup instructions"""
    print("\n🚀 Startup Instructions")
    print("-" * 40)
    
    print("To start the complete system:")
    print()
    
    print("1. Start Backend:")
    print("   cd backend")
    print("   source ../venv/bin/activate")
    print("   PORT=80 HOST=0.0.0.0 ENVIRONMENT=development python main.py")
    print()
    
    print("2. Start Frontend (in a new terminal):")
    print("   cd frontend")
    print("   npm start")
    print()
    
    print("3. Access the application:")
    print("   Frontend: http://localhost:3000")
    print("   Backend API: http://localhost:80")
    print("   API Docs: http://localhost:80/docs")
    print()
    
    print("4. Alternative: Use the full system script:")
    print("   python run_full_system.py")

def main():
    """Main verification function"""
    print("🔍 MT5 Dashboard Setup Verification")
    print("=" * 60)
    
    # Verify each component
    backend_ok = verify_backend_setup()
    frontend_ok = verify_frontend_setup()
    database_ok = verify_database_setup()
    environment_ok = verify_environment_config()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Setup Verification Summary")
    print("=" * 60)
    
    components = [
        ("Backend", backend_ok),
        ("Frontend", frontend_ok),
        ("Database", database_ok),
        ("Environment", environment_ok),
    ]
    
    all_ok = True
    for component, status in components:
        print(f"  {component}: {'✅ READY' if status else '❌ ISSUES'}")
        if not status:
            all_ok = False
    
    print()
    
    if all_ok:
        print("🎉 All components are ready!")
        print("The MT5 Dashboard system is properly configured and ready to run.")
        generate_startup_instructions()
    else:
        print("⚠️  Some components have issues that need to be resolved.")
        print("Please check the details above and fix any problems before starting the system.")
    
    return all_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)