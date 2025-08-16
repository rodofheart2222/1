"""
Command Dispatcher Integration Example

This module demonstrates how the CommandDispatcher integrates with
other services in the MT5 COC Dashboard system.
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any

from .command_dispatcher import CommandDispatcher, CommandFilter, ScheduledCommandExecutor
from .mt5_communication import MT5CommunicationInterface
from .ea_data_collector import EADataCollector
from ..models.ea import EA
from ..models.command import Command
from ..database.connection import get_db_session


class IntegratedCommandManager:
    """
    Integrated command manager that combines CommandDispatcher
    with EA data collection and monitoring
    """
    
    def __init__(self):
        """Initialize the integrated command manager"""
        self.mt5_interface = MT5CommunicationInterface()
        self.command_dispatcher = CommandDispatcher(self.mt5_interface)
        self.ea_collector = EADataCollector(self.mt5_interface)
        self.scheduled_executor = ScheduledCommandExecutor(self.command_dispatcher)
        
        # Register command callbacks
        self._register_callbacks()
        
        print("Integrated Command Manager initialized")
    
    def _register_callbacks(self):
        """Register callbacks for command execution events"""
        
        def on_pause_executed(command, success):
            if success:
                print(f" EA {command.ea_id} paused successfully")
                # Update EA status in database
                self._update_ea_status(command.ea_id, 'paused')
            else:
                print(f" Failed to pause EA {command.ea_id}")
        
        def on_resume_executed(command, success):
            if success:
                print(f" EA {command.ea_id} resumed successfully")
                # Update EA status in database
                self._update_ea_status(command.ea_id, 'active')
            else:
                print(f" Failed to resume EA {command.ea_id}")
        
        def on_risk_adjusted(command, success):
            if success:
                data = command.get_command_data()
                new_risk = data.get('new_risk_level', 'unknown')
                print(f" EA {command.ea_id} risk adjusted to {new_risk}")
                # Update EA risk config in database
                self._update_ea_risk(command.ea_id, new_risk)
            else:
                print(f" Failed to adjust risk for EA {command.ea_id}")
        
        # Register callbacks
        self.command_dispatcher.register_execution_callback('pause', on_pause_executed)
        self.command_dispatcher.register_execution_callback('resume', on_resume_executed)
        self.command_dispatcher.register_execution_callback('adjust_risk', on_risk_adjusted)
    
    def _update_ea_status(self, ea_id: int, status: str):
        """Update EA status in database"""
        try:
            with get_db_session() as session:
                ea = session.query(EA).filter(EA.id == ea_id).first()
                if ea:
                    ea.status = status
                    session.commit()
                    print(f"  Database updated: EA {ea_id} status -> {status}")
        except Exception as e:
            print(f"  Error updating EA status: {e}")
    
    def _update_ea_risk(self, ea_id: int, risk_level: float):
        """Update EA risk configuration in database"""
        try:
            with get_db_session() as session:
                ea = session.query(EA).filter(EA.id == ea_id).first()
                if ea:
                    ea.risk_config = risk_level
                    session.commit()
                    print(f"  Database updated: EA {ea_id} risk -> {risk_level}")
        except Exception as e:
            print(f"  Error updating EA risk: {e}")
    
    async def start_monitoring(self):
        """Start the integrated monitoring system"""
        print("Starting integrated monitoring system...")
        
        # Start scheduled command executor
        await self.scheduled_executor.start()
        print(" Scheduled command executor started")
        
        # Start EA data collection loop
        asyncio.create_task(self._ea_monitoring_loop())
        print(" EA monitoring loop started")
        
        print("Integrated monitoring system is running")
    
    async def stop_monitoring(self):
        """Stop the integrated monitoring system"""
        print("Stopping integrated monitoring system...")
        
        # Stop scheduled command executor
        await self.scheduled_executor.stop()
        print(" Scheduled command executor stopped")
        
        print("Integrated monitoring system stopped")
    
    async def _ea_monitoring_loop(self):
        """Main EA monitoring loop"""
        while True:
            try:
                # Collect EA data
                ea_reports = self.ea_collector.collect_all_ea_data()
                
                if ea_reports:
                    print(f"Collected data from {len(ea_reports)} EAs")
                    
                    # Check for disconnected EAs
                    await self._check_disconnected_eas(ea_reports)
                    
                    # Check for performance issues
                    await self._check_performance_issues(ea_reports)
                    
                    # Check for risk violations
                    await self._check_risk_violations(ea_reports)
                
                # Wait before next collection
                await asyncio.sleep(30)  # Collect every 30 seconds
                
            except Exception as e:
                print(f"Error in EA monitoring loop: {e}")
                await asyncio.sleep(30)
    
    async def _check_disconnected_eas(self, ea_reports: Dict[int, Any]):
        """Check for disconnected EAs and take action"""
        connection_status = self.mt5_interface.check_ea_connections()
        disconnected = connection_status.get('disconnected', [])
        
        if disconnected:
            print(f" Found {len(disconnected)} disconnected EAs: {disconnected}")
            
            # Mark disconnected EAs as error status
            for magic_number in disconnected:
                try:
                    with get_db_session() as session:
                        ea = session.query(EA).filter(EA.magic_number == magic_number).first()
                        if ea and ea.status != 'error':
                            ea.status = 'error'
                            ea.last_seen = datetime.now()
                            session.commit()
                            print(f"  Marked EA {magic_number} as disconnected")
                except Exception as e:
                    print(f"  Error updating disconnected EA {magic_number}: {e}")
    
    async def _check_performance_issues(self, ea_reports: Dict[int, Any]):
        """Check for EA performance issues and take action"""
        for magic_number, report in ea_reports.items():
            try:
                metrics = report.performance_metrics
                
                # Check for high drawdown
                if metrics.get('drawdown', 0) > 15.0:  # 15% drawdown threshold
                    print(f" High drawdown detected for EA {magic_number}: {metrics['drawdown']}%")
                    
                    # Create pause command
                    with get_db_session() as session:
                        ea = session.query(EA).filter(EA.magic_number == magic_number).first()
                        if ea:
                            command = self.command_dispatcher.create_command(
                                ea.id, 'pause',
                                parameters={'reason': f'High drawdown: {metrics["drawdown"]}%'}
                            )
                            if command:
                                print(f"  Created pause command {command.id} for high drawdown EA")
                
                # Check for low profit factor
                if metrics.get('profit_factor', 0) < 1.1:  # Below 1.1 PF threshold
                    print(f" Low profit factor for EA {magic_number}: {metrics['profit_factor']}")
                    
                    # Create risk reduction command
                    with get_db_session() as session:
                        ea = session.query(EA).filter(EA.magic_number == magic_number).first()
                        if ea and ea.risk_config > 0.5:
                            new_risk = ea.risk_config * 0.8  # Reduce risk by 20%
                            command = self.command_dispatcher.create_command(
                                ea.id, 'adjust_risk',
                                parameters={
                                    'new_risk_level': new_risk,
                                    'reason': f'Low profit factor: {metrics["profit_factor"]}'
                                }
                            )
                            if command:
                                print(f"  Created risk reduction command {command.id}")
                
            except Exception as e:
                print(f"Error checking performance for EA {magic_number}: {e}")
    
    async def _check_risk_violations(self, ea_reports: Dict[int, Any]):
        """Check for risk violations and take action"""
        total_exposure = 0
        high_risk_eas = []
        
        for magic_number, report in ea_reports.items():
            try:
                # Calculate exposure (simplified)
                exposure = report.open_positions * report.current_profit
                total_exposure += abs(exposure)
                
                # Check individual EA risk
                if abs(exposure) > 1000:  # $1000 exposure threshold
                    high_risk_eas.append((magic_number, exposure))
                
            except Exception as e:
                print(f"Error calculating risk for EA {magic_number}: {e}")
        
        # Check total portfolio exposure
        if total_exposure > 5000:  # $5000 total exposure threshold
            print(f" High portfolio exposure: ${total_exposure:.2f}")
            
            # Create emergency stop for all active EAs
            commands = self.command_dispatcher.emergency_stop_all()
            print(f"  Created {len(commands)} emergency stop commands")
        
        # Handle individual high-risk EAs
        for magic_number, exposure in high_risk_eas:
            print(f" High exposure EA {magic_number}: ${exposure:.2f}")
            
            with get_db_session() as session:
                ea = session.query(EA).filter(EA.magic_number == magic_number).first()
                if ea:
                    # Close positions command
                    command = self.command_dispatcher.create_command(
                        ea.id, 'close_positions',
                        parameters={'reason': f'High exposure: ${exposure:.2f}'}
                    )
                    if command:
                        print(f"  Created close positions command {command.id}")
    
    def create_strategy_commands(self, strategy_tag: str, action: str, **kwargs):
        """Create commands for all EAs with specific strategy"""
        print(f"Creating {action} commands for strategy: {strategy_tag}")
        
        if action == 'pause':
            commands = self.command_dispatcher.pause_strategy(strategy_tag)
        elif action == 'resume':
            commands = self.command_dispatcher.resume_strategy(strategy_tag)
        elif action == 'adjust_risk':
            new_risk = kwargs.get('new_risk', 1.0)
            commands = self.command_dispatcher.adjust_strategy_risk(strategy_tag, new_risk)
        else:
            print(f"Unknown action: {action}")
            return []
        
        print(f"Created {len(commands)} {action} commands for {strategy_tag}")
        return commands
    
    def create_symbol_commands(self, symbol: str, action: str, **kwargs):
        """Create commands for all EAs trading specific symbol"""
        print(f"Creating {action} commands for symbol: {symbol}")
        
        if action == 'pause':
            commands = self.command_dispatcher.pause_symbol(symbol)
        elif action == 'resume':
            commands = self.command_dispatcher.resume_symbol(symbol)
        else:
            print(f"Unknown action: {action}")
            return []
        
        print(f"Created {len(commands)} {action} commands for {symbol}")
        return commands
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        # Get command queue status
        command_status = self.command_dispatcher.get_command_queue_status()
        
        # Get MT5 communication status
        mt5_status = self.mt5_interface.get_system_status()
        
        # Get EA connection status
        connection_status = self.mt5_interface.check_ea_connections()
        
        return {
            'timestamp': datetime.now().isoformat(),
            'command_queue': command_status,
            'mt5_communication': mt5_status,
            'ea_connections': connection_status,
            'monitoring_active': self.scheduled_executor.running
        }


async def integration_example():
    """Example of using the integrated command manager"""
    
    print("=== Integrated Command Manager Example ===\n")
    
    # Initialize integrated manager
    manager = IntegratedCommandManager()
    
    # Start monitoring
    await manager.start_monitoring()
    
    try:
        # Let the system run for a short time
        print("System running for 10 seconds...")
        await asyncio.sleep(10)
        
        # Create some example commands
        print("\nCreating example commands:")
        
        # Pause all Compression strategy EAs
        compression_commands = manager.create_strategy_commands('Compression_v1', 'pause')
        
        # Reduce risk for all EURUSD EAs
        eurusd_filter = CommandFilter(symbols=['EURUSD'])
        eurusd_commands = manager.command_dispatcher.create_batch_commands(
            eurusd_filter, 'adjust_risk',
            parameters={'new_risk_level': 0.8, 'reason': 'Market volatility'}
        )
        print(f"Created {len(eurusd_commands)} risk adjustment commands for EURUSD")
        
        # Get system status
        print("\nSystem Status:")
        status = manager.get_system_status()
        print(f"  Command queue: {status['command_queue']['pending_commands']} pending")
        print(f"  Connected EAs: {len(status['ea_connections']['connected'])}")
        print(f"  Monitoring active: {status['monitoring_active']}")
        
        # Let commands execute
        print("\nWaiting for command execution...")
        await asyncio.sleep(5)
        
    finally:
        # Stop monitoring
        await manager.stop_monitoring()
    
    print("\n=== Integration example completed ===")


if __name__ == '__main__':
    """Run integration example when script is executed directly"""
    
    try:
        asyncio.run(integration_example())
    except KeyboardInterrupt:
        print("\nIntegration example interrupted by user")
    except Exception as e:
        print(f"\nError running integration example: {e}")