"""
News Service Integration Example

This example demonstrates how to integrate the news event filtering system
with the MT5 COC Dashboard system.
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any

from .news_service import NewsEventFilter, NewsEventScheduler
from .ea_data_collector import EADataCollector
from .command_dispatcher import CommandDispatcher
from ..database.connection import get_db_session


class NewsIntegratedTradingManager:
    """
    Integrated trading manager that combines news filtering with EA management
    """
    
    def __init__(self):
        self.db_session = None  # Will use context managers instead
        self.news_filter = NewsEventFilter(self.db_session)
        self.news_scheduler = NewsEventScheduler()
        self.ea_collector = EADataCollector()
        self.command_dispatcher = CommandDispatcher()
        
        # Configuration
        self.auto_pause_on_news = True
        self.high_impact_symbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'XAUUSD']
        self.news_check_interval = 60  # seconds
    
    async def start_news_monitoring(self):
        """Start continuous news monitoring and EA management"""
        print("Starting news-integrated trading monitoring...")
        
        while True:
            try:
                await self.check_and_handle_news_events()
                await asyncio.sleep(self.news_check_interval)
                
            except Exception as e:
                print(f"Error in news monitoring loop: {e}")
                await asyncio.sleep(30)  # Wait before retrying
    
    async def check_and_handle_news_events(self):
        """Check for news events and handle EA pausing/resuming"""
        current_time = datetime.now()
        
        # Check for emergency high-impact events
        emergency_alerts = self.news_scheduler.emergency_news_check()
        
        if emergency_alerts:
            await self.handle_emergency_news_alerts(emergency_alerts)
        
        # Check trading status for all active symbols
        active_eas = self.ea_collector.get_active_eas()
        
        for ea_data in active_eas:
            symbol = ea_data.get('symbol')
            if not symbol:
                continue
            
            trading_status = self.news_filter.check_trading_allowed(symbol, current_time)
            
            if not trading_status['trading_allowed']:
                await self.handle_trading_restriction(ea_data, trading_status)
            else:
                await self.handle_trading_allowed(ea_data, trading_status)
    
    async def handle_emergency_news_alerts(self, alerts: List[Dict[str, Any]]):
        """Handle emergency high-impact news alerts"""
        for alert in alerts:
            print(f"EMERGENCY NEWS ALERT: {alert['message']}")
            
            if alert['type'] == 'ACTIVE_BLACKOUT':
                # Immediately pause all affected EAs
                event_data = alert['event']
                affected_symbols = self.get_affected_symbols(event_data['currency'])
                
                await self.pause_eas_by_symbols(affected_symbols, reason="Emergency news blackout")
                
            elif alert['type'] == 'UPCOMING_BLACKOUT':
                # Send warning and prepare for upcoming blackout
                event_data = alert['event']
                affected_symbols = self.get_affected_symbols(event_data['currency'])
                
                await self.send_news_warning(affected_symbols, alert)
    
    async def handle_trading_restriction(self, ea_data: Dict[str, Any], trading_status: Dict[str, Any]):
        """Handle when trading is restricted due to news"""
        ea_id = ea_data.get('magic_number')
        symbol = ea_data.get('symbol')
        
        if not ea_id or not symbol:
            return
        
        # Check if EA is already paused for news
        if ea_data.get('status') == 'news_paused':
            return  # Already handled
        
        print(f"Pausing EA {ea_id} ({symbol}) due to news restrictions")
        
        # Get the highest impact restriction
        highest_impact = trading_status.get('highest_impact_level', 'unknown')
        active_restrictions = trading_status.get('active_restrictions', [])
        
        # Create pause command with news context
        pause_command = {
            'command_type': 'pause',
            'parameters': {
                'reason': 'news_restriction',
                'impact_level': highest_impact,
                'restrictions': active_restrictions,
                'auto_resume': True
            },
            'target_eas': [ea_id],
            'execution_time': datetime.now()
        }
        
        await self.command_dispatcher.queue_command(pause_command)
        
        # Log the action
        self.log_news_action(ea_id, symbol, 'PAUSED', trading_status)
    
    async def handle_trading_allowed(self, ea_data: Dict[str, Any], trading_status: Dict[str, Any]):
        """Handle when trading is allowed (resume if previously paused for news)"""
        ea_id = ea_data.get('magic_number')
        symbol = ea_data.get('symbol')
        
        if not ea_id or not symbol:
            return
        
        # Check if EA was paused for news and should be resumed
        if ea_data.get('status') == 'news_paused':
            print(f"Resuming EA {ea_id} ({symbol}) - news restrictions lifted")
            
            # Create resume command
            resume_command = {
                'command_type': 'resume',
                'parameters': {
                    'reason': 'news_restriction_lifted',
                    'auto_resumed': True
                },
                'target_eas': [ea_id],
                'execution_time': datetime.now()
            }
            
            await self.command_dispatcher.queue_command(resume_command)
            
            # Log the action
            self.log_news_action(ea_id, symbol, 'RESUMED', trading_status)
    
    async def pause_eas_by_symbols(self, symbols: List[str], reason: str):
        """Pause all EAs trading the specified symbols"""
        active_eas = self.ea_collector.get_active_eas()
        
        affected_eas = [
            ea for ea in active_eas 
            if ea.get('symbol') in symbols and ea.get('status') != 'news_paused'
        ]
        
        if not affected_eas:
            return
        
        ea_ids = [ea.get('magic_number') for ea in affected_eas if ea.get('magic_number')]
        
        batch_command = {
            'command_type': 'pause',
            'parameters': {
                'reason': reason,
                'batch_operation': True,
                'auto_resume': True
            },
            'target_eas': ea_ids,
            'execution_time': datetime.now()
        }
        
        await self.command_dispatcher.queue_batch_command(batch_command)
        
        print(f"Paused {len(ea_ids)} EAs due to: {reason}")
    
    async def send_news_warning(self, symbols: List[str], alert: Dict[str, Any]):
        """Send warning about upcoming news events"""
        warning_message = {
            'type': 'NEWS_WARNING',
            'message': alert['message'],
            'affected_symbols': symbols,
            'timestamp': datetime.now().isoformat(),
            'event_data': alert['event']
        }
        
        # This would typically be sent via WebSocket to the dashboard
        print(f"NEWS WARNING: {json.dumps(warning_message, indent=2)}")
    
    def get_affected_symbols(self, currency: str) -> List[str]:
        """Get list of symbols affected by a currency's news events"""
        affected_symbols = []
        
        # Get all active symbols from EAs
        active_eas = self.ea_collector.get_active_eas()
        active_symbols = list(set(ea.get('symbol') for ea in active_eas if ea.get('symbol')))
        
        for symbol in active_symbols:
            # Check if currency affects this symbol
            if len(symbol) >= 6:  # Forex pair
                base_currency = symbol[:3]
                quote_currency = symbol[3:6]
                if currency in [base_currency, quote_currency]:
                    affected_symbols.append(symbol)
            else:  # Index or commodity
                if currency.upper() in symbol.upper():
                    affected_symbols.append(symbol)
        
        return affected_symbols
    
    def log_news_action(self, ea_id: int, symbol: str, action: str, trading_status: Dict[str, Any]):
        """Log news-related actions for audit trail"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'ea_id': ea_id,
            'symbol': symbol,
            'action': action,
            'trading_status': trading_status,
            'type': 'NEWS_ACTION'
        }
        
        # This would typically be stored in a log table or file
        print(f"NEWS ACTION LOG: {json.dumps(log_entry, indent=2)}")
    
    def get_news_dashboard_data(self) -> Dict[str, Any]:
        """Get news data formatted for dashboard display"""
        current_time = datetime.now()
        
        # Get today's events
        todays_events = self.news_filter.get_todays_events()
        
        # Get active restrictions
        active_restrictions = self.news_filter.get_active_restrictions()
        
        # Get upcoming high-impact events
        upcoming_high_impact = self.news_filter.get_filtered_events(
            impact_levels=['high'],
            start_time=current_time,
            end_time=current_time + timedelta(hours=24)
        )
        
        # Get affected symbols summary
        affected_symbols_summary = {}
        for restriction in active_restrictions:
            affected_symbols = self.get_affected_symbols(restriction.currency)
            for symbol in affected_symbols:
                if symbol not in affected_symbols_summary:
                    affected_symbols_summary[symbol] = []
                affected_symbols_summary[symbol].append({
                    'currency': restriction.currency,
                    'impact_level': restriction.impact_level,
                    'description': restriction.description,
                    'blackout_end': restriction.blackout_end.isoformat()
                })
        
        return {
            'current_time': current_time.isoformat(),
            'todays_events': [event.to_dict() for event in todays_events],
            'active_restrictions': [event.to_dict() for event in active_restrictions],
            'upcoming_high_impact': [event.to_dict() for event in upcoming_high_impact],
            'affected_symbols_summary': affected_symbols_summary,
            'total_events_today': len(todays_events),
            'active_restrictions_count': len(active_restrictions),
            'trading_blocked_symbols': list(affected_symbols_summary.keys())
        }


class NewsConfigurationManager:
    """Manages news filtering configuration"""
    
    def __init__(self):
        self.news_filter = NewsEventFilter()
    
    def update_impact_level_settings(self, impact_level: str, pre_minutes: int, post_minutes: int):
        """Update blackout period settings for an impact level"""
        if impact_level not in ['high', 'medium', 'low']:
            raise ValueError("Impact level must be 'high', 'medium', or 'low'")
        
        if pre_minutes < 0 or post_minutes < 0:
            raise ValueError("Blackout minutes cannot be negative")
        
        self.news_filter.update_blackout_periods(impact_level, pre_minutes, post_minutes)
        
        print(f"Updated {impact_level} impact blackout periods: {pre_minutes} min before, {post_minutes} min after")
    
    def get_current_settings(self) -> Dict[str, Any]:
        """Get current news filtering settings"""
        return {
            'blackout_periods': self.news_filter.default_blackout_periods.copy(),
            'api_status': 'connected',  # Would check actual API status
            'last_update': datetime.now().isoformat(),
            'auto_update_enabled': True
        }
    
    def test_news_integration(self) -> Dict[str, Any]:
        """Test news integration functionality"""
        test_results = {
            'database_connection': False,
            'api_connection': False,
            'event_parsing': False,
            'blackout_calculation': False,
            'symbol_matching': False
        }
        
        try:
            # Test database connection
            with get_db_session() as db_session:
                db_session.execute("SELECT 1")
                test_results['database_connection'] = True
            
            # Test API connection (mock)
            api_client = self.news_filter.api_client
            events = api_client.fetch_economic_calendar()
            test_results['api_connection'] = len(events) > 0
            
            # Test event parsing
            if events:
                test_event = events[0]
                required_fields = ['time', 'currency', 'impact', 'event']
                test_results['event_parsing'] = all(field in test_event for field in required_fields)
            
            # Test blackout calculation
            from ..models.news import NewsEvent
            test_news_event = NewsEvent(
                event_time=datetime.now(),
                currency='USD',
                impact_level='high',
                description='Test Event',
                pre_minutes=30,
                post_minutes=30
            )
            test_results['blackout_calculation'] = (
                test_news_event.blackout_start < test_news_event.event_time < test_news_event.blackout_end
            )
            
            # Test symbol matching
            test_results['symbol_matching'] = test_news_event.affects_symbol('EURUSD')
            
        except Exception as e:
            print(f"Error in news integration test: {e}")
        
        return test_results


# Example usage and demonstration
async def main():
    """Example of how to use the news integration system"""
    
    # Initialize the integrated trading manager
    trading_manager = NewsIntegratedTradingManager()
    
    # Initialize configuration manager
    config_manager = NewsConfigurationManager()
    
    # Test the integration
    print("Testing news integration...")
    test_results = config_manager.test_news_integration()
    print(f"Test results: {json.dumps(test_results, indent=2)}")
    
    # Update news events
    print("\nFetching latest news events...")
    news_filter = NewsEventFilter()
    stored_count = news_filter.fetch_and_store_news_events()
    print(f"Stored {stored_count} new events")
    
    # Get dashboard data
    print("\nGetting news dashboard data...")
    dashboard_data = trading_manager.get_news_dashboard_data()
    print(f"Dashboard data: {json.dumps(dashboard_data, indent=2)}")
    
    # Configure blackout periods
    print("\nConfiguring blackout periods...")
    config_manager.update_impact_level_settings('high', 90, 90)
    config_manager.update_impact_level_settings('medium', 45, 45)
    config_manager.update_impact_level_settings('low', 15, 15)
    
    current_settings = config_manager.get_current_settings()
    print(f"Current settings: {json.dumps(current_settings, indent=2)}")
    
    # Start monitoring (would run continuously in production)
    print("\nStarting news monitoring (demo - will run for 30 seconds)...")
    try:
        await asyncio.wait_for(trading_manager.start_news_monitoring(), timeout=30.0)
    except asyncio.TimeoutError:
        print("Demo completed")


if __name__ == '__main__':
    asyncio.run(main())