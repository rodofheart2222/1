"""
Central Configuration Loader
Loads configuration from root config.json file
"""
import json
import os
from pathlib import Path

# Path to the central config file (now in frontend/src for React compatibility)
CONFIG_FILE = Path(__file__).parent.parent.parent / "frontend" / "src" / "config.json"

def load_config():
    """Load configuration from central config.json file"""
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Warning: Central config file not found at {CONFIG_FILE}")
        return {}
    except json.JSONDecodeError as e:
        print(f"Error parsing central config file: {e}")
        return {}

# Load the configuration
_config = load_config()

# ==========================================
# BACKEND SERVER CONFIGURATION
# ==========================================

# Primary backend host and port (with environment variable overrides)
BACKEND_HOST = os.getenv("HOST", _config.get("backend", {}).get("host", "127.0.0.1"))
BACKEND_PORT = int(os.getenv("PORT", _config.get("backend", {}).get("port", 80)))

# Backend URL construction
BACKEND_BASE_URL = f"http://{BACKEND_HOST}:{BACKEND_PORT}"

# Default constants for environment.py compatibility
DEFAULT_HOST = BACKEND_HOST
DEFAULT_API_PORT = BACKEND_PORT
DEFAULT_WS_PORT = int(os.getenv("WS_PORT", _config.get("websocket", {}).get("port", 8765)))
DEFAULT_FRONTEND_PORT = int(_config.get("frontend", {}).get("dev", {}).get("port", 3000))

# ==========================================
# FRONTEND CONFIGURATION
# ==========================================

# Frontend URLs from central config
frontend_config = _config.get("frontend", {})
FRONTEND_DEV_URL = frontend_config.get("dev", {}).get("url", "http://127.0.0.1:3000")
FRONTEND_PROD_URL = frontend_config.get("prod", {}).get("url", "http://127.0.0.1:80")

# ==========================================
# WEBSOCKET CONFIGURATION
# ==========================================

# WebSocket settings (with environment variable overrides)
websocket_config = _config.get("websocket", {})
WS_HOST = os.getenv("WS_HOST", websocket_config.get("host", "127.0.0.1"))
WS_PORT = int(os.getenv("WS_PORT", websocket_config.get("port", 8765)))
WS_URL = f"ws://{WS_HOST}:{WS_PORT}"

# ==========================================
# CORS CONFIGURATION
# ==========================================

# Get CORS origins from central config
cors_config = _config.get("cors", {})
DEFAULT_CORS_ORIGINS = cors_config.get("development", [])
PRODUCTION_CORS_ORIGINS = cors_config.get("production", [])

# Get CORS origins from environment or use defaults
CORS_ORIGINS_ENV = os.getenv("CORS_ORIGINS")
if CORS_ORIGINS_ENV:
    CORS_ORIGINS = CORS_ORIGINS_ENV.split(",")
else:
    CORS_ORIGINS = DEFAULT_CORS_ORIGINS.copy()

# Add production origins if in production
if os.getenv("RAILWAY_ENVIRONMENT"):
    CORS_ORIGINS.extend(PRODUCTION_CORS_ORIGINS)

# ==========================================
# EXTERNAL API CONFIGURATION  
# ==========================================

# News API configuration (with environment variable override)
news_config = _config.get("external_apis", {}).get("news", {})
NEWS_API_BASE_URL = os.getenv("NEWS_API_URL", news_config.get("base_url", "https://api.forexfactory.com"))
NEWS_API_CALENDAR_ENDPOINT = news_config.get("calendar_endpoint", "/calendar")
NEWS_API_FULL_URL = f"{NEWS_API_BASE_URL}{NEWS_API_CALENDAR_ENDPOINT}"

# ==========================================
# DATABASE CONFIGURATION
# ==========================================

# Database paths (with environment variable override)
db_config = _config.get("database", {})
DATABASE_PATH = os.getenv("DATABASE_PATH", db_config.get("path", "data/mt5_dashboard.db"))
DATA_DIR = db_config.get("data_dir", "data")
LOGS_DIR = db_config.get("logs_dir", "logs")

# ==========================================
# API CONFIGURATION
# ==========================================

api_config = _config.get("api", {})
API_TIMEOUT = api_config.get("timeout", 15000)
API_ENDPOINTS = api_config.get("endpoints", {})

# ==========================================
# HELPER FUNCTIONS
# ==========================================

def get_docs_url():
    """Get the API documentation URL"""
    return f"{BACKEND_BASE_URL}/docs"

def get_health_url():
    """Get the health check URL"""
    return f"{BACKEND_BASE_URL}/health"

def is_development():
    """Check if running in development mode"""
    return os.getenv("ENVIRONMENT", "development") == "development"

def is_production():
    """Check if running in production mode"""
    return os.getenv("RAILWAY_ENVIRONMENT") is not None

def should_allow_all_cors():
    """Determine if CORS should allow all origins (development mode)"""
    return is_development()

def get_config():
    """Get the full configuration dictionary"""
    return _config

# Export commonly used configurations
__all__ = [
    'BACKEND_HOST', 'BACKEND_PORT', 'BACKEND_BASE_URL',
    'DEFAULT_HOST', 'DEFAULT_API_PORT', 'DEFAULT_WS_PORT', 'DEFAULT_FRONTEND_PORT',
    'FRONTEND_DEV_URL', 'FRONTEND_PROD_URL', 
    'CORS_ORIGINS', 'DEFAULT_CORS_ORIGINS', 'PRODUCTION_CORS_ORIGINS',
    'NEWS_API_BASE_URL', 'NEWS_API_FULL_URL',
    'WS_HOST', 'WS_PORT', 'WS_URL',
    'DATABASE_PATH', 'DATA_DIR', 'LOGS_DIR',
    'API_TIMEOUT', 'API_ENDPOINTS',
    'get_docs_url', 'get_health_url',
    'is_development', 'is_production', 'should_allow_all_cors',
    'get_config'
]
