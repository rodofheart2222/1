"""
API module exports for the MT5 Dashboard backend.

This module re-exports the API routers with consistent naming.
"""

from . import ea_routes as ea_api
from . import backtest_routes as backtest_api
from . import news_routes as news_api
from . import trade_routes as trade_api

# Optional: also export other available APIs
from . import mt5_routes as mt5_api
from . import simple_backtest_routes as simple_backtest_api
from . import ea_sync_routes as ea_sync_api

__all__ = [
    'ea_api',
    'backtest_api', 
    'news_api',
    'trade_api',
    'mt5_api',
    'simple_backtest_api',
    'ea_sync_api'
]