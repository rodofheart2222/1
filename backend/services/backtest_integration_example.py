"""
Backtest Comparison Integration Example

This example demonstrates how to use the backtest comparison module
to parse MT5 backtest reports and compare them with live performance.
"""

import logging
from datetime import datetime

from .backtest_parser import BacktestHTMLParser, BacktestMetrics
from .backtest_comparison import BacktestComparison, DeviationReport
from ..models.performance import PerformanceMetrics

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def example_mt5_backtest_html():
    """Example MT5 backtest HTML report"""
    return """
    <html>
    <head><title>Strategy Tester Report</title></head>
    <body>
    <table>
    <tr><td>Symbol</td><td>EURUSD</td></tr>
    <tr><td>Period</td><td>H1</td></tr>
    <tr><td>Model</td><td>Every tick</td></tr>
    <tr><td>Profit factor</td><td>1.85</td></tr>
    <tr><td>Expected payoff</td><td>15.25</td></tr>
    <tr><td>Maximal drawdown</td><td>8.5%</td></tr>
    <tr><td>Profit trades (% of total)</td><td>125 (62.5%)</td></tr>
    <tr><td>Total deals</td><td>200</td></tr>
    <tr><td>Total net profit</td><td>3050.00</td></tr>
    </table>
    </body>
    </html>
    """

def demonstrate_backtest_parsing():
    """Demonstrate parsing MT5 backtest HTML report"""
    print("=== Backtest HTML Parsing Demo ===")
    
    parser = BacktestHTMLParser()
    html_content = example_mt5_backtest_html()
    
    # Parse the HTML report
    metrics = parser.parse_html_report(html_content)
    
    if metrics:
        print(" Successfully parsed backtest report:")
        print(f"   Profit Factor: {metrics.profit_factor}")
        print(f"   Expected Payoff: {metrics.expected_payoff}")
        print(f"   Drawdown: {metrics.drawdown}%")
        print(f"   Win Rate: {metrics.win_rate}%")
        print(f"   Trade Count: {metrics.trade_count}")
        print(f"   Total Profit: {metrics.total_profit}")
        return metrics
    else:
        print(" Failed to parse backtest report")
        return None

def demonstrate_performance_comparison():
    """Demonstrate comparing live vs backtest performance"""
    print("\n=== Performance Comparison Demo ===")
    
    # Get backtest metrics from parsing demo
    backtest_metrics = demonstrate_backtest_parsing()
    if not backtest_metrics:
        return
    
    # Create mock live performance metrics (worse than backtest)
    live_metrics = PerformanceMetrics(
        ea_id=1,
        total_profit=2100.0,  # Lower than backtest
        profit_factor=1.25,   # 32% down from 1.85
        expected_payoff=9.5,  # 38% down from 15.25
        drawdown=12.8,        # 51% higher than 8.5
        z_score=1.8,
        trade_count=180,      # Fewer trades
        win_rate=58.0         # Lower win rate
    )
    
    print(f"\n Live Performance:")
    print(f"   Profit Factor: {live_metrics.profit_factor} (vs {backtest_metrics.profit_factor} backtest)")
    print(f"   Expected Payoff: {live_metrics.expected_payoff} (vs {backtest_metrics.expected_payoff} backtest)")
    print(f"   Drawdown: {live_metrics.drawdown}% (vs {backtest_metrics.drawdown}% backtest)")
    print(f"   Win Rate: {live_metrics.win_rate}% (vs {backtest_metrics.win_rate}% backtest)")
    
    # Perform comparison
    comparison = BacktestComparison()
    deviation_report = comparison.calculate_deviation(live_metrics, backtest_metrics)
    
    print(f"\n Deviation Analysis:")
    print(f"   Overall Status: {deviation_report.overall_status.upper()}")
    print(f"   Visual Indicator: {comparison.get_visual_indicator(deviation_report)}")
    print(f"   Profit Factor Deviation: {deviation_report.profit_factor_deviation:.1f}%")
    print(f"   Expected Payoff Deviation: {deviation_report.expected_payoff_deviation:.1f}%")
    print(f"   Drawdown Deviation: {deviation_report.drawdown_deviation:.1f}%")
    print(f"   Win Rate Deviation: {deviation_report.win_rate_deviation:.1f}%")
    
    print(f"\n Alerts ({len(deviation_report.alerts)}):")
    for alert in deviation_report.alerts:
        print(f"   {alert.message}")
    
    print(f"\n Recommendation: {deviation_report.recommendation}")
    
    # Check if EA should be flagged for demotion
    should_flag = comparison.should_flag_for_demotion(deviation_report)
    print(f"\n️  Flag for Demotion: {'YES' if should_flag else 'NO'}")
    
    return deviation_report

def demonstrate_good_performance():
    """Demonstrate comparison with good live performance"""
    print("\n=== Good Performance Demo ===")
    
    # Create backtest metrics
    backtest_metrics = BacktestMetrics(
        profit_factor=1.5,
        expected_payoff=12.0,
        drawdown=6.0,
        win_rate=65.0,
        trade_count=150
    )
    
    # Create good live performance (similar to backtest)
    live_metrics = PerformanceMetrics(
        ea_id=2,
        total_profit=1800.0,
        profit_factor=1.48,   # Only 1.3% down
        expected_payoff=11.5, # Only 4.2% down
        drawdown=6.2,         # Slightly higher but acceptable
        z_score=2.1,
        trade_count=145,
        win_rate=63.5         # Slightly lower but acceptable
    )
    
    comparison = BacktestComparison()
    deviation_report = comparison.calculate_deviation(live_metrics, backtest_metrics)
    
    print(f" Good Performance Example:")
    print(f"   Overall Status: {deviation_report.overall_status.upper()}")
    print(f"   Visual Indicator: {comparison.get_visual_indicator(deviation_report)}")
    print(f"   Alerts: {len(deviation_report.alerts)}")
    print(f"   Recommendation: {deviation_report.recommendation}")
    print(f"   Flag for Demotion: {'YES' if comparison.should_flag_for_demotion(deviation_report) else 'NO'}")

def main():
    """Run all demonstration examples"""
    print(" MT5 Backtest Comparison Module Demo")
    print("=" * 50)
    
    try:
        # Demo 1: Parse backtest HTML
        demonstrate_backtest_parsing()
        
        # Demo 2: Compare poor performance
        demonstrate_performance_comparison()
        
        # Demo 3: Compare good performance
        demonstrate_good_performance()
        
        print("\n All demonstrations completed successfully!")
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        print(f"\n Demo failed: {e}")

if __name__ == "__main__":
    main()