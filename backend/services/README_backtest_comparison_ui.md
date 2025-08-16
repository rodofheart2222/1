# Backtest Comparison UI Implementation

## Overview

The Backtest Comparison UI provides a comprehensive interface for uploading MT5 backtest reports, comparing live EA performance against backtest benchmarks, and monitoring performance deviations with visual alerts and auto-flagging capabilities.

## Features Implemented

### 1. Drag-and-Drop Upload Interface
- **File Upload Modal**: Modal dialog for selecting EA and uploading HTML backtest reports
- **Drag-and-Drop Support**: Users can drag MT5 HTML reports directly into the upload area
- **File Validation**: Only accepts .html and .htm files
- **EA Selection**: Dropdown to select which EA the backtest report belongs to

### 2. Live vs Backtest Comparison Dashboard
- **Deviation Reports Table**: Shows all EAs with their performance deviations
- **Status Indicators**: Color-coded status (Good 🟢, Warning 🟡, Critical )
- **Metric Comparisons**: 
  - Profit Factor deviation
  - Expected Payoff deviation
  - Drawdown deviation
  - Win Rate deviation
- **Progress Bars**: Visual representation of deviation percentages
- **Expandable Rows**: Detailed information including recommendations and alerts

### 3. Visual Alerts for Performance Degradation
- **Color-Coded Indicators**: 
  - Green: Performance within acceptable range
  - Yellow: Warning level deviations (15-30% for most metrics)
  - Red: Critical level deviations (>30% for most metrics)
- **Alert Messages**: Descriptive messages like " Live profit_factor down 35.2% from backtest"
- **Critical Alert Banner**: System-wide alert when critical deviations are detected
- **Alert Badges**: Show number and type of alerts per EA

### 4. Performance Trend Charts
- **Interactive Charts**: Line charts showing live vs backtest metrics over time
- **Multiple Metrics**: Profit Factor, Expected Payoff, Drawdown trends
- **Modal Display**: Charts open in dedicated modal windows
- **Historical Data**: 30-day trend visualization

### 5. Auto-Flagging Notifications
- **Automatic Detection**: System automatically flags EAs with critical performance issues
- **Flagging Criteria**:
  - Profit Factor drops >30% from backtest
  - Multiple critical alerts (2 or more)
  - Consecutive days of performance degradation
- **Action Recommendations**: 
  - "CONTINUE: Performance within acceptable range"
  - "MONITOR: Watch closely for further degradation"
  - "URGENT: Review EA settings and consider risk reduction"
  - "IMMEDIATE ACTION: Consider EA demotion or shutdown"

## Technical Implementation

### Frontend Components

#### BacktestComparisonPanel.js
Main component providing:
- Upload interface with drag-and-drop support
- Performance summary statistics
- Deviation reports table with filtering and search
- Chart modal for trend visualization
- Integration with dashboard context

#### Key Features:
```javascript
// File upload with validation
const handleFileUpload = async (file, eaId) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('ea_id', eaId);
  // Upload to backend API
};

// Status color coding
const getStatusColor = (status) => {
  switch (status) {
    case 'good': return 'success';
    case 'warning': return 'warning';
    case 'critical': return 'error';
  }
};

// Deviation visualization
const getDeviationColor = (deviation) => {
  if (Math.abs(deviation) >= 30) return '#ff4d4f';
  if (Math.abs(deviation) >= 15) return '#faad14';
  return '#52c41a';
};
```

### Backend Services

#### backtest_routes.py
API endpoints for:
- `/api/backtest/upload` - Upload and parse HTML reports
- `/api/backtest/benchmarks` - Get all backtest benchmarks
- `/api/backtest/deviations` - Get deviation reports
- `/api/backtest/flagged` - Get EAs flagged for demotion
- `/api/backtest/compare` - Compare specific EA performance

#### backtest_service.py
Core service providing:
- HTML report parsing and storage
- Live vs backtest comparison
- Deviation calculation and alerting
- Auto-flagging logic

#### backtest_comparison.py
Comparison engine with:
- Configurable deviation thresholds
- Alert level determination
- Recommendation generation
- Visual indicator selection

### Integration Features

#### Real-time Monitoring
```python
class BacktestComparisonIntegration:
    async def monitor_performance_deviations(self):
        # Get all deviation reports
        deviation_reports = self.backtest_service.get_all_deviations()
        
        # Process each report for auto-actions
        for report in deviation_reports:
            if self.should_auto_flag_ea(report):
                await self.auto_flag_ea_for_demotion(report)
        
        # Broadcast updates to frontend
        await self.broadcast_deviation_updates(deviation_reports)
```

#### WebSocket Integration
- Real-time updates when new backtest reports are uploaded
- Live deviation status changes
- Auto-flagging notifications
- Performance alert broadcasting

## Usage Instructions

### 1. Upload Backtest Report
1. Click "Upload Report" button
2. Select the EA from dropdown
3. Drag and drop MT5 HTML backtest report or click to browse
4. System automatically parses and stores the benchmark

### 2. Monitor Performance Deviations
1. View the main comparison table showing all EAs
2. Use filters to focus on specific status levels (Good/Warning/Critical)
3. Search by symbol or strategy name
4. Click on rows to expand for detailed information

### 3. Analyze Trends
1. Click "Chart" button for any EA
2. View interactive trend charts comparing live vs backtest performance
3. Identify patterns and degradation over time

### 4. Handle Alerts
1. Review critical alerts in the banner
2. Check EA recommendations in expanded rows
3. Use "Flag" button for critical EAs to mark for demotion
4. Monitor auto-flagged EAs in the system

## Configuration

### Deviation Thresholds
```python
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
```

### Auto-Flagging Criteria
```python
self.auto_flag_thresholds = {
    'profit_factor_drop': -30.0,  # Auto-flag if PF drops >30%
    'multiple_critical_alerts': 2,  # Auto-flag if 2+ critical alerts
    'consecutive_degradation_days': 3  # Auto-flag after 3 days of degradation
}
```

## Testing

Comprehensive test suite covering:
- Component rendering and interaction
- File upload functionality
- Data filtering and searching
- Chart modal operations
- Error handling
- API integration

Run tests:
```bash
npm test BacktestComparisonPanel.test.js
```

## Requirements Satisfied

 **2.1**: Upload backtest reports - HTML reports accepted and parsed for PF, EP, DD, Win Rate, Trade Count  
 **2.2**: Live vs backtest comparison - Highlights PF drops, drawdown increases, and significant deviations  
 **2.3**: Visual alerts for performance degradation - Color-coded indicators ( Live PF down >30%)  
 **2.4**: Auto-flagging integration - EAs auto-flagged for demotion based on performance deviation  

## Future Enhancements

1. **Batch Upload**: Support for uploading multiple backtest reports at once
2. **Historical Comparison**: Compare against multiple historical backtests
3. **Custom Thresholds**: Allow users to configure deviation thresholds per EA
4. **Export Reports**: Export deviation reports to PDF or Excel
5. **Advanced Charts**: More chart types and technical indicators
6. **Mobile Optimization**: Responsive design for mobile devices