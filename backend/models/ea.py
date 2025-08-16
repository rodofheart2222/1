"""
EA (Expert Advisor) related models
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base
import json
from datetime import datetime
from typing import Dict, Any, Optional, List

class EA(Base):
    """EA Registry and Configuration"""
    __tablename__ = "eas"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    magic_number = Column(Integer, unique=True, nullable=False, index=True)
    symbol = Column(String(10), nullable=False, index=True)
    strategy_tag = Column(String(100), nullable=False, index=True)
    risk_config = Column(Float, default=1.0)
    status = Column(String(20), default='active')  # active, paused, error
    created_at = Column(DateTime, default=func.now())
    last_seen = Column(DateTime, default=func.now())
    
    # Relationships
    status_records = relationship("EAStatus", back_populates="ea", cascade="all, delete-orphan")
    performance_history = relationship("PerformanceHistory", back_populates="ea", cascade="all, delete-orphan")
    trades = relationship("Trade", back_populates="ea", cascade="all, delete-orphan")
    backtest_benchmarks = relationship("BacktestBenchmark", back_populates="ea", cascade="all, delete-orphan")
    commands = relationship("Command", back_populates="ea", cascade="all, delete-orphan")
    tags = relationship("EATag", back_populates="ea", cascade="all, delete-orphan")
    group_memberships = relationship("EAGroupMembership", back_populates="ea", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<EA(magic_number={self.magic_number}, symbol={self.symbol}, strategy={self.strategy_tag})>"
    
    def to_dict(self, include_tags: bool = False, include_groups: bool = False) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result = {
            'id': self.id,
            'magic_number': self.magic_number,
            'symbol': self.symbol,
            'strategy_tag': self.strategy_tag,
            'risk_config': self.risk_config,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None
        }
        
        if include_tags and self.tags:
            result['tags'] = {tag.tag_name: tag.tag_value for tag in self.tags}
        
        if include_groups and self.group_memberships:
            result['groups'] = [membership.group.group_name for membership in self.group_memberships]
        
        return result
    
    def get_tags_dict(self) -> Dict[str, str]:
        """Get tags as a dictionary"""
        return {tag.tag_name: tag.tag_value for tag in self.tags}
    
    def get_groups_list(self) -> List[str]:
        """Get list of group names this EA belongs to"""
        return [membership.group.group_name for membership in self.group_memberships]

class EAStatus(Base):
    """Real-time EA Status"""
    __tablename__ = "ea_status"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ea_id = Column(Integer, ForeignKey('eas.id'), nullable=False, index=True)
    timestamp = Column(DateTime, default=func.now(), index=True)
    current_profit = Column(Float, default=0.0)
    open_positions = Column(Integer, default=0)
    sl_value = Column(Float)
    tp_value = Column(Float)
    trailing_active = Column(Boolean, default=False)
    module_status = Column(Text)  # JSON format
    
    # Relationship
    ea = relationship("EA", back_populates="status_records")
    
    def __repr__(self):
        return f"<EAStatus(ea_id={self.ea_id}, profit={self.current_profit}, positions={self.open_positions})>"
    
    def get_module_status(self) -> Dict[str, Any]:
        """Parse module status JSON"""
        if self.module_status:
            try:
                return json.loads(self.module_status)
            except json.JSONDecodeError:
                return {}
        return {}
    
    def set_module_status(self, status_dict: Dict[str, Any]):
        """Set module status from dictionary"""
        self.module_status = json.dumps(status_dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'ea_id': self.ea_id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'current_profit': self.current_profit,
            'open_positions': self.open_positions,
            'sl_value': self.sl_value,
            'tp_value': self.tp_value,
            'trailing_active': self.trailing_active,
            'module_status': self.get_module_status()
        }