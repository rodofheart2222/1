"""
EA Data Collection Service Integration

This module provides a high-level interface for integrating the EA data collection
service into the main application.
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from .ea_data_collector import EADataCollector, PortfolioAggregator
from .mt5_communication import MT5CommunicationInterface
from ..database.connection import test_database_connection
from ..database.init_db import init_database

logger = logging.getLogger(__name__)


class EADataService:
    """
    High-level service for EA data collection and management
    """
    
    def __init__(self, 
                 collection_interval: int = 30,
                 heartbeat_timeout: int = 90,
                 auto_start: bool = False):
        """
        Initialize EA data service
        
        Args:
            collection_interval: Data collection interval in seconds
            heartbeat_timeout: EA heartbeat timeout in seconds
            auto_start: Whether to automatically start collection
        """
        self.collection_interval = collection_interval
        self.heartbeat_timeout = heartbeat_timeout
        
        # Initialize components
        self.mt5_interface = MT5CommunicationInterface(
            heartbeat_timeout=heartbeat_timeout
        )
        self.data_collector = EADataCollector(
            mt5_interface=self.mt5_interface,
            collection_interval=collection_interval
        )
        self.portfolio_aggregator = PortfolioAggregator()
        
        self.is_initialized = False
        self.collection_task = None
        
        logger.info(f"EADataService initialized with {collection_interval}s interval")
        
        if auto_start:
            asyncio.create_task(self.initialize_and_start())
    
    async def initialize(self) -> bool:
        """
        Initialize the service and database
        
        Returns:
            True if initialization successful
        """
        try:
            logger.info("Initializing EA Data Service...")
            
            # Test database connection
            if not test_database_connection():
                logger.error("Database connection failed")
                return False
            
            # Initialize database tables if needed
            try:
                init_database()
                logger.info("Database initialized successfully")
            except Exception as e:
                logger.warning(f"Database initialization warning: {e}")
            
            # Test MT5 communication
            system_status = self.mt5_interface.get_system_status()
            logger.info(f"MT5 communication status: {system_status['communication_mode']}")
            
            self.is_initialized = True
            logger.info("EA Data Service initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Service initialization failed: {e}")
            return False
    
    async def start_collection(self) -> bool:
        """
        Start continuous data collection
        
        Returns:
            True if collection started successfully
        """
        if not self.is_initialized:
            logger.warning("Service not initialized, initializing now...")
            if not await self.initialize():
                return False
        
        if self.collection_task and not self.collection_task.done():
            logger.warning("Data collection already running")
            return True
        
        try:
            logger.info("Starting EA data collection...")
            self.collection_task = asyncio.create_task(
                self.data_collector.start_collection()
            )
            
            # Wait a moment to ensure it starts properly
            await asyncio.sleep(1)
            
            if self.data_collector.is_running:
                logger.info("EA data collection started successfully")
                return True
            else:
                logger.error("Failed to start data collection")
                return False
                
        except Exception as e:
            logger.error(f"Error starting data collection: {e}")
            return False
    
    async def stop_collection(self) -> bool:
        """
        Stop continuous data collection
        
        Returns:
            True if collection stopped successfully
        """
        try:
            logger.info("Stopping EA data collection...")
            
            if self.data_collector.is_running:
                self.data_collector.stop_collection()
            
            if self.collection_task and not self.collection_task.done():
                self.collection_task.cancel()
                try:
                    await self.collection_task
                except asyncio.CancelledError:
                    pass
            
            logger.info("EA data collection stopped")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping data collection: {e}")
            return False
    
    async def collect_data_once(self) -> Dict[str, Any]:
        """
        Perform a single data collection cycle
        
        Returns:
            Collection result dictionary
        """
        if not self.is_initialized:
            if not await self.initialize():
                return {'status': 'error', 'error': 'Service not initialized'}
        
        try:
            result = await self.data_collector.collect_and_process_data()
            logger.info(f"Single collection completed: {result['status']}")
            return result
        except Exception as e:
            logger.error(f"Single collection failed: {e}")
            return {'status': 'error', 'error': str(e)}
    
    async def get_portfolio_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive portfolio summary
        
        Returns:
            Portfolio summary dictionary
        """
        try:
            # Get overall portfolio metrics
            portfolio_metrics = await self.portfolio_aggregator.calculate_portfolio_metrics()
            
            # Get performance breakdown
            breakdown = await self.portfolio_aggregator.get_performance_breakdown()
            
            # Get EA connection status
            connection_status = self.mt5_interface.check_ea_connections()
            
            # Get collection statistics
            collection_stats = self.data_collector.get_collection_stats()
            
            summary = {
                'portfolio_metrics': {
                    'total_profit': portfolio_metrics.total_profit,
                    'profit_factor': portfolio_metrics.profit_factor,
                    'win_rate': portfolio_metrics.win_rate,
                    'total_drawdown': portfolio_metrics.total_drawdown,
                    'expected_payoff': portfolio_metrics.expected_payoff,
                    'total_trades': portfolio_metrics.total_trades,
                    'active_eas': portfolio_metrics.active_eas,
                    'total_eas': portfolio_metrics.total_eas,
                    'symbols': portfolio_metrics.symbols,
                    'strategies': portfolio_metrics.strategies,
                    'last_updated': portfolio_metrics.last_updated.isoformat()
                },
                'performance_breakdown': breakdown,
                'connection_status': connection_status,
                'collection_stats': collection_stats,
                'service_status': {
                    'is_initialized': self.is_initialized,
                    'is_collecting': self.data_collector.is_running,
                    'collection_interval': self.collection_interval,
                    'heartbeat_timeout': self.heartbeat_timeout
                },
                'timestamp': datetime.now().isoformat()
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting portfolio summary: {e}")
            return {'error': str(e), 'timestamp': datetime.now().isoformat()}
    
    async def get_ea_details(self, magic_number: int = None) -> Dict[str, Any]:
        """
        Get detailed information about specific EA or all EAs
        
        Args:
            magic_number: Optional EA magic number filter
            
        Returns:
            EA details dictionary
        """
        try:
            # Get EA performance metrics
            ea_metrics = await self.portfolio_aggregator.get_ea_performance_metrics(magic_number)
            
            # Get connection status for specific EA if requested
            connection_info = None
            if magic_number:
                connection_info = {
                    'status': self.mt5_interface.heartbeat_monitor.get_ea_status(magic_number),
                    'last_seen': self.mt5_interface.heartbeat_monitor.known_eas.get(magic_number)
                }
            
            return {
                'ea_metrics': [
                    {
                        'magic_number': metrics.magic_number,
                        'total_profit': metrics.total_profit,
                        'profit_factor': metrics.profit_factor,
                        'expected_payoff': metrics.expected_payoff,
                        'drawdown': metrics.drawdown,
                        'z_score': metrics.z_score,
                        'win_rate': metrics.win_rate,
                        'trade_count': metrics.trade_count,
                        'last_calculated': metrics.last_calculated.isoformat()
                    }
                    for metrics in ea_metrics
                ],
                'connection_info': connection_info,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting EA details: {e}")
            return {'error': str(e), 'timestamp': datetime.now().isoformat()}
    
    async def send_ea_command(self, magic_number: int, command_type: str, parameters: Dict[str, Any] = None) -> bool:
        """
        Send command to specific EA
        
        Args:
            magic_number: EA magic number
            command_type: Command type (pause, resume, adjust_risk, etc.)
            parameters: Optional command parameters
            
        Returns:
            True if command sent successfully
        """
        try:
            success = self.mt5_interface.send_command(magic_number, command_type, parameters)
            
            if success:
                logger.info(f"Command '{command_type}' sent to EA {magic_number}")
            else:
                logger.error(f"Failed to send command '{command_type}' to EA {magic_number}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending command to EA {magic_number}: {e}")
            return False
    
    async def send_batch_command(self, magic_numbers: list, command_type: str, parameters: Dict[str, Any] = None) -> Dict[int, bool]:
        """
        Send command to multiple EAs
        
        Args:
            magic_numbers: List of EA magic numbers
            command_type: Command type
            parameters: Optional command parameters
            
        Returns:
            Dictionary mapping magic_number to success status
        """
        try:
            results = self.mt5_interface.send_batch_command(magic_numbers, command_type, parameters)
            
            successful = sum(1 for success in results.values() if success)
            logger.info(f"Batch command '{command_type}': {successful}/{len(magic_numbers)} successful")
            
            return results
            
        except Exception as e:
            logger.error(f"Error sending batch command: {e}")
            return {mn: False for mn in magic_numbers}
    
    async def get_system_health(self) -> Dict[str, Any]:
        """
        Get comprehensive system health information
        
        Returns:
            System health dictionary
        """
        try:
            # Get MT5 system status
            mt5_status = self.mt5_interface.get_system_status()
            
            # Get collection statistics
            collection_stats = self.data_collector.get_collection_stats()
            
            # Get database connection status
            db_status = test_database_connection()
            
            # Get EA connection summary
            connection_status = self.mt5_interface.check_ea_connections()
            
            health = {
                'overall_status': 'healthy' if (
                    db_status and 
                    self.is_initialized and 
                    len(connection_status.get('connected', [])) > 0
                ) else 'degraded',
                'database_status': 'connected' if db_status else 'disconnected',
                'service_initialized': self.is_initialized,
                'collection_running': self.data_collector.is_running,
                'mt5_communication': mt5_status,
                'ea_connections': {
                    'connected_count': len(connection_status.get('connected', [])),
                    'disconnected_count': len(connection_status.get('disconnected', [])),
                    'connected_eas': connection_status.get('connected', []),
                    'disconnected_eas': connection_status.get('disconnected', [])
                },
                'collection_performance': {
                    'success_rate': collection_stats.get('success_rate', 0),
                    'total_collections': collection_stats.get('total_collections', 0),
                    'validation_errors': collection_stats.get('validation_errors', 0),
                    'last_collection': collection_stats.get('last_collection_time')
                },
                'timestamp': datetime.now().isoformat()
            }
            
            return health
            
        except Exception as e:
            logger.error(f"Error getting system health: {e}")
            return {
                'overall_status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def initialize_and_start(self):
        """Initialize service and start collection (convenience method)"""
        if await self.initialize():
            await self.start_collection()
    
    async def cleanup(self):
        """Clean up resources"""
        try:
            await self.stop_collection()
            
            # Clean up old data
            cleanup_stats = self.mt5_interface.cleanup_old_data(hours=24)
            logger.info(f"Cleanup completed: {cleanup_stats}")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


# Global service instance
ea_service = EADataService()


# Convenience functions for easy integration
async def initialize_ea_service(collection_interval: int = 30, heartbeat_timeout: int = 90) -> bool:
    """Initialize the global EA service"""
    global ea_service
    ea_service = EADataService(collection_interval, heartbeat_timeout)
    return await ea_service.initialize()


async def start_ea_collection() -> bool:
    """Start EA data collection"""
    return await ea_service.start_collection()


async def stop_ea_collection() -> bool:
    """Stop EA data collection"""
    return await ea_service.stop_collection()


async def get_portfolio_summary() -> Dict[str, Any]:
    """Get portfolio summary"""
    return await ea_service.get_portfolio_summary()


async def get_system_health() -> Dict[str, Any]:
    """Get system health"""
    return await ea_service.get_system_health()


async def send_ea_command(magic_number: int, command_type: str, parameters: Dict[str, Any] = None) -> bool:
    """Send command to EA"""
    return await ea_service.send_ea_command(magic_number, command_type, parameters)