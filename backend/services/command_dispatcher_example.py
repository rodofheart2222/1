"""
Command Dispatcher Usage Examples

This module demonstrates how to use the CommandDispatcher service
for managing EA commands in the MT5 COC Dashboard system.
"""

import asyncio
from datetime import datetime, timedelta
from .command_dispatcher import CommandDispatcher, CommandFilter, ScheduledCommandExecutor
from .mt5_communication import MT5CommunicationInterface


async def main():
    """Main example function demonstrating CommandDispatcher usage"""
    
    # Initialize MT5 communication interface
    mt5_interface = MT5CommunicationInterface()
    
    # Initialize command dispatcher with 5-minute acknowledgment timeout
    dispatcher = CommandDispatcher(mt5_interface, acknowledgment_timeout=300)
    
    print("=== Command Dispatcher Examples ===\n")
    
    # Example 1: Create individual EA commands
    print("1. Creating individual EA commands:")
    
    # Pause a specific EA
    pause_command = dispatcher.pause_ea(ea_id=1)
    if pause_command:
        print(f"   Created pause command {pause_command.id} for EA 1")
    
    # Resume a specific EA with scheduled execution
    scheduled_time = datetime.now() + timedelta(minutes=5)
    resume_command = dispatcher.resume_ea(ea_id=1, scheduled_time=scheduled_time)
    if resume_command:
        print(f"   Created scheduled resume command {resume_command.id} for EA 1")
    
    # Adjust risk for a specific EA
    risk_command = dispatcher.adjust_ea_risk(ea_id=2, new_risk=1.5)
    if risk_command:
        print(f"   Created risk adjustment command {risk_command.id} for EA 2")
    
    print()
    
    # Example 2: Create batch commands using filters
    print("2. Creating batch commands with filters:")
    
    # Pause all EAs trading EURUSD
    eurusd_filter = CommandFilter(symbols=['EURUSD'])
    eurusd_commands = dispatcher.create_batch_commands(
        eurusd_filter, 'pause', 
        parameters={'reason': 'High volatility expected'}
    )
    print(f"   Created {len(eurusd_commands)} pause commands for EURUSD EAs")
    
    # Adjust risk for all EAs with specific strategy
    strategy_filter = CommandFilter(strategy_tags=['Compression_v1'])
    strategy_commands = dispatcher.create_batch_commands(
        strategy_filter, 'adjust_risk',
        parameters={'new_risk_level': 0.8, 'reason': 'Risk reduction'}
    )
    print(f"   Created {len(strategy_commands)} risk adjustment commands for Compression_v1 strategy")
    
    # Resume all active EAs at market open
    market_open = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)
    if market_open < datetime.now():
        market_open += timedelta(days=1)
    
    active_filter = CommandFilter(ea_statuses=['active'])
    resume_commands = dispatcher.create_batch_commands(
        active_filter, 'resume',
        scheduled_time=market_open
    )
    print(f"   Created {len(resume_commands)} scheduled resume commands for market open")
    
    print()
    
    # Example 3: Execute pending commands
    print("3. Executing pending commands:")
    
    pending_commands = dispatcher.get_pending_commands(limit=5)
    print(f"   Found {len(pending_commands)} pending commands")
    
    if pending_commands:
        results = dispatcher.execute_pending_commands(max_commands=5)
        successful = sum(1 for r in results if r.success)
        print(f"   Executed {len(results)} commands, {successful} successful")
        
        # Show execution results
        for result in results[:3]:  # Show first 3 results
            status = "SUCCESS" if result.success else "FAILED"
            print(f"   - Command {result.command_id}: {status}")
            if result.error_message:
                print(f"     Error: {result.error_message}")
    
    print()
    
    # Example 4: Command acknowledgment handling
    print("4. Command acknowledgment handling:")
    
    # Simulate command acknowledgment
    if pause_command:
        success = dispatcher.acknowledge_command(pause_command.id, 12345)
        print(f"   Acknowledged command {pause_command.id}: {success}")
    
    # Check for acknowledgment timeouts
    timed_out = dispatcher.check_acknowledgment_timeouts()
    if timed_out:
        print(f"   Found {len(timed_out)} timed out commands: {timed_out}")
    else:
        print("   No timed out commands found")
    
    print()
    
    # Example 5: Command queue status
    print("5. Command queue status:")
    
    status = dispatcher.get_command_queue_status()
    print(f"   Total commands: {status['total_commands']}")
    print(f"   Pending commands: {status['pending_commands']}")
    print(f"   Executed commands: {status['executed_commands']}")
    print(f"   Pending acknowledgments: {status['pending_acknowledgments']}")
    print(f"   Command types: {status['command_types']}")
    
    print()
    
    # Example 6: Emergency operations
    print("6. Emergency operations:")
    
    # Emergency stop all EAs
    emergency_commands = dispatcher.emergency_stop_all()
    print(f"   Created {len(emergency_commands)} emergency stop commands")
    
    # Close all positions
    close_commands = dispatcher.close_all_positions()
    print(f"   Created {len(close_commands)} close positions commands")
    
    print()
    
    # Example 7: Convenience methods for strategy management
    print("7. Strategy management:")
    
    # Pause all EAs with specific strategy
    pause_strategy_commands = dispatcher.pause_strategy('Expansion_v2')
    print(f"   Paused {len(pause_strategy_commands)} EAs with Expansion_v2 strategy")
    
    # Adjust risk for all EAs trading specific symbol
    symbol_risk_commands = dispatcher.adjust_strategy_risk('Compression_v1', 1.2)
    print(f"   Adjusted risk for {len(symbol_risk_commands)} EAs with Compression_v1 strategy")
    
    # Resume all EAs trading specific symbol
    symbol_resume_commands = dispatcher.resume_symbol('GBPUSD')
    print(f"   Resumed {len(symbol_resume_commands)} EAs trading GBPUSD")
    
    print()
    
    # Example 8: Command cancellation
    print("8. Command cancellation:")
    
    if resume_command:
        cancelled = dispatcher.cancel_command(resume_command.id)
        print(f"   Cancelled command {resume_command.id}: {cancelled}")
    
    print()
    
    # Example 9: Cleanup operations
    print("9. Cleanup operations:")
    
    # Clean up old commands (older than 7 days)
    cleaned_count = dispatcher.cleanup_old_commands(days=7)
    print(f"   Cleaned up {cleaned_count} old commands")
    
    print()
    
    # Example 10: Scheduled command executor
    print("10. Scheduled command executor:")
    
    # Create scheduled executor that runs every 30 seconds
    executor = ScheduledCommandExecutor(dispatcher, execution_interval=30)
    
    print("   Starting scheduled executor...")
    await executor.start()
    
    # Let it run for a short time
    print("   Executor running for 5 seconds...")
    await asyncio.sleep(5)
    
    print("   Stopping scheduled executor...")
    await executor.stop()
    
    print("   Scheduled executor stopped")
    
    print("\n=== Examples completed ===")


def demonstrate_command_filters():
    """Demonstrate different ways to create command filters"""
    
    print("=== Command Filter Examples ===\n")
    
    # Filter by symbol
    symbol_filter = CommandFilter(symbols=['EURUSD', 'GBPUSD'])
    print("1. Symbol filter:", symbol_filter.to_dict())
    
    # Filter by strategy tag
    strategy_filter = CommandFilter(strategy_tags=['Compression_v1', 'Expansion_v2'])
    print("2. Strategy filter:", strategy_filter.to_dict())
    
    # Filter by risk level
    risk_filter = CommandFilter(risk_levels=[1.0, 1.5, 2.0])
    print("3. Risk level filter:", risk_filter.to_dict())
    
    # Filter by EA status
    status_filter = CommandFilter(ea_statuses=['active', 'paused'])
    print("4. Status filter:", status_filter.to_dict())
    
    # Filter by specific magic numbers
    magic_filter = CommandFilter(magic_numbers=[12345, 67890, 11111])
    print("5. Magic number filter:", magic_filter.to_dict())
    
    # Combined filter
    combined_filter = CommandFilter(
        symbols=['EURUSD'],
        strategy_tags=['Compression_v1'],
        ea_statuses=['active']
    )
    print("6. Combined filter:", combined_filter.to_dict())
    
    print()


def demonstrate_command_callbacks():
    """Demonstrate command execution callbacks"""
    
    print("=== Command Callback Examples ===\n")
    
    # Initialize dispatcher
    mt5_interface = MT5CommunicationInterface()
    dispatcher = CommandDispatcher(mt5_interface)
    
    # Define callback functions
    def pause_callback(command, success):
        print(f"Pause command {command.id} executed: {'SUCCESS' if success else 'FAILED'}")
        if success:
            print(f"  EA {command.ea_id} has been paused")
    
    def resume_callback(command, success):
        print(f"Resume command {command.id} executed: {'SUCCESS' if success else 'FAILED'}")
        if success:
            print(f"  EA {command.ea_id} has been resumed")
    
    def risk_callback(command, success):
        print(f"Risk adjustment command {command.id} executed: {'SUCCESS' if success else 'FAILED'}")
        if success:
            data = command.get_command_data()
            print(f"  EA {command.ea_id} risk adjusted to {data.get('new_risk_level')}")
    
    # Register callbacks
    dispatcher.register_execution_callback('pause', pause_callback)
    dispatcher.register_execution_callback('resume', resume_callback)
    dispatcher.register_execution_callback('adjust_risk', risk_callback)
    
    print("Registered callbacks for pause, resume, and adjust_risk commands")
    print("Callbacks will be executed when commands are processed")
    
    print()


if __name__ == '__main__':
    """Run examples when script is executed directly"""
    
    print("MT5 Command Dispatcher Examples")
    print("=" * 50)
    
    # Run filter examples
    demonstrate_command_filters()
    
    # Run callback examples
    demonstrate_command_callbacks()
    
    # Run main async examples
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExamples interrupted by user")
    except Exception as e:
        print(f"\nError running examples: {e}")