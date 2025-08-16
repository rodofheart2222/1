"""
Performance tracking models
"""
from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base
from datetime import datetime, date
from typing import Dict, Any
from dataclasses import dataclass

@dataclass
class PerformanceMetrics:
    """Data class for performance metrics used in comparisons"""
    ea_id: int
    total_profit: float
    profit_factor: float
    expected_payoff: float
    drawdown: float
    z_score: float
    trade_count: int
    win_rate: float = 0.0  # Optional field for win rate
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'ea_id': self.ea_id,
            'total_profit': self.total_profit,
            'profit_factor': self.profit_factor,
            'expected_payoff': self.expected_payoff,
            'drawdown': self.drawdown,
            'z_score': self.z_score,
            'trade_count': self.trade_count,
            'win_rate': self.win_rate
        }

class PerformanceHistory(Base):
    """Performance Metrics History"""
    __tablename__ = "performance_history"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ea_id = Column(Integer, ForeignKey('eas.id'), nullable=False, index=True)
    date = Column(Date, default=func.date('now'), index=True)
    total_profit = Column(Float, default=0.0)
    profit_factor = Column(Float, default=0.0)
    expected_payoff = Column(Float, default=0.0)
    drawdown = Column(Float, default=0.0)
    z_score = Column(Float, default=0.0)
    trade_count = Column(Integer, default=0)
    
    # Relationship
    ea = relationship("EA", back_populates="performance_history")
    
    def __repr__(self):
        return f"<PerformanceHistory(ea_id={self.ea_id}, date={self.date}, pf={self.profit_factor})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'ea_id': self.ea_id,
            'date': self.date.isoformat() if self.date else None,
            'total_profit': self.total_profit,
            'profit_factor': self.profit_factor,
            'expected_payoff': self.expected_payoff,
            'drawdown': self.drawdown,
            'z_score': self.z_score,
            'trade_count': self.trade_count
        }

class BacktestBenchmark(Base):
    """Backtest Benchmarks"""
    __tablename__ = "backtest_benchmarks"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ea_id = Column(Integer, ForeignKey('eas.id'), nullable=False)
    profit_factor = Column(Float, nullable=False)
    expected_payoff = Column(Float, nullable=False)
    drawdown = Column(Float, nullable=False)
    win_rate = Column(Float, nullable=False)
    trade_count = Column(Integer, nullable=False)
    upload_date = Column(DateTime, default=func.now())
    
    # Relationship
    ea = relationship("EA", back_populates="backtest_benchmarks")
    
    def __repr__(self):
        return f"<BacktestBenchmark(ea_id={self.ea_id}, pf={self.profit_factor}, wr={self.win_rate})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'ea_id': self.ea_id,
            'profit_factor': self.profit_factor,
            'expected_payoff': self.expected_payoff,
            'drawdown': self.drawdown,
            'win_rate': self.win_rate,
            'trade_count': self.trade_count,
            'upload_date': self.upload_date.isoformat() if self.upload_date else None
        }
    
    def calculate_deviation(self, live_metrics: Dict[str, float]) -> Dict[str, float]:
        """Calculate deviation between backtest and live performance"""
        deviations = {}
        
        if 'profit_factor' in live_metrics:
            pf_deviation = ((live_metrics['profit_factor'] - self.profit_factor) / self.profit_factor) * 100
            deviations['profit_factor_deviation'] = round(pf_deviation, 2)
        
        if 'expected_payoff' in live_metrics:
            ep_deviation = ((live_metrics['expected_payoff'] - self.expected_payoff) / self.expected_payoff) * 100
            deviations['expected_payoff_deviation'] = round(ep_deviation, 2)
        
        if 'drawdown' in live_metrics:
            dd_deviation = ((live_metrics['drawdown'] - self.drawdown) / self.drawdown) * 100
            deviations['drawdown_deviation'] = round(dd_deviation, 2)
        
        if 'win_rate' in live_metrics:
            wr_deviation = ((live_metrics['win_rate'] - self.win_rate) / self.win_rate) * 100
            deviations['win_rate_deviation'] = round(wr_deviation, 2)
        
        return deviations