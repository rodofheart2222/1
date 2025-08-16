#!/usr/bin/env python3
"""
Setup News System

This script ensures the news system is properly initialized with database tables
and populated with mock news events.
"""

import os
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_news_system():
    """Setup the complete news system"""
    
    print("=" * 60)
    print("SETTING UP NEWS SYSTEM")
    print("=" * 60)
    
    try:
        # 1. Initialize database
        print("\n1. Initializing database...")
        from database.init_db import init_database, verify_database_integrity
        
        db_path = os.getenv("DATABASE_PATH", "data/mt5_dashboard.db")
        print(f"   Database path: {db_path}")
        
        # Create data directory
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        init_success = init_database(db_path)
        if init_success:
            print("   ✅ Database initialized successfully")
        else:
            print("   ❌ Database initialization failed")
            return False
        
        # 2. Verify database integrity
        print("\n2. Verifying database integrity...")
        integrity_ok = verify_database_integrity(db_path)
        if integrity_ok:
            print("   ✅ Database integrity verified")
        else:
            print("   ❌ Database integrity check failed")
            return False
        
        # 3. Check news events table
        print("\n3. Checking news events table...")
        from database.connection import get_db_session
        from models.news import NewsEvent
        
        with get_db_session() as session:
            event_count = session.query(NewsEvent).count()
            print(f"   Current news events in database: {event_count}")
        
        # 4. Populate with mock news events
        print("\n4. Populating news events...")
        from services.news_service import NewsEventFilter, NewsEventScheduler
        
        news_filter = NewsEventFilter()
        scheduler = NewsEventScheduler()
        
        # Run daily update to populate events
        sync_result = scheduler.daily_news_update()
        print(f"   Sync result: {sync_result}")
        
        # Verify events were added
        with get_db_session() as session:
            new_event_count = session.query(NewsEvent).count()
            print(f"   News events after sync: {new_event_count}")
        
        # 5. Test news service functionality
        print("\n5. Testing news service...")
        
        # Test today's events
        todays_events = news_filter.get_todays_events()
        print(f"   Today's events: {len(todays_events)}")
        
        # Test filtered events
        all_events = news_filter.get_filtered_events()
        print(f"   All events: {len(all_events)}")
        
        # Test high impact events
        high_impact = news_filter.get_filtered_events(impact_levels=['high'])
        print(f"   High impact events: {len(high_impact)}")
        
        # Test trading status
        trading_status = news_filter.check_trading_allowed('EURUSD')
        print(f"   EURUSD trading allowed: {trading_status['trading_allowed']}")
        
        # 6. Show sample events
        if todays_events:
            print("\n6. Sample events:")
            for i, event in enumerate(todays_events[:3]):
                print(f"   Event {i+1}:")
                print(f"     Time: {event['event_time']}")
                print(f"     Currency: {event['currency']}")
                print(f"     Impact: {event['impact_level']}")
                print(f"     Description: {event['description']}")
        
        print("\n✅ News system setup completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error setting up news system: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_news_api():
    """Test the news API endpoints"""
    
    print("\n" + "=" * 60)
    print("TESTING NEWS API ENDPOINTS")
    print("=" * 60)
    
    try:
        import requests
        import json
        
        base_url = "http://155.138.174.196:8000"
        
        endpoints = [
            "/api/news/events/today",
            "/api/news/events/upcoming?hours=24",
            "/api/news/config/impact-levels"
        ]
        
        for endpoint in endpoints:
            print(f"\n🔍 Testing: {endpoint}")
            try:
                response = requests.get(f"{base_url}{endpoint}", timeout=5)
                print(f"   Status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    if 'events' in data:
                        print(f"   Events: {len(data['events'])}")
                    else:
                        print(f"   Response: {list(data.keys())}")
                else:
                    print(f"   Error: {response.text}")
                    
            except requests.exceptions.ConnectionError:
                print(f"   ⚠️  Server not running - start with: python main.py")
            except Exception as e:
                print(f"   ❌ Error: {e}")
        
    except ImportError:
        print("   ⚠️  requests module not available for API testing")

if __name__ == "__main__":
    print("News System Setup Tool")
    
    success = setup_news_system()
    
    if success:
        print("\n" + "=" * 60)
        print("SETUP COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Start the backend server: python main.py")
        print("2. Test the news endpoints: python test_news_endpoint.py")
        print("3. Check the dashboard for news events")
        
        # Optionally test API if server is running
        if len(sys.argv) > 1 and sys.argv[1] == "--test-api":
            test_news_api()
    else:
        print("\n" + "=" * 60)
        print("SETUP FAILED!")
        print("=" * 60)
        sys.exit(1)