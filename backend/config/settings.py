"""
Configuration settings for MT5 COC Dashboard Backend
"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database settings
    DATABASE_URL: str = "data/mt5_dashboard.db"
    
    # Server settings
    HOST: str = "155.138.174.196"
    PORT: int = 80
    DEBUG: bool = True
    
    # WebSocket settings
    WS_HOST: str = "155.138.174.196"
    WS_PORT: int = 8765
    
    # MT5 Communication settings
    MT5_GLOBAL_VAR_PREFIX: str = "COC_EA_"
    MT5_COMMAND_PREFIX: str = "COC_CMD_"
    MT5_HEARTBEAT_INTERVAL: int = 30  # seconds
    MT5_TIMEOUT: int = 120  # seconds
    
    # News API settings
    NEWS_API_URL: str = "https://api.forexfactory.com/calendar"
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