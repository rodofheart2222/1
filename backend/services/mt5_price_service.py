"""
MT5 Price Data Service

This service provides real-time price data from MetaTrader 5 using the metatrader5 module.
It handles connection management, price streaming, and data formatting for WebSocket broadcasting.
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, asdict
import threading
from concurrent.futures import ThreadPoolExecutor

try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False
    logging.warning("MetaTrader5 module not available. Price service will use mock data.")

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class PriceData:
    """Price data structure"""
    symbol: str
    bid: float
    ask: float
    spread: float
    timestamp: datetime
    volume: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'symbol': self.symbol,
            'bid': self.bid,
            'ask': self.ask,
            'spread': self.spread,
            'price': (self.bid + self.ask) / 2,  # Mid price
            'timestamp': self.timestamp.isoformat(),
            'volume': self.volume
        }


@dataclass
class ChartData:
    """Chart data structure for mini charts"""
    symbol: str
    timeframe: str
    data: List[Dict[str, Any]]
    current_price: float
    price_change: float
    last_update: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'symbol': self.symbol,
            'timeframe': self.timeframe,
            'data': self.data,
            'currentPrice': self.current_price,  # Use camelCase for frontend consistency
            'current_price': self.current_price,  # Keep snake_case for backward compatibility
            'priceChange': self.price_change,  # Use camelCase for frontend consistency
            'price_change': self.price_change,  # Keep snake_case for backward compatibility
            'lastUpdate': self.last_update.isoformat(),  # Use camelCase for frontend consistency
            'last_update': self.last_update.isoformat()  # Keep snake_case for backward compatibility
        }


class MT5PriceService:
    """
    Service for getting real-time price data from MetaTrader 5
    """
    
    def __init__(self):
        self.mt5_connected = False
        self.subscribed_symbols: Set[str] = set()
        self.price_cache: Dict[str, PriceData] = {}
        self.chart_cache: Dict[str, ChartData] = {}
        self.price_callbacks: List[callable] = []
        self.running = False
        self.executor = ThreadPoolExecutor(max_workers=2)
        self.update_interval = 0.5  # seconds - faster updates for more realistic movement
        
        # Mock data for fallback
        self.mock_prices = {
            'EURUSD': 1.0847,
            'GBPUSD': 1.2634,
            'USDJPY': 149.82,
            'USDCHF': 0.8756,
            'AUDUSD': 0.6523,
            'USDCAD': 1.3789,
            'NZDUSD': 0.5987,
            'XAUUSD': 2034.67
        }
        
    async def initialize(self) -> bool:
        """Initialize MT5 connection"""
        if not MT5_AVAILABLE:
            logger.warning("MT5 not available, using mock data")
            return True
            
        try:
            # Run MT5 initialization in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            success = await loop.run_in_executor(
                self.executor, 
                self._initialize_mt5
            )
            
            if success:
                logger.info("MT5 Price Service initialized successfully")
                self.mt5_connected = True
            else:
                logger.error("Failed to initialize MT5, using mock data")
                
            return True
            
        except Exception as e:
            logger.error(f"Error initializing MT5 Price Service: {e}")
            return True  # Continue with mock data
    
    def _initialize_mt5(self) -> bool:
        """Initialize MT5 in thread (blocking operation)"""
        try:
            if not mt5.initialize():
                logger.error(f"MT5 initialization failed: {mt5.last_error()}")
                return False
                
            # Get account info
            account_info = mt5.account_info()
            if account_info is None:
                logger.error("Failed to get account info")
                return False
                
            logger.info(f"Connected to MT5 account: {account_info.login}")
            return True
            
        except Exception as e:
            logger.error(f"MT5 initialization error: {e}")
            return False
    
    async def shutdown(self):
        """Shutdown the price service"""
        self.running = False
        
        if MT5_AVAILABLE and self.mt5_connected:
            try:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(self.executor, mt5.shutdown)
                logger.info("MT5 connection closed")
            except Exception as e:
                logger.error(f"Error shutting down MT5: {e}")
        
        self.executor.shutdown(wait=True)
    
    def add_price_callback(self, callback: callable):
        """Add callback for price updates"""
        self.price_callbacks.append(callback)
    
    def remove_price_callback(self, callback: callable):
        """Remove price callback"""
        if callback in self.price_callbacks:
            self.price_callbacks.remove(callback)
    
    async def subscribe_symbol(self, symbol: str) -> bool:
        """Subscribe to price updates for a symbol"""
        try:
            self.subscribed_symbols.add(symbol)
            logger.info(f"Subscribed to price updates for {symbol}")
            
            # Get initial price data
            await self._update_symbol_price(symbol)
            return True
            
        except Exception as e:
            logger.error(f"Error subscribing to {symbol}: {e}")
            return False
    
    async def unsubscribe_symbol(self, symbol: str):
        """Unsubscribe from price updates for a symbol"""
        self.subscribed_symbols.discard(symbol)
        if symbol in self.price_cache:
            del self.price_cache[symbol]
        if symbol in self.chart_cache:
            del self.chart_cache[symbol]
        logger.info(f"Unsubscribed from {symbol}")
    
    async def start_price_stream(self):
        """Start the price streaming loop"""
        if self.running:
            return
            
        self.running = True
        logger.info("Starting price stream")
        
        while self.running:
            try:
                # Update prices for all subscribed symbols
                tasks = []
                for symbol in self.subscribed_symbols.copy():
                    task = self._update_symbol_price(symbol)
                    tasks.append(task)
                
                if tasks:
                    await asyncio.gather(*tasks, return_exceptions=True)
                
                # Notify callbacks
                await self._notify_price_callbacks()
                
                await asyncio.sleep(self.update_interval)
                
            except Exception as e:
                logger.error(f"Error in price stream: {e}")
                await asyncio.sleep(1)
    
    async def _update_symbol_price(self, symbol: str):
        """Update price data for a symbol"""
        try:
            if MT5_AVAILABLE and self.mt5_connected:
                # Get real price from MT5
                loop = asyncio.get_event_loop()
                tick = await loop.run_in_executor(
                    self.executor,
                    mt5.symbol_info_tick,
                    symbol
                )
                
                if tick is not None:
                    price_data = PriceData(
                        symbol=symbol,
                        bid=tick.bid,
                        ask=tick.ask,
                        spread=tick.ask - tick.bid,
                        timestamp=datetime.fromtimestamp(tick.time),
                        volume=tick.volume
                    )
                    self.price_cache[symbol] = price_data
                    return
            
            # Fallback to mock data
            await self._generate_mock_price(symbol)
            
        except Exception as e:
            logger.error(f"Error updating price for {symbol}: {e}")
            await self._generate_mock_price(symbol)
    
    async def _generate_mock_price(self, symbol: str):
        """Generate realistic mock price data with proper random movement"""
        try:
            import random
            import math
            
            base_price = self.mock_prices.get(symbol, 1.0000)
            
            # Get previous price for realistic movement
            previous_price = base_price
            if symbol in self.price_cache:
                previous_price = (self.price_cache[symbol].bid + self.price_cache[symbol].ask) / 2
            
            # Symbol-specific volatility and characteristics
            if symbol.upper() == 'XAUUSD':
                volatility = 2.5  # Gold is more volatile
                spread_pips = 0.5
                decimal_places = 2
            elif symbol.upper() in ['USDJPY', 'EURJPY', 'GBPJPY']:
                volatility = 0.05  # JPY pairs
                spread_pips = 0.002
                decimal_places = 3
            else:
                volatility = 0.0008  # Major currency pairs
                spread_pips = 0.00002
                decimal_places = 5
            
            # Generate realistic price movement using multiple factors
            current_time = time.time()
            
            # Base random walk with mean reversion
            random_factor = random.gauss(0, 1)  # Normal distribution
            mean_reversion = (base_price - previous_price) * 0.1  # Pull back to base price
            momentum = random.uniform(-0.3, 0.3)  # Short-term momentum
            
            # Combine factors for price change
            price_change = (random_factor * volatility * 0.3 + 
                          mean_reversion + 
                          momentum * volatility * 0.2)
            
            # Add some trending behavior occasionally
            trend_factor = math.sin(current_time / 300) * volatility * 0.1  # 5-minute cycle
            price_change += trend_factor
            
            # Apply the change
            new_price = previous_price + price_change
            
            # Ensure price doesn't drift too far from base (within 2% for currencies, 5% for gold)
            max_deviation = base_price * (0.05 if symbol.upper() == 'XAUUSD' else 0.02)
            if abs(new_price - base_price) > max_deviation:
                # Pull back towards base price
                new_price = base_price + (new_price - base_price) * 0.5
            
            # Calculate realistic bid/ask spread
            spread = spread_pips + random.uniform(0, spread_pips * 0.5)  # Variable spread
            bid = new_price - spread / 2
            ask = new_price + spread / 2
            
            # Round to appropriate decimal places
            bid = round(bid, decimal_places)
            ask = round(ask, decimal_places)
            spread = round(ask - bid, decimal_places)
            
            # Generate realistic volume
            base_volume = 100000
            volume_variation = random.uniform(0.5, 2.0)
            volume = int(base_volume * volume_variation)
            
            price_data = PriceData(
                symbol=symbol,
                bid=bid,
                ask=ask,
                spread=spread,
                timestamp=datetime.now(),
                volume=volume
            )
            
            self.price_cache[symbol] = price_data
            
        except Exception as e:
            logger.error(f"Error generating mock price for {symbol}: {e}")
    
    async def _notify_price_callbacks(self):
        """Notify all price callbacks"""
        if not self.price_callbacks or not self.price_cache:
            return
            
        try:
            # Prepare price update data
            price_updates = {}
            for symbol, price_data in self.price_cache.items():
                price_updates[symbol] = price_data.to_dict()
            
            # Notify all callbacks
            for callback in self.price_callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(price_updates)
                    else:
                        callback(price_updates)
                except Exception as e:
                    logger.error(f"Error in price callback: {e}")
                    
        except Exception as e:
            logger.error(f"Error notifying price callbacks: {e}")
    
    async def get_chart_data(self, symbol: str, timeframe: str = '1H', points: int = 50) -> Optional[ChartData]:
        """Get chart data for mini charts"""
        try:
            if MT5_AVAILABLE and self.mt5_connected:
                # Get real chart data from MT5
                chart_data = await self._get_mt5_chart_data(symbol, timeframe, points)
                if chart_data:
                    self.chart_cache[f"{symbol}_{timeframe}"] = chart_data
                    return chart_data
            
            # Fallback to mock chart data
            return await self._generate_mock_chart_data(symbol, timeframe, points)
            
        except Exception as e:
            logger.error(f"Error getting chart data for {symbol}: {e}")
            return await self._generate_mock_chart_data(symbol, timeframe, points)
    
    async def _get_mt5_chart_data(self, symbol: str, timeframe: str, points: int) -> Optional[ChartData]:
        """Get chart data from MT5"""
        try:
            # Map timeframe strings to MT5 constants
            timeframe_map = {
                '1M': mt5.TIMEFRAME_M1,
                '5M': mt5.TIMEFRAME_M5,
                '15M': mt5.TIMEFRAME_M15,
                '1H': mt5.TIMEFRAME_H1,
                '4H': mt5.TIMEFRAME_H4,
                '1D': mt5.TIMEFRAME_D1
            }
            
            mt5_timeframe = timeframe_map.get(timeframe, mt5.TIMEFRAME_H1)
            
            # Get rates from MT5
            loop = asyncio.get_event_loop()
            rates = await loop.run_in_executor(
                self.executor,
                mt5.copy_rates_from_pos,
                symbol,
                mt5_timeframe,
                0,
                points
            )
            
            if rates is None or len(rates) == 0:
                return None
            
            # Convert to chart data format
            chart_points = []
            for rate in rates:
                chart_points.append({
                    'timestamp': datetime.fromtimestamp(rate['time']).isoformat(),
                    'open': float(rate['open']),
                    'high': float(rate['high']),
                    'low': float(rate['low']),
                    'close': float(rate['close']),
                    'volume': int(rate['tick_volume'])
                })
            
            current_price = float(rates[-1]['close'])
            price_change = current_price - float(rates[-2]['close']) if len(rates) > 1 else 0.0
            
            return ChartData(
                symbol=symbol,
                timeframe=timeframe,
                data=chart_points,
                current_price=current_price,
                price_change=price_change,
                last_update=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error getting MT5 chart data: {e}")
            return None
    
    async def _generate_mock_chart_data(self, symbol: str, timeframe: str, points: int) -> ChartData:
        """Generate realistic mock chart data with proper OHLC candles"""
        import random
        import math
        
        base_price = self.mock_prices.get(symbol, 1.0000)
        data = []
        price = base_price
        now = datetime.now()
        
        # Timeframe intervals in minutes
        intervals = {
            '1M': 1,
            '5M': 5,
            '15M': 15,
            '1H': 60,
            '4H': 240,
            '1D': 1440
        }
        
        interval_minutes = intervals.get(timeframe, 60)
        
        # Symbol-specific parameters
        if symbol.upper() == 'XAUUSD':
            volatility = 3.0
            decimal_places = 2
            max_deviation = base_price * 0.05  # 5% max deviation
        elif symbol.upper() in ['USDJPY', 'EURJPY', 'GBPJPY']:
            volatility = 0.08
            decimal_places = 3
            max_deviation = base_price * 0.02  # 2% max deviation
        else:
            volatility = 0.0012
            decimal_places = 5
            max_deviation = base_price * 0.02  # 2% max deviation
        
        for i in range(points):
            timestamp = now - timedelta(minutes=(points - i - 1) * interval_minutes)
            
            # Generate realistic price movement with multiple factors
            time_factor = (i + time.time()) / 100  # Time-based seed
            
            # Random walk with mean reversion
            random_change = random.gauss(0, volatility * 0.3)
            mean_reversion = (base_price - price) * 0.05
            trend = math.sin(time_factor / 50) * volatility * 0.2  # Longer trend cycles
            
            # Combine factors
            price_change = random_change + mean_reversion + trend
            
            # Apply change but keep within bounds
            new_price = price + price_change
            if abs(new_price - base_price) > max_deviation:
                new_price = base_price + (new_price - base_price) * 0.7
            
            # Generate OHLC for this candle
            open_price = price
            close_price = new_price
            
            # Generate high and low with realistic behavior
            candle_range = abs(close_price - open_price) + volatility * random.uniform(0.2, 0.8)
            
            # High is typically above both open and close
            high = max(open_price, close_price) + candle_range * random.uniform(0.1, 0.6)
            
            # Low is typically below both open and close
            low = min(open_price, close_price) - candle_range * random.uniform(0.1, 0.6)
            
            # Ensure high >= max(open, close) and low <= min(open, close)
            high = max(high, open_price, close_price)
            low = min(low, open_price, close_price)
            
            # Round to appropriate decimal places
            open_price = round(open_price, decimal_places)
            high = round(high, decimal_places)
            low = round(low, decimal_places)
            close_price = round(close_price, decimal_places)
            
            # Generate realistic volume based on volatility and time
            base_volume = 50000
            volatility_factor = abs(close_price - open_price) / (volatility * 2) + 0.5
            time_factor = 1 + 0.3 * math.sin(time_factor / 10)  # Volume cycles
            volume = int(base_volume * volatility_factor * time_factor * random.uniform(0.7, 1.5))
            
            data.append({
                'timestamp': timestamp.isoformat(),
                'open': open_price,
                'high': high,
                'low': low,
                'close': close_price,
                'volume': volume
            })
            
            # Update price for next iteration
            price = close_price
        
        # Calculate price change from first to last
        price_change = data[-1]['close'] - data[0]['close'] if len(data) > 1 else 0.0
        
        return ChartData(
            symbol=symbol,
            timeframe=timeframe,
            data=data,
            current_price=data[-1]['close'],
            price_change=round(price_change, decimal_places),
            last_update=now
        )
    
    def get_current_price(self, symbol: str) -> Optional[PriceData]:
        """Get current price for a symbol"""
        return self.price_cache.get(symbol)
    
    def get_subscribed_symbols(self) -> List[str]:
        """Get list of subscribed symbols"""
        return list(self.subscribed_symbols)
    
    def get_price_cache(self) -> Dict[str, Dict[str, Any]]:
        """Get all cached prices"""
        return {symbol: price.to_dict() for symbol, price in self.price_cache.items()}


# Global instance
mt5_price_service = MT5PriceService()