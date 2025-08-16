"""
News event models
"""
from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from .base import Base
from datetime import datetime, timedelta
from typing import Dict, Any, List

class NewsEvent(Base):
    """News Events"""
    __tablename__ = "news_events"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    event_time = Column(DateTime, nullable=False, index=True)
    currency = Column(String(10), nullable=False)
    impact_level = Column(String(10), nullable=False)  # high, medium, low
    description = Column(Text, nullable=False)
    pre_minutes = Column(Integer, default=30)
    post_minutes = Column(Integer, default=30)
    
    def __repr__(self):
        return f"<NewsEvent(currency={self.currency}, impact={self.impact_level}, time={self.event_time})>"
    
    @property
    def blackout_start(self) -> datetime:
        """Calculate blackout period start time"""
        return self.event_time - timedelta(minutes=self.pre_minutes)
    
    @property
    def blackout_end(self) -> datetime:
        """Calculate blackout period end time"""
        return self.event_time + timedelta(minutes=self.post_minutes)
    
    def is_in_blackout_period(self, check_time: datetime = None) -> bool:
        """Check if given time (or current time) is in blackout period"""
        if check_time is None:
            check_time = datetime.now()
        
        return self.blackout_start <= check_time <= self.blackout_end
    
    def affects_symbol(self, symbol: str) -> bool:
        """Check if this news event affects the given trading symbol"""
        symbol_upper = symbol.upper()
        currency_upper = self.currency.upper()
        
        # Extract currency pairs from symbol (e.g., EURUSD -> EUR, USD)
        if len(symbol_upper) >= 6:
            base_currency = symbol_upper[:3]
            quote_currency = symbol_upper[3:6]
            return currency_upper in [base_currency, quote_currency]
        
        # For indices and commodities, check direct match
        return currency_upper in symbol_upper
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'event_time': self.event_time.isoformat() if self.event_time else None,
            'currency': self.currency,
            'impact_level': self.impact_level,
            'description': self.description,
            'pre_minutes': self.pre_minutes,
            'post_minutes': self.post_minutes,
            'blackout_start': self.blackout_start.isoformat(),
            'blackout_end': self.blackout_end.isoformat(),
            'is_active': self.is_in_blackout_period()
        }
    
    @classmethod
    def get_active_restrictions(cls, db_session, symbol: str = None) -> List['NewsEvent']:
        """Get currently active news restrictions"""
        current_time = datetime.now()
        
        query = db_session.query(cls).filter(
            cls.blackout_start <= current_time,
            cls.blackout_end >= current_time
        )
        
        active_events = query.all()
        
        if symbol:
            # Filter events that affect the specific symbol
            return [event for event in active_events if event.affects_symbol(symbol)]
        
        return active_events
    
    @classmethod
    def is_trading_allowed(cls, db_session, symbol: str) -> bool:
        """Check if trading is allowed for the given symbol"""
        active_restrictions = cls.get_active_restrictions(db_session, symbol)
        return len(active_restrictions) == 0