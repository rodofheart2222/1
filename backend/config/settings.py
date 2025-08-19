"""
Configuration settings for MT5 COC Dashboard Backend
"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings

# Import centralized configuration
try:
    from .central_config import DATABASE_PATH
except ImportError:
    DATABASE_PATH = "data/mt5_dashboard.db"  # Fallback

class Settings(BaseSettings):
    # Database settings - now uses centralized configuration
    DATABASE_URL: str = DATABASE_PATH
    
    # Server settings - now managed in config/urls.py
    # HOST: str = "127.0.0.1"  # Deprecated - use config.urls.BACKEND_HOST
    # PORT: int = 80         # Deprecated - use config.urls.BACKEND_PORT
    DEBUG: bool = True
    
    # WebSocket settings - now managed in config/urls.py
    # WS_HOST: str = "127.0.0.1"  # Deprecated - use config.urls.WS_HOST
    # WS_PORT: int = 8765         # Deprecated - use config.urls.WS_PORT
    
    # MT5 Communication settings
    MT5_GLOBAL_VAR_PREFIX: str = "COC_EA_"
    MT5_COMMAND_PREFIX: str = "COC_CMD_"
    MT5_HEARTBEAT_INTERVAL: int = 30  # seconds
    MT5_TIMEOUT: int = 120  # seconds
    
    # News API settings - now managed in config/urls.py
    # NEWS_API_URL: str = "https://api.forexfactory.com/calendar"  # Deprecated - use config.urls.NEWS_API_FULL_URL
    NEWS_UPDATE_INTERVAL: int = 3600  # 1 hour in seconds
    
    # Performance settings
    MAX_CONCURRENT_EAS: int = 100
    DATA_RETENTION_DAYS: int = 90
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/mt5_dashboard.log"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Global settings instance
settings = Settings()