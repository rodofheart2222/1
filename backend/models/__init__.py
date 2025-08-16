"""
SQLAlchemy models for MT5 COC Dashboard
"""
from .base import Base, engine, SessionLocal, get_db, create_tables, drop_tables
from .ea import EA, EAStatus
from .performance import PerformanceHistory, BacktestBenchmark
from .trade import Trade
from .news import NewsEvent
from .command import Command
from .ea_tag import EATag, EAGroup, EAGroupMembership

# Export all models
__all__ = [
    'Base',
    'engine', 
    'SessionLocal',
    'get_db',
    'create_tables',
    'drop_tables',
    'EA',
    'EAStatus',
    'PerformanceHistory',
    'BacktestBenchmark',
    'Trade',
    'NewsEvent',
    'Command',
    'EATag',
    'EAGroup',
    'EAGroupMembership'
]