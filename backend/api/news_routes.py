"""
News API Routes
Handles news events and trading restrictions
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime, timedelta
import logging

# Import news service
try:
    from services.news_service import NewsEventFilter
    NEWS_SERVICE_AVAILABLE = True
except ImportError:
    NEWS_SERVICE_AVAILABLE = False
    logging.warning("News service not available - using mock data")

router = APIRouter(prefix="/api/news", tags=["News Events"])

# Initialize news service
if NEWS_SERVICE_AVAILABLE:
    news_filter = NewsEventFilter()
else:
    news_filter = None

@router.get("/events/upcoming")
async def get_upcoming_news_events(
    hours: int = Query(default=24, description="Hours ahead to look for events"),
    impact_levels: Optional[str] = Query(default=None, description="Comma-separated impact levels (high,medium,low)"),
    currencies: Optional[str] = Query(default=None, description="Comma-separated currencies (USD,EUR,GBP)")
):
    """Get upcoming news events"""
    try:
        if not NEWS_SERVICE_AVAILABLE or not news_filter:
            # Return mock data if service is not available
            return _get_mock_news_events(hours, impact_levels, currencies)
        
        # Parse filters
        impact_filter = impact_levels.split(',') if impact_levels else None
        currency_filter = currencies.split(',') if currencies else None
        
        # Get time range
        start_time = datetime.now()
        end_time = start_time + timedelta(hours=hours)
        
        # Get filtered events
        events = news_filter.get_filtered_events(
            impact_levels=impact_filter,
            currencies=currency_filter,
            start_time=start_time,
            end_time=end_time
        )
        
        return {
            "success": True,
            "events": events,
            "count": len(events),
            "time_range": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat()
            },
            "source": "news_service"
        }
        
    except Exception as e:
        logging.error(f"Error fetching news events: {e}")
        # Fallback to mock data
        return _get_mock_news_events(hours, impact_levels, currencies)


@router.get("/blackout/active")
async def get_active_blackout_periods(
    symbol: Optional[str] = Query(default=None, description="Trading symbol to check")
):
    """Get currently active news blackout periods"""
    try:
        if not NEWS_SERVICE_AVAILABLE or not news_filter:
            # Return mock data if service is not available
            return _get_mock_active_restrictions(symbol)
        
        # Get active restrictions
        active_restrictions = news_filter.get_active_restrictions(symbol)
        
        return {
            "success": True,
            "active_restrictions": active_restrictions,
            "count": len(active_restrictions),
            "symbol": symbol,
            "check_time": datetime.now().isoformat(),
            "source": "news_service"
        }
        
    except Exception as e:
        logging.error(f"Error fetching active restrictions: {e}")
        return _get_mock_active_restrictions(symbol)


@router.get("/trading-allowed/{symbol}")
async def check_trading_allowed(symbol: str):
    """Check if trading is currently allowed for a symbol"""
    try:
        if not NEWS_SERVICE_AVAILABLE or not news_filter:
            # Return mock data if service is not available
            return {
                "success": True,
                "trading_allowed": True,
                "symbol": symbol,
                "active_restrictions": [],
                "highest_impact_level": None,
                "check_time": datetime.now().isoformat(),
                "source": "mock_fallback"
            }
        
        # Check trading status
        trading_status = news_filter.check_trading_allowed(symbol)
        
        return {
            "success": True,
            **trading_status,
            "source": "news_service"
        }
        
    except Exception as e:
        logging.error(f"Error checking trading status for {symbol}: {e}")
        return {
            "success": False,
            "error": str(e),
            "trading_allowed": True,  # Default to allow trading on error
            "symbol": symbol,
            "source": "error_fallback"
        }


@router.get("/events/today")
async def get_todays_news_events(
    impact_levels: Optional[str] = Query(default=None, description="Comma-separated impact levels")
):
    """Get today's news events"""
    try:
        if not NEWS_SERVICE_AVAILABLE or not news_filter:
            return _get_mock_todays_events(impact_levels)
        
        # Parse impact levels
        impact_filter = impact_levels.split(',') if impact_levels else None
        
        # Get today's events
        events = news_filter.get_todays_events(impact_filter)
        
        return {
            "success": True,
            "events": events,
            "count": len(events),
            "date": datetime.now().date().isoformat(),
            "source": "news_service"
        }
        
    except Exception as e:
        logging.error(f"Error fetching today's events: {e}")
        return _get_mock_todays_events(impact_levels)


@router.post("/events/refresh")
async def refresh_news_events():
    """Manually refresh news events from external API"""
    try:
        if not NEWS_SERVICE_AVAILABLE or not news_filter:
            return {
                "success": False,
                "message": "News service not available",
                "source": "mock_fallback"
            }
        
        # Fetch and store new events
        start_date = datetime.now()
        end_date = start_date + timedelta(days=7)
        
        stored_count = news_filter.fetch_and_store_news_events(start_date, end_date)
        
        return {
            "success": True,
            "message": f"Successfully refreshed news events",
            "stored_count": stored_count,
            "refresh_time": datetime.now().isoformat(),
            "source": "news_service"
        }
        
    except Exception as e:
        logging.error(f"Error refreshing news events: {e}")
        return {
            "success": False,
            "error": str(e),
            "source": "error_fallback"
        }


def _get_mock_news_events(hours: int, impact_levels: str = None, currencies: str = None):
    """Generate mock news events for fallback"""
    now = datetime.now()
    
    # Parse filters
    impact_filter = impact_levels.split(',') if impact_levels else ['high', 'medium', 'low']
    currency_filter = currencies.split(',') if currencies else ['USD', 'EUR', 'GBP', 'JPY', 'AUD', 'CAD', 'CHF']
    
    mock_events = []
    
    # Generate events for the requested time period
    for i in range(min(hours // 4, 10)):  # Generate up to 10 events, one every 4 hours
        event_time = now + timedelta(hours=i * 4 + 2)
        
        # Cycle through currencies and impacts
        currency = currency_filter[i % len(currency_filter)]
        impact = impact_filter[i % len(impact_filter)]
        
        # Generate event based on currency
        event_names = {
            'USD': ['Non-Farm Payrolls', 'Federal Reserve Rate Decision', 'GDP Growth Rate', 'Consumer Price Index'],
            'EUR': ['ECB Interest Rate Decision', 'German GDP', 'Eurozone Inflation', 'ECB Press Conference'],
            'GBP': ['Bank of England Rate Decision', 'UK GDP', 'UK Inflation Rate', 'Manufacturing PMI'],
            'JPY': ['Bank of Japan Rate Decision', 'Japanese GDP', 'Tokyo CPI', 'Industrial Production'],
            'AUD': ['RBA Interest Rate Decision', 'Australian GDP', 'Employment Change', 'Retail Sales'],
            'CAD': ['Bank of Canada Rate Decision', 'Canadian GDP', 'Employment Change', 'CPI'],
            'CHF': ['Swiss National Bank Rate', 'Swiss GDP', 'Swiss CPI', 'KOF Economic Barometer']
        }
        
        event_name = event_names.get(currency, ['Economic Data Release'])[i % len(event_names.get(currency, ['Economic Data Release']))]
        
        # Calculate blackout periods
        blackout_config = {
            'high': {'pre': 60, 'post': 60},
            'medium': {'pre': 30, 'post': 30},
            'low': {'pre': 15, 'post': 15}
        }
        
        config = blackout_config.get(impact, blackout_config['medium'])
        blackout_start = event_time - timedelta(minutes=config['pre'])
        blackout_end = event_time + timedelta(minutes=config['post'])
        
        mock_events.append({
            'id': i + 1,
            'event_time': event_time.isoformat(),
            'currency': currency,
            'impact_level': impact,
            'description': event_name,
            'pre_minutes': config['pre'],
            'post_minutes': config['post'],
            'blackout_start': blackout_start.isoformat(),
            'blackout_end': blackout_end.isoformat(),
            'is_active': blackout_start <= now <= blackout_end
        })
    
    return {
        "success": True,
        "events": mock_events,
        "count": len(mock_events),
        "time_range": {
            "start": now.isoformat(),
            "end": (now + timedelta(hours=hours)).isoformat()
        },
        "source": "mock_fallback"
    }


def _get_mock_active_restrictions(symbol: str = None):
    """Generate mock active restrictions"""
    now = datetime.now()
    
    # Check if we're in a mock blackout period (for demonstration)
    # Let's say there's a restriction every 6 hours for 30 minutes
    minutes_since_midnight = (now.hour * 60) + now.minute
    is_in_blackout = (minutes_since_midnight % 360) < 30  # 30 minutes every 6 hours
    
    active_restrictions = []
    
    if is_in_blackout:
        # Create a mock active restriction
        blackout_start = now.replace(minute=0, second=0, microsecond=0)
        blackout_end = blackout_start + timedelta(minutes=30)
        
        active_restrictions.append({
            'id': 1,
            'event_time': blackout_start.isoformat(),
            'currency': 'USD',
            'impact_level': 'high',
            'description': 'Federal Reserve Rate Decision',
            'pre_minutes': 15,
            'post_minutes': 15,
            'blackout_start': blackout_start.isoformat(),
            'blackout_end': blackout_end.isoformat(),
            'is_active': True
        })
    
    return {
        "success": True,
        "active_restrictions": active_restrictions,
        "count": len(active_restrictions),
        "symbol": symbol,
        "check_time": now.isoformat(),
        "source": "mock_fallback"
    }


def _get_mock_todays_events(impact_levels: str = None):
    """Generate mock events for today"""
    now = datetime.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Parse impact levels
    impact_filter = impact_levels.split(',') if impact_levels else ['high', 'medium', 'low']
    
    mock_events = [
        {
            'id': 1,
            'event_time': today_start.replace(hour=8, minute=30).isoformat(),
            'currency': 'USD',
            'impact_level': 'high',
            'description': 'Non-Farm Payrolls',
            'pre_minutes': 60,
            'post_minutes': 60,
            'blackout_start': today_start.replace(hour=7, minute=30).isoformat(),
            'blackout_end': today_start.replace(hour=9, minute=30).isoformat(),
            'is_active': False
        },
        {
            'id': 2,
            'event_time': today_start.replace(hour=14, minute=0).isoformat(),
            'currency': 'EUR',
            'impact_level': 'medium',
            'description': 'ECB Interest Rate Decision',
            'pre_minutes': 30,
            'post_minutes': 30,
            'blackout_start': today_start.replace(hour=13, minute=30).isoformat(),
            'blackout_end': today_start.replace(hour=14, minute=30).isoformat(),
            'is_active': False
        },
        {
            'id': 3,
            'event_time': today_start.replace(hour=16, minute=30).isoformat(),
            'currency': 'GBP',
            'impact_level': 'low',
            'description': 'Manufacturing PMI',
            'pre_minutes': 15,
            'post_minutes': 15,
            'blackout_start': today_start.replace(hour=16, minute=15).isoformat(),
            'blackout_end': today_start.replace(hour=16, minute=45).isoformat(),
            'is_active': False
        }
    ]
    
    # Filter by impact levels
    filtered_events = [e for e in mock_events if e['impact_level'] in impact_filter]
    
    return {
        "success": True,
        "events": filtered_events,
        "count": len(filtered_events),
        "date": now.date().isoformat(),
        "source": "mock_fallback"
    }