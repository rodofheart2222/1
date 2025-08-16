#!/usr/bin/env python3
"""
Populate News Database

This script populates the news database with mock events for testing.
"""

import asyncio
import sys
from datetime import datetime, timedelta

def populate_news_database():
    """Populate the news database with mock events"""
    
    print("=" * 60)
    print("POPULATING NEWS DATABASE")
    print("=" * 60)
    
    try:
        from services.news_service import NewsEventFilter, NewsEventScheduler
        
        print("\n1. Creating NewsEventFilter...")
        news_filter = NewsEventFilter()
        
        print("\n2. Fetching and storing news events...")
        # This will use the mock data from the API client
        stored_count = news_filter.fetch_and_store_news_events()
        print(f"   Stored {stored_count} events in database")
        
        print("\n3. Verifying stored events...")
        all_events = news_filter.get_filtered_events()
        print(f"   Total events in database: {len(all_events)}")
        
        if all_events:
            print("\n4. Sample events:")
            for i, event in enumerate(all_events[:3]):  # Show first 3 events
                print(f"   Event {i+1}:")
                print(f"     Time: {event['event_time']}")
                print(f"     Currency: {event['currency']}")
                print(f"     Impact: {event['impact_level']}")
                print(f"     Description: {event['description']}")
        
        print("\n5. Testing today's events...")
        todays_events = news_filter.get_todays_events()
        print(f"   Today's events: {len(todays_events)}")
        
        print("\n6. Testing upcoming events...")
        upcoming_events = news_filter.get_filtered_events(
            start_time=datetime.now(),
            end_time=datetime.now() + timedelta(hours=24)
        )
        print(f"   Upcoming events (next 24h): {len(upcoming_events)}")
        
        print("\n✅ Database population completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error populating database: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def check_database_status():
    """Check the current status of the news database"""
    
    print("\n" + "=" * 60)
    print("DATABASE STATUS CHECK")
    print("=" * 60)
    
    try:
        from services.news_service import NewsEventFilter
        from database.connection import get_db_session
        from models.news import NewsEvent
        
        news_filter = NewsEventFilter()
        
        print("\n1. Checking database connection...")
        with get_db_session() as session:
            event_count = session.query(NewsEvent).count()
            print(f"   Total events in database: {event_count}")
            
            if event_count > 0:
                # Get date range of events
                earliest = session.query(NewsEvent.event_time).order_by(NewsEvent.event_time.asc()).first()
                latest = session.query(NewsEvent.event_time).order_by(NewsEvent.event_time.desc()).first()
                
                print(f"   Date range: {earliest[0]} to {latest[0]}")
                
                # Count by impact level
                high_count = session.query(NewsEvent).filter(NewsEvent.impact_level == 'high').count()
                medium_count = session.query(NewsEvent).filter(NewsEvent.impact_level == 'medium').count()
                low_count = session.query(NewsEvent).filter(NewsEvent.impact_level == 'low').count()
                
                print(f"   Impact levels: High={high_count}, Medium={medium_count}, Low={low_count}")
        
        print("\n2. Testing service methods...")
        
        # Test today's events
        todays_events = news_filter.get_todays_events()
        print(f"   Today's events: {len(todays_events)}")
        
        # Test filtered events
        high_impact = news_filter.get_filtered_events(impact_levels=['high'])
        print(f"   High impact events: {len(high_impact)}")
        
        print("\n✅ Database status check completed!")
        
    except Exception as e:
        print(f"\n❌ Error checking database: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("News Database Management Tool")
    
    if len(sys.argv) > 1 and sys.argv[1] == "check":
        check_database_status()
    else:
        populate_news_database()
        check_database_status()