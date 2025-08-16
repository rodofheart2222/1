#!/usr/bin/env python3
"""
Environment Loader Utility

Loads environment variables from .env file if it exists.
This should be imported at the start of main scripts.
"""

import os
from pathlib import Path


def load_env_file(env_file_path: str = ".env"):
    """Load environment variables from .env file"""
    env_path = Path(env_file_path)
    
    if not env_path.exists():
        return False
    
    try:
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue
                
                # Parse key=value pairs
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # Remove quotes if present
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]
                    
                    # Only set if not already in environment
                    if key not in os.environ:
                        os.environ[key] = value
        
        return True
        
    except Exception as e:
        print(f"Warning: Failed to load .env file: {e}")
        return False


def load_env():
    """Load environment variables from .env file in current directory"""
    return load_env_file(".env")


# Auto-load when imported
if __name__ != "__main__":
    load_env()


if __name__ == "__main__":
    # Test the loader
    print("Testing environment loader...")
    
    if load_env():
        print("✅ .env file loaded successfully")
        
        # Show some config values
        print("\nEnvironment variables loaded:")
        env_vars = [
            "MT5_HOST", "MT5_API_PORT", "MT5_WS_PORT", 
            "MT5_FRONTEND_PORT", "ENVIRONMENT", "MT5_AUTH_TOKEN"
        ]
        
        for var in env_vars:
            value = os.getenv(var, "Not set")
            if "TOKEN" in var and value != "Not set":
                value = value[:8] + "..." if len(value) > 8 else value
            print(f"  {var}: {value}")
    else:
        print("⚠️  No .env file found or failed to load")
        print("Create a .env file based on .env.example")