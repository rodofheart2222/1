"""
Environment Configuration Management

Centralized configuration management for the MT5 Dashboard system.
All hardcoded values should be moved here and made configurable via environment variables.
"""

import os
from typing import Optional

# Import centralized configuration
try:
    from .central_config import (
        DEFAULT_HOST, 
        DEFAULT_API_PORT, 
        DEFAULT_WS_PORT, 
        DEFAULT_FRONTEND_PORT
    )
except ImportError:
    from central_config import (
        DEFAULT_HOST, 
        DEFAULT_API_PORT, 
        DEFAULT_WS_PORT, 
        DEFAULT_FRONTEND_PORT
    )


class Config:
    """Configuration class for MT5 Dashboard system"""
    
    # Server Configuration - now uses centralized config
    DEFAULT_HOST: str = DEFAULT_HOST
    DEFAULT_API_PORT: int = DEFAULT_API_PORT
    DEFAULT_WS_PORT: int = DEFAULT_WS_PORT
    DEFAULT_FRONTEND_PORT: int = DEFAULT_FRONTEND_PORT
    
    # Production overrides (for backward compatibility)
    PRODUCTION_API_PORT: int = 80
    
    # Security Configuration
    DEFAULT_AUTH_TOKEN: str = "dashboard_token_2024"
    
    # Database Configuration
    DEFAULT_DB_PATH: str = "data/mt5_dashboard.db"
    
    @classmethod
    def get_host(cls) -> str:
        """Get server host from environment or default"""
        return os.getenv("MT5_HOST", cls.DEFAULT_HOST)
    
    @classmethod
    def get_api_port(cls) -> int:
        """Get API port from environment or default"""
        # Check for production environment
        if os.getenv("ENVIRONMENT") == "production":
            return int(os.getenv("MT5_API_PORT", cls.PRODUCTION_API_PORT))
        return int(os.getenv("MT5_API_PORT", cls.DEFAULT_API_PORT))
    
    @classmethod
    def get_ws_port(cls) -> int:
        """Get WebSocket port from environment or default"""
        return int(os.getenv("MT5_WS_PORT", cls.DEFAULT_WS_PORT))
    
    @classmethod
    def get_frontend_port(cls) -> int:
        """Get frontend port from environment or default"""
        return int(os.getenv("MT5_FRONTEND_PORT", cls.DEFAULT_FRONTEND_PORT))
    
    @classmethod
    def get_auth_token(cls) -> str:
        """Get authentication token from environment or default"""
        return os.getenv("MT5_AUTH_TOKEN", cls.DEFAULT_AUTH_TOKEN)
    
    @classmethod
    def get_db_path(cls) -> str:
        """Get database path from environment or default"""
        return os.getenv("MT5_DB_PATH", cls.DEFAULT_DB_PATH)
    
    @classmethod
    def get_external_host(cls) -> str:
        """Get external host for client connections"""
        # For client connections, use external host if provided
        external_host = os.getenv("MT5_EXTERNAL_HOST")
        if external_host:
            return external_host
        
        # Fallback to regular host, but warn if it's 0.0.0.0
        host = cls.get_host()
        if host == "0.0.0.0":
            # Default to localhost for client connections
            return "127.0.0.1"
        return host
    
    @classmethod
    def is_production(cls) -> bool:
        """Check if running in production environment"""
        return os.getenv("ENVIRONMENT", "development").lower() == "production"
    
    @classmethod
    def is_development(cls) -> bool:
        """Check if running in development environment"""
        return not cls.is_production()
    
    @classmethod
    def get_log_level(cls) -> str:
        """Get logging level from environment"""
        return os.getenv("LOG_LEVEL", "INFO").upper()
    
    @classmethod
    def get_cors_origins(cls) -> list:
        """Get CORS origins from environment"""
        origins_str = os.getenv("CORS_ORIGINS", "")
        if origins_str:
            return [origin.strip() for origin in origins_str.split(",")]
        
        # Default CORS origins for development
        if cls.is_development():
            host = cls.get_external_host()
            api_port = cls.get_api_port()
            frontend_port = cls.get_frontend_port()
            
            # Import central URL configuration
            try:
                from backend.config.urls import DEFAULT_CORS_ORIGINS
            except ImportError:
                from config.urls import DEFAULT_CORS_ORIGINS
            
            return DEFAULT_CORS_ORIGINS
        
        return []
    
    @classmethod
    def get_all_config(cls) -> dict:
        """Get all configuration as dictionary for debugging"""
        return {
            "host": cls.get_host(),
            "external_host": cls.get_external_host(),
            "api_port": cls.get_api_port(),
            "ws_port": cls.get_ws_port(),
            "frontend_port": cls.get_frontend_port(),
            "auth_token": cls.get_auth_token()[:8] + "...",  # Masked for security
            "db_path": cls.get_db_path(),
            "environment": "production" if cls.is_production() else "development",
            "log_level": cls.get_log_level(),
            "cors_origins": cls.get_cors_origins(),
        }


# Convenience functions for backward compatibility
def get_host() -> str:
    return Config.get_host()

def get_api_port() -> int:
    return Config.get_api_port()

def get_ws_port() -> int:
    return Config.get_ws_port()

def get_frontend_port() -> int:
    return Config.get_frontend_port()

def get_auth_token() -> str:
    return Config.get_auth_token()

def get_external_host() -> str:
    return Config.get_external_host()