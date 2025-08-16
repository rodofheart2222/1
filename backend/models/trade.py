"""
Trade related models
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base
from datetime import datetime
from typing import Dict, Any, Optional

class Trade(Base):
    """Trade Journal"""
    __tablename__ = "trades"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ea_id = Column(Integer, ForeignKey('eas.id'), nullable=False, index=True)
    symbol = Column(String(10), nullable=False, index=True)
    order_type = Column(String(20), nullable=False)  # BUY, SELL, BUY_LIMIT, SELL_LIMIT, etc.
    volume = Column(Float, nullable=False)
    open_price = Column(Float, nullable=False)
    close_price = Column(Float)
    profit = Column(Float, default=0.0)
    open_time = Column(DateTime, nullable=False, index=True)
    close_time = Column(DateTime)
    
    # Relationship
    ea = relationship("EA", back_populates="trades")
    
    def __repr__(self):
        return f"<Trade(ea_id={self.ea_id}, symbol={self.symbol}, type={self.order_type}, profit={self.profit})>"
    
    @property
    def is_closed(self) -> bool:
        """Check if trade is closed"""
        return self.close_time is not None and self.close_price is not None
    
    @property
    def duration_minutes(self) -> Optional[int]:
        """Calculate trade duration in minutes"""
        if self.is_closed:
            delta = self.close_time - self.open_time
            return int(delta.total_seconds() / 60)
        return None
    
    @property
    def is_profitable(self) -> bool:
        """Check if trade is profitable"""
        return self.profit > 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'ea_id': self.ea_id,
            'symbol': self.symbol,
            'order_type': self.order_type,
            'volume': self.volume,
            'open_price': self.open_price,
            'close_price': self.close_price,
            'profit': self.profit,
            'open_time': self.open_time.isoformat() if self.open_time else None,
            'close_time': self.close_time.isoformat() if self.close_time else None,
            'is_closed': self.is_closed,
            'duration_minutes': self.duration_minutes,
            'is_profitable': self.is_profitable
        }
    
    def to_journal_format(self) -> str:
        """Format trade for journal display as specified in requirements"""
        order_prefix = "[LIMIT]" if "LIMIT" in self.order_type else "[MARKET]"
        action = "Buy" if "BUY" in self.order_type else "Sell"
        
        if self.is_closed:
            return f"{order_prefix} {self.symbol} {action} {self.volume} @ {self.open_price} -> {self.close_price} (P/L: {self.profit})"
        else:
            return f"{order_prefix} {self.symbol} {action} {self.volume} @ {self.open_price} (Open)"
    
    @classmethod
    def calculate_performance_metrics(cls, trades_list) -> Dict[str, float]:
        """Calculate performance metrics from a list of trades"""
        if not trades_list:
            return {
                'total_profit': 0.0,
                'profit_factor': 0.0,
                'expected_payoff': 0.0,
                'win_rate': 0.0,
                'trade_count': 0
            }
        
        closed_trades = [t for t in trades_list if t.is_closed]
        
        if not closed_trades:
            return {
                'total_profit': 0.0,
                'profit_factor': 0.0,
                'expected_payoff': 0.0,
                'win_rate': 0.0,
                'trade_count': 0
            }
        
        total_profit = sum(t.profit for t in closed_trades)
        winning_trades = [t for t in closed_trades if t.profit > 0]
        losing_trades = [t for t in closed_trades if t.profit < 0]
        
        gross_profit = sum(t.profit for t in winning_trades) if winning_trades else 0
        gross_loss = abs(sum(t.profit for t in losing_trades)) if losing_trades else 0
        
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else gross_profit
        expected_payoff = total_profit / len(closed_trades) if closed_trades else 0
        win_rate = (len(winning_trades) / len(closed_trades)) * 100 if closed_trades else 0
        
        return {
            'total_profit': round(total_profit, 2),
            'profit_factor': round(profit_factor, 2),
            'expected_payoff': round(expected_payoff, 2),
            'win_rate': round(win_rate, 2),
            'trade_count': len(closed_trades)
        }