"""
Backtest Comparison Service

This module handles comparison between live EA performance and backtest benchmarks,
calculates deviations, and generates alerts for performance degradation.
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging
from datetime import datetime

from .backtest_parser import BacktestMetrics
from models.performance import PerformanceMetrics

logger = logging.getLogger(__name__)

class AlertLevel(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"

@dataclass
class DeviationAlert:
    """Alert for performance deviation"""
    ea_id: int
    metric_name: str
    live_value: float
    backtest_value: float
    deviation_percent: float
    alert_level: AlertLevel
    message: str
    timestamp: datetime
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for API responses"""
        return {
            'ea_id': self.ea_id,
            'metric_name': self.metric_name,
            'live_value': self.live_value,
            'backtest_value': self.backtest_value,
            'deviation_percent': self.deviation_percent,
            'alert_level': self.alert_level.value,
            'message': self.message,
            'timestamp': self.timestamp.isoformat()
        }

@dataclass
class DeviationReport:
    """Complete deviation analysis report"""
    ea_id: int
    overall_status: str  # "good", "warning", "critical"
    profit_factor_deviation: float
    expected_payoff_deviation: float
    drawdown_deviation: float
    win_rate_deviation: float
    alerts: List[DeviationAlert]
    recommendation: str  # Action recommendation
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for API responses"""
        return {
            'ea_id': self.ea_id,
            'overall_status': self.overall_status,
            'profit_factor_deviation': self.profit_factor_deviation,
            'expected_payoff_deviation': self.expected_payoff_deviation,
            'drawdown_deviation': self.drawdown_deviation,
            'win_rate_deviation': self.win_rate_deviation,
            'alerts': [alert.to_dict() for alert in self.alerts],
            'recommendation': self.recommendation
        }

class BacktestComparison:
    """Service for comparing live performance with backtest benchmarks"""
    
    def __init__(self):
        # Performance deviation thresholds
        self.thresholds = {
            'profit_factor': {
                'warning': 15.0,  # 15% deviation triggers warning
                'critical': 30.0  # 30% deviation triggers critical alert
            },
            'expected_payoff': {
                'warning': 20.0,
                'critical': 40.0
            },
            'drawdown': {
                'warning': 25.0,  # Drawdown increase of 25% is concerning
                'critical': 50.0
            },
            'win_rate': {
                'warning': 10.0,
                'critical': 20.0
            }
        }
    
    def calculate_deviation(self, live_metrics: PerformanceMetrics, 
                          backtest_metrics: BacktestMetrics) -> DeviationReport:
        """
        Calculate performance deviations between live and backtest metrics
        
        Args:
            live_metrics: Current live performance metrics
            backtest_metrics: Backtest benchmark metrics
            
        Returns:
            DeviationReport with detailed analysis
        """
        alerts = []
        
        # Calculate individual metric deviations
        pf_deviation = self._calculate_percentage_deviation(
            live_metrics.profit_factor, backtest_metrics.profit_factor
        )
        
        ep_deviation = self._calculate_percentage_deviation(
            live_metrics.expected_payoff, backtest_metrics.expected_payoff
        )
        
        # For drawdown, we want to alert when live drawdown is HIGHER than backtest
        dd_deviation = self._calculate_drawdown_deviation(
            live_metrics.drawdown, backtest_metrics.drawdown
        )
        
        wr_deviation = self._calculate_percentage_deviation(
            live_metrics.win_rate if hasattr(live_metrics, 'win_rate') else 0.0,
            backtest_metrics.win_rate
        )
        
        # Generate alerts for each metric
        alerts.extend(self._check_metric_deviation(
            live_metrics.ea_id, 'profit_factor', 
            live_metrics.profit_factor, backtest_metrics.profit_factor, pf_deviation
        ))
        
        alerts.extend(self._check_metric_deviation(
            live_metrics.ea_id, 'expected_payoff',
            live_metrics.expected_payoff, backtest_metrics.expected_payoff, ep_deviation
        ))
        
        alerts.extend(self._check_drawdown_deviation(
            live_metrics.ea_id, live_metrics.drawdown, backtest_metrics.drawdown, dd_deviation
        ))
        
        # Determine overall status
        overall_status = self._determine_overall_status(alerts)
        
        # Generate recommendation
        recommendation = self._generate_recommendation(overall_status, alerts)
        
        return DeviationReport(
            ea_id=live_metrics.ea_id,
            overall_status=overall_status,
            profit_factor_deviation=pf_deviation,
            expected_payoff_deviation=ep_deviation,
            drawdown_deviation=dd_deviation,
            win_rate_deviation=wr_deviation,
            alerts=alerts,
            recommendation=recommendation
        )
    
    def _calculate_percentage_deviation(self, live_value: float, backtest_value: float) -> float:
        """Calculate percentage deviation (negative means live is worse)"""
        if backtest_value == 0:
            return 0.0
        return ((live_value - backtest_value) / backtest_value) * 100
    
    def _calculate_drawdown_deviation(self, live_dd: float, backtest_dd: float) -> float:
        """Calculate drawdown deviation (positive means live drawdown is higher)"""
        return live_dd - backtest_dd
    
    def _check_metric_deviation(self, ea_id: int, metric_name: str, 
                              live_value: float, backtest_value: float, 
                              deviation: float) -> List[DeviationAlert]:
        """Check if metric deviation exceeds thresholds and generate alerts"""
        alerts = []
        
        if metric_name not in self.thresholds:
            return alerts
        
        thresholds = self.thresholds[metric_name]
        abs_deviation = abs(deviation)
        
        if abs_deviation >= thresholds['critical']:
            alert_level = AlertLevel.CRITICAL
            if deviation < 0:
                message = f" Live {metric_name} down {abs_deviation:.1f}% from backtest"
            else:
                message = f"🟢 Live {metric_name} up {abs_deviation:.1f}% from backtest"
        elif abs_deviation >= thresholds['warning']:
            alert_level = AlertLevel.WARNING
            if deviation < 0:
                message = f"🟡 Live {metric_name} down {abs_deviation:.1f}% from backtest"
            else:
                message = f"🟡 Live {metric_name} up {abs_deviation:.1f}% from backtest"
        else:
            return alerts  # No alert needed
        
        alerts.append(DeviationAlert(
            ea_id=ea_id,
            metric_name=metric_name,
            live_value=live_value,
            backtest_value=backtest_value,
            deviation_percent=deviation,
            alert_level=alert_level,
            message=message,
            timestamp=datetime.now()
        ))
        
        return alerts
    
    def _check_drawdown_deviation(self, ea_id: int, live_dd: float, 
                                backtest_dd: float, deviation: float) -> List[DeviationAlert]:
        """Check drawdown deviation (higher live drawdown is bad)"""
        alerts = []
        
        if deviation <= 0:
            return alerts  # Live drawdown is better or same as backtest
        
        deviation_percent = (deviation / backtest_dd) * 100 if backtest_dd > 0 else 0
        
        if deviation_percent >= self.thresholds['drawdown']['critical']:
            alert_level = AlertLevel.CRITICAL
            message = f" Live drawdown {deviation_percent:.1f}% higher than backtest"
        elif deviation_percent >= self.thresholds['drawdown']['warning']:
            alert_level = AlertLevel.WARNING
            message = f"🟡 Live drawdown {deviation_percent:.1f}% higher than backtest"
        else:
            return alerts
        
        alerts.append(DeviationAlert(
            ea_id=ea_id,
            metric_name='drawdown',
            live_value=live_dd,
            backtest_value=backtest_dd,
            deviation_percent=deviation_percent,
            alert_level=alert_level,
            message=message,
            timestamp=datetime.now()
        ))
        
        return alerts
    
    def _determine_overall_status(self, alerts: List[DeviationAlert]) -> str:
        """Determine overall EA status based on alerts"""
        if any(alert.alert_level == AlertLevel.CRITICAL for alert in alerts):
            return "critical"
        elif any(alert.alert_level == AlertLevel.WARNING for alert in alerts):
            return "warning"
        else:
            return "good"
    
    def _generate_recommendation(self, status: str, alerts: List[DeviationAlert]) -> str:
        """Generate action recommendation based on status and alerts"""
        if status == "critical":
            critical_alerts = [a for a in alerts if a.alert_level == AlertLevel.CRITICAL]
            if len(critical_alerts) >= 2:
                return "IMMEDIATE ACTION: Consider EA demotion or shutdown"
            else:
                return "URGENT: Review EA settings and consider risk reduction"
        elif status == "warning":
            return "MONITOR: Watch closely for further degradation"
        else:
            return "CONTINUE: Performance within acceptable range"
    
    def should_flag_for_demotion(self, deviation_report: DeviationReport) -> bool:
        """
        Determine if EA should be flagged for demotion based on performance
        
        Args:
            deviation_report: Complete deviation analysis
            
        Returns:
            True if EA should be flagged for demotion
        """
        # Flag for demotion if:
        # 1. Overall status is critical
        # 2. Multiple critical alerts
        # 3. Profit factor down more than 30%
        
        if deviation_report.overall_status == "critical":
            return True
        
        critical_alerts = [a for a in deviation_report.alerts 
                          if a.alert_level == AlertLevel.CRITICAL]
        
        if len(critical_alerts) >= 2:
            return True
        
        # Check specific profit factor threshold
        if deviation_report.profit_factor_deviation <= -30.0:
            return True
        
        return False
    
    def get_visual_indicator(self, deviation_report: DeviationReport) -> str:
        """Get visual indicator emoji for dashboard display"""
        if deviation_report.overall_status == "critical":
            return "🔴"
        elif deviation_report.overall_status == "warning":
            return "🟡"
        else:
            return "🟢"