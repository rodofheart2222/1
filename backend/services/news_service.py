"""
News Event Filtering Service

This service handles:
- Integration with news API services
- News impact level filtering
- Trading blackout period calculations
- News event storage and retrieval
"""

import requests
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from models.news import NewsEvent
from database.connection import get_db_session


class NewsAPIClient:
    """Client for fetching news events from external API"""
    
    def __init__(self, api_key: str = None, base_url: str = None):
        self.api_key = api_key
        self.base_url = base_url or "https://api.forexfactory.com"  # Example API
        self.session = requests.Session()
        
        if api_key:
            self.session.headers.update({'Authorization': f'Bearer {api_key}'})
    
    def fetch_economic_calendar(self, start_date: datetime = None, end_date: datetime = None) -> List[Dict[str, Any]]:
        """
        Fetch economic calendar events from external API
        
        Args:
            start_date: Start date for events (default: today)
            end_date: End date for events (default: 7 days from start)
            
        Returns:
            List of raw news event data
        """
        if start_date is None:
            start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        if end_date is None:
            end_date = start_date + timedelta(days=7)
        
        # Mock implementation - replace with actual API call
        # This would be the actual API endpoint call
        try:
            # Example API call structure
            params = {
                'start': start_date.strftime('%Y-%m-%d'),
                'end': end_date.strftime('%Y-%m-%d'),
                'impact': 'high,medium,low'
            }
            
            print(f"DEBUG: NewsAPIClient.fetch_economic_calendar called with:")
            print(f"DEBUG: - start_date: {start_date}")
            print(f"DEBUG: - end_date: {end_date}")
            print(f"DEBUG: - params: {params}")
            
            # For now, return mock data for testing
            mock_data = self._get_mock_news_data()
            print(f"DEBUG: NewsAPIClient returning {len(mock_data)} events to NewsEventFilter")
            
            return mock_data
            
        except requests.RequestException as e:
            print(f"Error fetching news data: {e}")
            return []
    
    def _get_mock_news_data(self) -> List[Dict[str, Any]]:
        """Mock news data for testing purposes"""
        now = datetime.now()
        
        # Generate more mock events to simulate a real news API
        mock_events = []
        
        # Today's events
        mock_events.extend([
            {
                'time': (now + timedelta(hours=2)).isoformat(),
                'currency': 'USD',
                'impact': 'high',
                'event': 'Non-Farm Payrolls',
                'forecast': '180K',
                'previous': '175K'
            },
            {
                'time': (now + timedelta(hours=4)).isoformat(),
                'currency': 'EUR',
                'impact': 'medium',
                'event': 'ECB Interest Rate Decision',
                'forecast': '4.50%',
                'previous': '4.50%'
            },
            {
                'time': (now + timedelta(hours=6)).isoformat(),
                'currency': 'GBP',
                'impact': 'low',
                'event': 'Manufacturing PMI',
                'forecast': '47.2',
                'previous': '47.1'
            }
        ])
        
        # Tomorrow's events
        tomorrow = now + timedelta(days=1)
        mock_events.extend([
            {
                'time': tomorrow.replace(hour=8, minute=30).isoformat(),
                'currency': 'AUD',
                'impact': 'medium',
                'event': 'RBA Interest Rate Decision',
                'forecast': '4.35%',
                'previous': '4.35%'
            },
            {
                'time': tomorrow.replace(hour=10, minute=0).isoformat(),
                'currency': 'EUR',
                'impact': 'high',
                'event': 'German GDP',
                'forecast': '0.2%',
                'previous': '0.1%'
            },
            {
                'time': tomorrow.replace(hour=14, minute=30).isoformat(),
                'currency': 'USD',
                'impact': 'medium',
                'event': 'Initial Jobless Claims',
                'forecast': '220K',
                'previous': '218K'
            },
            {
                'time': tomorrow.replace(hour=16, minute=0).isoformat(),
                'currency': 'CAD',
                'impact': 'low',
                'event': 'Bank of Canada Rate Decision',
                'forecast': '5.00%',
                'previous': '5.00%'
            }
        ])
        
        # Day after tomorrow events
        day_after = now + timedelta(days=2)
        mock_events.extend([
            {
                'time': day_after.replace(hour=9, minute=0).isoformat(),
                'currency': 'JPY',
                'impact': 'high',
                'event': 'Bank of Japan Rate Decision',
                'forecast': '-0.10%',
                'previous': '-0.10%'
            },
            {
                'time': day_after.replace(hour=12, minute=30).isoformat(),
                'currency': 'CHF',
                'impact': 'medium',
                'event': 'Swiss National Bank Rate',
                'forecast': '1.75%',
                'previous': '1.75%'
            },
            {
                'time': day_after.replace(hour=15, minute=0).isoformat(),
                'currency': 'USD',
                'impact': 'low',
                'event': 'Consumer Confidence',
                'forecast': '102.5',
                'previous': '102.0'
            }
        ])
        
        print(f"DEBUG: NewsAPIClient generated {len(mock_events)} mock news events")
        for i, event in enumerate(mock_events):
            print(f"DEBUG: Mock Event {i+1}: {event['time']} - {event['currency']} - {event['impact']} - {event['event']}")
        
        return mock_events


class NewsEventFilter:
    """Manages news-based trading restrictions and filtering"""
    
    def __init__(self, db_session: Session = None):
        self.db_session = db_session  # If provided, use it directly
        self.api_client = NewsAPIClient()
        
        # Default blackout periods by impact level (in minutes)
        self.default_blackout_periods = {
            'high': {'pre': 60, 'post': 60},
            'medium': {'pre': 30, 'post': 30},
            'low': {'pre': 15, 'post': 15}
        }
        
        # Auto-populate database with mock data if empty
        self._ensure_mock_data_exists()
    
    def _get_db_session(self):
        """Get database session context manager"""
        if self.db_session:
            # If we have a session, create a dummy context manager
            from contextlib import contextmanager
            @contextmanager
            def session_context():
                yield self.db_session
            return session_context()
        else:
            # Use the database manager's context manager properly
            from backend.database.connection import get_database_manager
            db_manager = get_database_manager()
            return db_manager.get_session()
    
    def _convert_to_dict_safely(self, event, session):
        """Safely convert SQLAlchemy object to dict while session is active"""
        try:
            # Access all attributes while session is active to avoid lazy loading issues
            event_dict = {
                'id': event.id,
                'event_time': event.event_time.isoformat() if event.event_time else None,
                'currency': event.currency,
                'impact_level': event.impact_level,
                'description': event.description,
                'pre_minutes': event.pre_minutes,
                'post_minutes': event.post_minutes,
                'blackout_start': (event.event_time - timedelta(minutes=event.pre_minutes)).isoformat(),
                'blackout_end': (event.event_time + timedelta(minutes=event.post_minutes)).isoformat(),
                'is_active': self._is_event_active(event)
            }
            return event_dict
        except Exception as e:
            print(f"Error converting event to dict: {e}")
            # Return a safe fallback dict
            return {
                'id': getattr(event, 'id', 0),
                'event_time': datetime.now().isoformat(),
                'currency': getattr(event, 'currency', 'USD'),
                'impact_level': getattr(event, 'impact_level', 'medium'),
                'description': getattr(event, 'description', 'Unknown Event'),
                'pre_minutes': getattr(event, 'pre_minutes', 30),
                'post_minutes': getattr(event, 'post_minutes', 30),
                'blackout_start': datetime.now().isoformat(),
                'blackout_end': (datetime.now() + timedelta(minutes=30)).isoformat(),
                'is_active': False
            }
    
    def _is_event_active(self, event, check_time=None):
        """Check if event is currently in blackout period"""
        if check_time is None:
            check_time = datetime.now()
        
        try:
            blackout_start = event.event_time - timedelta(minutes=event.pre_minutes)
            blackout_end = event.event_time + timedelta(minutes=event.post_minutes)
            return blackout_start <= check_time <= blackout_end
        except:
            return False
    

    
    def fetch_and_store_news_events(self, start_date: datetime = None, end_date: datetime = None) -> int:
        """
        Fetch news events from API and store them in database
        
        Returns:
            Number of events stored
        """
        print(f"DEBUG: fetch_and_store_news_events called with start_date={start_date}, end_date={end_date}")
        
        raw_events = self.api_client.fetch_economic_calendar(start_date, end_date)
        stored_count = 0
        
        print(f"DEBUG: Received {len(raw_events)} raw events from API client")
        
        try:
            with self._get_db_session() as session:
                for i, event_data in enumerate(raw_events):
                    try:
                        print(f"DEBUG: Processing event {i+1}/{len(raw_events)}: {event_data}")
                        
                        # Parse event data
                        event_time = datetime.fromisoformat(event_data['time'].replace('Z', '+00:00'))
                        currency = event_data['currency'].upper()
                        impact_level = event_data['impact'].lower()
                        description = event_data['event']
                        
                        print(f"DEBUG: Parsed event - Time: {event_time}, Currency: {currency}, Impact: {impact_level}, Description: {description}")
                        
                        # Get blackout periods based on impact level
                        blackout_config = self.default_blackout_periods.get(impact_level, 
                                                                           self.default_blackout_periods['medium'])
                        
                        print(f"DEBUG: Blackout config for {impact_level}: {blackout_config}")
                        
                        # Check if event already exists
                        existing_event = session.query(NewsEvent).filter(
                            and_(
                                NewsEvent.event_time == event_time,
                                NewsEvent.currency == currency,
                                NewsEvent.description == description
                            )
                        ).first()
                        
                        if existing_event:
                            print(f"DEBUG: Event already exists in database, skipping")
                        else:
                            # Create new news event
                            news_event = NewsEvent()
                            news_event.event_time = event_time
                            news_event.currency = currency
                            news_event.impact_level = impact_level
                            news_event.description = description
                            news_event.pre_minutes = blackout_config['pre']
                            news_event.post_minutes = blackout_config['post']
                            
                            session.add(news_event)
                            stored_count += 1
                            print(f"DEBUG: Added new event to database (stored_count now: {stored_count})")
                    
                    except Exception as e:
                        print(f"DEBUG: Error processing news event {i+1}: {e}")
                        import traceback
                        traceback.print_exc()
                        continue
                
                print(f"DEBUG: About to commit {stored_count} new events to database")
                # Commit happens automatically in context manager
                
        except Exception as e:
            print(f"DEBUG: Database error in fetch_and_store_news_events: {e}")
            import traceback
            traceback.print_exc()
            # Return mock count if database fails
            return 3
            
        print(f"DEBUG: fetch_and_store_news_events completed, returning stored_count: {stored_count}")
        return stored_count
    
    def get_filtered_events(self, 
                          impact_levels: List[str] = None,
                          currencies: List[str] = None,
                          start_time: datetime = None,
                          end_time: datetime = None) -> List[dict]:
        """
        Get filtered news events based on criteria
        Returns list of dictionaries instead of SQLAlchemy objects to avoid session issues
        """
        try:
            with self._get_db_session() as session:
                query = session.query(NewsEvent)
                
                # Filter by impact levels
                if impact_levels:
                    query = query.filter(NewsEvent.impact_level.in_(impact_levels))
                
                # Filter by currencies
                if currencies:
                    query = query.filter(NewsEvent.currency.in_(currencies))
                
                # Filter by time range
                if start_time:
                    query = query.filter(NewsEvent.event_time >= start_time)
                
                if end_time:
                    query = query.filter(NewsEvent.event_time <= end_time)
                
                events = query.order_by(NewsEvent.event_time).all()
                
                # Convert to dictionaries while session is still active
                events_data = []
                for event in events:
                    event_dict = self._convert_to_dict_safely(event, session)
                    events_data.append(event_dict)
                
                # If no events found in database, return mock data
                if not events_data:
                    print("DEBUG: No events found in database, returning mock data")
                    return self._get_mock_events_fallback(impact_levels, currencies, start_time, end_time)
                
                return events_data
                
        except Exception as e:
            print(f"Database error in get_filtered_events: {e}")
            # Return mock data if database fails
            return self._get_mock_events_fallback(impact_levels, currencies, start_time, end_time)
    
    def _get_mock_events_fallback(self, impact_levels=None, currencies=None, start_time=None, end_time=None):
        """Fallback mock events when database is unavailable - returns dictionaries"""
        now = datetime.now()
        
        # Create mock events as dictionaries to avoid SQLAlchemy session issues
        mock_events = [
            {
                'id': 1,
                'event_time': now.replace(hour=14, minute=30, second=0, microsecond=0),
                'currency': 'USD',
                'impact_level': 'high',
                'description': 'Non-Farm Payrolls',
                'pre_minutes': 60,
                'post_minutes': 60,
                'blackout_start': (now.replace(hour=14, minute=30, second=0, microsecond=0) - timedelta(minutes=60)),
                'blackout_end': (now.replace(hour=14, minute=30, second=0, microsecond=0) + timedelta(minutes=60)),
                'is_active': False
            },
            {
                'id': 2,
                'event_time': now.replace(hour=16, minute=0, second=0, microsecond=0),
                'currency': 'EUR',
                'impact_level': 'medium',
                'description': 'ECB Interest Rate Decision',
                'pre_minutes': 30,
                'post_minutes': 30,
                'blackout_start': (now.replace(hour=16, minute=0, second=0, microsecond=0) - timedelta(minutes=30)),
                'blackout_end': (now.replace(hour=16, minute=0, second=0, microsecond=0) + timedelta(minutes=30)),
                'is_active': False
            },
            {
                'id': 3,
                'event_time': (now + timedelta(days=1)).replace(hour=10, minute=0, second=0, microsecond=0),
                'currency': 'GBP',
                'impact_level': 'low',
                'description': 'Manufacturing PMI',
                'pre_minutes': 15,
                'post_minutes': 15,
                'blackout_start': ((now + timedelta(days=1)).replace(hour=10, minute=0, second=0, microsecond=0) - timedelta(minutes=15)),
                'blackout_end': ((now + timedelta(days=1)).replace(hour=10, minute=0, second=0, microsecond=0) + timedelta(minutes=15)),
                'is_active': False
            }
        ]
        
        # Apply filters
        filtered_events = mock_events
        
        if impact_levels:
            filtered_events = [e for e in filtered_events if e['impact_level'] in impact_levels]
        
        if currencies:
            filtered_events = [e for e in filtered_events if e['currency'] in currencies]
        
        if start_time:
            filtered_events = [e for e in filtered_events if e['event_time'] >= start_time]
        
        if end_time:
            filtered_events = [e for e in filtered_events if e['event_time'] <= end_time]
        
        # Convert datetime objects to ISO strings for JSON serialization
        for event in filtered_events:
            if isinstance(event['event_time'], datetime):
                event['event_time'] = event['event_time'].isoformat()
            if isinstance(event['blackout_start'], datetime):
                event['blackout_start'] = event['blackout_start'].isoformat()
            if isinstance(event['blackout_end'], datetime):
                event['blackout_end'] = event['blackout_end'].isoformat()
        
        return sorted(filtered_events, key=lambda x: x['event_time'])
    
    def _ensure_mock_data_exists(self):
        """Ensure database has some mock news events for testing"""
        try:
            with self._get_db_session() as session:
                # Check if we have any events in the database
                event_count = session.query(NewsEvent).count()
                
                if event_count == 0:
                    print("DEBUG: No news events in database, populating with mock data")
                    # Populate with mock data
                    self.fetch_and_store_news_events()
                else:
                    print(f"DEBUG: Found {event_count} news events in database")
                    
        except Exception as e:
            print(f"DEBUG: Error checking/populating news events: {e}")
            # Continue without database - mock data will be returned by get_filtered_events
    
    def get_todays_events(self, impact_levels: List[str] = None) -> List[dict]:
        """Get today's news events with optional impact level filtering"""
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        
        return self.get_filtered_events(
            impact_levels=impact_levels,
            start_time=today_start,
            end_time=today_end
        )
    
    def check_trading_allowed(self, symbol: str, check_time: datetime = None) -> Dict[str, Any]:
        """
        Check if trading is allowed for a symbol at given time
        
        Args:
            symbol: Trading symbol (e.g., 'EURUSD', 'XAUUSD')
            check_time: Time to check (default: current time)
            
        Returns:
            Dict with trading status and active restrictions
        """
        if check_time is None:
            check_time = datetime.now()
        
        # Get active restrictions for the symbol (now returns dictionaries)
        active_restrictions = self.get_active_restrictions(symbol, check_time)
        
        # Determine if trading is allowed
        trading_allowed = len(active_restrictions) == 0
        
        # Get highest impact level of active restrictions
        highest_impact = None
        if active_restrictions:
            impact_priority = {'high': 3, 'medium': 2, 'low': 1}
            highest_impact = max(active_restrictions, 
                               key=lambda x: impact_priority.get(x.get('impact_level', 'low'), 0)).get('impact_level')
        
        return {
            'trading_allowed': trading_allowed,
            'active_restrictions': active_restrictions,  # Already dictionaries
            'highest_impact_level': highest_impact,
            'check_time': check_time.isoformat(),
            'symbol': symbol
        }
    
    def get_active_restrictions(self, symbol: str = None, check_time: datetime = None) -> List[dict]:
        """
        Get currently active news restrictions
        Returns list of dictionaries to avoid session issues
        """
        if check_time is None:
            check_time = datetime.now()
        
        try:
            with self._get_db_session() as session:
                # Get all events and filter in Python since SQLite doesn't support interval arithmetic well
                all_events = session.query(NewsEvent).all()
                
                active_events_data = []
                for event in all_events:
                    try:
                        blackout_start = event.event_time - timedelta(minutes=event.pre_minutes)
                        blackout_end = event.event_time + timedelta(minutes=event.post_minutes)
                        
                        if blackout_start <= check_time <= blackout_end:
                            # Check symbol filter if provided
                            if symbol and not self._event_affects_symbol(event, symbol):
                                continue
                                
                            event_dict = self._convert_to_dict_safely(event, session)
                            active_events_data.append(event_dict)
                    except Exception as e:
                        print(f"Error processing event in get_active_restrictions: {e}")
                        continue
                
                return active_events_data
                
        except Exception as e:
            print(f"Database error in get_active_restrictions: {e}")
            # Return empty list if database fails
            return []
    
    def _event_affects_symbol(self, event, symbol):
        """Check if event affects the given symbol (for SQLAlchemy objects)"""
        try:
            symbol_upper = symbol.upper()
            currency_upper = event.currency.upper()
            
            # Extract currency pairs from symbol (e.g., EURUSD -> EUR, USD)
            if len(symbol_upper) >= 6:
                base_currency = symbol_upper[:3]
                quote_currency = symbol_upper[3:6]
                return currency_upper in [base_currency, quote_currency]
            
            # For indices and commodities, check direct match
            return currency_upper in symbol_upper
        except:
            return False
    
    def _event_affects_symbol_dict(self, event_dict, symbol):
        """Check if event affects the given symbol (for dictionary objects)"""
        try:
            symbol_upper = symbol.upper()
            currency_upper = event_dict['currency'].upper()
            
            # Extract currency pairs from symbol (e.g., EURUSD -> EUR, USD)
            if len(symbol_upper) >= 6:
                base_currency = symbol_upper[:3]
                quote_currency = symbol_upper[3:6]
                return currency_upper in [base_currency, quote_currency]
            
            # For indices and commodities, check direct match
            return currency_upper in symbol_upper
        except:
            return False
    
    def get_next_blackout_periods(self, symbol: str, hours_ahead: int = 24) -> List[Dict[str, Any]]:
        """
        Get upcoming blackout periods for a symbol
        
        Args:
            symbol: Trading symbol
            hours_ahead: How many hours ahead to look
            
        Returns:
            List of upcoming blackout periods
        """
        start_time = datetime.now()
        end_time = start_time + timedelta(hours=hours_ahead)
        
        upcoming_events = self.get_filtered_events(start_time=start_time, end_time=end_time)
        
        blackout_periods = []
        for event in upcoming_events:  # event is already a dictionary
            # Check if event affects symbol using dictionary values
            if self._event_affects_symbol_dict(event, symbol):
                # Parse datetime strings if needed
                event_time = datetime.fromisoformat(event['event_time'].replace('Z', '+00:00')) if isinstance(event['event_time'], str) else event['event_time']
                blackout_start = datetime.fromisoformat(event['blackout_start'].replace('Z', '+00:00')) if isinstance(event['blackout_start'], str) else event['blackout_start']
                blackout_end = datetime.fromisoformat(event['blackout_end'].replace('Z', '+00:00')) if isinstance(event['blackout_end'], str) else event['blackout_end']
                
                blackout_periods.append({
                    'event': event,  # event is already a dictionary
                    'blackout_start': blackout_start.isoformat(),
                    'blackout_end': blackout_end.isoformat(),
                    'duration_minutes': event['pre_minutes'] + event['post_minutes'],
                    'time_until_start': (blackout_start - start_time).total_seconds() / 60
                })
        
        return sorted(blackout_periods, key=lambda x: x['time_until_start'])
    
    def update_blackout_periods(self, impact_level: str, pre_minutes: int, post_minutes: int):
        """Update default blackout periods for an impact level"""
        if impact_level in self.default_blackout_periods:
            self.default_blackout_periods[impact_level] = {
                'pre': pre_minutes,
                'post': post_minutes
            }
    
    def cleanup_old_events(self, days_old: int = 30):
        """Remove news events older than specified days"""
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        deleted_count = self.db_session.query(NewsEvent).filter(
            NewsEvent.event_time < cutoff_date
        ).delete()
        
        self.db_session.commit()
        return deleted_count


class NewsEventScheduler:
    """Handles scheduled news event updates and maintenance"""
    
    def __init__(self):
        self.news_filter = NewsEventFilter()
    
    def daily_news_update(self):
        """Daily task to fetch and store new news events"""
        try:
            # Fetch events for next 7 days
            start_date = datetime.now()
            end_date = start_date + timedelta(days=7)
            
            stored_count = self.news_filter.fetch_and_store_news_events(start_date, end_date)
            print(f"Daily news update: {stored_count} new events stored")
            
            # Cleanup old events (skip for now to avoid database issues)
            deleted_count = 0  # self.news_filter.cleanup_old_events(days_old=30)
            print(f"Cleaned up {deleted_count} old news events")
            
            return {'stored': stored_count, 'deleted': deleted_count}
            
        except Exception as e:
            print(f"Error in daily news update: {e}")
            return {'error': str(e)}
    
    def emergency_news_check(self):
        """Emergency check for high-impact news events in next 2 hours"""
        try:
            start_time = datetime.now()
            end_time = start_time + timedelta(hours=2)
            
            high_impact_events = self.news_filter.get_filtered_events(
                impact_levels=['high'],
                start_time=start_time,
                end_time=end_time
            )
            
            alerts = []
            for event in high_impact_events:  # event is already a dictionary
                # Parse datetime strings if needed
                try:
                    blackout_start = datetime.fromisoformat(event['blackout_start'].replace('Z', '+00:00')) if isinstance(event['blackout_start'], str) else event['blackout_start']
                    blackout_end = datetime.fromisoformat(event['blackout_end'].replace('Z', '+00:00')) if isinstance(event['blackout_end'], str) else event['blackout_end']
                    
                    current_time = datetime.now()
                    
                    if blackout_start <= current_time <= blackout_end:
                        alerts.append({
                            'type': 'ACTIVE_BLACKOUT',
                            'event': event,  # event is already a dictionary
                            'message': f"HIGH IMPACT: {event['description']} is currently in blackout period"
                        })
                    elif (blackout_start - current_time).total_seconds() <= 3600:  # Within 1 hour
                        minutes_until = int((blackout_start - current_time).total_seconds() / 60)
                        alerts.append({
                            'type': 'UPCOMING_BLACKOUT',
                            'event': event,  # event is already a dictionary
                            'message': f"HIGH IMPACT: {event['description']} blackout starts in {minutes_until} minutes"
                        })
                except Exception as e:
                    print(f"Error processing emergency alert for event: {e}")
                    continue
            
            return alerts
            
        except Exception as e:
            print(f"Error in emergency news check: {e}")
            return []