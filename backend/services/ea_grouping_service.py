"""
EA Grouping and Tagging Service

This module provides the EAGroupingService class for managing EA tags, groups,
and filtered command execution based on grouping criteria.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union, Set
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func

from ..database.connection import get_db_session
from ..models.ea import EA
from ..models.ea_tag import EATag, EAGroup, EAGroupMembership
from ..models.command import Command
from .command_dispatcher import CommandDispatcher, CommandFilter

# Configure logging
logger = logging.getLogger(__name__)


class EAGroupingService:
    """
    Service for managing EA grouping, tagging, and filtered operations
    """
    
    def __init__(self, command_dispatcher: Optional[CommandDispatcher] = None):
        """
        Initialize EAGroupingService
        
        Args:
            command_dispatcher: Optional CommandDispatcher for executing commands
        """
        self.command_dispatcher = command_dispatcher
        logger.info("EAGroupingService initialized")
    
    # Tag Management Methods
    
    def add_tag(self, ea_id: int, tag_name: str, tag_value: Optional[str] = None) -> bool:
        """
        Add a tag to an EA
        
        Args:
            ea_id: EA ID
            tag_name: Name of the tag
            tag_value: Optional value for the tag
            
        Returns:
            True if tag was added successfully
        """
        try:
            with get_db_session() as session:
                # Check if EA exists
                ea = session.query(EA).filter(EA.id == ea_id).first()
                if not ea:
                    logger.error(f"EA with ID {ea_id} not found")
                    return False
                
                # Check if tag already exists
                existing_tag = session.query(EATag).filter(
                    and_(EATag.ea_id == ea_id, EATag.tag_name == tag_name)
                ).first()
                
                if existing_tag:
                    # Update existing tag
                    existing_tag.tag_value = tag_value
                    logger.info(f"Updated tag '{tag_name}' for EA {ea_id}")
                else:
                    # Create new tag
                    new_tag = EATag(
                        ea_id=ea_id,
                        tag_name=tag_name,
                        tag_value=tag_value
                    )
                    session.add(new_tag)
                    logger.info(f"Added tag '{tag_name}' to EA {ea_id}")
                
                session.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error adding tag to EA {ea_id}: {e}")
            return False
    
    def remove_tag(self, ea_id: int, tag_name: str) -> bool:
        """
        Remove a tag from an EA
        
        Args:
            ea_id: EA ID
            tag_name: Name of the tag to remove
            
        Returns:
            True if tag was removed successfully
        """
        try:
            with get_db_session() as session:
                tag = session.query(EATag).filter(
                    and_(EATag.ea_id == ea_id, EATag.tag_name == tag_name)
                ).first()
                
                if not tag:
                    logger.warning(f"Tag '{tag_name}' not found for EA {ea_id}")
                    return False
                
                session.delete(tag)
                session.commit()
                
                logger.info(f"Removed tag '{tag_name}' from EA {ea_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error removing tag from EA {ea_id}: {e}")
            return False
    
    def get_ea_tags(self, ea_id: int) -> Dict[str, str]:
        """
        Get all tags for an EA
        
        Args:
            ea_id: EA ID
            
        Returns:
            Dictionary of tag_name -> tag_value
        """
        try:
            with get_db_session() as session:
                tags = session.query(EATag).filter(EATag.ea_id == ea_id).all()
                return {tag.tag_name: tag.tag_value for tag in tags}
                
        except Exception as e:
            logger.error(f"Error getting tags for EA {ea_id}: {e}")
            return {}
    
    def find_eas_by_tag(self, tag_name: str, tag_value: Optional[str] = None) -> List[EA]:
        """
        Find EAs by tag criteria
        
        Args:
            tag_name: Name of the tag
            tag_value: Optional specific value to match
            
        Returns:
            List of matching EA objects
        """
        try:
            with get_db_session() as session:
                query = session.query(EA).join(EATag).filter(EATag.tag_name == tag_name)
                
                if tag_value is not None:
                    query = query.filter(EATag.tag_value == tag_value)
                
                eas = query.all()
                logger.debug(f"Found {len(eas)} EAs with tag '{tag_name}'")
                return eas
                
        except Exception as e:
            logger.error(f"Error finding EAs by tag: {e}")
            return []
    
    def get_all_tag_names(self) -> List[str]:
        """
        Get all unique tag names in the system
        
        Returns:
            List of unique tag names
        """
        try:
            with get_db_session() as session:
                tag_names = session.query(EATag.tag_name).distinct().all()
                return [name[0] for name in tag_names]
                
        except Exception as e:
            logger.error(f"Error getting tag names: {e}")
            return []
    
    def get_tag_usage_stats(self) -> Dict[str, int]:
        """
        Get usage statistics for all tags
        
        Returns:
            Dictionary of tag_name -> usage_count
        """
        try:
            with get_db_session() as session:
                stats = session.query(
                    EATag.tag_name,
                    func.count(EATag.id).label('count')
                ).group_by(EATag.tag_name).all()
                
                return {stat.tag_name: stat.count for stat in stats}
                
        except Exception as e:
            logger.error(f"Error getting tag usage stats: {e}")
            return {}
    
    # Group Management Methods
    
    def create_group(self, group_name: str, group_type: str, description: Optional[str] = None) -> Optional[EAGroup]:
        """
        Create a new EA group
        
        Args:
            group_name: Name of the group
            group_type: Type of group (symbol, strategy, risk_level, custom)
            description: Optional description
            
        Returns:
            Created EAGroup object or None if failed
        """
        try:
            with get_db_session() as session:
                # Check if group already exists
                existing_group = session.query(EAGroup).filter(
                    EAGroup.group_name == group_name
                ).first()
                
                if existing_group:
                    logger.warning(f"Group '{group_name}' already exists")
                    return existing_group
                
                # Create new group
                new_group = EAGroup(
                    group_name=group_name,
                    group_type=group_type,
                    description=description
                )
                
                session.add(new_group)
                session.commit()
                session.refresh(new_group)
                
                logger.info(f"Created group '{group_name}' of type '{group_type}'")
                return new_group
                
        except Exception as e:
            logger.error(f"Error creating group: {e}")
            return None
    
    def delete_group(self, group_id: int) -> bool:
        """
        Delete an EA group
        
        Args:
            group_id: ID of the group to delete
            
        Returns:
            True if group was deleted successfully
        """
        try:
            with get_db_session() as session:
                group = session.query(EAGroup).filter(EAGroup.id == group_id).first()
                
                if not group:
                    logger.warning(f"Group with ID {group_id} not found")
                    return False
                
                session.delete(group)
                session.commit()
                
                logger.info(f"Deleted group '{group.group_name}'")
                return True
                
        except Exception as e:
            logger.error(f"Error deleting group {group_id}: {e}")
            return False
    
    def add_ea_to_group(self, ea_id: int, group_id: int) -> bool:
        """
        Add an EA to a group
        
        Args:
            ea_id: EA ID
            group_id: Group ID
            
        Returns:
            True if EA was added to group successfully
        """
        try:
            with get_db_session() as session:
                # Check if EA and group exist
                ea = session.query(EA).filter(EA.id == ea_id).first()
                group = session.query(EAGroup).filter(EAGroup.id == group_id).first()
                
                if not ea:
                    logger.error(f"EA with ID {ea_id} not found")
                    return False
                
                if not group:
                    logger.error(f"Group with ID {group_id} not found")
                    return False
                
                # Check if membership already exists
                existing_membership = session.query(EAGroupMembership).filter(
                    and_(
                        EAGroupMembership.ea_id == ea_id,
                        EAGroupMembership.group_id == group_id
                    )
                ).first()
                
                if existing_membership:
                    logger.warning(f"EA {ea_id} is already in group {group_id}")
                    return True
                
                # Create new membership
                membership = EAGroupMembership(ea_id=ea_id, group_id=group_id)
                session.add(membership)
                session.commit()
                
                logger.info(f"Added EA {ea_id} to group '{group.group_name}'")
                return True
                
        except Exception as e:
            logger.error(f"Error adding EA {ea_id} to group {group_id}: {e}")
            return False
    
    def remove_ea_from_group(self, ea_id: int, group_id: int) -> bool:
        """
        Remove an EA from a group
        
        Args:
            ea_id: EA ID
            group_id: Group ID
            
        Returns:
            True if EA was removed from group successfully
        """
        try:
            with get_db_session() as session:
                membership = session.query(EAGroupMembership).filter(
                    and_(
                        EAGroupMembership.ea_id == ea_id,
                        EAGroupMembership.group_id == group_id
                    )
                ).first()
                
                if not membership:
                    logger.warning(f"EA {ea_id} is not in group {group_id}")
                    return False
                
                session.delete(membership)
                session.commit()
                
                logger.info(f"Removed EA {ea_id} from group {group_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error removing EA {ea_id} from group {group_id}: {e}")
            return False
    
    def get_group_members(self, group_id: int) -> List[EA]:
        """
        Get all EAs in a group
        
        Args:
            group_id: Group ID
            
        Returns:
            List of EA objects in the group
        """
        try:
            with get_db_session() as session:
                eas = session.query(EA).join(EAGroupMembership).filter(
                    EAGroupMembership.group_id == group_id
                ).all()
                
                logger.debug(f"Found {len(eas)} EAs in group {group_id}")
                return eas
                
        except Exception as e:
            logger.error(f"Error getting group members: {e}")
            return []
    
    def get_ea_groups(self, ea_id: int) -> List[EAGroup]:
        """
        Get all groups an EA belongs to
        
        Args:
            ea_id: EA ID
            
        Returns:
            List of EAGroup objects
        """
        try:
            with get_db_session() as session:
                groups = session.query(EAGroup).join(EAGroupMembership).filter(
                    EAGroupMembership.ea_id == ea_id
                ).all()
                
                logger.debug(f"EA {ea_id} belongs to {len(groups)} groups")
                return groups
                
        except Exception as e:
            logger.error(f"Error getting EA groups: {e}")
            return []
    
    def get_all_groups(self, group_type: Optional[str] = None) -> List[EAGroup]:
        """
        Get all groups, optionally filtered by type
        
        Args:
            group_type: Optional group type filter
            
        Returns:
            List of EAGroup objects
        """
        try:
            with get_db_session() as session:
                query = session.query(EAGroup)
                
                if group_type:
                    query = query.filter(EAGroup.group_type == group_type)
                
                groups = query.all()
                logger.debug(f"Found {len(groups)} groups")
                return groups
                
        except Exception as e:
            logger.error(f"Error getting groups: {e}")
            return []
    
    # Auto-grouping Methods
    
    def auto_group_by_symbol(self) -> Dict[str, int]:
        """
        Automatically create and populate symbol-based groups
        
        Returns:
            Dictionary of symbol -> group_id
        """
        try:
            with get_db_session() as session:
                # Get all unique symbols
                symbols = session.query(EA.symbol).distinct().all()
                symbol_groups = {}
                
                for (symbol,) in symbols:
                    group_name = f"Symbol_{symbol}"
                    
                    # Create or get group
                    group = session.query(EAGroup).filter(
                        EAGroup.group_name == group_name
                    ).first()
                    
                    if not group:
                        group = EAGroup(
                            group_name=group_name,
                            group_type='symbol',
                            description=f'Auto-generated group for symbol {symbol}'
                        )
                        session.add(group)
                        session.flush()  # Get ID without committing
                    
                    # Add all EAs with this symbol to the group
                    eas = session.query(EA).filter(EA.symbol == symbol).all()
                    for ea in eas:
                        # Check if membership already exists
                        existing = session.query(EAGroupMembership).filter(
                            and_(
                                EAGroupMembership.ea_id == ea.id,
                                EAGroupMembership.group_id == group.id
                            )
                        ).first()
                        
                        if not existing:
                            membership = EAGroupMembership(ea_id=ea.id, group_id=group.id)
                            session.add(membership)
                    
                    symbol_groups[symbol] = group.id
                
                session.commit()
                logger.info(f"Auto-grouped {len(symbol_groups)} symbols")
                return symbol_groups
                
        except Exception as e:
            logger.error(f"Error auto-grouping by symbol: {e}")
            return {}
    
    def auto_group_by_strategy(self) -> Dict[str, int]:
        """
        Automatically create and populate strategy-based groups
        
        Returns:
            Dictionary of strategy_tag -> group_id
        """
        try:
            with get_db_session() as session:
                # Get all unique strategy tags
                strategies = session.query(EA.strategy_tag).distinct().all()
                strategy_groups = {}
                
                for (strategy_tag,) in strategies:
                    group_name = f"Strategy_{strategy_tag.replace(' ', '_')}"
                    
                    # Create or get group
                    group = session.query(EAGroup).filter(
                        EAGroup.group_name == group_name
                    ).first()
                    
                    if not group:
                        group = EAGroup(
                            group_name=group_name,
                            group_type='strategy',
                            description=f'Auto-generated group for strategy {strategy_tag}'
                        )
                        session.add(group)
                        session.flush()
                    
                    # Add all EAs with this strategy to the group
                    eas = session.query(EA).filter(EA.strategy_tag == strategy_tag).all()
                    for ea in eas:
                        # Check if membership already exists
                        existing = session.query(EAGroupMembership).filter(
                            and_(
                                EAGroupMembership.ea_id == ea.id,
                                EAGroupMembership.group_id == group.id
                            )
                        ).first()
                        
                        if not existing:
                            membership = EAGroupMembership(ea_id=ea.id, group_id=group.id)
                            session.add(membership)
                    
                    strategy_groups[strategy_tag] = group.id
                
                session.commit()
                logger.info(f"Auto-grouped {len(strategy_groups)} strategies")
                return strategy_groups
                
        except Exception as e:
            logger.error(f"Error auto-grouping by strategy: {e}")
            return {}
    
    def auto_group_by_risk_level(self) -> Dict[float, int]:
        """
        Automatically create and populate risk level-based groups
        
        Returns:
            Dictionary of risk_level -> group_id
        """
        try:
            with get_db_session() as session:
                # Get all unique risk levels (rounded to 2 decimal places)
                risk_levels = session.query(
                    func.round(EA.risk_config, 2).label('risk_level')
                ).distinct().all()
                
                risk_groups = {}
                
                for (risk_level,) in risk_levels:
                    group_name = f"Risk_{risk_level}"
                    
                    # Create or get group
                    group = session.query(EAGroup).filter(
                        EAGroup.group_name == group_name
                    ).first()
                    
                    if not group:
                        group = EAGroup(
                            group_name=group_name,
                            group_type='risk_level',
                            description=f'Auto-generated group for risk level {risk_level}'
                        )
                        session.add(group)
                        session.flush()
                    
                    # Add all EAs with this risk level to the group
                    eas = session.query(EA).filter(
                        func.round(EA.risk_config, 2) == risk_level
                    ).all()
                    
                    for ea in eas:
                        # Check if membership already exists
                        existing = session.query(EAGroupMembership).filter(
                            and_(
                                EAGroupMembership.ea_id == ea.id,
                                EAGroupMembership.group_id == group.id
                            )
                        ).first()
                        
                        if not existing:
                            membership = EAGroupMembership(ea_id=ea.id, group_id=group.id)
                            session.add(membership)
                    
                    risk_groups[risk_level] = group.id
                
                session.commit()
                logger.info(f"Auto-grouped {len(risk_groups)} risk levels")
                return risk_groups
                
        except Exception as e:
            logger.error(f"Error auto-grouping by risk level: {e}")
            return {}
    
    # Advanced Filtering and Command Execution
    
    def find_eas_by_criteria(self, 
                           symbols: Optional[List[str]] = None,
                           strategy_tags: Optional[List[str]] = None,
                           risk_levels: Optional[List[float]] = None,
                           statuses: Optional[List[str]] = None,
                           tags: Optional[Dict[str, str]] = None,
                           groups: Optional[List[str]] = None) -> List[EA]:
        """
        Find EAs by multiple criteria
        
        Args:
            symbols: List of symbols to filter by
            strategy_tags: List of strategy tags to filter by
            risk_levels: List of risk levels to filter by
            statuses: List of statuses to filter by
            tags: Dictionary of tag_name -> tag_value to filter by
            groups: List of group names to filter by
            
        Returns:
            List of matching EA objects
        """
        try:
            with get_db_session() as session:
                query = session.query(EA).options(
                    joinedload(EA.tags),
                    joinedload(EA.group_memberships).joinedload(EAGroupMembership.group)
                )
                
                # Apply basic filters
                if symbols:
                    query = query.filter(EA.symbol.in_(symbols))
                
                if strategy_tags:
                    query = query.filter(EA.strategy_tag.in_(strategy_tags))
                
                if risk_levels:
                    query = query.filter(EA.risk_config.in_(risk_levels))
                
                if statuses:
                    query = query.filter(EA.status.in_(statuses))
                
                # Apply tag filters
                if tags:
                    for tag_name, tag_value in tags.items():
                        query = query.join(EATag).filter(
                            and_(
                                EATag.tag_name == tag_name,
                                EATag.tag_value == tag_value
                            )
                        )
                
                # Apply group filters
                if groups:
                    query = query.join(EAGroupMembership).join(EAGroup).filter(
                        EAGroup.group_name.in_(groups)
                    )
                
                eas = query.distinct().all()
                logger.debug(f"Found {len(eas)} EAs matching criteria")
                return eas
                
        except Exception as e:
            logger.error(f"Error finding EAs by criteria: {e}")
            return []
    
    def execute_command_by_tags(self, 
                              command_type: str,
                              tags: Dict[str, str],
                              parameters: Optional[Dict[str, Any]] = None,
                              scheduled_time: Optional[datetime] = None) -> List[Command]:
        """
        Execute command on EAs matching tag criteria
        
        Args:
            command_type: Type of command to execute
            tags: Dictionary of tag_name -> tag_value to filter by
            parameters: Optional command parameters
            scheduled_time: Optional scheduled execution time
            
        Returns:
            List of created Command objects
        """
        if not self.command_dispatcher:
            logger.error("No command dispatcher available")
            return []
        
        try:
            # Find matching EAs
            matching_eas = self.find_eas_by_criteria(tags=tags)
            
            if not matching_eas:
                logger.warning("No EAs found matching tag criteria")
                return []
            
            # Create commands for matching EAs
            commands = []
            for ea in matching_eas:
                command = self.command_dispatcher.create_command(
                    ea_id=ea.id,
                    command_type=command_type,
                    parameters=parameters,
                    scheduled_time=scheduled_time
                )
                if command:
                    commands.append(command)
            
            logger.info(f"Created {len(commands)} commands for tag-filtered EAs")
            return commands
            
        except Exception as e:
            logger.error(f"Error executing command by tags: {e}")
            return []
    
    def execute_command_by_groups(self, 
                                command_type: str,
                                group_names: List[str],
                                parameters: Optional[Dict[str, Any]] = None,
                                scheduled_time: Optional[datetime] = None) -> List[Command]:
        """
        Execute command on EAs in specified groups
        
        Args:
            command_type: Type of command to execute
            group_names: List of group names to target
            parameters: Optional command parameters
            scheduled_time: Optional scheduled execution time
            
        Returns:
            List of created Command objects
        """
        if not self.command_dispatcher:
            logger.error("No command dispatcher available")
            return []
        
        try:
            # Find matching EAs
            matching_eas = self.find_eas_by_criteria(groups=group_names)
            
            if not matching_eas:
                logger.warning("No EAs found in specified groups")
                return []
            
            # Create commands for matching EAs
            commands = []
            for ea in matching_eas:
                command = self.command_dispatcher.create_command(
                    ea_id=ea.id,
                    command_type=command_type,
                    parameters=parameters,
                    scheduled_time=scheduled_time
                )
                if command:
                    commands.append(command)
            
            logger.info(f"Created {len(commands)} commands for group-filtered EAs")
            return commands
            
        except Exception as e:
            logger.error(f"Error executing command by groups: {e}")
            return []
    
    # Utility Methods
    
    def get_grouping_summary(self) -> Dict[str, Any]:
        """
        Get summary of grouping and tagging system
        
        Returns:
            Dictionary with system summary
        """
        try:
            with get_db_session() as session:
                # Count totals
                total_eas = session.query(EA).count()
                total_groups = session.query(EAGroup).count()
                total_tags = session.query(EATag).count()
                total_memberships = session.query(EAGroupMembership).count()
                
                # Group counts by type
                group_types = session.query(
                    EAGroup.group_type,
                    func.count(EAGroup.id).label('count')
                ).group_by(EAGroup.group_type).all()
                
                group_type_counts = {gt.group_type: gt.count for gt in group_types}
                
                # Tag usage stats
                tag_stats = self.get_tag_usage_stats()
                
                summary = {
                    'total_eas': total_eas,
                    'total_groups': total_groups,
                    'total_tags': total_tags,
                    'total_memberships': total_memberships,
                    'group_types': group_type_counts,
                    'tag_usage': tag_stats,
                    'last_updated': datetime.now().isoformat()
                }
                
                return summary
                
        except Exception as e:
            logger.error(f"Error getting grouping summary: {e}")
            return {
                'total_eas': 0,
                'total_groups': 0,
                'total_tags': 0,
                'total_memberships': 0,
                'group_types': {},
                'tag_usage': {},
                'last_updated': datetime.now().isoformat()
            }
    
    def cleanup_empty_groups(self) -> int:
        """
        Remove groups that have no members
        
        Returns:
            Number of groups removed
        """
        try:
            with get_db_session() as session:
                # Find groups with no members
                empty_groups = session.query(EAGroup).outerjoin(EAGroupMembership).filter(
                    EAGroupMembership.group_id.is_(None)
                ).all()
                
                count = len(empty_groups)
                
                for group in empty_groups:
                    session.delete(group)
                
                session.commit()
                
                logger.info(f"Cleaned up {count} empty groups")
                return count
                
        except Exception as e:
            logger.error(f"Error cleaning up empty groups: {e}")
            return 0