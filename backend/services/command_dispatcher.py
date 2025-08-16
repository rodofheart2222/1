"""
Command Dispatcher Service

This module provides the CommandDispatcher class for managing and executing
commands to MT5 Expert Advisors. It handles command queuing, scheduling,
batch operations, acknowledgment tracking, and timeout handling.
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Callable
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from ..database.connection import get_db_session
from ..models.command import Command
from ..models.ea import EA
from .mt5_communication import MT5CommunicationInterface

# Configure logging
logger = logging.getLogger(__name__)


class CommandExecutionResult:
    """Result of command execution"""
    
    def __init__(self, command_id: int, magic_number: int, success: bool, 
                 error_message: Optional[str] = None, execution_time: Optional[datetime] = None):
        self.command_id = command_id
        self.magic_number = magic_number
        self.success = success
        self.error_message = error_message
        self.execution_time = execution_time or datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'command_id': self.command_id,
            'magic_number': self.magic_number,
            'success': self.success,
            'error_message': self.error_message,
            'execution_time': self.execution_time.isoformat() if self.execution_time else None
        }


class CommandFilter:
    """Filter criteria for batch command operations"""
    
    def __init__(self, 
                 symbols: Optional[List[str]] = None,
                 strategy_tags: Optional[List[str]] = None,
                 risk_levels: Optional[List[float]] = None,
                 ea_statuses: Optional[List[str]] = None,
                 magic_numbers: Optional[List[int]] = None):
        self.symbols = symbols or []
        self.strategy_tags = strategy_tags or []
        self.risk_levels = risk_levels or []
        self.ea_statuses = ea_statuses or []
        self.magic_numbers = magic_numbers or []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'symbols': self.symbols,
            'strategy_tags': self.strategy_tags,
            'risk_levels': self.risk_levels,
            'ea_statuses': self.ea_statuses,
            'magic_numbers': self.magic_numbers
        }


class CommandDispatcher:
    """
    Command Dispatcher for managing EA commands
    
    Handles command queuing, scheduling, batch operations, and acknowledgment tracking.
    """
    
    def __init__(self, mt5_interface: MT5CommunicationInterface, 
                 acknowledgment_timeout: int = 300):
        """
        Initialize CommandDispatcher
        
        Args:
            mt5_interface: MT5 communication interface
            acknowledgment_timeout: Timeout in seconds for command acknowledgment
        """
        self.mt5_interface = mt5_interface
        self.acknowledgment_timeout = acknowledgment_timeout
        self.pending_acknowledgments: Dict[int, datetime] = {}  # command_id -> sent_time
        self.execution_callbacks: Dict[str, Callable] = {}  # command_type -> callback
        
        logger.info(f"CommandDispatcher initialized with {acknowledgment_timeout}s acknowledgment timeout")
    
    def register_execution_callback(self, command_type: str, callback: Callable) -> None:
        """
        Register a callback for command execution events
        
        Args:
            command_type: Type of command
            callback: Callback function to execute
        """
        self.execution_callbacks[command_type] = callback
        logger.debug(f"Registered callback for command type: {command_type}")
    
    def create_command(self, 
                      ea_id: Optional[int],
                      command_type: str,
                      parameters: Optional[Dict[str, Any]] = None,
                      scheduled_time: Optional[datetime] = None) -> Optional[Command]:
        """
        Create a new command in the queue
        
        Args:
            ea_id: EA ID (None for global commands)
            command_type: Type of command
            parameters: Command parameters
            scheduled_time: When to execute the command
            
        Returns:
            Created Command object or None if failed
        """
        try:
            with get_db_session() as session:
                command = Command(
                    ea_id=ea_id,
                    command_type=command_type,
                    scheduled_time=scheduled_time or datetime.now()
                )
                
                if parameters:
                    command.set_command_data(parameters)
                
                session.add(command)
                session.commit()
                session.refresh(command)
                
                logger.info(f"Created command {command.id}: {command_type} for EA {ea_id}")
                return command
                
        except Exception as e:
            logger.error(f"Error creating command: {e}")
            return None
    
    def create_batch_commands(self, 
                             filter_criteria: CommandFilter,
                             command_type: str,
                             parameters: Optional[Dict[str, Any]] = None,
                             scheduled_time: Optional[datetime] = None) -> List[Command]:
        """
        Create batch commands for multiple EAs based on filter criteria
        
        Args:
            filter_criteria: Filter to select target EAs
            command_type: Type of command
            parameters: Command parameters
            scheduled_time: When to execute the commands
            
        Returns:
            List of created Command objects
        """
        try:
            with get_db_session() as session:
                # Build query based on filter criteria
                query = session.query(EA)
                
                if filter_criteria.symbols:
                    query = query.filter(EA.symbol.in_(filter_criteria.symbols))
                
                if filter_criteria.strategy_tags:
                    query = query.filter(EA.strategy_tag.in_(filter_criteria.strategy_tags))
                
                if filter_criteria.risk_levels:
                    query = query.filter(EA.risk_config.in_(filter_criteria.risk_levels))
                
                if filter_criteria.ea_statuses:
                    query = query.filter(EA.status.in_(filter_criteria.ea_statuses))
                
                if filter_criteria.magic_numbers:
                    query = query.filter(EA.magic_number.in_(filter_criteria.magic_numbers))
                
                target_eas = query.all()
                
                if not target_eas:
                    logger.warning("No EAs found matching filter criteria")
                    return []
                
                # Create commands for each matching EA
                commands = []
                for ea in target_eas:
                    command = Command(
                        ea_id=ea.id,
                        command_type=command_type,
                        scheduled_time=scheduled_time or datetime.now()
                    )
                    
                    if parameters:
                        command.set_command_data(parameters)
                    
                    session.add(command)
                    commands.append(command)
                
                session.commit()
                
                # Refresh all commands to get IDs
                for command in commands:
                    session.refresh(command)
                
                logger.info(f"Created {len(commands)} batch commands of type {command_type}")
                return commands
                
        except Exception as e:
            logger.error(f"Error creating batch commands: {e}")
            return []
    
    def get_pending_commands(self, limit: Optional[int] = None) -> List[Command]:
        """
        Get pending commands that are due for execution
        
        Args:
            limit: Maximum number of commands to return
            
        Returns:
            List of pending Command objects
        """
        try:
            with get_db_session() as session:
                query = session.query(Command).filter(
                    and_(
                        Command.executed == False,
                        Command.scheduled_time <= datetime.now()
                    )
                ).order_by(Command.scheduled_time)
                
                if limit:
                    query = query.limit(limit)
                
                commands = query.all()
                logger.debug(f"Found {len(commands)} pending commands")
                return commands
                
        except Exception as e:
            logger.error(f"Error getting pending commands: {e}")
            return []
    
    def execute_command(self, command: Command) -> CommandExecutionResult:
        """
        Execute a single command
        
        Args:
            command: Command to execute
            
        Returns:
            CommandExecutionResult object
        """
        try:
            # Get EA magic number if this is an EA-specific command
            magic_number = None
            if command.ea_id:
                with get_db_session() as session:
                    ea = session.query(EA).filter(EA.id == command.ea_id).first()
                    if not ea:
                        error_msg = f"EA with ID {command.ea_id} not found"
                        logger.error(error_msg)
                        return CommandExecutionResult(
                            command.id, 0, False, error_msg
                        )
                    magic_number = ea.magic_number
            
            # Send command via MT5 interface
            command_data = command.get_command_data()
            
            if magic_number:
                # EA-specific command
                success = self.mt5_interface.send_command(
                    magic_number, command.command_type, command_data
                )
            else:
                # Global command - send to all connected EAs
                connected_eas = self.mt5_interface.check_ea_connections()['connected']
                if not connected_eas:
                    error_msg = "No connected EAs found for global command"
                    logger.warning(error_msg)
                    return CommandExecutionResult(
                        command.id, 0, False, error_msg
                    )
                
                results = self.mt5_interface.send_batch_command(
                    connected_eas, command.command_type, command_data
                )
                success = any(results.values())
            
            if success:
                # Mark command as executed
                with get_db_session() as session:
                    db_command = session.query(Command).filter(Command.id == command.id).first()
                    if db_command:
                        db_command.mark_executed()
                        session.commit()
                
                # Track for acknowledgment if needed
                if magic_number:
                    self.pending_acknowledgments[command.id] = datetime.now()
                
                # Execute callback if registered
                if command.command_type in self.execution_callbacks:
                    try:
                        self.execution_callbacks[command.command_type](command, True)
                    except Exception as e:
                        logger.error(f"Error in execution callback: {e}")
                
                logger.info(f"Successfully executed command {command.id}")
                return CommandExecutionResult(command.id, magic_number or 0, True)
            else:
                error_msg = f"Failed to send command {command.id} via MT5 interface"
                logger.error(error_msg)
                return CommandExecutionResult(
                    command.id, magic_number or 0, False, error_msg
                )
                
        except Exception as e:
            error_msg = f"Error executing command {command.id}: {e}"
            logger.error(error_msg)
            return CommandExecutionResult(
                command.id, magic_number or 0, False, error_msg
            )
    
    def execute_pending_commands(self, max_commands: int = 50) -> List[CommandExecutionResult]:
        """
        Execute all pending commands
        
        Args:
            max_commands: Maximum number of commands to execute in one batch
            
        Returns:
            List of CommandExecutionResult objects
        """
        pending_commands = self.get_pending_commands(max_commands)
        results = []
        
        for command in pending_commands:
            result = self.execute_command(command)
            results.append(result)
            
            # Small delay between commands to avoid overwhelming MT5
            if len(pending_commands) > 1:
                import time
                time.sleep(0.1)
        
        successful = sum(1 for r in results if r.success)
        logger.info(f"Executed {len(results)} commands, {successful} successful")
        
        return results
    
    def cancel_command(self, command_id: int) -> bool:
        """
        Cancel a pending command
        
        Args:
            command_id: ID of command to cancel
            
        Returns:
            True if successfully cancelled
        """
        try:
            with get_db_session() as session:
                command = session.query(Command).filter(
                    and_(
                        Command.id == command_id,
                        Command.executed == False
                    )
                ).first()
                
                if not command:
                    logger.warning(f"Command {command_id} not found or already executed")
                    return False
                
                session.delete(command)
                session.commit()
                
                # Remove from pending acknowledgments if present
                if command_id in self.pending_acknowledgments:
                    del self.pending_acknowledgments[command_id]
                
                logger.info(f"Cancelled command {command_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error cancelling command {command_id}: {e}")
            return False
    
    def acknowledge_command(self, command_id: int, magic_number: int) -> bool:
        """
        Acknowledge command execution by EA
        
        Args:
            command_id: ID of acknowledged command
            magic_number: Magic number of EA that acknowledged
            
        Returns:
            True if acknowledgment was processed
        """
        try:
            if command_id in self.pending_acknowledgments:
                del self.pending_acknowledgments[command_id]
                logger.info(f"Command {command_id} acknowledged by EA {magic_number}")
                
                # Execute acknowledgment callback if registered
                callback_key = f"acknowledge_{command_id}"
                if callback_key in self.execution_callbacks:
                    try:
                        self.execution_callbacks[callback_key](command_id, magic_number)
                        del self.execution_callbacks[callback_key]
                    except Exception as e:
                        logger.error(f"Error in acknowledgment callback: {e}")
                
                return True
            else:
                logger.warning(f"No pending acknowledgment found for command {command_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error processing acknowledgment for command {command_id}: {e}")
            return False
    
    def check_acknowledgment_timeouts(self) -> List[int]:
        """
        Check for commands that have timed out waiting for acknowledgment
        
        Returns:
            List of timed out command IDs
        """
        current_time = datetime.now()
        timeout_threshold = timedelta(seconds=self.acknowledgment_timeout)
        timed_out_commands = []
        
        for command_id, sent_time in list(self.pending_acknowledgments.items()):
            if current_time - sent_time > timeout_threshold:
                timed_out_commands.append(command_id)
                del self.pending_acknowledgments[command_id]
                logger.warning(f"Command {command_id} acknowledgment timed out")
        
        return timed_out_commands
    
    def get_command_queue_status(self) -> Dict[str, Any]:
        """
        Get status of command queue
        
        Returns:
            Dictionary with queue status information
        """
        try:
            with get_db_session() as session:
                total_commands = session.query(Command).count()
                pending_commands = session.query(Command).filter(Command.executed == False).count()
                executed_commands = session.query(Command).filter(Command.executed == True).count()
                
                # Get commands by type - simplified query
                command_types_query = session.query(Command.command_type).distinct().all()
                command_types = {}
                for (cmd_type,) in command_types_query:
                    count = session.query(Command).filter(Command.command_type == cmd_type).count()
                    command_types[cmd_type] = count
                
                status = {
                    'total_commands': total_commands,
                    'pending_commands': pending_commands,
                    'executed_commands': executed_commands,
                    'pending_acknowledgments': len(self.pending_acknowledgments),
                    'command_types': command_types,
                    'acknowledgment_timeout': self.acknowledgment_timeout,
                    'last_check': datetime.now().isoformat()
                }
                
                return status
                
        except Exception as e:
            logger.error(f"Error getting command queue status: {e}")
            return {
                'total_commands': 0,
                'pending_commands': 0,
                'executed_commands': 0,
                'pending_acknowledgments': len(self.pending_acknowledgments),
                'command_types': {},
                'acknowledgment_timeout': self.acknowledgment_timeout,
                'last_check': datetime.now().isoformat()
            }
    
    def cleanup_old_commands(self, days: int = 7) -> int:
        """
        Clean up old executed commands
        
        Args:
            days: Age threshold in days
            
        Returns:
            Number of commands cleaned up
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            with get_db_session() as session:
                old_commands = session.query(Command).filter(
                    and_(
                        Command.executed == True,
                        Command.created_at < cutoff_date
                    )
                ).all()
                
                count = len(old_commands)
                
                for command in old_commands:
                    session.delete(command)
                
                session.commit()
                
                logger.info(f"Cleaned up {count} old commands")
                return count
                
        except Exception as e:
            logger.error(f"Error cleaning up old commands: {e}")
            return 0
    
    # Convenience methods for common command types
    
    def pause_ea(self, ea_id: int, scheduled_time: Optional[datetime] = None) -> Optional[Command]:
        """Create pause command for specific EA"""
        return self.create_command(ea_id, 'pause', scheduled_time=scheduled_time)
    
    def resume_ea(self, ea_id: int, scheduled_time: Optional[datetime] = None) -> Optional[Command]:
        """Create resume command for specific EA"""
        return self.create_command(ea_id, 'resume', scheduled_time=scheduled_time)
    
    def adjust_ea_risk(self, ea_id: int, new_risk: float, scheduled_time: Optional[datetime] = None) -> Optional[Command]:
        """Create risk adjustment command for specific EA"""
        return self.create_command(
            ea_id, 'adjust_risk', 
            parameters={'new_risk_level': new_risk},
            scheduled_time=scheduled_time
        )
    
    def close_ea_positions(self, ea_id: int, scheduled_time: Optional[datetime] = None) -> Optional[Command]:
        """Create close positions command for specific EA"""
        return self.create_command(ea_id, 'close_positions', scheduled_time=scheduled_time)
    
    def pause_strategy(self, strategy_tag: str, scheduled_time: Optional[datetime] = None) -> List[Command]:
        """Create pause commands for all EAs with specific strategy tag"""
        filter_criteria = CommandFilter(strategy_tags=[strategy_tag])
        return self.create_batch_commands(filter_criteria, 'pause', scheduled_time=scheduled_time)
    
    def resume_strategy(self, strategy_tag: str, scheduled_time: Optional[datetime] = None) -> List[Command]:
        """Create resume commands for all EAs with specific strategy tag"""
        filter_criteria = CommandFilter(strategy_tags=[strategy_tag])
        return self.create_batch_commands(filter_criteria, 'resume', scheduled_time=scheduled_time)
    
    def adjust_strategy_risk(self, strategy_tag: str, new_risk: float, scheduled_time: Optional[datetime] = None) -> List[Command]:
        """Create risk adjustment commands for all EAs with specific strategy tag"""
        filter_criteria = CommandFilter(strategy_tags=[strategy_tag])
        return self.create_batch_commands(
            filter_criteria, 'adjust_risk',
            parameters={'new_risk_level': new_risk},
            scheduled_time=scheduled_time
        )
    
    def pause_symbol(self, symbol: str, scheduled_time: Optional[datetime] = None) -> List[Command]:
        """Create pause commands for all EAs trading specific symbol"""
        filter_criteria = CommandFilter(symbols=[symbol])
        return self.create_batch_commands(filter_criteria, 'pause', scheduled_time=scheduled_time)
    
    def resume_symbol(self, symbol: str, scheduled_time: Optional[datetime] = None) -> List[Command]:
        """Create resume commands for all EAs trading specific symbol"""
        filter_criteria = CommandFilter(symbols=[symbol])
        return self.create_batch_commands(filter_criteria, 'resume', scheduled_time=scheduled_time)
    
    def emergency_stop_all(self) -> List[Command]:
        """Create emergency stop commands for all active EAs"""
        filter_criteria = CommandFilter(ea_statuses=['active'])
        return self.create_batch_commands(filter_criteria, 'pause')
    
    def close_all_positions(self) -> List[Command]:
        """Create close positions commands for all active EAs"""
        filter_criteria = CommandFilter(ea_statuses=['active'])
        return self.create_batch_commands(filter_criteria, 'close_positions')


class ScheduledCommandExecutor:
    """
    Scheduled command executor that runs in background
    """
    
    def __init__(self, command_dispatcher: CommandDispatcher, 
                 execution_interval: int = 30):
        """
        Initialize scheduled executor
        
        Args:
            command_dispatcher: CommandDispatcher instance
            execution_interval: Interval in seconds between execution cycles
        """
        self.command_dispatcher = command_dispatcher
        self.execution_interval = execution_interval
        self.running = False
        self.task = None
        
        logger.info(f"ScheduledCommandExecutor initialized with {execution_interval}s interval")
    
    async def start(self) -> None:
        """Start the scheduled executor"""
        if self.running:
            logger.warning("ScheduledCommandExecutor is already running")
            return
        
        self.running = True
        self.task = asyncio.create_task(self._execution_loop())
        logger.info("ScheduledCommandExecutor started")
    
    async def stop(self) -> None:
        """Stop the scheduled executor"""
        if not self.running:
            return
        
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        
        logger.info("ScheduledCommandExecutor stopped")
    
    async def _execution_loop(self) -> None:
        """Main execution loop"""
        while self.running:
            try:
                # Execute pending commands
                results = self.command_dispatcher.execute_pending_commands()
                
                # Check for acknowledgment timeouts
                timed_out = self.command_dispatcher.check_acknowledgment_timeouts()
                if timed_out:
                    logger.warning(f"Found {len(timed_out)} timed out commands: {timed_out}")
                
                # Log execution summary if there were commands
                if results:
                    successful = sum(1 for r in results if r.success)
                    logger.debug(f"Execution cycle: {successful}/{len(results)} commands successful")
                
                # Wait for next cycle
                await asyncio.sleep(self.execution_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in execution loop: {e}")
                await asyncio.sleep(self.execution_interval)