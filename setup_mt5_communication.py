#!/usr/bin/env python3
"""
Setup MT5 Communication
Create EA data files to simulate MT5 EAs communicating with the system
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
import time

# Add backend to path
sys.path.append('backend')

from services.mt5_communication import MT5CommunicationInterface, SoldierReport

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_realistic_ea_data():
    """Create realistic EA data that simulates actual MT5 EAs"""
    
    # Define realistic EA configurations
    ea_configs = [
        {
            'magic_number': 12345,
            'symbol': 'EURUSD',
            'strategy_tag': 'Compression_v1',
            'base_profit': 150.75,
            'positions': 2,
            'risk_level': 1.0
        },
        {
            'magic_number': 67890,
            'symbol': 'GBPUSD', 
            'strategy_tag': 'Scalper_v2',
            'base_profit': -25.30,
            'positions': 1,
            'risk_level': 0.5
        },
        {
            'magic_number': 11111,
            'symbol': 'USDJPY',
            'strategy_tag': 'Trend_v1',
            'base_profit': 89.45,
            'positions': 0,
            'risk_level': 1.5
        },
        {
            'magic_number': 22222,
            'symbol': 'AUDUSD',
            'strategy_tag': 'Breakout_v1',
            'base_profit': 234.12,
            'positions': 3,
            'risk_level': 2.0
        },
        {
            'magic_number': 33333,
            'symbol': 'USDCAD',
            'strategy_tag': 'Grid_v1',
            'base_profit': -67.89,
            'positions': 5,
            'risk_level': 0.8
        }
    ]
    
    reports = []
    current_time = datetime.now()
    
    for config in ea_configs:
        # Create realistic soldier report
        report = SoldierReport(
            magic_number=config['magic_number'],
            symbol=config['symbol'],
            strategy_tag=config['strategy_tag'],
            current_profit=config['base_profit'],
            open_positions=config['positions'],
            trade_status='active',
            sl_value=0.0,
            tp_value=0.0,
            trailing_active=config['positions'] > 0,
            module_status={
                'BB': 'active',
                'RSI': 'signal',
                'MA': 'trend',
                'risk_manager': 'active'
            },
            performance_metrics={
                'pf': 1.2 + (config['base_profit'] / 1000.0),
                'ep': abs(config['base_profit']),
                'dd': max(0, -config['base_profit'] * 0.1),
                'zscore': config['base_profit'] / 100.0
            },
            last_trades=[
                {
                    'ticket': 12345 + i,
                    'symbol': config['symbol'],
                    'profit': config['base_profit'] / max(1, config['positions']),
                    'close_time': (current_time - timedelta(hours=i)).isoformat()
                } for i in range(min(3, config['positions'] + 1))
            ],
            coc_override=False,
            last_update=current_time
        )
        
        reports.append(report)
    
    return reports

def write_ea_data_to_mt5_globals(reports):
    """Write EA data to MT5 global variables directory"""
    try:
        globals_dir = Path("data/mt5_globals")
        globals_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Writing {len(reports)} EA reports to MT5 globals...")
        
        for report in reports:
            # Create global variable file name
            var_name = f"COC_EA_{report.magic_number}_DATA"
            var_file = globals_dir / f"{var_name}.txt"
            
            # Convert report to JSON
            report_data = report.to_dict()
            report_json = json.dumps(report_data, indent=2)
            
            # Write to file
            var_file.write_text(report_json)
            logger.info(f"  Written EA {report.magic_number} ({report.symbol}) data")
        
        logger.info("Successfully wrote all EA data to MT5 globals")
        return True
        
    except Exception as e:
        logger.error(f"Error writing EA data to MT5 globals: {e}")
        return False

def write_ea_data_to_fallback(reports):
    """Write EA data to fallback directory"""
    try:
        fallback_dir = Path("data/mt5_fallback/ea_data")
        fallback_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Writing {len(reports)} EA reports to fallback...")
        
        for report in reports:
            # Create fallback file
            ea_file = fallback_dir / f"ea_{report.magic_number}.json"
            
            # Convert report to JSON with timestamp
            report_data = report.to_dict()
            report_data['file_timestamp'] = datetime.now().isoformat()
            report_json = json.dumps(report_data, indent=2)
            
            # Write to file
            ea_file.write_text(report_json)
            logger.info(f"  Written EA {report.magic_number} ({report.symbol}) fallback data")
        
        logger.info("Successfully wrote all EA data to fallback")
        return True
        
    except Exception as e:
        logger.error(f"Error writing EA data to fallback: {e}")
        return False

def create_heartbeat_files(reports):
    """Create heartbeat files for EAs"""
    try:
        heartbeat_dir = Path("data/mt5_fallback/heartbeat")
        heartbeat_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Creating heartbeat files for {len(reports)} EAs...")
        
        current_time = datetime.now()
        
        for report in reports:
            heartbeat_file = heartbeat_dir / f"ea_{report.magic_number}_heartbeat.txt"
            heartbeat_file.write_text(current_time.isoformat())
            logger.info(f"  Created heartbeat for EA {report.magic_number}")
        
        logger.info("Successfully created all heartbeat files")
        return True
        
    except Exception as e:
        logger.error(f"Error creating heartbeat files: {e}")
        return False

def test_mt5_communication():
    """Test MT5 communication interface"""
    try:
        logger.info("Testing MT5 communication interface...")
        
        # Initialize MT5 interface
        mt5_interface = MT5CommunicationInterface()
        
        # Try to collect EA data
        ea_reports = mt5_interface.collect_ea_data()
        
        if ea_reports:
            logger.info(f"Successfully collected {len(ea_reports)} EA reports:")
            for magic_number, report in ea_reports.items():
                logger.info(f"  EA {magic_number}: {report.symbol} - Profit: {report.current_profit}, Positions: {report.open_positions}")
            return True
        else:
            logger.warning("No EA reports collected from MT5 interface")
            return False
        
    except Exception as e:
        logger.error(f"Error testing MT5 communication: {e}")
        return False

def setup_continuous_updates():
    """Setup continuous EA data updates to simulate live trading"""
    try:
        logger.info("Setting up continuous EA data updates...")
        
        # Create initial reports
        reports = create_realistic_ea_data()
        
        # Write initial data
        write_ea_data_to_mt5_globals(reports)
        write_ea_data_to_fallback(reports)
        create_heartbeat_files(reports)
        
        logger.info("Continuous updates setup complete")
        logger.info("EA data will be updated every 30 seconds to simulate live trading")
        
        return True
        
    except Exception as e:
        logger.error(f"Error setting up continuous updates: {e}")
        return False

def update_ea_data_continuously():
    """Continuously update EA data to simulate live trading"""
    try:
        logger.info("Starting continuous EA data updates...")
        
        update_count = 0
        
        while True:
            update_count += 1
            logger.info(f"Update cycle {update_count}")
            
            # Create updated reports with slight variations
            reports = create_realistic_ea_data()
            
            # Add some randomness to simulate live trading
            import random
            for report in reports:
                # Vary profit slightly
                variation = random.uniform(-5.0, 5.0)
                report.current_profit += variation
                
                # Occasionally change positions
                if random.random() < 0.1:  # 10% chance
                    report.open_positions = max(0, report.open_positions + random.choice([-1, 0, 1]))
                
                # Update timestamp
                report.last_update = datetime.now()
            
            # Write updated data
            write_ea_data_to_mt5_globals(reports)
            write_ea_data_to_fallback(reports)
            create_heartbeat_files(reports)
            
            logger.info(f"Updated {len(reports)} EA reports")
            
            # Wait 30 seconds before next update
            time.sleep(30)
            
    except KeyboardInterrupt:
        logger.info("Continuous updates stopped by user")
    except Exception as e:
        logger.error(f"Error in continuous updates: {e}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Setup MT5 Communication")
    parser.add_argument("--setup", action="store_true", help="Setup EA data files")
    parser.add_argument("--test", action="store_true", help="Test MT5 communication")
    parser.add_argument("--continuous", action="store_true", help="Run continuous updates")
    
    args = parser.parse_args()
    
    if args.setup:
        success = setup_continuous_updates()
        print(f"MT5 communication setup: {'SUCCESS' if success else 'FAILED'}")
    elif args.test:
        success = test_mt5_communication()
        print(f"MT5 communication test: {'SUCCESS' if success else 'FAILED'}")
    elif args.continuous:
        update_ea_data_continuously()
    else:
        print("Use --setup to create EA data, --test to test communication, or --continuous for live updates")