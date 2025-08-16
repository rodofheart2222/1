# Backtest Comparison Module

## Overview

The backtest comparison module provides comprehensive functionality for parsing MT5 backtest HTML reports, comparing live EA performance against backtest benchmarks, and generating alerts for performance degradation.

## Components Implemented

### 1. HTML Report Parser (`backtest_parser.py`)

**Features:**
- Parses MT5 backtest HTML reports to extract key metrics
- Supports multiple HTML formats and layouts
- Robust regex patterns for metric extraction
- Handles edge cases like missing data and malformed HTML

**Extracted Metrics:**
- Profit Factor (PF)
- Expected Payoff (EP)
- Maximum Drawdown (DD)
- Win Rate (WR)
- Trade Count
- Total Net Profit

**Usage:**
```python
from backend.services.backtest_parser import BacktestHTMLParser

parser = BacktestHTMLParser()
metrics = parser.parse_html_report(html_content)
# or
metrics = parser.parse_file("backtest_report.html")
```

### 2. Deviation Calculator (`backtest_comparison.py`)

**Features:**
- Compares live performance with backtest benchmarks
- Calculates percentage deviations for all metrics
- Generates tiered alerts (INFO, WARNING, CRITICAL)
- Provides visual indicators and recommendations
- Auto-flagging logic for EA demotion

**Alert Thresholds:**
- Profit Factor: Warning at 15%, Critical at 30% deviation
- Expected Payoff: Warning at 20%, Critical at 40% deviation
- Drawdown: Warning at 25%, Critical at 50% increase
- Win Rate: Warning at 10%, Critical at 20% deviation

**Usage:**
```python
from backend.services.backtest_comparison import BacktestComparison

comparison = BacktestComparison()
deviation_report = comparison.calculate_deviation(live_metrics, backtest_metrics)
should_flag = comparison.should_flag_for_demotion(deviation_report)
```

### 3. Backtest Service (`backtest_service.py`)

**Features:**
- High-level API for backtest operations
- Database integration for benchmark storage
- Batch processing for multiple EAs
- Summary statistics and reporting

**Key Methods:**
- `upload_backtest_report()` - Parse and store backtest data
- `compare_with_backtest()` - Compare live vs backtest performance
- `get_eas_flagged_for_demotion()` - Get EAs requiring attention
- `get_benchmark_summary()` - Portfolio-level statistics

### 4. Performance Metrics Model (`models/performance.py`)

**Added:**
- `PerformanceMetrics` dataclass for standardized metric handling
- Integration with existing `PerformanceHistory` and `BacktestBenchmark` models

## Requirements Fulfilled

 **Requirement 2.1**: Accept HTML reports from MT5 and extract PF, EP, DD, Win Rate, and Trade Count
 **Requirement 2.2**: Highlight PF drops, drawdown increases, and other significant deviations
 **Requirement 2.3**: Flag with visual indicators ( Live PF down >30%)
 **Requirement 2.4**: Auto-flag EAs for demotion or recovery mode based on performance deviation

## Testing

Comprehensive test suite implemented:

### Parser Tests (`test_backtest_parser.py`)
-  Complete HTML report parsing
-  Alternative format handling
-  Missing metrics detection
-  Invalid HTML handling
-  Case insensitive parsing
-  Extra whitespace handling
-  File parsing functionality

### Comparison Tests (`test_backtest_comparison.py`)
-  Normal performance scenarios
-  Warning level deviations
-  Critical level deviations
-  Percentage deviation calculations
-  Drawdown deviation logic
-  Alert generation
-  Overall status determination
-  Recommendation generation
-  Demotion flagging logic
-  Visual indicator generation

### Integration Example (`backtest_integration_example.py`)
-  End-to-end parsing demonstration
-  Performance comparison scenarios
-  Alert generation examples
-  Good vs poor performance comparison

## Database Schema

The module integrates with the existing `backtest_benchmarks` table:

```sql
CREATE TABLE backtest_benchmarks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ea_id INTEGER NOT NULL,
    profit_factor REAL NOT NULL,
    expected_payoff REAL NOT NULL,
    drawdown REAL NOT NULL,
    win_rate REAL NOT NULL,
    trade_count INTEGER NOT NULL,
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ea_id) REFERENCES eas(id) ON DELETE CASCADE
);
```

## Example Output

### Critical Performance Alert
```
 Deviation Analysis:
   Overall Status: CRITICAL
   Visual Indicator: 
   Profit Factor Deviation: -32.4%
   Expected Payoff Deviation: -37.7%
   Drawdown Deviation: 4.3%

 Alerts (3):
    Live profit_factor down 32.4% from backtest
   🟡 Live expected_payoff down 37.7% from backtest
    Live drawdown 50.6% higher than backtest

 Recommendation: IMMEDIATE ACTION: Consider EA demotion or shutdown
️  Flag for Demotion: YES
```

### Good Performance
```
 Good Performance Example:
   Overall Status: GOOD
   Visual Indicator: 🟢
   Alerts: 0
   Recommendation: CONTINUE: Performance within acceptable range
   Flag for Demotion: NO
```

## Integration Points

The backtest comparison module integrates with:

1. **EA Data Collector** - Receives live performance metrics
2. **Command Dispatcher** - Can trigger EA demotion commands
3. **Dashboard Frontend** - Provides visual indicators and alerts
4. **Database Layer** - Stores benchmarks and retrieves live data

## Next Steps

The module is ready for integration with:
- WebSocket server for real-time alerts
- Frontend dashboard components
- Automated EA management workflows
- Performance monitoring systems