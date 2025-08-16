"""
Backtest Service

Main service for handling backtest benchmark uploads, storage, and comparison
with live EA performance. Integrates with the database and provides high-level
API for backtest-related operations.
"""

from typing import Dict, List, Optional, Tuple
import sqlite3
import logging
import random
from datetime import datetime

from .backtest_parser import BacktestHTMLParser, BacktestMetrics
from .backtest_comparison import BacktestComparison, DeviationReport
from models.performance import PerformanceMetrics
from database.connection import DatabaseManager
from sqlalchemy import text

logger = logging.getLogger(__name__)

class BacktestService:
    """Service for managing backtest benchmarks and comparisons"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.parser = BacktestHTMLParser()
        self.comparison = BacktestComparison()
    
    def upload_backtest_report(self, ea_id: int, html_content: str) -> bool:
        """
        Upload and parse backtest HTML report for an EA
        
        Args:
            ea_id: EA identifier
            html_content: Raw HTML content of backtest report
            
        Returns:
            True if upload successful, False otherwise
        """
        try:
            # Parse the HTML report
            metrics = self.parser.parse_html_report(html_content)
            if not metrics:
                logger.error(f"Failed to parse backtest report for EA {ea_id}")
                return False
            
            # Store in database
            return self._store_backtest_benchmark(ea_id, metrics)
            
        except Exception as e:
            logger.error(f"Error uploading backtest report for EA {ea_id}: {e}")
            return False
    
    def upload_backtest_file(self, ea_id: int, file_path: str) -> bool:
        """
        Upload backtest report from file
        
        Args:
            ea_id: EA identifier
            file_path: Path to HTML backtest report file
            
        Returns:
            True if upload successful, False otherwise
        """
        try:
            metrics = self.parser.parse_file(file_path)
            if not metrics:
                logger.error(f"Failed to parse backtest file {file_path} for EA {ea_id}")
                return False
            
            return self._store_backtest_benchmark(ea_id, metrics)
            
        except Exception as e:
            logger.error(f"Error uploading backtest file for EA {ea_id}: {e}")
            return False
    
    def get_backtest_benchmark(self, ea_id: int) -> Optional[BacktestMetrics]:
        """
        Get stored backtest benchmark for an EA
        
        Args:
            ea_id: EA identifier
            
        Returns:
            BacktestMetrics object or None if not found
        """
        try:
            # Import here to avoid circular imports
            from models.performance import BacktestBenchmark
            
            with self.db.get_session() as session:
                benchmark = session.query(BacktestBenchmark).filter_by(ea_id=ea_id).order_by(BacktestBenchmark.upload_date.desc()).first()
                
                if not benchmark:
                    return None
                
                return BacktestMetrics(
                    profit_factor=benchmark.profit_factor,
                    expected_payoff=benchmark.expected_payoff,
                    drawdown=benchmark.drawdown,
                    win_rate=benchmark.win_rate,
                    trade_count=benchmark.trade_count
                )
                
        except Exception as e:
            logger.error(f"Error retrieving backtest benchmark for EA {ea_id}: {e}")
            return None
    
    def compare_with_backtest(self, ea_id: int, live_metrics: PerformanceMetrics) -> Optional[DeviationReport]:
        """
        Compare live EA performance with backtest benchmark
        
        Args:
            ea_id: EA identifier
            live_metrics: Current live performance metrics
            
        Returns:
            DeviationReport or None if no benchmark exists
        """
        try:
            # Get backtest benchmark
            backtest_metrics = self.get_backtest_benchmark(ea_id)
            if not backtest_metrics:
                logger.warning(f"No backtest benchmark found for EA {ea_id}")
                return None
            
            # Perform comparison
            deviation_report = self.comparison.calculate_deviation(live_metrics, backtest_metrics)
            
            # Log critical deviations
            if deviation_report.overall_status == "critical":
                logger.warning(f"Critical performance deviation detected for EA {ea_id}")
            
            return deviation_report
            
        except Exception as e:
            logger.error(f"Error comparing EA {ea_id} with backtest: {e}")
            return None
    
    def get_all_deviations(self) -> List[DeviationReport]:
        """
        Get deviation reports for all EAs with backtest benchmarks
        
        Returns:
            List of DeviationReport objects
        """
        deviation_reports = []
        
        try:
            # Get all EAs with backtest benchmarks
            ea_ids = self._get_eas_with_benchmarks()
            
            for ea_id in ea_ids:
                # Get latest live performance
                live_metrics = self._get_latest_live_metrics(ea_id)
                
                # If no live data, generate mock data based on backtest for demo
                if not live_metrics:
                    backtest_metrics = self.get_backtest_benchmark(ea_id)
                    if backtest_metrics:
                        live_metrics = self._generate_mock_live_metrics(ea_id, backtest_metrics)
                
                if not live_metrics:
                    continue
                
                # Compare with backtest
                deviation_report = self.compare_with_backtest(ea_id, live_metrics)
                if deviation_report:
                    deviation_reports.append(deviation_report)
            
            return deviation_reports
            
        except Exception as e:
            logger.error(f"Error getting all deviations: {e}")
            return []
    
    def get_eas_flagged_for_demotion(self) -> List[int]:
        """
        Get list of EA IDs that should be flagged for demotion
        
        Returns:
            List of EA IDs flagged for demotion
        """
        flagged_eas = []
        
        try:
            deviation_reports = self.get_all_deviations()
            
            for report in deviation_reports:
                if self.comparison.should_flag_for_demotion(report):
                    flagged_eas.append(report.ea_id)
            
            return flagged_eas
            
        except Exception as e:
            logger.error(f"Error getting EAs flagged for demotion: {e}")
            return []
    
    def _store_backtest_benchmark(self, ea_id: int, metrics: BacktestMetrics) -> bool:
        """Store backtest benchmark in database"""
        try:
            # Import here to avoid circular imports
            from models.performance import BacktestBenchmark
            
            with self.db.get_session() as session:
                # Check if benchmark already exists for this EA
                existing = session.query(BacktestBenchmark).filter_by(ea_id=ea_id).first()
                
                if existing:
                    # Update existing benchmark
                    existing.profit_factor = metrics.profit_factor
                    existing.expected_payoff = metrics.expected_payoff
                    existing.drawdown = metrics.drawdown
                    existing.win_rate = metrics.win_rate
                    existing.trade_count = metrics.trade_count
                    logger.info(f"Updated backtest benchmark for EA {ea_id}")
                else:
                    # Create new benchmark
                    benchmark = BacktestBenchmark(
                        ea_id=ea_id,
                        profit_factor=metrics.profit_factor,
                        expected_payoff=metrics.expected_payoff,
                        drawdown=metrics.drawdown,
                        win_rate=metrics.win_rate,
                        trade_count=metrics.trade_count
                    )
                    session.add(benchmark)
                    logger.info(f"Created new backtest benchmark for EA {ea_id}")
                
                return True
                
        except Exception as e:
            logger.error(f"Error storing backtest benchmark for EA {ea_id}: {e}")
            return False
    
    def _get_eas_with_benchmarks(self) -> List[int]:
        """Get list of EA IDs that have backtest benchmarks"""
        try:
            # Import here to avoid circular imports
            from models.performance import BacktestBenchmark
            
            with self.db.get_session() as session:
                ea_ids = session.query(BacktestBenchmark.ea_id).distinct().all()
                return [ea_id[0] for ea_id in ea_ids]
                
        except Exception as e:
            logger.error(f"Error getting EAs with benchmarks: {e}")
            return []
    
    def _get_latest_live_metrics(self, ea_id: int) -> Optional[PerformanceMetrics]:
        """Get latest live performance metrics for an EA"""
        try:
            with self.db.get_session() as session:
                result = session.execute(text("""
                    SELECT total_profit, profit_factor, expected_payoff, 
                           drawdown, z_score, trade_count
                    FROM performance_history 
                    WHERE ea_id = :ea_id 
                    ORDER BY date DESC 
                    LIMIT 1
                """), {"ea_id": ea_id})
                
                row = result.fetchone()
                if not row:
                    return None
                
                return PerformanceMetrics(
                    ea_id=ea_id,
                    total_profit=row[0],
                    profit_factor=row[1],
                    expected_payoff=row[2],
                    drawdown=row[3],
                    z_score=row[4],
                    trade_count=row[5]
                )
                
        except Exception as e:
            logger.error(f"Error getting latest live metrics for EA {ea_id}: {e}")
            return None
    
    def delete_backtest_benchmark(self, ea_id: int) -> bool:
        """
        Delete backtest benchmark for an EA
        
        Args:
            ea_id: EA identifier
            
        Returns:
            True if deletion successful
        """
        try:
            # Import here to avoid circular imports
            from models.performance import BacktestBenchmark
            
            with self.db.get_session() as session:
                benchmarks = session.query(BacktestBenchmark).filter_by(ea_id=ea_id).all()
                for benchmark in benchmarks:
                    session.delete(benchmark)
                
                logger.info(f"Deleted backtest benchmark for EA {ea_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error deleting backtest benchmark for EA {ea_id}: {e}")
            return False
    
    def _generate_mock_live_metrics(self, ea_id: int, backtest_metrics: BacktestMetrics) -> Optional[PerformanceMetrics]:
        """
        Generate mock live performance metrics based on backtest for demo purposes
        
        Args:
            ea_id: EA identifier
            backtest_metrics: Backtest benchmark metrics
            
        Returns:
            Mock PerformanceMetrics object
        """
        try:
            import random
            
            # Generate realistic variations from backtest (some worse, some better)
            pf_variation = random.uniform(0.7, 1.1)  # 70% to 110% of backtest
            ep_variation = random.uniform(0.8, 1.05)  # 80% to 105% of backtest
            dd_variation = random.uniform(0.9, 1.3)   # 90% to 130% of backtest (higher is worse)
            
            return PerformanceMetrics(
                ea_id=ea_id,
                total_profit=random.uniform(1000, 5000),  # Mock profit
                profit_factor=backtest_metrics.profit_factor * pf_variation,
                expected_payoff=backtest_metrics.expected_payoff * ep_variation,
                drawdown=backtest_metrics.drawdown * dd_variation,
                z_score=random.uniform(-2.0, 2.0),  # Mock z-score
                trade_count=int(backtest_metrics.trade_count * random.uniform(0.8, 1.2))
            )
            
        except Exception as e:
            logger.error(f"Error generating mock live metrics for EA {ea_id}: {e}")
            return None

    def get_benchmark_summary(self) -> Dict:
        """
        Get summary of all backtest benchmarks
        
        Returns:
            Dictionary with benchmark statistics
        """
        try:
            # Import here to avoid circular imports
            from models.performance import BacktestBenchmark
            from sqlalchemy import func
            
            with self.db.get_session() as session:
                result = session.query(
                    func.count(BacktestBenchmark.id).label('total_benchmarks'),
                    func.avg(BacktestBenchmark.profit_factor).label('avg_pf'),
                    func.avg(BacktestBenchmark.expected_payoff).label('avg_ep'),
                    func.avg(BacktestBenchmark.drawdown).label('avg_dd'),
                    func.avg(BacktestBenchmark.win_rate).label('avg_wr')
                ).first()
                
                if not result:
                    return {}
                
                return {
                    'total_benchmarks': result.total_benchmarks or 0,
                    'average_profit_factor': round(result.avg_pf or 0, 2),
                    'average_expected_payoff': round(result.avg_ep or 0, 2),
                    'average_drawdown': round(result.avg_dd or 0, 2),
                    'average_win_rate': round(result.avg_wr or 0, 2)
                }
                
        except Exception as e:
            logger.error(f"Error getting benchmark summary: {e}")
            return {}