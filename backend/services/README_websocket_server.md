# WebSocket Server for Real-time Communication

This module implements a WebSocket server for real-time communication between the MT5 Dashboard backend and frontend clients. It provides secure, authenticated connections with message broadcasting capabilities for EA updates, portfolio changes, and system alerts.

## Features

- **Real-time Communication**: WebSocket-based bidirectional communication
- **Authentication**: Token-based client authentication
- **Channel Subscriptions**: Clients can subscribe to specific message types
- **Message Broadcasting**: Broadcast messages to all clients or specific channel subscribers
- **Heartbeat Monitoring**: Automatic detection and cleanup of stale connections
- **Error Handling**: Robust error handling for connection failures and invalid messages
- **Integration Ready**: Easy integration with existing backend services

## Components

### 1. WebSocketServer (`websocket_server.py`)

Main WebSocket server implementation with the following capabilities:

- **Connection Management**: Handle client connections and disconnections
- **Authentication**: Secure token-based authentication
- **Message Routing**: Route messages based on type and subscriptions
- **Broadcasting**: Send messages to all clients or specific subscribers
- **Heartbeat Monitoring**: Monitor client health and cleanup stale connections

### 2. WebSocketClient (`websocket_client.py`)

Client helper for testing and integration:

- **Connection Handling**: Connect to WebSocket server
- **Authentication**: Authenticate with server using token
- **Message Handling**: Register handlers for different message types
- **Subscriptions**: Subscribe/unsubscribe from message channels

### 3. Integration Service (`websocket_integration_example.py`)

Example integration with existing backend services:

- **EA Data Monitoring**: Monitor EA status and broadcast updates
- **Portfolio Monitoring**: Calculate and broadcast portfolio metrics
- **Command Monitoring**: Monitor command execution and broadcast results
- **Alert System**: Broadcast system alerts and notifications

## Message Types

The WebSocket server supports the following message types:

### Client to Server Messages

- `auth`: Client authentication with token
- `subscribe`: Subscribe to message channels
- `unsubscribe`: Unsubscribe from message channels
- `heartbeat`: Client heartbeat ping

### Server to Client Messages

- `connection`: Connection status and welcome message
- `auth_response`: Authentication result
- `subscription_response`: Subscription confirmation
- `heartbeat_response`: Heartbeat pong
- `ea_update`: EA status update
- `portfolio_update`: Portfolio statistics update
- `trade_update`: New trade information
- `news_update`: News event update
- `command_update`: Command execution update
- `alert`: System alert or warning
- `error`: Error message

## Channel Subscriptions

Clients can subscribe to specific channels to receive targeted updates:

- `ea_updates`: Individual EA status updates
- `portfolio_updates`: Portfolio-wide statistics
- `trade_updates`: New trade notifications
- `news_updates`: News event notifications
- `command_updates`: Command execution results
- `alerts`: System alerts and warnings

## Usage Examples

### Starting the WebSocket Server

```python
from websocket_server import WebSocketServer

# Create and start server
server = WebSocketServer(
    host="127.0.0.1",
    port=8765,
    auth_token="your_auth_token"
)

await server.start_server()
```

### Using the Startup Script

```bash
# Start basic WebSocket server
python start_websocket_server.py

# Start with custom settings
python start_websocket_server.py --host 0.0.0.0 --port 8080 --auth-token "custom_token"

# Start with full integration services
python start_websocket_server.py --integrated
```

### Client Connection Example

```python
from websocket_client import WebSocketClient

# Create client
client = WebSocketClient("ws://127.0.0.1:8765", "your_auth_token")

# Register message handler
async def handle_ea_update(data):
    print(f"EA Update: {data}")

client.register_message_handler("ea_update", handle_ea_update)

# Connect and authenticate
await client.connect()
await client.authenticate()

# Subscribe to channels
await client.subscribe(["ea_updates", "portfolio_updates"])
```

### Broadcasting Messages

```python
# Broadcast EA update
await server.broadcast_ea_update({
    "ea_id": 12345,
    "symbol": "EURUSD",
    "status": "active",
    "current_profit": 150.75
})

# Broadcast portfolio update
await server.broadcast_portfolio_update({
    "total_profit": 2450.30,
    "active_eas": 15,
    "drawdown_pct": 3.8
})

# Broadcast alert
await server.broadcast_alert({
    "level": "warning",
    "message": "EA 12345 drawdown exceeds 10%",
    "ea_id": 12345
})
```

## Configuration

### Server Configuration

- `host`: Server host address (default: "127.0.0.1")
- `port`: Server port (default: 8765)
- `auth_token`: Authentication token for clients
- `heartbeat_interval`: Heartbeat check interval in seconds (default: 30)
- `heartbeat_timeout`: Client timeout in seconds (default: 60)

### Environment Variables

You can configure the server using environment variables:

```bash
export WEBSOCKET_HOST=127.0.0.1
export WEBSOCKET_PORT=8765
export WEBSOCKET_AUTH_TOKEN=your_secure_token
```

## Security Considerations

1. **Authentication**: All clients must authenticate with a valid token
2. **Token Security**: Use strong, unique tokens for production
3. **Network Security**: Consider using WSS (WebSocket Secure) for production
4. **Rate Limiting**: Implement rate limiting for production deployments
5. **Input Validation**: All incoming messages are validated and sanitized

## Testing

### Unit Tests

Run the comprehensive test suite:

```bash
# Run simplified tests
python -m pytest test_websocket_simple.py -v

# Run manual integration tests
python test_websocket_manual.py
```

### Manual Testing

Test the server manually using the provided test scripts:

```bash
# Test basic functionality
python test_websocket_manual.py

# Test with WebSocket client tools
wscat -c ws://127.0.0.1:8765
```

## Integration with Frontend

The WebSocket server is designed to work with Electron-based frontend applications. Here's how to integrate:

### JavaScript/TypeScript Client

```javascript
const ws = new WebSocket('ws://127.0.0.1:8765');

// Authenticate
ws.onopen = () => {
    ws.send(JSON.stringify({
        type: 'auth',
        data: { token: 'your_auth_token' }
    }));
};

// Handle messages
ws.onmessage = (event) => {
    const message = JSON.parse(event.data);
    
    switch (message.type) {
        case 'ea_update':
            updateEADisplay(message.data);
            break;
        case 'portfolio_update':
            updatePortfolioDisplay(message.data);
            break;
        case 'alert':
            showAlert(message.data);
            break;
    }
};

// Subscribe to channels
function subscribeToChannels() {
    ws.send(JSON.stringify({
        type: 'subscribe',
        data: { channels: ['ea_updates', 'portfolio_updates', 'alerts'] }
    }));
}
```

## Performance Considerations

- **Connection Limits**: Server can handle hundreds of concurrent connections
- **Message Batching**: Consider batching frequent updates to reduce network overhead
- **Memory Usage**: Server automatically cleans up disconnected clients
- **CPU Usage**: Minimal CPU overhead for message broadcasting
- **Network Bandwidth**: Efficient JSON message format minimizes bandwidth usage

## Troubleshooting

### Common Issues

1. **Connection Refused**: Check if server is running and port is available
2. **Authentication Failed**: Verify auth token matches server configuration
3. **Messages Not Received**: Check client subscriptions and server logs
4. **High Memory Usage**: Monitor for client connection leaks

### Debugging

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Monitoring

Monitor server health:

```python
# Get connected clients
clients = server.get_connected_clients()
print(f"Connected clients: {len(clients)}")

# Check server status
print(f"Server running: {server.running}")
```

## Requirements Fulfilled

This implementation fulfills the following requirements from the specification:

- **Requirement 7.4**: Secure command queue between EA and COC
- **Requirement 6.3**: Real-time data synchronization and updates

## Files

- `websocket_server.py`: Main WebSocket server implementation
- `websocket_client.py`: Client helper for testing and integration
- `websocket_integration_example.py`: Integration with backend services
- `start_websocket_server.py`: Server startup script
- `test_websocket_simple.py`: Unit tests
- `test_websocket_manual.py`: Manual integration tests
- `README_websocket_server.md`: This documentation file