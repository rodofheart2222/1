#!/usr/bin/env python3
"""
Demo of the complete backtest system
"""
import sys
sys.path.append('backend')

from services.backtest_parser import BacktestHTMLParser
from services.backtest_comparison import BacktestComparison
from models.performance import PerformanceMetrics
import json

def demo_backtest_system():
    """Demonstrate the complete backtest system"""
    
    print("🚀 Backtest Comparison System Demo")
    print("=" * 50)
    
    # Initialize services
    parser = BacktestHTMLParser()
    comparison = BacktestComparison()
    
    # Parse the CNN EA backtest report
    print("\n📊 Parsing CNN EA Backtest Report...")
    backtest_metrics = parser.parse_file('backend/services/ReportTester-10007209416.html')
    
    if not backtest_metrics:
        print("❌ Failed to parse backtest report")
        return
    
    print("✅ Backtest Benchmark Established:")
    print(f"   📈 Profit Factor: {backtest_metrics.profit_factor}")
    print(f"   💰 Expected Payoff: ${backtest_metrics.expected_payoff}")
    print(f"   📉 Max Drawdown: {backtest_metrics.drawdown}%")
    print(f"   🎯 Win Rate: {backtest_metrics.win_rate}%")
    print(f"   📊 Total Trades: {backtest_metrics.trade_count}")
    print(f"   💵 Total Profit: ${backtest_metrics.total_profit}")
    
    # Simulate different live performance scenarios
    scenarios = [
        {
            "name": "🟢 Good Performance",
            "metrics": PerformanceMetrics(
                ea_id=777777,
                total_profit=380.0,
                profit_factor=1.72,
                expected_payoff=0.45,
                drawdown=5.2,
                z_score=-20.1,
                trade_count=1800,
                win_rate=78.5
            )
        },
        {
            "name": "🟡 Warning Performance", 
            "metrics": PerformanceMetrics(
                ea_id=777777,
                total_profit=280.0,
                profit_factor=1.35,
                expected_payoff=0.28,
                drawdown=8.5,
                z_score=-15.2,
                trade_count=1200,
                win_rate=68.5
            )
        },
        {
            "name": "🔴 Critical Performance",
            "metrics": PerformanceMetrics(
                ea_id=777777,
                total_profit=150.0,
                profit_factor=0.95,
                expected_payoff=0.15,
                drawdown=12.8,
                z_score=-8.3,
                trade_count=800,
                win_rate=55.2
            )
        }
    ]
    
    print("\n🔍 Performance Analysis Results:")
    print("=" * 50)
    
    for scenario in scenarios:
        print(f"\n{scenario['name']}")
        print("-" * 30)
        
        # Perform comparison
        deviation_report = comparison.calculate_deviation(scenario['metrics'], backtest_metrics)
        
        # Display results
        print(f"Status: {deviation_report.overall_status.upper()}")
        print(f"Profit Factor: {scenario['metrics'].profit_factor} ({deviation_report.profit_factor_deviation:+.1f}%)")
        print(f"Expected Payoff: ${scenario['metrics'].expected_payoff} ({deviation_report.expected_payoff_deviation:+.1f}%)")
        print(f"Drawdown: {scenario['metrics'].drawdown}% ({deviation_report.drawdown_deviation:+.1f}%)")
        print(f"Win Rate: {scenario['metrics'].win_rate}% ({deviation_report.win_rate_deviation:+.1f}%)")
        
        # Show alerts
        if deviation_report.alerts:
            print("Alerts:")
            for alert in deviation_report.alerts:
                print(f"  • {alert.message}")
        
        print(f"Recommendation: {deviation_report.recommendation}")
        
        # Check demotion flag
        should_flag = comparison.should_flag_for_demotion(deviation_report)
        if should_flag:
            print("🚨 FLAGGED FOR DEMOTION")
        
        # Visual indicator
        emoji = comparison.get_visual_indicator(deviation_report)
        print(f"Dashboard Indicator: {emoji}")
    
    print("\n📋 API Endpoints Available:")
    print("=" * 50)
    print("POST /api/backtest/upload          - Upload backtest HTML report")
    print("GET  /api/backtest/benchmarks      - Get all benchmarks")
    print("GET  /api/backtest/benchmark/{id}  - Get specific benchmark")
    print("GET  /api/backtest/deviations      - Get deviation reports")
    print("POST /api/backtest/compare/{id}    - Compare live vs backtest")
    print("GET  /api/backtest/flagged-eas     - Get EAs flagged for demotion")
    print("GET  /api/backtest/health          - Service health check")
    
    print("\n✅ Backtest Comparison System Ready!")
    print("The system can now:")
    print("• Parse MT5 backtest HTML reports")
    print("• Store benchmark performance metrics")
    print("• Compare live EA performance with backtests")
    print("• Generate alerts for performance degradation")
    print("• Flag EAs for demotion when performance is critical")
    print("• Provide visual indicators for dashboard display")

if __name__ == "__main__":
    demo_backtest_system()