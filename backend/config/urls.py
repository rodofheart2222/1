"""
Backend URL Configuration
DEPRECATED: This file is deprecated. Use backend.config.central_config instead.
All configuration now comes from the central config.json file in the project root.
"""

# Import from central configuration
from .central_config import (
    BACKEND_HOST, BACKEND_PORT, BACKEND_BASE_URL,
    FRONTEND_DEV_URL, FRONTEND_PROD_URL,
    WS_HOST, WS_PORT, WS_URL,
    CORS_ORIGINS, DEFAULT_CORS_ORIGINS, PRODUCTION_CORS_ORIGINS,
    NEWS_API_BASE_URL, NEWS_API_FULL_URL,
    DATABASE_PATH, DATA_DIR, LOGS_DIR,
    API_TIMEOUT, API_ENDPOINTS,
    get_docs_url, get_health_url,
    is_development, is_production, should_allow_all_cors
)

# All configuration variables are now imported from central_config.py above
# This ensures single source of truth from the root config.json file

# Export commonly used configurations
__all__ = [
    'BACKEND_HOST', 'BACKEND_PORT', 'BACKEND_BASE_URL',
    'FRONTEND_DEV_URL', 'FRONTEND_PROD_URL', 
    'CORS_ORIGINS', 'DEFAULT_CORS_ORIGINS', 'PRODUCTION_CORS_ORIGINS',
    'NEWS_API_BASE_URL', 'NEWS_API_FULL_URL',
    'WS_HOST', 'WS_PORT', 'WS_URL',
    'DATABASE_PATH', 'DATA_DIR', 'LOGS_DIR',
    'get_docs_url', 'get_health_url',
    'is_development', 'is_production', 'should_allow_all_cors'
]
