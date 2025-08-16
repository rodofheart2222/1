# WebSocket Integration for TickerBar

## Overview

The TickerBar component has been updated to receive real-time MT5 price data via WebSocket connection. This provides live market data instead of static demo prices.

## How It Works

1. **WebSocket Connection**: The TickerBar connects to the backend WebSocket server at `ws://155.138.174.196:8765`
2. **Authentication**: Authenticates with token `dashboard_token`
3. **Price Subscription**: Subscribes to price updates for major forex symbols
4. **Real-time Updates**: Receives price updates and displays them with smooth animations

## Data Flow

```
MT5 Terminal → Backend MT5 Service → WebSocket Server → Frontend TickerBar
```

## Price Data Structure

The WebSocket sends price updates in this format:

```json
{
  "type": "price_update",
  "data": {
    "EURUSD": {
      "symbol": "EURUSD",
      "bid": 1.0847,
      "ask": 1.0849,
      "spread": 0.0002,
      "price": 1.0848,
      "timestamp": "2024-01-01T12:00:00",
      "volume": 150000
    }
  }
}
```

## Features

- **Real-time Updates**: Live price feeds from MT5
- **Fallback System**: Falls back to demo data if WebSocket fails
- **Status Indicators**: Shows connection status and data source
- **Smooth Animations**: Price changes animate smoothly
- **Consistent Pricing**: Updates chartService for app-wide consistency

## Status Indicators

- **MT5 LIVE**: Connected to WebSocket receiving MT5 data
- **DEMO DATA**: Using fallback demo data
- **CONNECTING**: Attempting to connect to WebSocket
- **OFFLINE**: No connection available

## Testing

Use the browser console to test the WebSocket integration:

```javascript
// Test WebSocket connection and price updates
window.testTickerWebSocket()

// Test price consistency across components
window.testPriceConsistency()
```

## Configuration

The WebSocket connection can be configured in the TickerBar component:

- **WebSocket URL**: `ws://155.138.174.196:8765`
- **Auth Token**: `dashboard_token`
- **Symbols**: Major forex pairs + Gold (XAUUSD)
- **Update Frequency**: Real-time as data arrives

## Troubleshooting

1. **No Connection**: Check if backend WebSocket server is running
2. **No Price Updates**: Verify MT5 service is connected and streaming
3. **Fallback Mode**: Component will use demo data if WebSocket fails
4. **Console Logs**: Check browser console for connection status and errors

## Backend Requirements

The backend must be running:
- WebSocket server on port 8765
- MT5 price service connected to MetaTrader 5
- Price streaming enabled for subscribed symbols