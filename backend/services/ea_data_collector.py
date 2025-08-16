"""
EA Data Collection and Processing Service

This module provides the EADataCollector class and related services for:
- Continuously polling MT5 Global Variables for EA data
- Validating and sanitizing incoming EA reports
- Calculating performance metrics (profit factor, drawdown, Z-score)
- Aggregating portfolio statistics
"""

import asyncio
import logging
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from services.mt5_communication import MT5CommunicationInterface, SoldierReport
from database.connection import get_db_session
from models.ea import EA, EAStatus
from models.performance import PerformanceHistory
from models.trade import Trade

logger = logging.getLogger(__name__)


@dataclass
class PortfolioMetrics:
    """Portfolio-level aggregated metrics"""
    total_profit: float
    total_drawdown: float
    win_rate: float
    total_trades: int
    active_eas: int
    total_eas: int
    profit_factor: float
    expected_payoff: float
    symbols: List[str]
    strategies: List[str]
    last_updated: datetime


@dataclass
class EAPerformanceMetrics:
    """Individual EA performance metrics"""
    magic_number: int
    total_profit: float
    profit_factor: float
    expected_payoff: float
    drawdown: float
    z_score: float
    win_rate: float
    trade_count: int
    last_calculated: datetime


class DataValidator:
    """Validates and sanitizes incoming EA report data"""
    
    @staticmethod
    def validate_soldier_report(report: SoldierReport) -> Tuple[bool, List[str]]:
        """
        Validate a SoldierReport for data integrity
        
        Args:
            report: SoldierReport to validate
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Validate magic number
        if not isinstance(report.magic_number, int) or report.magic_number <= 0:
            errors.append("Invalid magic_number: must be positive integer")
        
        # Validate symbol
        if not isinstance(report.symbol, str) or len(report.symbol) < 2:
            errors.append("Invalid symbol: must be non-empty string")
        
        # Validate strategy tag
        if not isinstance(report.strategy_tag, str) or len(report.strategy_tag) < 1:
            errors.append("Invalid strategy_tag: must be non-empty string")
        
        # Validate numeric fields
        numeric_fields = [
            ('current_profit', report.current_profit),
            ('sl_value', report.sl_value),
            ('tp_value', report.tp_value)
        ]
        
        for field_name, value in numeric_fields:
            if not isinstance(value, (int, float)):
                errors.append(f"Invalid {field_name}: must be numeric")
        
        # Validate integer fields
        if not isinstance(report.open_positions, int) or report.open_positions < 0:
            errors.append("Invalid open_positions: must be non-negative integer")
        
        # Validate boolean fields
        boolean_fields = [
            ('trailing_active', report.trailing_active),
            ('coc_override', report.coc_override)
        ]
        
        for field_name, value in boolean_fields:
            if not isinstance(value, bool):
                errors.append(f"Invalid {field_name}: must be boolean")
        
        # Validate module_status
        if not isinstance(report.module_status, dict):
            errors.append("Invalid module_status: must be dictionary")
        
        # Validate performance_metrics
        if not isinstance(report.performance_metrics, dict):
            errors.append("Invalid performance_metrics: must be dictionary")
        else:
            required_metrics = ['total_profit', 'profit_factor', 'expected_payoff', 'drawdown', 'z_score']
            for metric in required_metrics:
                if metric not in report.performance_metrics:
                    errors.append(f"Missing performance metric: {metric}")
                elif not isinstance(report.performance_metrics[metric], (int, float)):
                    errors.append(f"Invalid performance metric {metric}: must be numeric")
        
        # Validate last_trades
        if not isinstance(report.last_trades, list):
            errors.append("Invalid last_trades: must be list")
        
        # Validate timestamp
        if not isinstance(report.last_update, datetime):
            errors.append("Invalid last_update: must be datetime")
        else:
            # Check if timestamp is too old (more than 5 minutes)
            age = datetime.now() - report.last_update
            if age > timedelta(minutes=5):
                errors.append(f"Stale data: last_update is {age.total_seconds():.0f} seconds old")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def sanitize_soldier_report(report: SoldierReport) -> SoldierReport:
        """
        Sanitize a SoldierReport by cleaning and normalizing data
        
        Args:
            report: SoldierReport to sanitize
            
        Returns:
            Sanitized SoldierReport
        """
        # Create a copy to avoid modifying original
        sanitized = SoldierReport(
            magic_number=int(report.magic_number),
            symbol=str(report.symbol).upper().strip(),
            strategy_tag=str(report.strategy_tag).strip(),
            current_profit=round(float(report.current_profit), 2),
            open_positions=max(0, int(report.open_positions)),
            trade_status=str(report.trade_status).lower().strip(),
            sl_value=round(float(report.sl_value), 5),
            tp_value=round(float(report.tp_value), 5),
            trailing_active=bool(report.trailing_active),
            module_status=dict(report.module_status),
            performance_metrics={
                k: round(float(v), 4) if isinstance(v, (int, float)) else v
                for k, v in report.performance_metrics.items()
            },
            last_trades=list(report.last_trades),
            coc_override=bool(report.coc_override),
            last_update=report.last_update
        )
        
        return sanitized


class PerformanceCalculator:
    """Calculates performance metrics for EAs and portfolio"""
    
    @staticmethod
    def calculate_profit_factor(trades: List[Trade]) -> float:
        """
        Calculate profit factor from trades
        
        Args:
            trades: List of closed trades
            
        Returns:
            Profit factor (gross profit / gross loss)
        """
        if not trades:
            return 0.0
        
        closed_trades = [t for t in trades if t.is_closed]
        if not closed_trades:
            return 0.0
        
        winning_trades = [t for t in closed_trades if t.profit > 0]
        losing_trades = [t for t in closed_trades if t.profit < 0]
        
        gross_profit = sum(t.profit for t in winning_trades) if winning_trades else 0
        gross_loss = abs(sum(t.profit for t in losing_trades)) if losing_trades else 0
        
        if gross_loss == 0:
            return gross_profit if gross_profit > 0 else 0.0
        
        return round(gross_profit / gross_loss, 4)
    
    @staticmethod
    def calculate_expected_payoff(trades: List[Trade]) -> float:
        """
        Calculate expected payoff (average profit per trade)
        
        Args:
            trades: List of closed trades
            
        Returns:
            Expected payoff
        """
        if not trades:
            return 0.0
        
        closed_trades = [t for t in trades if t.is_closed]
        if not closed_trades:
            return 0.0
        
        total_profit = sum(t.profit for t in closed_trades)
        return round(total_profit / len(closed_trades), 4)
    
    @staticmethod
    def calculate_drawdown(trades: List[Trade]) -> float:
        """
        Calculate maximum drawdown from trades
        
        Args:
            trades: List of trades (sorted by close time)
            
        Returns:
            Maximum drawdown percentage
        """
        if not trades:
            return 0.0
        
        closed_trades = [t for t in trades if t.is_closed]
        if not closed_trades:
            return 0.0
        
        # Sort by close time
        sorted_trades = sorted(closed_trades, key=lambda x: x.close_time or x.open_time)
        
        # Calculate running balance
        running_balance = 0.0
        peak_balance = 0.0
        max_drawdown = 0.0
        
        for trade in sorted_trades:
            running_balance += trade.profit
            
            if running_balance > peak_balance:
                peak_balance = running_balance
            
            if peak_balance > 0:
                current_drawdown = ((peak_balance - running_balance) / peak_balance) * 100
                max_drawdown = max(max_drawdown, current_drawdown)
        
        return round(max_drawdown, 4)
    
    @staticmethod
    def calculate_z_score(trades: List[Trade]) -> float:
        """
        Calculate Z-score for trade sequence randomness
        
        Args:
            trades: List of closed trades
            
        Returns:
            Z-score value
        """
        if not trades:
            return 0.0
        
        closed_trades = [t for t in trades if t.is_closed]
        if len(closed_trades) < 2:
            return 0.0
        
        # Create win/loss sequence
        sequence = [1 if t.profit > 0 else 0 for t in closed_trades]
        
        # Count runs
        runs = 1
        for i in range(1, len(sequence)):
            if sequence[i] != sequence[i-1]:
                runs += 1
        
        # Count wins and losses
        wins = sum(sequence)
        losses = len(sequence) - wins
        
        if wins == 0 or losses == 0:
            return 0.0
        
        # Calculate expected runs and standard deviation
        n = len(sequence)
        expected_runs = ((2 * wins * losses) / n) + 1
        variance = ((2 * wins * losses) * (2 * wins * losses - n)) / (n * n * (n - 1))
        
        if variance <= 0:
            return 0.0
        
        std_dev = variance ** 0.5
        z_score = (runs - expected_runs) / std_dev
        
        return round(z_score, 4)
    
    @staticmethod
    def calculate_win_rate(trades: List[Trade]) -> float:
        """
        Calculate win rate percentage
        
        Args:
            trades: List of closed trades
            
        Returns:
            Win rate percentage
        """
        if not trades:
            return 0.0
        
        closed_trades = [t for t in trades if t.is_closed]
        if not closed_trades:
            return 0.0
        
        winning_trades = [t for t in closed_trades if t.profit > 0]
        win_rate = (len(winning_trades) / len(closed_trades)) * 100
        
        return round(win_rate, 2)


class EADataCollector:
    """
    Main EA data collection service that continuously polls MT5 Global Variables
    and processes EA reports
    """
    
    def __init__(self, 
                 mt5_interface: MT5CommunicationInterface = None,
                 collection_interval: int = 30,
                 max_retries: int = 3):
        """
        Initialize EA data collector
        
        Args:
            mt5_interface: MT5 communication interface
            collection_interval: Data collection interval in seconds
            max_retries: Maximum retries for failed operations
        """
        self.mt5_interface = mt5_interface or MT5CommunicationInterface()
        self.collection_interval = collection_interval
        self.max_retries = max_retries
        self.validator = DataValidator()
        self.calculator = PerformanceCalculator()
        
        self.is_running = False
        self.last_collection_time = None
        self.collection_stats = {
            'total_collections': 0,
            'successful_collections': 0,
            'failed_collections': 0,
            'validation_errors': 0,
            'last_error': None
        }
        
        logger.info(f"EADataCollector initialized with {collection_interval}s interval")
    
    async def start_collection(self):
        """Start continuous data collection"""
        if self.is_running:
            logger.warning("Data collection already running")
            return
        
        self.is_running = True
        logger.info("Starting EA data collection")
        
        try:
            while self.is_running:
                await self.collect_and_process_data()
                await asyncio.sleep(self.collection_interval)
        except Exception as e:
            logger.error(f"Data collection stopped due to error: {e}")
            self.is_running = False
            raise
    
    def stop_collection(self):
        """Stop continuous data collection"""
        self.is_running = False
        logger.info("Stopping EA data collection")
    
    async def collect_and_process_data(self) -> Dict[str, Any]:
        """
        Collect and process data from all EAs
        
        Returns:
            Dictionary with collection results
        """
        collection_start = datetime.now()
        self.collection_stats['total_collections'] += 1
        
        try:
            # Collect raw data from MT5
            raw_reports = self.mt5_interface.collect_ea_data()
            
            if not raw_reports:
                logger.debug("No EA data collected")
                return {'status': 'no_data', 'ea_count': 0}
            
            # Process each EA report
            processed_reports = {}
            validation_errors = []
            
            for magic_number, report in raw_reports.items():
                try:
                    # Validate report
                    is_valid, errors = self.validator.validate_soldier_report(report)
                    
                    if not is_valid:
                        validation_errors.extend([f"EA {magic_number}: {error}" for error in errors])
                        self.collection_stats['validation_errors'] += 1
                        continue
                    
                    # Sanitize report
                    sanitized_report = self.validator.sanitize_soldier_report(report)
                    
                    # Store in database
                    await self._store_ea_data(sanitized_report)
                    
                    processed_reports[magic_number] = sanitized_report
                    
                except Exception as e:
                    logger.error(f"Error processing EA {magic_number}: {e}")
                    validation_errors.append(f"EA {magic_number}: Processing error - {str(e)}")
            
            # Update performance metrics
            await self._update_performance_metrics(processed_reports)
            
            # Update collection stats
            self.collection_stats['successful_collections'] += 1
            self.last_collection_time = collection_start
            
            collection_time = (datetime.now() - collection_start).total_seconds()
            
            result = {
                'status': 'success',
                'ea_count': len(processed_reports),
                'validation_errors': validation_errors,
                'collection_time_seconds': round(collection_time, 3),
                'timestamp': collection_start.isoformat()
            }
            
            logger.debug(f"Data collection completed: {len(processed_reports)} EAs processed in {collection_time:.3f}s")
            return result
            
        except Exception as e:
            self.collection_stats['failed_collections'] += 1
            self.collection_stats['last_error'] = str(e)
            logger.error(f"Data collection failed: {e}")
            
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': collection_start.isoformat()
            }
    
    async def _store_ea_data(self, report: SoldierReport):
        """
        Store EA data in database
        
        Args:
            report: Sanitized SoldierReport
        """
        try:
            with get_db_session() as session:
                # Get or create EA record
                ea = session.query(EA).filter(EA.magic_number == report.magic_number).first()
                
                if not ea:
                    # Create new EA record
                    ea = EA(
                        magic_number=report.magic_number,
                        symbol=report.symbol,
                        strategy_tag=report.strategy_tag,
                        status='active'
                    )
                    session.add(ea)
                    session.flush()  # Get the ID
                    logger.info(f"Created new EA record: {report.magic_number}")
                else:
                    # Update existing EA
                    ea.symbol = report.symbol
                    ea.strategy_tag = report.strategy_tag
                    ea.last_seen = datetime.now()
                    ea.status = 'active'
                
                # Create EA status record
                ea_status = EAStatus(
                    ea_id=ea.id,
                    timestamp=report.last_update,
                    current_profit=report.current_profit,
                    open_positions=report.open_positions,
                    sl_value=report.sl_value,
                    tp_value=report.tp_value,
                    trailing_active=report.trailing_active
                )
                ea_status.set_module_status(report.module_status)
                
                session.add(ea_status)
                session.commit()
                
        except Exception as e:
            logger.error(f"Error storing EA data for {report.magic_number}: {e}")
            raise
    
    async def _update_performance_metrics(self, reports: Dict[int, SoldierReport]):
        """
        Update performance metrics for processed EAs
        
        Args:
            reports: Dictionary of processed SoldierReports
        """
        try:
            with get_db_session() as session:
                for magic_number, report in reports.items():
                    # Get EA record
                    ea = session.query(EA).filter(EA.magic_number == magic_number).first()
                    if not ea:
                        continue
                    
                    # Get recent trades for performance calculation
                    recent_trades = session.query(Trade).filter(
                        Trade.ea_id == ea.id,
                        Trade.close_time.isnot(None)
                    ).order_by(desc(Trade.close_time)).limit(100).all()
                    
                    if recent_trades:
                        # Calculate performance metrics
                        profit_factor = self.calculator.calculate_profit_factor(recent_trades)
                        expected_payoff = self.calculator.calculate_expected_payoff(recent_trades)
                        drawdown = self.calculator.calculate_drawdown(recent_trades)
                        z_score = self.calculator.calculate_z_score(recent_trades)
                        win_rate = self.calculator.calculate_win_rate(recent_trades)
                        total_profit = sum(t.profit for t in recent_trades)
                    else:
                        # Use metrics from report if no trades in database
                        metrics = report.performance_metrics
                        profit_factor = metrics.get('profit_factor', 0.0)
                        expected_payoff = metrics.get('expected_payoff', 0.0)
                        drawdown = metrics.get('drawdown', 0.0)
                        z_score = metrics.get('z_score', 0.0)
                        win_rate = 0.0
                        total_profit = metrics.get('total_profit', 0.0)
                    
                    # Create or update performance history
                    today = datetime.now().date()
                    perf_record = session.query(PerformanceHistory).filter(
                        PerformanceHistory.ea_id == ea.id,
                        PerformanceHistory.date == today
                    ).first()
                    
                    if perf_record:
                        # Update existing record
                        perf_record.total_profit = total_profit
                        perf_record.profit_factor = profit_factor
                        perf_record.expected_payoff = expected_payoff
                        perf_record.drawdown = drawdown
                        perf_record.z_score = z_score
                        perf_record.trade_count = len(recent_trades)
                    else:
                        # Create new record
                        perf_record = PerformanceHistory(
                            ea_id=ea.id,
                            date=today,
                            total_profit=total_profit,
                            profit_factor=profit_factor,
                            expected_payoff=expected_payoff,
                            drawdown=drawdown,
                            z_score=z_score,
                            trade_count=len(recent_trades)
                        )
                        session.add(perf_record)
                
                session.commit()
                
        except Exception as e:
            logger.error(f"Error updating performance metrics: {e}")
            raise
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get data collection statistics
        
        Returns:
            Dictionary with collection statistics
        """
        stats = self.collection_stats.copy()
        stats.update({
            'is_running': self.is_running,
            'collection_interval': self.collection_interval,
            'last_collection_time': self.last_collection_time.isoformat() if self.last_collection_time else None,
            'success_rate': (
                (stats['successful_collections'] / stats['total_collections'] * 100)
                if stats['total_collections'] > 0 else 0
            )
        })
        return stats


class PortfolioAggregator:
    """
    Service for calculating portfolio-level aggregated statistics
    """
    
    def __init__(self):
        self.calculator = PerformanceCalculator()
        logger.info("PortfolioAggregator initialized")
    
    async def calculate_portfolio_metrics(self, 
                                        symbol_filter: str = None,
                                        strategy_filter: str = None,
                                        risk_filter: float = None) -> PortfolioMetrics:
        """
        Calculate aggregated portfolio metrics with optional filters
        
        Args:
            symbol_filter: Filter by symbol (e.g., 'EURUSD')
            strategy_filter: Filter by strategy tag
            risk_filter: Filter by risk configuration
            
        Returns:
            PortfolioMetrics object
        """
        try:
            with get_db_session() as session:
                # Build base query
                ea_query = session.query(EA).filter(EA.status == 'active')
                
                # Apply filters
                if symbol_filter:
                    ea_query = ea_query.filter(EA.symbol == symbol_filter)
                if strategy_filter:
                    ea_query = ea_query.filter(EA.strategy_tag.like(f'%{strategy_filter}%'))
                if risk_filter is not None:
                    ea_query = ea_query.filter(EA.risk_config == risk_filter)
                
                active_eas = ea_query.all()
                
                if not active_eas:
                    return PortfolioMetrics(
                        total_profit=0.0,
                        total_drawdown=0.0,
                        win_rate=0.0,
                        total_trades=0,
                        active_eas=0,
                        total_eas=0,
                        profit_factor=0.0,
                        expected_payoff=0.0,
                        symbols=[],
                        strategies=[],
                        last_updated=datetime.now()
                    )
                
                # Get all trades for active EAs
                ea_ids = [ea.id for ea in active_eas]
                all_trades = session.query(Trade).filter(
                    Trade.ea_id.in_(ea_ids),
                    Trade.close_time.isnot(None)
                ).all()
                
                # Calculate aggregated metrics
                total_profit = sum(t.profit for t in all_trades)
                profit_factor = self.calculator.calculate_profit_factor(all_trades)
                expected_payoff = self.calculator.calculate_expected_payoff(all_trades)
                win_rate = self.calculator.calculate_win_rate(all_trades)
                
                # Calculate portfolio drawdown (max drawdown across all EAs)
                max_drawdown = 0.0
                for ea in active_eas:
                    ea_trades = [t for t in all_trades if t.ea_id == ea.id]
                    if ea_trades:
                        ea_drawdown = self.calculator.calculate_drawdown(ea_trades)
                        max_drawdown = max(max_drawdown, ea_drawdown)
                
                # Get unique symbols and strategies
                symbols = list(set(ea.symbol for ea in active_eas))
                strategies = list(set(ea.strategy_tag for ea in active_eas))
                
                # Get total EA count (including inactive)
                total_ea_count = session.query(EA).count()
                
                return PortfolioMetrics(
                    total_profit=round(total_profit, 2),
                    total_drawdown=round(max_drawdown, 2),
                    win_rate=round(win_rate, 2),
                    total_trades=len(all_trades),
                    active_eas=len(active_eas),
                    total_eas=total_ea_count,
                    profit_factor=round(profit_factor, 4),
                    expected_payoff=round(expected_payoff, 4),
                    symbols=sorted(symbols),
                    strategies=sorted(strategies),
                    last_updated=datetime.now()
                )
                
        except Exception as e:
            logger.error(f"Error calculating portfolio metrics: {e}")
            raise
    
    async def get_performance_breakdown(self) -> Dict[str, Any]:
        """
        Get detailed performance breakdown by symbol and strategy
        
        Returns:
            Dictionary with performance breakdown
        """
        try:
            with get_db_session() as session:
                # Get performance by symbol
                symbol_performance = {}
                symbols = session.query(EA.symbol).distinct().all()
                
                for (symbol,) in symbols:
                    symbol_metrics = await self.calculate_portfolio_metrics(symbol_filter=symbol)
                    symbol_performance[symbol] = {
                        'total_profit': symbol_metrics.total_profit,
                        'profit_factor': symbol_metrics.profit_factor,
                        'win_rate': symbol_metrics.win_rate,
                        'active_eas': symbol_metrics.active_eas,
                        'total_trades': symbol_metrics.total_trades
                    }
                
                # Get performance by strategy
                strategy_performance = {}
                strategies = session.query(EA.strategy_tag).distinct().all()
                
                for (strategy,) in strategies:
                    strategy_metrics = await self.calculate_portfolio_metrics(strategy_filter=strategy)
                    strategy_performance[strategy] = {
                        'total_profit': strategy_metrics.total_profit,
                        'profit_factor': strategy_metrics.profit_factor,
                        'win_rate': strategy_metrics.win_rate,
                        'active_eas': strategy_metrics.active_eas,
                        'total_trades': strategy_metrics.total_trades
                    }
                
                return {
                    'by_symbol': symbol_performance,
                    'by_strategy': strategy_performance,
                    'last_updated': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error getting performance breakdown: {e}")
            raise
    
    async def get_ea_performance_metrics(self, magic_number: int = None) -> List[EAPerformanceMetrics]:
        """
        Get performance metrics for specific EA or all EAs
        
        Args:
            magic_number: Optional EA magic number filter
            
        Returns:
            List of EAPerformanceMetrics
        """
        try:
            with get_db_session() as session:
                # Build query
                ea_query = session.query(EA)
                if magic_number:
                    ea_query = ea_query.filter(EA.magic_number == magic_number)
                
                eas = ea_query.all()
                metrics_list = []
                
                for ea in eas:
                    # Get recent trades
                    trades = session.query(Trade).filter(
                        Trade.ea_id == ea.id,
                        Trade.close_time.isnot(None)
                    ).order_by(desc(Trade.close_time)).limit(100).all()
                    
                    if trades:
                        # Calculate metrics
                        total_profit = sum(t.profit for t in trades)
                        profit_factor = self.calculator.calculate_profit_factor(trades)
                        expected_payoff = self.calculator.calculate_expected_payoff(trades)
                        drawdown = self.calculator.calculate_drawdown(trades)
                        z_score = self.calculator.calculate_z_score(trades)
                        win_rate = self.calculator.calculate_win_rate(trades)
                        
                        metrics = EAPerformanceMetrics(
                            magic_number=ea.magic_number,
                            total_profit=round(total_profit, 2),
                            profit_factor=round(profit_factor, 4),
                            expected_payoff=round(expected_payoff, 4),
                            drawdown=round(drawdown, 2),
                            z_score=round(z_score, 4),
                            win_rate=round(win_rate, 2),
                            trade_count=len(trades),
                            last_calculated=datetime.now()
                        )
                        
                        metrics_list.append(metrics)
                
                return metrics_list
                
        except Exception as e:
            logger.error(f"Error getting EA performance metrics: {e}")
            raise