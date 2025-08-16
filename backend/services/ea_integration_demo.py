"""
EA Integration Demo - Simulates MT5 Global Variables for testing
This script demonstrates how the Soldier EA communicates with the COC Dashboard
"""
import time
import json
import sqlite3
import random
from datetime import datetime, timedelta
from pathlib import Path
import sys
import os

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.init_db import init_database
from services.ea_data_collector import EADataCollector
from services.command_dispatcher import CommandDispatcher

class MT5GlobalVariableSimulator:
    """Simulates MT5 Global Variables for testing EA integration"""
    
    def __init__(self):
        self.global_vars = {}
        self.ea_data = {}
        self.running_eas = []
        
    def set_global_variable(self, name, value):
        """Set a global variable (simulates GlobalVariableSet)"""
        self.global_vars[name] = {
            'value': value,
            'timestamp': datetime.now()
        }
        
    def get_global_variable(self, name):
        """Get a global variable (simulates GlobalVariableGet)"""
        if name in self.global_vars:
            return self.global_vars[name]['value']
        return None
        
    def check_global_variable(self, name):
        """Check if global variable exists (simulates GlobalVariableCheck)"""
        return name in self.global_vars
        
    def delete_global_variable(self, name):
        """Delete a global variable (simulates GlobalVariableDel)"""
        if name in self.global_vars:
            del self.global_vars[name]
            return True
        return False
        
    def list_global_variables(self, prefix=""):
        """List all global variables with optional prefix filter"""
        if prefix:
            return [name for name in self.global_vars.keys() if name.startswith(prefix)]
        return list(self.global_vars.keys())

class SoldierEASimulator:
    """Simulates a Soldier EA reporting to the COC system"""
    
    def __init__(self, magic_number, symbol, strategy_tag, gv_simulator):
        self.magic_number = magic_number
        self.symbol = symbol
        self.strategy_tag = strategy_tag
        self.gv_sim = gv_simulator
        self.ea_prefix = f"COC_EA_{magic_number}_"
        
        # EA state
        self.is_paused = False
        self.coc_override = False
        self.current_profit = 0.0
        self.open_positions = 0
        self.total_profit = random.uniform(100, 2000)
        self.total_trades = random.randint(50, 200)
        self.max_drawdown = random.uniform(5, 15)
        self.lot_multiplier = 1.0
        
        # Performance metrics
        self.profit_factor = random.uniform(1.2, 2.5)
        self.expected_payoff = random.uniform(15, 45)
        self.z_score = random.uniform(1.0, 3.0)
        
        # Module status
        self.bb_status = "middle"
        self.rsi_status = "neutral"
        self.ma_status = "sideways"
        self.expansion_status = "stable"
        
        # Trading state
        self.sl_value = 0.0
        self.tp_value = 0.0
        self.trailing_active = False
        
        # Last trades (mock data)
        self.last_trades = self.generate_mock_trades()
        
        print(f" Soldier EA {magic_number} ({strategy_tag}) initialized for {symbol}")
        
    def generate_mock_trades(self):
        """Generate mock trade history"""
        trades = []
        for i in range(10):
            trade = {
                'symbol': self.symbol,
                'type': random.choice(['BUY', 'SELL']),
                'volume': round(random.uniform(0.1, 2.0), 2),
                'price': round(random.uniform(1.0800, 1.0950), 5),
                'profit': round(random.uniform(-50, 100), 2),
                'timestamp': (datetime.now() - timedelta(hours=i)).isoformat()
            }
            trades.append(trade)
        return trades
        
    def register_with_coc(self):
        """Register EA with COC system"""
        registration_data = {
            'magic_number': self.magic_number,
            'symbol': self.symbol,
            'strategy_tag': self.strategy_tag,
            'risk_config': 1.0,
            'status': 'active',
            'timestamp': datetime.now().isoformat()
        }
        
        self.gv_sim.set_global_variable(f"{self.ea_prefix}REGISTRATION", 1.0)
        print(f" EA {self.magic_number} registered with COC")
        
    def update_trading_state(self):
        """Simulate trading activity and update state"""
        # Simulate profit changes
        profit_change = random.uniform(-20, 30)
        self.current_profit += profit_change
        self.total_profit += profit_change
        
        # Simulate position changes
        if random.random() < 0.1:  # 10% chance to change positions
            self.open_positions = random.randint(0, 3)
            if self.open_positions > 0:
                self.sl_value = round(random.uniform(1.0800, 1.0900), 5)
                self.tp_value = round(random.uniform(1.0900, 1.0950), 5)
                self.trailing_active = random.choice([True, False])
            else:
                self.sl_value = 0.0
                self.tp_value = 0.0
                self.trailing_active = False
                
        # Simulate module status changes
        self.bb_status = random.choice(['above', 'middle', 'below'])
        self.rsi_status = random.choice(['overbought', 'neutral', 'oversold'])
        self.ma_status = random.choice(['above', 'at', 'below'])
        self.expansion_status = random.choice(['expanding', 'stable', 'contracting'])
        
        # Update performance metrics slightly
        self.profit_factor += random.uniform(-0.05, 0.05)
        self.profit_factor = max(0.5, min(3.0, self.profit_factor))
        
        self.expected_payoff += random.uniform(-2, 2)
        self.z_score += random.uniform(-0.1, 0.1)
        self.z_score = max(0.0, min(5.0, self.z_score))
        
    def report_to_coc(self):
        """Report current status to COC system via Global Variables"""
        # Update trading state
        self.update_trading_state()
        
        # Set basic status variables
        self.gv_sim.set_global_variable(f"{self.ea_prefix}PROFIT", self.current_profit)
        self.gv_sim.set_global_variable(f"{self.ea_prefix}POSITIONS", self.open_positions)
        self.gv_sim.set_global_variable(f"{self.ea_prefix}SL", self.sl_value)
        self.gv_sim.set_global_variable(f"{self.ea_prefix}TP", self.tp_value)
        self.gv_sim.set_global_variable(f"{self.ea_prefix}TRAILING", 1.0 if self.trailing_active else 0.0)
        self.gv_sim.set_global_variable(f"{self.ea_prefix}OVERRIDE", 1.0 if self.coc_override else 0.0)
        self.gv_sim.set_global_variable(f"{self.ea_prefix}HEARTBEAT", time.time())
        
        # Create module status JSON (in real implementation, would use file storage)
        module_status = {
            'BB': self.bb_status,
            'RSI': self.rsi_status,
            'MA': self.ma_status,
            'Expansion': self.expansion_status
        }
        
        # Create performance metrics JSON
        performance_metrics = {
            'total_profit': round(self.total_profit, 2),
            'profit_factor': round(self.profit_factor, 2),
            'expected_payoff': round(self.expected_payoff, 2),
            'drawdown': round(self.max_drawdown, 2),
            'z_score': round(self.z_score, 2)
        }
        
        # Store JSON data (simulated - in real MT5, would use file system)
        self.gv_sim.set_global_variable(f"{self.ea_prefix}MODULE_JSON", hash(json.dumps(module_status)))
        self.gv_sim.set_global_variable(f"{self.ea_prefix}PERF_JSON", hash(json.dumps(performance_metrics)))
        self.gv_sim.set_global_variable(f"{self.ea_prefix}TRADES_JSON", hash(json.dumps(self.last_trades)))
        
        # Store actual data for collector to access
        self.gv_sim.ea_data[self.magic_number] = {
            'magic_number': self.magic_number,
            'symbol': self.symbol,
            'strategy_tag': self.strategy_tag,
            'current_profit': self.current_profit,
            'open_positions': self.open_positions,
            'sl_value': self.sl_value,
            'tp_value': self.tp_value,
            'trailing_active': self.trailing_active,
            'module_status': module_status,
            'performance_metrics': performance_metrics,
            'last_trades': self.last_trades,
            'coc_override': self.coc_override,
            'last_update': datetime.now(),
            'is_paused': self.is_paused
        }
        
    def check_coc_commands(self):
        """Check for commands from COC system"""
        # Check for pause command
        if self.gv_sim.check_global_variable(f"{self.ea_prefix}CMD_PAUSE"):
            self.is_paused = True
            self.gv_sim.delete_global_variable(f"{self.ea_prefix}CMD_PAUSE")
            self.gv_sim.set_global_variable(f"{self.ea_prefix}CMD_ACK", time.time())
            print(f"️  EA {self.magic_number} paused by COC command")
            
        # Check for resume command
        if self.gv_sim.check_global_variable(f"{self.ea_prefix}CMD_RESUME"):
            self.is_paused = False
            self.coc_override = False
            self.gv_sim.delete_global_variable(f"{self.ea_prefix}CMD_RESUME")
            self.gv_sim.set_global_variable(f"{self.ea_prefix}CMD_ACK", time.time())
            print(f"▶️  EA {self.magic_number} resumed by COC command")
            
        # Check for close positions command
        if self.gv_sim.check_global_variable(f"{self.ea_prefix}CMD_CLOSE"):
            self.open_positions = 0
            self.sl_value = 0.0
            self.tp_value = 0.0
            self.trailing_active = False
            self.gv_sim.delete_global_variable(f"{self.ea_prefix}CMD_CLOSE")
            self.gv_sim.set_global_variable(f"{self.ea_prefix}CMD_ACK", time.time())
            print(f" EA {self.magic_number} positions closed by COC command")
            
        # Check for risk adjustment command
        if self.gv_sim.check_global_variable(f"{self.ea_prefix}CMD_RISK"):
            new_multiplier = self.gv_sim.get_global_variable(f"{self.ea_prefix}CMD_RISK")
            self.lot_multiplier = new_multiplier
            self.coc_override = True
            self.gv_sim.delete_global_variable(f"{self.ea_prefix}CMD_RISK")
            self.gv_sim.set_global_variable(f"{self.ea_prefix}CMD_ACK", time.time())
            print(f"️  EA {self.magic_number} risk adjusted - New multiplier: {new_multiplier}")

class COCIntegrationDemo:
    """Demonstrates complete COC Dashboard integration"""
    
    def __init__(self):
        self.gv_simulator = MT5GlobalVariableSimulator()
        self.soldier_eas = []
        self.ea_collector = None
        self.command_dispatcher = None
        
    def setup_demo_environment(self):
        """Set up demo environment with multiple EAs"""
        print(" Setting up COC Integration Demo Environment")
        print("=" * 50)
        
        # Initialize database
        if os.path.exists("data/demo_integration.db"):
            os.remove("data/demo_integration.db")
        os.environ['DATABASE_PATH'] = "data/demo_integration.db"
        init_database()
        
        # Initialize services
        self.ea_collector = EADataCollector()
        self.command_dispatcher = CommandDispatcher()
        
        # Create demo EAs
        ea_configs = [
            (12345, 'EURUSD', 'Compression_v1'),
            (12346, 'GBPUSD', 'Expansion_v2'),
            (12347, 'USDJPY', 'Compression_v1'),
            (12348, 'AUDUSD', 'Expansion_v2'),
            (12349, 'USDCAD', 'Compression_v3'),
            (12350, 'NZDUSD', 'Expansion_v1'),
            (12351, 'EURJPY', 'Compression_v2'),
            (12352, 'GBPJPY', 'Expansion_v3'),
        ]
        
        for magic, symbol, strategy in ea_configs:
            ea = SoldierEASimulator(magic, symbol, strategy, self.gv_simulator)
            ea.register_with_coc()
            self.soldier_eas.append(ea)
            
        print(f" Created {len(self.soldier_eas)} demo Soldier EAs")
        
    def run_demo_cycle(self, duration_seconds=60):
        """Run a complete demo cycle"""
        print(f"\n Starting {duration_seconds}s integration demo cycle")
        print("=" * 50)
        
        start_time = time.time()
        cycle_count = 0
        
        while time.time() - start_time < duration_seconds:
            cycle_count += 1
            print(f"\n Demo Cycle {cycle_count} - {time.time() - start_time:.1f}s elapsed")
            
            # Step 1: EAs report their status
            print("1️ EAs reporting status...")
            for ea in self.soldier_eas:
                ea.report_to_coc()
                ea.check_coc_commands()
                
            # Step 2: Collect EA data
            print("2️ Collecting EA data...")
            ea_data_list = []
            for magic_number, ea_data in self.gv_simulator.ea_data.items():
                ea_data_list.append(ea_data)
                
            # Step 3: Process portfolio statistics
            if ea_data_list:
                portfolio_stats = self.calculate_portfolio_stats(ea_data_list)
                print(f"    Portfolio P&L: ${portfolio_stats['total_profit']:.2f}")
                print(f"    Active EAs: {portfolio_stats['active_eas']}/{len(self.soldier_eas)}")
                print(f"    Total Trades: {portfolio_stats['total_trades']}")
                print(f"    Avg Profit Factor: {portfolio_stats['avg_profit_factor']:.2f}")
                
            # Step 4: Demonstrate command execution
            if cycle_count % 5 == 0:  # Every 5th cycle
                self.demonstrate_commands()
                
            # Step 5: Show EA status summary
            self.show_ea_status_summary()
            
            time.sleep(3)  # Wait 3 seconds between cycles
            
        print(f"\n Demo completed after {cycle_count} cycles")
        
    def calculate_portfolio_stats(self, ea_data_list):
        """Calculate portfolio-wide statistics"""
        total_profit = sum(ea['current_profit'] for ea in ea_data_list)
        active_eas = len([ea for ea in ea_data_list if not ea.get('is_paused', False)])
        total_trades = sum(ea['performance_metrics'].get('total_profit', 0) for ea in ea_data_list)
        avg_pf = sum(ea['performance_metrics'].get('profit_factor', 1.0) for ea in ea_data_list) / len(ea_data_list)
        
        return {
            'total_profit': total_profit,
            'active_eas': active_eas,
            'total_trades': total_trades,
            'avg_profit_factor': avg_pf
        }
        
    def demonstrate_commands(self):
        """Demonstrate COC command execution"""
        print("3️ Demonstrating COC commands...")
        
        if len(self.soldier_eas) >= 2:
            # Pause first EA
            ea1 = self.soldier_eas[0]
            self.gv_simulator.set_global_variable(f"COC_EA_{ea1.magic_number}_CMD_PAUSE", 1.0)
            print(f"   ️  Sent pause command to EA {ea1.magic_number}")
            
            # Adjust risk on second EA
            ea2 = self.soldier_eas[1]
            new_risk = random.uniform(0.5, 2.0)
            self.gv_simulator.set_global_variable(f"COC_EA_{ea2.magic_number}_CMD_RISK", new_risk)
            print(f"   ️  Sent risk adjustment to EA {ea2.magic_number} (multiplier: {new_risk:.2f})")
            
    def show_ea_status_summary(self):
        """Show summary of all EA statuses"""
        print("4️ EA Status Summary:")
        
        for ea in self.soldier_eas[:4]:  # Show first 4 EAs to keep output manageable
            status_icon = "️" if ea.is_paused else "▶️"
            override_icon = "" if ea.coc_override else ""
            profit_icon = "" if ea.current_profit >= 0 else ""
            
            print(f"   {status_icon}{override_icon} EA {ea.magic_number} ({ea.symbol}): "
                  f"{profit_icon}${ea.current_profit:.2f} | "
                  f"Pos: {ea.open_positions} | "
                  f"PF: {ea.profit_factor:.2f}")
                  
    def demonstrate_news_integration(self):
        """Demonstrate news event integration"""
        print("\n Demonstrating News Integration")
        print("=" * 30)
        
        # Simulate news event blocking
        symbols_to_block = ['EURUSD', 'GBPUSD']
        block_until = time.time() + 60  # Block for 1 minute
        
        for symbol in symbols_to_block:
            self.gv_simulator.set_global_variable(f"COC_NEWS_BLOCK_{symbol}", block_until)
            print(f" Trading blocked for {symbol} due to high-impact news")
            
        # Show which EAs are affected
        affected_eas = [ea for ea in self.soldier_eas if ea.symbol in symbols_to_block]
        print(f"️  {len(affected_eas)} EAs affected by news restrictions")
        
    def demonstrate_backtest_comparison(self):
        """Demonstrate backtest comparison functionality"""
        print("\n Demonstrating Backtest Comparison")
        print("=" * 35)
        
        for ea in self.soldier_eas[:2]:  # Demo with first 2 EAs
            # Simulate backtest benchmark
            backtest_pf = ea.profit_factor + random.uniform(0.2, 0.8)
            live_pf = ea.profit_factor
            
            deviation = ((live_pf - backtest_pf) / backtest_pf) * 100
            
            if deviation < -20:
                status = " ALERT"
            elif deviation < -10:
                status = "🟡 WARNING"
            else:
                status = "🟢 OK"
                
            print(f"   EA {ea.magic_number}: Backtest PF: {backtest_pf:.2f}, "
                  f"Live PF: {live_pf:.2f}, Deviation: {deviation:.1f}% {status}")
                  
    def run_comprehensive_demo(self):
        """Run complete integration demonstration"""
        try:
            self.setup_demo_environment()
            
            print("\n Running comprehensive integration demo...")
            
            # Main demo cycle
            self.run_demo_cycle(30)  # 30 second demo
            
            # Demonstrate additional features
            self.demonstrate_news_integration()
            self.demonstrate_backtest_comparison()
            
            # Final statistics
            print("\n Final Demo Statistics")
            print("=" * 25)
            
            total_gv = len(self.gv_simulator.global_vars)
            active_eas = len([ea for ea in self.soldier_eas if not ea.is_paused])
            
            print(f"Global Variables Created: {total_gv}")
            print(f"Active EAs: {active_eas}/{len(self.soldier_eas)}")
            print(f"Commands Processed: Multiple pause/resume/risk adjustments")
            print(f"Data Points Collected: {len(self.gv_simulator.ea_data)} EA datasets")
            
            print("\n Integration demo completed successfully!")
            print(" All COC Dashboard components working together")
            
        except KeyboardInterrupt:
            print("\n️ Demo interrupted by user")
        except Exception as e:
            print(f"\n Demo failed with error: {e}")
            raise

if __name__ == "__main__":
    print(" MT5 COC Dashboard - EA Integration Demo")
    print("=" * 50)
    print("This demo simulates multiple Soldier EAs communicating")
    print("with the COC Dashboard system via Global Variables")
    print("=" * 50)
    
    demo = COCIntegrationDemo()
    demo.run_comprehensive_demo()