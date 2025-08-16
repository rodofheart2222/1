"""
Example usage of EA Data Collection and Processing Service

This script demonstrates how to use the EADataCollector and related services
for collecting and processing MT5 EA data.
"""

import asyncio
import logging
from datetime import datetime
from .ea_data_collector import EADataCollector, PortfolioAggregator
from .mt5_communication import MT5CommunicationInterface

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def demo_data_collection():
    """Demonstrate EA data collection"""
    logger.info("Starting EA Data Collection Demo")
    
    # Initialize MT5 communication interface
    mt5_interface = MT5CommunicationInterface()
    
    # Initialize data collector with 30-second collection interval
    collector = EADataCollector(
        mt5_interface=mt5_interface,
        collection_interval=30,
        max_retries=3
    )
    
    # Perform a single data collection cycle
    logger.info("Performing single data collection...")
    result = await collector.collect_and_process_data()
    
    logger.info(f"Collection result: {result}")
    
    # Get collection statistics
    stats = collector.get_collection_stats()
    logger.info(f"Collection statistics: {stats}")
    
    return result


async def demo_portfolio_aggregation():
    """Demonstrate portfolio aggregation"""
    logger.info("Starting Portfolio Aggregation Demo")
    
    # Initialize portfolio aggregator
    aggregator = PortfolioAggregator()
    
    # Calculate overall portfolio metrics
    logger.info("Calculating portfolio metrics...")
    portfolio_metrics = await aggregator.calculate_portfolio_metrics()
    
    logger.info(f"Portfolio Metrics:")
    logger.info(f"  Total Profit: ${portfolio_metrics.total_profit:.2f}")
    logger.info(f"  Profit Factor: {portfolio_metrics.profit_factor:.4f}")
    logger.info(f"  Win Rate: {portfolio_metrics.win_rate:.2f}%")
    logger.info(f"  Total Drawdown: {portfolio_metrics.total_drawdown:.2f}%")
    logger.info(f"  Active EAs: {portfolio_metrics.active_eas}/{portfolio_metrics.total_eas}")
    logger.info(f"  Total Trades: {portfolio_metrics.total_trades}")
    logger.info(f"  Symbols: {portfolio_metrics.symbols}")
    logger.info(f"  Strategies: {portfolio_metrics.strategies}")
    
    # Get performance breakdown by symbol and strategy
    logger.info("Getting performance breakdown...")
    breakdown = await aggregator.get_performance_breakdown()
    
    logger.info("Performance by Symbol:")
    for symbol, metrics in breakdown['by_symbol'].items():
        logger.info(f"  {symbol}: Profit=${metrics['total_profit']:.2f}, "
                   f"PF={metrics['profit_factor']:.2f}, "
                   f"WR={metrics['win_rate']:.1f}%")
    
    logger.info("Performance by Strategy:")
    for strategy, metrics in breakdown['by_strategy'].items():
        logger.info(f"  {strategy}: Profit=${metrics['total_profit']:.2f}, "
                   f"PF={metrics['profit_factor']:.2f}, "
                   f"WR={metrics['win_rate']:.1f}%")
    
    # Get individual EA performance metrics
    logger.info("Getting EA performance metrics...")
    ea_metrics = await aggregator.get_ea_performance_metrics()
    
    logger.info(f"Individual EA Performance ({len(ea_metrics)} EAs):")
    for metrics in ea_metrics[:5]:  # Show first 5 EAs
        logger.info(f"  EA {metrics.magic_number}: "
                   f"Profit=${metrics.total_profit:.2f}, "
                   f"PF={metrics.profit_factor:.2f}, "
                   f"DD={metrics.drawdown:.2f}%, "
                   f"Z-Score={metrics.z_score:.2f}")
    
    return portfolio_metrics, breakdown, ea_metrics


async def demo_filtered_portfolio_metrics():
    """Demonstrate filtered portfolio metrics"""
    logger.info("Starting Filtered Portfolio Metrics Demo")
    
    aggregator = PortfolioAggregator()
    
    # Filter by symbol
    logger.info("Portfolio metrics for EURUSD only:")
    eurusd_metrics = await aggregator.calculate_portfolio_metrics(symbol_filter="EURUSD")
    logger.info(f"  EURUSD Profit: ${eurusd_metrics.total_profit:.2f}")
    logger.info(f"  EURUSD Active EAs: {eurusd_metrics.active_eas}")
    
    # Filter by strategy
    logger.info("Portfolio metrics for Compression strategies:")
    compression_metrics = await aggregator.calculate_portfolio_metrics(strategy_filter="Compression")
    logger.info(f"  Compression Profit: ${compression_metrics.total_profit:.2f}")
    logger.info(f"  Compression Active EAs: {compression_metrics.active_eas}")
    
    # Filter by risk level
    logger.info("Portfolio metrics for risk level 1.0:")
    risk_metrics = await aggregator.calculate_portfolio_metrics(risk_filter=1.0)
    logger.info(f"  Risk 1.0 Profit: ${risk_metrics.total_profit:.2f}")
    logger.info(f"  Risk 1.0 Active EAs: {risk_metrics.active_eas}")
    
    return eurusd_metrics, compression_metrics, risk_metrics


async def demo_continuous_collection():
    """Demonstrate continuous data collection"""
    logger.info("Starting Continuous Collection Demo")
    
    # Initialize components
    mt5_interface = MT5CommunicationInterface()
    collector = EADataCollector(
        mt5_interface=mt5_interface,
        collection_interval=10,  # Collect every 10 seconds for demo
        max_retries=3
    )
    
    # Start continuous collection in background
    logger.info("Starting continuous data collection...")
    collection_task = asyncio.create_task(collector.start_collection())
    
    # Let it run for 60 seconds
    await asyncio.sleep(60)
    
    # Stop collection
    logger.info("Stopping data collection...")
    collector.stop_collection()
    
    # Wait for collection task to finish
    try:
        await collection_task
    except Exception as e:
        logger.info(f"Collection stopped: {e}")
    
    # Get final statistics
    final_stats = collector.get_collection_stats()
    logger.info(f"Final collection statistics: {final_stats}")
    
    return final_stats


async def demo_performance_calculations():
    """Demonstrate performance calculation methods"""
    logger.info("Starting Performance Calculations Demo")
    
    from .ea_data_collector import PerformanceCalculator
    from ..models.trade import Trade
    from unittest.mock import Mock
    
    calculator = PerformanceCalculator()
    
    # Create sample trades for demonstration
    sample_trades = []
    
    # Create winning trades
    for i in range(6):
        trade = Mock(spec=Trade)
        trade.profit = 50.0 + (i * 10)  # Profits: 50, 60, 70, 80, 90, 100
        trade.is_closed = True
        trade.close_time = datetime.now()
        sample_trades.append(trade)
    
    # Create losing trades
    for i in range(4):
        trade = Mock(spec=Trade)
        trade.profit = -30.0 - (i * 5)  # Losses: -30, -35, -40, -45
        trade.is_closed = True
        trade.close_time = datetime.now()
        sample_trades.append(trade)
    
    # Calculate performance metrics
    profit_factor = calculator.calculate_profit_factor(sample_trades)
    expected_payoff = calculator.calculate_expected_payoff(sample_trades)
    drawdown = calculator.calculate_drawdown(sample_trades)
    z_score = calculator.calculate_z_score(sample_trades)
    win_rate = calculator.calculate_win_rate(sample_trades)
    
    logger.info("Sample Performance Calculations:")
    logger.info(f"  Total Trades: {len(sample_trades)}")
    logger.info(f"  Profit Factor: {profit_factor:.4f}")
    logger.info(f"  Expected Payoff: ${expected_payoff:.2f}")
    logger.info(f"  Maximum Drawdown: {drawdown:.2f}%")
    logger.info(f"  Z-Score: {z_score:.4f}")
    logger.info(f"  Win Rate: {win_rate:.2f}%")
    
    return {
        'profit_factor': profit_factor,
        'expected_payoff': expected_payoff,
        'drawdown': drawdown,
        'z_score': z_score,
        'win_rate': win_rate
    }


async def main():
    """Main demo function"""
    logger.info("=== EA Data Collection Service Demo ===")
    
    try:
        # Demo 1: Single data collection
        logger.info("\n--- Demo 1: Single Data Collection ---")
        collection_result = await demo_data_collection()
        
        # Demo 2: Portfolio aggregation
        logger.info("\n--- Demo 2: Portfolio Aggregation ---")
        portfolio_metrics, breakdown, ea_metrics = await demo_portfolio_aggregation()
        
        # Demo 3: Filtered portfolio metrics
        logger.info("\n--- Demo 3: Filtered Portfolio Metrics ---")
        filtered_metrics = await demo_filtered_portfolio_metrics()
        
        # Demo 4: Performance calculations
        logger.info("\n--- Demo 4: Performance Calculations ---")
        performance_results = await demo_performance_calculations()
        
        # Demo 5: Continuous collection (commented out for quick demo)
        # logger.info("\n--- Demo 5: Continuous Collection ---")
        # continuous_stats = await demo_continuous_collection()
        
        logger.info("\n=== Demo Complete ===")
        
        return {
            'collection_result': collection_result,
            'portfolio_metrics': portfolio_metrics,
            'breakdown': breakdown,
            'ea_metrics': ea_metrics,
            'filtered_metrics': filtered_metrics,
            'performance_results': performance_results
        }
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        raise


if __name__ == "__main__":
    # Run the demo
    asyncio.run(main())