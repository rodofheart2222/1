"""
EA Grouping Service Integration Example

This example demonstrates how to integrate the EA Grouping Service
with the WebSocket server and command dispatcher for real-time
grouping and tagging operations.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any, List

from .ea_grouping_service import EAGroupingService
from .command_dispatcher import CommandDispatcher
from .mt5_communication import MT5CommunicationInterface
from .websocket_server import DashboardWebSocketServer
from ..database.connection import get_db_session
from ..models.ea import EA

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EAGroupingWebSocketHandler:
    """
    WebSocket handler for EA grouping and tagging operations
    """
    
    def __init__(self, websocket_server: DashboardWebSocketServer):
        self.websocket_server = websocket_server
        self.mt5_interface = MT5CommunicationInterface()
        self.command_dispatcher = CommandDispatcher(self.mt5_interface)
        self.grouping_service = EAGroupingService(self.command_dispatcher)
        
        # Register WebSocket event handlers
        self.register_handlers()
        
        logger.info("EAGroupingWebSocketHandler initialized")
    
    def register_handlers(self):
        """Register WebSocket event handlers for grouping operations"""
        
        # Group management handlers
        self.websocket_server.register_handler('get_grouping_data', self.handle_get_grouping_data)
        self.websocket_server.register_handler('get_grouping_stats', self.handle_get_grouping_stats)
        self.websocket_server.register_handler('create_group', self.handle_create_group)
        self.websocket_server.register_handler('delete_group', self.handle_delete_group)
        self.websocket_server.register_handler('add_ea_to_group', self.handle_add_ea_to_group)
        self.websocket_server.register_handler('remove_ea_from_group', self.handle_remove_ea_from_group)
        
        # Auto-grouping handlers
        self.websocket_server.register_handler('auto_group_by_symbol', self.handle_auto_group_by_symbol)
        self.websocket_server.register_handler('auto_group_by_strategy', self.handle_auto_group_by_strategy)
        self.websocket_server.register_handler('auto_group_by_risk_level', self.handle_auto_group_by_risk_level)
        
        # Tag management handlers
        self.websocket_server.register_handler('add_ea_tag', self.handle_add_ea_tag)
        self.websocket_server.register_handler('remove_ea_tag', self.handle_remove_ea_tag)
        self.websocket_server.register_handler('get_ea_tags', self.handle_get_ea_tags)
        
        # Command execution handlers
        self.websocket_server.register_handler('execute_command_by_groups', self.handle_execute_command_by_groups)
        self.websocket_server.register_handler('execute_command_by_tags', self.handle_execute_command_by_tags)
        self.websocket_server.register_handler('execute_command_by_criteria', self.handle_execute_command_by_criteria)
        
        logger.info("Registered all grouping WebSocket handlers")
    
    async def handle_get_grouping_data(self, websocket, data: Dict[str, Any]):
        """Get all grouping data (groups, tags, etc.)"""
        try:
            # Get all groups
            groups = self.grouping_service.get_all_groups()
            groups_data = [group.to_dict() for group in groups]
            
            # Get all EAs with their tags and groups
            with get_db_session() as session:
                eas = session.query(EA).all()
                eas_data = []
                
                for ea in eas:
                    ea_dict = ea.to_dict(include_tags=True, include_groups=True)
                    eas_data.append(ea_dict)
            
            # Get tag usage stats
            tag_stats = self.grouping_service.get_tag_usage_stats()
            
            response_data = {
                'groups': groups_data,
                'eas': eas_data,
                'tag_stats': tag_stats
            }
            
            await self.websocket_server.send_to_client(
                websocket, 'grouping_data_update', response_data
            )
            
        except Exception as e:
            logger.error(f"Error getting grouping data: {e}")
            await self.websocket_server.send_error(websocket, str(e))
    
    async def handle_get_grouping_stats(self, websocket, data: Dict[str, Any]):
        """Get grouping system statistics"""
        try:
            stats = self.grouping_service.get_grouping_summary()
            
            await self.websocket_server.send_to_client(
                websocket, 'grouping_stats_update', stats
            )
            
        except Exception as e:
            logger.error(f"Error getting grouping stats: {e}")
            await self.websocket_server.send_error(websocket, str(e))
    
    async def handle_create_group(self, websocket, data: Dict[str, Any]):
        """Create a new group"""
        try:
            group_name = data.get('group_name')
            group_type = data.get('group_type', 'custom')
            description = data.get('description')
            
            if not group_name:
                raise ValueError("Group name is required")
            
            group = self.grouping_service.create_group(
                group_name, group_type, description
            )
            
            if group:
                # Broadcast update to all clients
                await self.broadcast_grouping_update()
                
                await self.websocket_server.send_to_client(
                    websocket, 'group_created', {
                        'success': True,
                        'group': group.to_dict()
                    }
                )
            else:
                await self.websocket_server.send_error(
                    websocket, "Failed to create group"
                )
                
        except Exception as e:
            logger.error(f"Error creating group: {e}")
            await self.websocket_server.send_error(websocket, str(e))
    
    async def handle_delete_group(self, websocket, data: Dict[str, Any]):
        """Delete a group"""
        try:
            group_id = data.get('group_id')
            
            if not group_id:
                raise ValueError("Group ID is required")
            
            success = self.grouping_service.delete_group(group_id)
            
            if success:
                # Broadcast update to all clients
                await self.broadcast_grouping_update()
                
                await self.websocket_server.send_to_client(
                    websocket, 'group_deleted', {'success': True}
                )
            else:
                await self.websocket_server.send_error(
                    websocket, "Failed to delete group"
                )
                
        except Exception as e:
            logger.error(f"Error deleting group: {e}")
            await self.websocket_server.send_error(websocket, str(e))
    
    async def handle_add_ea_to_group(self, websocket, data: Dict[str, Any]):
        """Add EA to group"""
        try:
            ea_id = data.get('ea_id')
            group_id = data.get('group_id')
            
            if not ea_id or not group_id:
                raise ValueError("EA ID and Group ID are required")
            
            success = self.grouping_service.add_ea_to_group(ea_id, group_id)
            
            if success:
                # Broadcast update to all clients
                await self.broadcast_grouping_update()
                
                await self.websocket_server.send_to_client(
                    websocket, 'ea_added_to_group', {'success': True}
                )
            else:
                await self.websocket_server.send_error(
                    websocket, "Failed to add EA to group"
                )
                
        except Exception as e:
            logger.error(f"Error adding EA to group: {e}")
            await self.websocket_server.send_error(websocket, str(e))
    
    async def handle_remove_ea_from_group(self, websocket, data: Dict[str, Any]):
        """Remove EA from group"""
        try:
            ea_id = data.get('ea_id')
            group_id = data.get('group_id')
            
            if not ea_id or not group_id:
                raise ValueError("EA ID and Group ID are required")
            
            success = self.grouping_service.remove_ea_from_group(ea_id, group_id)
            
            if success:
                # Broadcast update to all clients
                await self.broadcast_grouping_update()
                
                await self.websocket_server.send_to_client(
                    websocket, 'ea_removed_from_group', {'success': True}
                )
            else:
                await self.websocket_server.send_error(
                    websocket, "Failed to remove EA from group"
                )
                
        except Exception as e:
            logger.error(f"Error removing EA from group: {e}")
            await self.websocket_server.send_error(websocket, str(e))
    
    async def handle_auto_group_by_symbol(self, websocket, data: Dict[str, Any]):
        """Auto-group EAs by symbol"""
        try:
            symbol_groups = self.grouping_service.auto_group_by_symbol()
            
            # Broadcast update to all clients
            await self.broadcast_grouping_update()
            
            await self.websocket_server.send_to_client(
                websocket, 'auto_grouping_complete', {
                    'success': True,
                    'type': 'symbol',
                    'groups_created': len(symbol_groups)
                }
            )
            
        except Exception as e:
            logger.error(f"Error auto-grouping by symbol: {e}")
            await self.websocket_server.send_error(websocket, str(e))
    
    async def handle_auto_group_by_strategy(self, websocket, data: Dict[str, Any]):
        """Auto-group EAs by strategy"""
        try:
            strategy_groups = self.grouping_service.auto_group_by_strategy()
            
            # Broadcast update to all clients
            await self.broadcast_grouping_update()
            
            await self.websocket_server.send_to_client(
                websocket, 'auto_grouping_complete', {
                    'success': True,
                    'type': 'strategy',
                    'groups_created': len(strategy_groups)
                }
            )
            
        except Exception as e:
            logger.error(f"Error auto-grouping by strategy: {e}")
            await self.websocket_server.send_error(websocket, str(e))
    
    async def handle_auto_group_by_risk_level(self, websocket, data: Dict[str, Any]):
        """Auto-group EAs by risk level"""
        try:
            risk_groups = self.grouping_service.auto_group_by_risk_level()
            
            # Broadcast update to all clients
            await self.broadcast_grouping_update()
            
            await self.websocket_server.send_to_client(
                websocket, 'auto_grouping_complete', {
                    'success': True,
                    'type': 'risk_level',
                    'groups_created': len(risk_groups)
                }
            )
            
        except Exception as e:
            logger.error(f"Error auto-grouping by risk level: {e}")
            await self.websocket_server.send_error(websocket, str(e))
    
    async def handle_add_ea_tag(self, websocket, data: Dict[str, Any]):
        """Add tag to EA"""
        try:
            ea_id = data.get('ea_id')
            tag_name = data.get('tag_name')
            tag_value = data.get('tag_value')
            
            if not ea_id or not tag_name:
                raise ValueError("EA ID and tag name are required")
            
            success = self.grouping_service.add_tag(ea_id, tag_name, tag_value)
            
            if success:
                # Broadcast update to all clients
                await self.broadcast_grouping_update()
                
                await self.websocket_server.send_to_client(
                    websocket, 'tag_added', {'success': True}
                )
            else:
                await self.websocket_server.send_error(
                    websocket, "Failed to add tag"
                )
                
        except Exception as e:
            logger.error(f"Error adding tag: {e}")
            await self.websocket_server.send_error(websocket, str(e))
    
    async def handle_remove_ea_tag(self, websocket, data: Dict[str, Any]):
        """Remove tag from EA"""
        try:
            ea_id = data.get('ea_id')
            tag_name = data.get('tag_name')
            
            if not ea_id or not tag_name:
                raise ValueError("EA ID and tag name are required")
            
            success = self.grouping_service.remove_tag(ea_id, tag_name)
            
            if success:
                # Broadcast update to all clients
                await self.broadcast_grouping_update()
                
                await self.websocket_server.send_to_client(
                    websocket, 'tag_removed', {'success': True}
                )
            else:
                await self.websocket_server.send_error(
                    websocket, "Failed to remove tag"
                )
                
        except Exception as e:
            logger.error(f"Error removing tag: {e}")
            await self.websocket_server.send_error(websocket, str(e))
    
    async def handle_get_ea_tags(self, websocket, data: Dict[str, Any]):
        """Get tags for specific EA"""
        try:
            ea_id = data.get('ea_id')
            
            if not ea_id:
                raise ValueError("EA ID is required")
            
            tags = self.grouping_service.get_ea_tags(ea_id)
            
            await self.websocket_server.send_to_client(
                websocket, 'ea_tags', {
                    'ea_id': ea_id,
                    'tags': tags
                }
            )
            
        except Exception as e:
            logger.error(f"Error getting EA tags: {e}")
            await self.websocket_server.send_error(websocket, str(e))
    
    async def handle_execute_command_by_groups(self, websocket, data: Dict[str, Any]):
        """Execute command on EAs in specified groups"""
        try:
            command_type = data.get('command_type')
            group_names = data.get('group_names', [])
            parameters = data.get('parameters', {})
            scheduled_time = data.get('scheduled_time')
            
            if not command_type or not group_names:
                raise ValueError("Command type and group names are required")
            
            # Parse scheduled time if provided
            if scheduled_time:
                scheduled_time = datetime.fromisoformat(scheduled_time)
            
            commands = self.grouping_service.execute_command_by_groups(
                command_type, group_names, parameters, scheduled_time
            )
            
            await self.websocket_server.send_to_client(
                websocket, 'command_execution_result', {
                    'success': True,
                    'affected_eas': len(commands),
                    'command_type': command_type,
                    'execution_method': 'groups'
                }
            )
            
        except Exception as e:
            logger.error(f"Error executing command by groups: {e}")
            await self.websocket_server.send_to_client(
                websocket, 'command_execution_result', {
                    'success': False,
                    'error': str(e)
                }
            )
    
    async def handle_execute_command_by_tags(self, websocket, data: Dict[str, Any]):
        """Execute command on EAs matching tag criteria"""
        try:
            command_type = data.get('command_type')
            tags = data.get('tags', {})
            parameters = data.get('parameters', {})
            scheduled_time = data.get('scheduled_time')
            
            if not command_type or not tags:
                raise ValueError("Command type and tags are required")
            
            # Parse scheduled time if provided
            if scheduled_time:
                scheduled_time = datetime.fromisoformat(scheduled_time)
            
            commands = self.grouping_service.execute_command_by_tags(
                command_type, tags, parameters, scheduled_time
            )
            
            await self.websocket_server.send_to_client(
                websocket, 'command_execution_result', {
                    'success': True,
                    'affected_eas': len(commands),
                    'command_type': command_type,
                    'execution_method': 'tags'
                }
            )
            
        except Exception as e:
            logger.error(f"Error executing command by tags: {e}")
            await self.websocket_server.send_to_client(
                websocket, 'command_execution_result', {
                    'success': False,
                    'error': str(e)
                }
            )
    
    async def handle_execute_command_by_criteria(self, websocket, data: Dict[str, Any]):
        """Execute command on EAs matching multiple criteria"""
        try:
            command_type = data.get('command_type')
            criteria = data.get('criteria', {})
            parameters = data.get('parameters', {})
            scheduled_time = data.get('scheduled_time')
            
            if not command_type:
                raise ValueError("Command type is required")
            
            # Parse scheduled time if provided
            if scheduled_time:
                scheduled_time = datetime.fromisoformat(scheduled_time)
            
            # Find matching EAs
            matching_eas = self.grouping_service.find_eas_by_criteria(
                symbols=criteria.get('symbols'),
                strategy_tags=criteria.get('strategy_tags'),
                risk_levels=criteria.get('risk_levels'),
                statuses=criteria.get('statuses'),
                tags=criteria.get('tags'),
                groups=criteria.get('groups')
            )
            
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
            
            await self.websocket_server.send_to_client(
                websocket, 'command_execution_result', {
                    'success': True,
                    'affected_eas': len(commands),
                    'command_type': command_type,
                    'execution_method': 'criteria'
                }
            )
            
        except Exception as e:
            logger.error(f"Error executing command by criteria: {e}")
            await self.websocket_server.send_to_client(
                websocket, 'command_execution_result', {
                    'success': False,
                    'error': str(e)
                }
            )
    
    async def broadcast_grouping_update(self):
        """Broadcast grouping data update to all connected clients"""
        try:
            # Get updated grouping data
            groups = self.grouping_service.get_all_groups()
            groups_data = [group.to_dict() for group in groups]
            
            # Get updated stats
            stats = self.grouping_service.get_grouping_summary()
            
            # Broadcast to all clients
            await self.websocket_server.broadcast({
                'type': 'grouping_data_update',
                'data': {
                    'groups': groups_data,
                    'stats': stats,
                    'timestamp': datetime.now().isoformat()
                }
            })
            
        except Exception as e:
            logger.error(f"Error broadcasting grouping update: {e}")


async def main():
    """
    Example of running the EA Grouping integration
    """
    try:
        # Initialize WebSocket server
        websocket_server = DashboardWebSocketServer(host='155.138.174.196', port=8765)
        
        # Initialize grouping handler
        grouping_handler = EAGroupingWebSocketHandler(websocket_server)
        
        # Start the server
        logger.info("Starting EA Grouping WebSocket server...")
        await websocket_server.start()
        
        # Keep running
        logger.info("EA Grouping server is running. Press Ctrl+C to stop.")
        await asyncio.Event().wait()
        
    except KeyboardInterrupt:
        logger.info("Shutting down EA Grouping server...")
    except Exception as e:
        logger.error(f"Error in main: {e}")
    finally:
        if 'websocket_server' in locals():
            await websocket_server.stop()


if __name__ == '__main__':
    asyncio.run(main())