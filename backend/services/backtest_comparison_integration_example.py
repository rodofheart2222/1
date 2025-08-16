"""
Backtest Comparison Integration Example

This example demonstrates how to integrate the backtest comparison functionality
into the main MT5 dashboard system, including real-time monitoring and alerting.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from .backtest_service import BacktestService
from .ea_data_collector import EADataCollector
from .websocket_server import WebSocketServer
from ..database.connection import DatabaseManager
from ..models.performance import PerformanceMetrics

logger = logging.getLogger(__name__)

class BacktestComparisonIntegration:
    """
    Integration service for backtest comparison functionality
    """
    
    def __init__(self, db_manager: DatabaseManager, websocket_server: WebSocketServer):
        self.db = db_manager
        self.websocket = websocket_server
        self.backtest_service = BacktestService(db_manager)
        self.ea_collector = EADataCollector(db_manager)
        
        # Configuration
        self.monitoring_interval = 300  # 5 minutes
        self.alert_cooldown = 3600  # 1 hour between same alerts
        self.last_alerts = {}  # Track last alert times
        
        # Performance thresholds for auto-actions
        self.auto_flag_thresholds = {
            'profit_factor_drop': -30.0,  # Auto-flag if PF drops >30%
            'multiple_critical_alerts': 2,  # Auto-flag if 2+ critical alerts
            'consecutive_degradation_days': 3  # Auto-flag after 3 days of degradation
        }
    
    async def start_monitoring(self):
        """Start continuous monitoring of backtest deviations"""
        logger.info("Starting backtest comparison monitoring")
        
        while True:
            try:
                await self.monitor_performance_deviations()
                await asyncio.sleep(self.monitoring_interval)
            except Exception as e:
                logger.error(f"Error in backtest monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying
    
    async def monitor_performance_deviations(self):
        """Monitor all EAs for performance deviations from backtest benchmarks"""
        try:
            # Get all deviation reports
            deviation_reports = self.backtest_service.get_all_deviations()
            
            if not deviation_reports:
                logger.debug("No deviation reports to monitor")
                return
            
            # Process each deviation report
            for report in deviation_reports:
                await self.process_deviation_report(report)
            
            # Broadcast updated deviation data to frontend
            await self.broadcast_deviation_updates(deviation_reports)
            
            logger.info(f"Monitored {len(deviation_reports)} EAs for backtest deviations")
            
        except Exception as e:
            logger.error(f"Error monitoring performance deviations: {e}")
    
    async def process_deviation_report(self, report):
        """Process individual deviation report and take appropriate actions"""
        try:
            ea_id = report.ea_id
            
            # Check if EA should be auto-flagged
            if self.should_auto_flag_ea(report):
                await self.auto_flag_ea_for_demotion(report)
            
            # Send alerts for critical deviations
            if report.overall_status == 'critical':
                await self.send_critical_deviation_alert(report)
            
            # Check for consecutive degradation
            await self.track_performance_degradation(report)
            
        except Exception as e:
            logger.error(f"Error processing deviation report for EA {report.ea_id}: {e}")
    
    def should_auto_flag_ea(self, report) -> bool:
        """Determine if EA should be automatically flagged for demotion"""
        # Check profit factor drop threshold
        if report.profit_factor_deviation <= self.auto_flag_thresholds['profit_factor_drop']:
            logger.warning(f"EA {report.ea_id} profit factor dropped {abs(report.profit_factor_deviation):.1f}%")
            return True
        
        # Check multiple critical alerts
        critical_alerts = [a for a in report.alerts if a.alert_level.value == 'critical']
        if len(critical_alerts) >= self.auto_flag_thresholds['multiple_critical_alerts']:
            logger.warning(f"EA {report.ea_id} has {len(critical_alerts)} critical alerts")
            return True
        
        return False
    
    async def auto_flag_ea_for_demotion(self, report):
        """Automatically flag EA for demotion due to poor performance"""
        try:
            ea_id = report.ea_id
            
            # Check if already flagged recently
            if self.is_recently_flagged(ea_id):
                return
            
            # Create flag command
            flag_command = {
                'type': 'flag_demotion',
                'ea_id': ea_id,
                'reason': f'Auto-flagged: {report.recommendation}',
                'deviation_report': report.to_dict(),
                'timestamp': datetime.now().isoformat(),
                'auto_generated': True
            }
            
            # Store flag in database (assuming command queue table exists)
            await self.store_flag_command(flag_command)
            
            # Broadcast flag notification
            await self.websocket.broadcast_message({
                'type': 'ea_auto_flagged',
                'data': flag_command
            })
            
            # Update last flagged time
            self.last_alerts[f"flag_{ea_id}"] = datetime.now()
            
            logger.warning(f"Auto-flagged EA {ea_id} for demotion")
            
        except Exception as e:
            logger.error(f"Error auto-flagging EA {report.ea_id}: {e}")
    
    async def send_critical_deviation_alert(self, report):
        """Send alert for critical performance deviation"""
        try:
            ea_id = report.ea_id
            alert_key = f"critical_{ea_id}"
            
            # Check alert cooldown
            if self.is_alert_on_cooldown(alert_key):
                return
            
            # Create alert message
            alert_message = {
                'type': 'critical_deviation_alert',
                'ea_id': ea_id,
                'status': report.overall_status,
                'message': f"Critical performance deviation detected for EA {ea_id}",
                'alerts': [alert.to_dict() for alert in report.alerts],
                'recommendation': report.recommendation,
                'timestamp': datetime.now().isoformat()
            }
            
            # Broadcast alert
            await self.websocket.broadcast_message({
                'type': 'performance_alert',
                'data': alert_message
            })
            
            # Update last alert time
            self.last_alerts[alert_key] = datetime.now()
            
            logger.warning(f"Sent critical deviation alert for EA {ea_id}")
            
        except Exception as e:
            logger.error(f"Error sending critical deviation alert for EA {report.ea_id}: {e}")
    
    async def track_performance_degradation(self, report):
        """Track consecutive days of performance degradation"""
        try:
            ea_id = report.ea_id
            
            # Store daily performance status
            await self.store_daily_performance_status(ea_id, report.overall_status)
            
            # Check for consecutive degradation
            consecutive_days = await self.get_consecutive_degradation_days(ea_id)
            
            if consecutive_days >= self.auto_flag_thresholds['consecutive_degradation_days']:
                logger.warning(f"EA {ea_id} has {consecutive_days} consecutive days of degradation")
                
                # Auto-flag if not already flagged
                if not self.is_recently_flagged(ea_id):
                    await self.auto_flag_ea_for_demotion(report)
            
        except Exception as e:
            logger.error(f"Error tracking performance degradation for EA {report.ea_id}: {e}")
    
    async def broadcast_deviation_updates(self, deviation_reports):
        """Broadcast updated deviation data to connected clients"""
        try:
            # Prepare summary data
            summary_data = {
                'total_monitored': len(deviation_reports),
                'critical_count': len([r for r in deviation_reports if r.overall_status == 'critical']),
                'warning_count': len([r for r in deviation_reports if r.overall_status == 'warning']),
                'good_count': len([r for r in deviation_reports if r.overall_status == 'good']),
                'flagged_eas': self.backtest_service.get_eas_flagged_for_demotion()
            }
            
            # Broadcast update
            await self.websocket.broadcast_message({
                'type': 'backtest_deviation_update',
                'data': {
                    'summary': summary_data,
                    'reports': [report.to_dict() for report in deviation_reports],
                    'timestamp': datetime.now().isoformat()
                }
            })
            
        except Exception as e:
            logger.error(f"Error broadcasting deviation updates: {e}")
    
    def is_recently_flagged(self, ea_id: int) -> bool:
        """Check if EA was recently flagged to avoid duplicate flags"""
        flag_key = f"flag_{ea_id}"
        if flag_key not in self.last_alerts:
            return False
        
        last_flag_time = self.last_alerts[flag_key]
        return (datetime.now() - last_flag_time).total_seconds() < 86400  # 24 hours
    
    def is_alert_on_cooldown(self, alert_key: str) -> bool:
        """Check if alert is on cooldown to prevent spam"""
        if alert_key not in self.last_alerts:
            return False
        
        last_alert_time = self.last_alerts[alert_key]
        return (datetime.now() - last_alert_time).total_seconds() < self.alert_cooldown
    
    async def store_flag_command(self, flag_command: Dict):
        """Store flag command in database"""
        try:
            with self.db.get_session() as session:
                session.execute("""
                    INSERT INTO command_queue 
                    (ea_id, command_type, command_data, scheduled_time, executed)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    flag_command['ea_id'],
                    flag_command['type'],
                    str(flag_command),  # JSON string
                    datetime.now(),
                    False
                ))
                
        except Exception as e:
            logger.error(f"Error storing flag command: {e}")
    
    async def store_daily_performance_status(self, ea_id: int, status: str):
        """Store daily performance status for trend tracking"""
        try:
            today = datetime.now().date()
            
            with self.db.get_session() as session:
                # Check if record exists for today
                existing = session.execute("""
                    SELECT id FROM daily_performance_status 
                    WHERE ea_id = ? AND date = ?
                """, (ea_id, today)).fetchone()
                
                if existing:
                    # Update existing record
                    session.execute("""
                        UPDATE daily_performance_status 
                        SET status = ?, updated_at = ?
                        WHERE ea_id = ? AND date = ?
                    """, (status, datetime.now(), ea_id, today))
                else:
                    # Insert new record
                    session.execute("""
                        INSERT INTO daily_performance_status 
                        (ea_id, date, status, created_at)
                        VALUES (?, ?, ?, ?)
                    """, (ea_id, today, status, datetime.now()))
                
        except Exception as e:
            logger.error(f"Error storing daily performance status: {e}")
    
    async def get_consecutive_degradation_days(self, ea_id: int) -> int:
        """Get number of consecutive days with warning/critical status"""
        try:
            with self.db.get_session() as session:
                # Get last 7 days of performance status
                seven_days_ago = datetime.now().date() - timedelta(days=7)
                
                results = session.execute("""
                    SELECT date, status FROM daily_performance_status 
                    WHERE ea_id = ? AND date >= ?
                    ORDER BY date DESC
                """, (ea_id, seven_days_ago)).fetchall()
                
                # Count consecutive degradation days from most recent
                consecutive_days = 0
                for date, status in results:
                    if status in ['warning', 'critical']:
                        consecutive_days += 1
                    else:
                        break
                
                return consecutive_days
                
        except Exception as e:
            logger.error(f"Error getting consecutive degradation days: {e}")
            return 0
    
    async def handle_manual_backtest_upload(self, ea_id: int, html_content: str) -> Dict:
        """Handle manual backtest report upload from frontend"""
        try:
            # Upload and parse report
            success = self.backtest_service.upload_backtest_report(ea_id, html_content)
            
            if not success:
                return {
                    'success': False,
                    'error': 'Failed to parse backtest report'
                }
            
            # Get updated deviation report
            live_metrics = self.backtest_service._get_latest_live_metrics(ea_id)
            if live_metrics:
                deviation_report = self.backtest_service.compare_with_backtest(ea_id, live_metrics)
                
                # Broadcast update
                if deviation_report:
                    await self.websocket.broadcast_message({
                        'type': 'backtest_uploaded',
                        'data': {
                            'ea_id': ea_id,
                            'deviation_report': deviation_report.to_dict(),
                            'timestamp': datetime.now().isoformat()
                        }
                    })
            
            return {
                'success': True,
                'message': 'Backtest report uploaded successfully',
                'ea_id': ea_id
            }
            
        except Exception as e:
            logger.error(f"Error handling manual backtest upload: {e}")
            return {
                'success': False,
                'error': 'Internal server error'
            }

# Example usage
async def main():
    """Example of how to integrate backtest comparison monitoring"""
    
    # Initialize components
    db_manager = DatabaseManager()
    websocket_server = WebSocketServer()
    
    # Create integration service
    backtest_integration = BacktestComparisonIntegration(db_manager, websocket_server)
    
    # Start monitoring in background
    monitoring_task = asyncio.create_task(backtest_integration.start_monitoring())
    
    # Start WebSocket server
    websocket_task = asyncio.create_task(websocket_server.start_server())
    
    # Run both tasks
    await asyncio.gather(monitoring_task, websocket_task)

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run the integration
    asyncio.run(main())