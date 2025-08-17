"""API module for backend services."""

from . import ea_routes as ea_api
from . import backtest_routes as backtest_api
from . import news_routes as news_api
from . import trade_routes as trade_api

__all__ = ['ea_api', 'backtest_api', 'news_api', 'trade_api']