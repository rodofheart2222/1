#!/usr/bin/env python3
"""
MT5 Dashboard Quick Start
========================

Minimal script to get the dashboard running quickly.
"""

import os
import sys
import subprocess
import time

def run_cmd(cmd, check=True):
    """Run a command and return success status"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if check and result.returncode != 0:
            print(f"Error: {result.stderr}")
            return False
        return True
    except Exception as e:
        print(f"Error running command: {e}")
        return False

print("MT5 Dashboard Quick Start")
print("=" * 50)

# Install minimal backend dependencies
print("\nInstalling essential Python packages...")
essential_packages = [
    "fastapi",
    "uvicorn[standard]",
    "sqlalchemy",
    "pydantic",
    "pydantic-settings",
    "python-multipart",
    "aiofiles",
    "pandas",
    "numpy",
    "requests",
    "python-dotenv",
    "websockets"
]

for package in essential_packages:
    print(f"Installing {package}...", end=" ")
    if run_cmd(f"pip3 install --user {package} 2>/dev/null || pip3 install --break-system-packages {package} 2>/dev/null", check=False):
        print("✓")
    else:
        print("✗")

# Create data directory
os.makedirs("data", exist_ok=True)

# Create a simple database initialization
print("\nInitializing database...")
db_init_code = '''
import sqlite3
import os

# Create data directory
os.makedirs("data", exist_ok=True)

# Connect to database
conn = sqlite3.connect("data/trading.db")
cursor = conn.cursor()

# Create basic tables
cursor.execute("""
CREATE TABLE IF NOT EXISTS eas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id TEXT,
    ea_name TEXT,
    status TEXT DEFAULT 'active',
    is_coc BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ea_name TEXT,
    symbol TEXT,
    trade_type TEXT,
    volume REAL,
    open_price REAL,
    close_price REAL,
    profit REAL,
    open_time TIMESTAMP,
    close_time TIMESTAMP
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS news_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    country TEXT,
    impact TEXT,
    forecast TEXT,
    previous TEXT,
    actual TEXT,
    event_time TIMESTAMP
)
""")

# Add some sample data
cursor.execute("INSERT OR IGNORE INTO eas (ea_name, account_id, is_coc) VALUES ('Commander EA', '12345', 1)")
cursor.execute("INSERT OR IGNORE INTO eas (ea_name, account_id, is_coc) VALUES ('Soldier EA 1', '12346', 0)")

conn.commit()
conn.close()
print("Database initialized successfully!")
'''

with open("_temp_db_init.py", "w") as f:
    f.write(db_init_code)

run_cmd("python3 _temp_db_init.py")
os.remove("_temp_db_init.py")

# Create backend .env file
print("\nCreating backend configuration...")
backend_env = """
DATABASE_URL=sqlite:///data/trading.db
CORS_ORIGINS=http://localhost:3000,http://localhost:8000,http://127.0.0.1:3000,http://127.0.0.1:8000
"""
with open("backend/.env", "w") as f:
    f.write(backend_env)

# Create frontend .env file
print("Creating frontend configuration...")
frontend_env = """GENERATE_SOURCEMAP=false
DISABLE_ESLINT_PLUGIN=true
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8001
PORT=3000
"""
with open("frontend/.env", "w") as f:
    f.write(frontend_env)

print("\n" + "=" * 50)
print("Setup complete! To start the dashboard:")
print("\n1. Start the backend (in one terminal):")
print("   cd /workspace && python3 -m uvicorn backend.main:app --reload")
print("\n2. Start the frontend (in another terminal):")
print("   cd /workspace/frontend && npm start")
print("\nOr use the automated startup:")
print("   python3 startup.py --skip-deps")
print("=" * 50)