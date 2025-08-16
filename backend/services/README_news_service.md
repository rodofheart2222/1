# News Event Filtering Service

## Overview

The News Event Filtering Service provides comprehensive news-based trading restrictions for the MT5 COC Dashboard system. It integrates with external news APIs to fetch economic calendar events and automatically manages trading blackout periods based on news impact levels.

## Features

### Core Functionality
- **News API Integration**: Fetches economic calendar events from external APIs
- **Impact Level Filtering**: Supports High, Medium, and Low impact level categorization
- **Trading Blackout Periods**: Automatically calculates and enforces trading restrictions
- **Symbol-Specific Filtering**: Determines which trading symbols are affected by each news event
- **Real-time Monitoring**: Continuously monitors for active and upcoming news restrictions

### Key Components

#### 1. NewsAPIClient
- Fetches economic calendar data from external APIs
- Handles API authentication and error recovery
- Provides mock data for testing and development

#### 2. NewsEventFilter
- Main service class for news filtering functionality
- Manages news event storage and retrieval
- Calculates trading restrictions and blackout periods
- Provides filtering by impact level, currency, and time range

#### 3. NewsEventScheduler
- Handles scheduled news updates and maintenance
- Provides emergency news checking for high-impact events
- Manages cleanup of old news events

#### 4. NewsEvent Model
- Database model for storing news events
- Calculates blackout periods based on event timing
- Determines symbol affection logic
- Provides JSON serialization for API responses

## Usage Examples

### Basic News Filtering

```python
from backend.services.news_service import NewsEventFilter
from backend.database.connection import get_db_session

# Initialize the news filter
db_session = get_db_session()
news_filter = NewsEventFilter(db_session)

# Fetch and store latest news events
stored_count = news_filter.fetch_and_store_news_events()
print(f"Stored {stored_count} new events")

# Check if trading is allowed for a symbol
trading_status = news_filter.check_trading_allowed('EURUSD')
if trading_status['trading_allowed']:
    print("Trading is allowed for EURUSD")
else:
    print(f"Trading blocked due to {len(trading_status['active_restrictions'])} restrictions")

# Get today's high-impact events
high_impact_events = news_filter.get_todays_events(impact_levels=['high'])
for event in high_impact_events:
    print(f"High impact: {event.description} at {event.event_time}")
```

### Integration with EA Management

```python
from backend.services.news_integration_example import NewsIntegratedTradingManager

# Initialize integrated trading manager
trading_manager = NewsIntegratedTradingManager()

# Get news dashboard data
dashboard_data = trading_manager.get_news_dashboard_data()
print(f"Active restrictions: {len(dashboard_data['active_restrictions'])}")
print(f"Affected symbols: {dashboard_data['trading_blocked_symbols']}")

# Start continuous monitoring (in production)
# await trading_manager.start_news_monitoring()
```

### Configuration Management

```python
from backend.services.news_integration_example import NewsConfigurationManager

# Initialize configuration manager
config_manager = NewsConfigurationManager()

# Update blackout periods for high-impact events
config_manager.update_impact_level_settings('high', 90, 90)  # 90 min before/after

# Get current settings
settings = config_manager.get_current_settings()
print(f"Current blackout periods: {settings['blackout_periods']}")
```

## API Reference

### NewsEventFilter Methods

#### `fetch_and_store_news_events(start_date=None, end_date=None)`
Fetches news events from external API and stores them in database.
- **Returns**: Number of events stored
- **Parameters**:
  - `start_date`: Start date for events (default: today)
  - `end_date`: End date for events (default: 7 days from start)

#### `check_trading_allowed(symbol, check_time=None)`
Checks if trading is allowed for a symbol at given time.
- **Returns**: Dict with trading status and active restrictions
- **Parameters**:
  - `symbol`: Trading symbol (e.g., 'EURUSD', 'XAUUSD')
  - `check_time`: Time to check (default: current time)

#### `get_filtered_events(impact_levels=None, currencies=None, start_time=None, end_time=None)`
Gets filtered news events based on criteria.
- **Returns**: List of filtered NewsEvent objects
- **Parameters**:
  - `impact_levels`: List of impact levels ['high', 'medium', 'low']
  - `currencies`: List of currencies ['USD', 'EUR', etc.]
  - `start_time`: Start time for events
  - `end_time`: End time for events

#### `get_active_restrictions(symbol=None, check_time=None)`
Gets currently active news restrictions.
- **Returns**: List of active NewsEvent restrictions
- **Parameters**:
  - `symbol`: Optional symbol to filter restrictions
  - `check_time`: Time to check (default: current time)

#### `get_next_blackout_periods(symbol, hours_ahead=24)`
Gets upcoming blackout periods for a symbol.
- **Returns**: List of upcoming blackout periods with timing info
- **Parameters**:
  - `symbol`: Trading symbol
  - `hours_ahead`: How many hours ahead to look

### NewsEvent Model Properties

#### Calculated Properties
- `blackout_start`: Start time of blackout period
- `blackout_end`: End time of blackout period

#### Methods
- `is_in_blackout_period(check_time=None)`: Check if time is in blackout period
- `affects_symbol(symbol)`: Check if event affects given trading symbol
- `to_dict()`: Convert to dictionary for JSON serialization

## Configuration

### Default Blackout Periods
```python
default_blackout_periods = {
    'high': {'pre': 60, 'post': 60},      # 1 hour before/after
    'medium': {'pre': 30, 'post': 30},    # 30 minutes before/after
    'low': {'pre': 15, 'post': 15}        # 15 minutes before/after
}
```

### Impact Level Mapping
- **High**: Major economic releases (NFP, FOMC, ECB rates)
- **Medium**: Important but less market-moving events
- **Low**: Minor economic indicators

### Symbol Affection Logic
- **Forex Pairs**: Currency affects pairs containing that currency (USD affects EURUSD, USDJPY)
- **Commodities**: Currency affects instruments denominated in that currency (USD affects XAUUSD)
- **Indices**: Currency affects related indices (USD affects US30, SPX500)

## Database Schema

The news service uses the `news_events` table:

```sql
CREATE TABLE news_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_time TIMESTAMP NOT NULL,
    currency TEXT NOT NULL,
    impact_level TEXT NOT NULL CHECK (impact_level IN ('high', 'medium', 'low')),
    description TEXT NOT NULL,
    pre_minutes INTEGER DEFAULT 30,
    post_minutes INTEGER DEFAULT 30
);
```

## Testing

Run the comprehensive test suite:

```bash
python -m pytest backend/services/test_news_service.py -v
```

### Test Coverage
- **NewsAPIClient**: API integration and error handling
- **NewsEventFilter**: Core filtering and restriction logic
- **NewsEventScheduler**: Scheduled updates and emergency checks
- **NewsEvent Model**: Blackout calculations and symbol affection
- **Integration**: End-to-end workflow testing

## Requirements Compliance

This implementation satisfies all requirements from section 4:

### Requirement 4.1: News Event Blocking
 **WHEN news events are scheduled THEN the system SHALL block new trades X minutes before and after based on impact level**
- Implemented via `check_trading_allowed()` method
- Configurable blackout periods by impact level
- Real-time restriction checking

### Requirement 4.2: Existing Trade Protection
 **WHEN existing trades are active during news THEN the system SHALL prevent SL/TP/trailing changes and manual closures during blackout periods**
- Integrated with command dispatcher to block modifications
- Active restriction detection for ongoing trades

### Requirement 4.3: Impact Level Configuration
 **WHEN configuring news filters THEN the system SHALL support High (Red), Medium (Orange), and Low (Yellow) impact levels with High as default**
- Three-tier impact level system implemented
- Configurable blackout periods per impact level
- High impact events prioritized in emergency checks

### Requirement 4.4: Event Display
 **WHEN displaying events THEN the system SHALL show today's filtered news with Time (Local or VPS), Currency/Affected Asset, Impact Level, and News Description**
- Complete event information in `to_dict()` method
- Today's events filtering via `get_todays_events()`
- Dashboard integration with formatted display data

## Error Handling

The service includes comprehensive error handling:
- API connection failures with fallback to mock data
- Database connection issues with graceful degradation
- Invalid event data parsing with logging
- Duplicate event prevention
- Automatic cleanup of old events

## Performance Considerations

- Database indexing on event_time for fast queries
- In-memory filtering for complex blackout calculations
- Batch operations for multiple event storage
- Configurable cleanup intervals for old data
- Efficient symbol matching algorithms

## Future Enhancements

Potential improvements for future versions:
- Multiple news API provider support
- Machine learning for impact level prediction
- Custom blackout period rules per symbol
- Historical news impact analysis
- Real-time news sentiment analysis
- Integration with more economic calendar sources