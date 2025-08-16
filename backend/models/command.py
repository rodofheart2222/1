"""
Command queue models
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base
from datetime import datetime
from typing import Dict, Any, Optional
import json

class Command(Base):
    """Command Queue"""
    __tablename__ = "command_queue"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ea_id = Column(Integer, ForeignKey('eas.id'), nullable=True, index=True)  # Nullable for global commands
    command_type = Column(String(50), nullable=False)
    command_data = Column(Text)  # JSON format
    scheduled_time = Column(DateTime, default=func.now())
    executed = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=func.now())
    
    # Relationship
    ea = relationship("EA", back_populates="commands")
    
    def __repr__(self):
        return f"<Command(ea_id={self.ea_id}, type={self.command_type}, executed={self.executed})>"
    
    def get_command_data(self) -> Dict[str, Any]:
        """Parse command data JSON"""
        if self.command_data:
            try:
                return json.loads(self.command_data)
            except json.JSONDecodeError:
                return {}
        return {}
    
    def set_command_data(self, data_dict: Dict[str, Any]):
        """Set command data from dictionary"""
        self.command_data = json.dumps(data_dict)
    
    @property
    def is_due(self) -> bool:
        """Check if command is due for execution"""
        return datetime.now() >= self.scheduled_time and not self.executed
    
    @property
    def is_global_command(self) -> bool:
        """Check if this is a global command (affects multiple EAs)"""
        return self.ea_id is None
    
    def mark_executed(self):
        """Mark command as executed"""
        self.executed = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'ea_id': self.ea_id,
            'command_type': self.command_type,
            'command_data': self.get_command_data(),
            'scheduled_time': self.scheduled_time.isoformat() if self.scheduled_time else None,
            'executed': self.executed,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_due': self.is_due,
            'is_global_command': self.is_global_command
        }
    
    @classmethod
    def create_pause_command(cls, ea_id: Optional[int] = None, scheduled_time: datetime = None) -> 'Command':
        """Create a pause command"""
        command = cls(
            ea_id=ea_id,
            command_type='pause',
            scheduled_time=scheduled_time or datetime.now()
        )
        command.set_command_data({'action': 'pause'})
        return command
    
    @classmethod
    def create_resume_command(cls, ea_id: Optional[int] = None, scheduled_time: datetime = None) -> 'Command':
        """Create a resume command"""
        command = cls(
            ea_id=ea_id,
            command_type='resume',
            scheduled_time=scheduled_time or datetime.now()
        )
        command.set_command_data({'action': 'resume'})
        return command
    
    @classmethod
    def create_risk_adjustment_command(cls, ea_id: Optional[int], new_risk: float, scheduled_time: datetime = None) -> 'Command':
        """Create a risk adjustment command"""
        command = cls(
            ea_id=ea_id,
            command_type='adjust_risk',
            scheduled_time=scheduled_time or datetime.now()
        )
        command.set_command_data({
            'action': 'adjust_risk',
            'new_risk_level': new_risk
        })
        return command
    
    @classmethod
    def create_close_positions_command(cls, ea_id: Optional[int] = None, scheduled_time: datetime = None) -> 'Command':
        """Create a close positions command"""
        command = cls(
            ea_id=ea_id,
            command_type='close_positions',
            scheduled_time=scheduled_time or datetime.now()
        )
        command.set_command_data({'action': 'close_all_positions'})
        return command