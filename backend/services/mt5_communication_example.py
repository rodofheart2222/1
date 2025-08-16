"""
Example usage of MT5 Communication Interface

This script demonstrates how to use the MT5 communication interface
to interact with Expert Advisors.
"""

import logging
import time
from datetime import datetime
from mt5_communication import MT5CommunicationInterface

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Main example function"""
    print("MT5 Communication Interface Example")
    print("=" * 40)
    
    # Initialize the communication interface
    interface = MT5CommunicationInterface(
        global_vars_dir="data/mt5_globals_example",
        fallback_dir="data/mt5_fallback_example",
        heartbeat_timeout=60
    )
    
    # Test communication with a sample EA
    magic_number = 12345
    print(f"\n1. Testing communication with EA {magic_number}")
    test_results = interface.test_communication(magic_number)
    print(f"   Global Variables Test: {'' if test_results['global_vars_test'] else ''}")
    print(f"   Fallback Test: {'' if test_results['fallback_test'] else ''}")
    print(f"   Heartbeat Status: {test_results['heartbeat_status']}")
    
    # Create sample EA data
    print(f"\n2. Creating sample EA data")
    sample_data = interface.data_parser.create_sample_ea_data(magic_number)
    interface.global_vars.write_global_variable(f"COC_EA_{magic_number}_DATA", sample_data)
    print(f"   Sample data written for EA {magic_number}")
    
    # Register EA for heartbeat monitoring
    print(f"\n3. Registering EA for heartbeat monitoring")
    interface.heartbeat_monitor.register_ea(magic_number)
    print(f"   EA {magic_number} registered for monitoring")
    
    # Collect EA data
    print(f"\n4. Collecting EA data")
    reports = interface.collect_ea_data()
    if reports:
        for ea_id, report in reports.items():
            print(f"   EA {ea_id}: {report.symbol} - Profit: ${report.current_profit:.2f}")
    else:
        print("   No EA data found")
    
    # Send commands to EA
    print(f"\n5. Sending commands to EA")
    
    # Send pause command
    success = interface.send_command(magic_number, "pause", {"reason": "example_test"})
    print(f"   Pause command: {'' if success else ''}")
    
    # Send resume command
    success = interface.send_command(magic_number, "resume")
    print(f"   Resume command: {'' if success else ''}")
    
    # Send batch command to multiple EAs
    ea_list = [12345, 67890, 11111]
    results = interface.send_batch_command(ea_list, "adjust_risk", {"risk_percent": 2.0})
    successful = sum(1 for success in results.values() if success)
    print(f"   Batch command: {successful}/{len(ea_list)} successful")
    
    # Check EA connections
    print(f"\n6. Checking EA connections")
    connection_status = interface.check_ea_connections()
    print(f"   Connected EAs: {connection_status['connected']}")
    print(f"   Disconnected EAs: {connection_status['disconnected']}")
    
    # Get system status
    print(f"\n7. System status")
    status = interface.get_system_status()
    print(f"   Communication Mode: {status['communication_mode']}")
    print(f"   Total EAs: {status['heartbeat_stats']['total_eas']}")
    print(f"   Connected: {status['heartbeat_stats']['connected_count']}")
    print(f"   Disconnected: {status['heartbeat_stats']['disconnected_count']}")
    
    # Test fallback mode
    print(f"\n8. Testing fallback mode")
    interface.switch_to_fallback_mode()
    
    # Write EA data to fallback
    fallback_data = {
        'magic_number': 67890,
        'symbol': 'GBPUSD',
        'strategy_tag': 'Expansion_v2',
        'current_profit': 250.75,
        'open_positions': 3,
        'trade_status': 'active',
        'sl_value': 1.2500,
        'tp_value': 1.2700,
        'trailing_active': True,
        'module_status': {'BB': 'active', 'RSI': 'overbought'},
        'performance_metrics': {'profit_factor': 1.8, 'drawdown': 5.5},
        'last_trades': [],
        'coc_override': False,
        'last_update': datetime.now().isoformat()
    }
    
    interface.file_fallback.write_ea_data(67890, fallback_data)
    print(f"   Fallback data written for EA 67890")
    
    # Collect data in fallback mode
    reports = interface.collect_ea_data()
    if reports:
        for ea_id, report in reports.items():
            print(f"   Fallback EA {ea_id}: {report.symbol} - Profit: ${report.current_profit:.2f}")
    
    # Switch back to global variables mode
    interface.switch_to_global_vars_mode()
    print(f"   Switched back to global variables mode")
    
    # Cleanup
    print(f"\n9. Cleanup")
    cleanup_stats = interface.cleanup_old_data(hours=0)  # Clean everything for demo
    print(f"   Cleanup completed: {cleanup_stats}")
    
    print(f"\nExample completed successfully!")


if __name__ == "__main__":
    main()