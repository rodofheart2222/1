"""
EA Tagging and Grouping models
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base
from typing import Dict, Any, List, Optional
from datetime import datetime


class EATag(Base):
    """Custom tags for EA instances"""
    __tablename__ = "ea_tags"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ea_id = Column(Integer, ForeignKey('eas.id'), nullable=False, index=True)
    tag_name = Column(String(100), nullable=False, index=True)
    tag_value = Column(Text)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    ea = relationship("EA", back_populates="tags")
    
    # Unique constraint
    __table_args__ = (UniqueConstraint('ea_id', 'tag_name', name='uq_ea_tag'),)
    
    def __repr__(self):
        return f"<EATag(ea_id={self.ea_id}, tag_name={self.tag_name}, tag_value={self.tag_value})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'ea_id': self.ea_id,
            'tag_name': self.tag_name,
            'tag_value': self.tag_value,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class EAGroup(Base):
    """Groups for organizing EAs"""
    __tablename__ = "ea_groups"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    group_name = Column(String(100), unique=True, nullable=False)
    group_type = Column(String(20), nullable=False, index=True)  # symbol, strategy, risk_level, custom
    description = Column(Text)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    memberships = relationship("EAGroupMembership", back_populates="group", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<EAGroup(name={self.group_name}, type={self.group_type})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'group_name': self.group_name,
            'group_type': self.group_type,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def get_member_count(self, session) -> int:
        """Get number of EAs in this group"""
        return session.query(EAGroupMembership).filter(
            EAGroupMembership.group_id == self.id
        ).count()
    
    def get_members(self, session) -> List['EA']:
        """Get all EA members of this group"""
        from .ea import EA
        return session.query(EA).join(EAGroupMembership).filter(
            EAGroupMembership.group_id == self.id
        ).all()


class EAGroupMembership(Base):
    """Many-to-many relationship between EAs and Groups"""
    __tablename__ = "ea_group_memberships"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ea_id = Column(Integer, ForeignKey('eas.id'), nullable=False, index=True)
    group_id = Column(Integer, ForeignKey('ea_groups.id'), nullable=False, index=True)
    added_at = Column(DateTime, default=func.now())
    
    # Relationships
    ea = relationship("EA", back_populates="group_memberships")
    group = relationship("EAGroup", back_populates="memberships")
    
    # Unique constraint
    __table_args__ = (UniqueConstraint('ea_id', 'group_id', name='uq_ea_group_membership'),)
    
    def __repr__(self):
        return f"<EAGroupMembership(ea_id={self.ea_id}, group_id={self.group_id})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'ea_id': self.ea_id,
            'group_id': self.group_id,
            'added_at': self.added_at.isoformat() if self.added_at else None
        }