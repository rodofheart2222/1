# MT5 Dashboard Configuration Guide

## Overview

The MT5 Dashboard system now uses environment-based configuration to eliminate hardcoded values and make deployment flexible across different environments.

## Configuration Methods

### 1. Environment File (.env)

Create a `.env` file in the project root:

```bash
# Copy the example file
cp .env.example .env

# Edit with your values
nano .env
```

### 2. System Environment Variables

Set environment variables directly:

```bash
export MT5_HOST=0.0.0.0
export MT5_API_PORT=80
export MT5_WS_PORT=8765
export MT5_AUTH_TOKEN=your_secure_token
```

### 3. Command Line Arguments

Override config with command line arguments:

```bash
python backend/start_complete_server.py --host 0.0.0.0 --port 80 --ws-port 8765
```

## Configuration Variables

### Server Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `MT5_HOST` | `0.0.0.0` | Server bind address (0.0.0.0 for all interfaces) |
| `MT5_EXTERNAL_HOST` | `127.0.0.1` | External host for client connections |
| `MT5_API_PORT` | `80` (dev) / `80` (prod) | FastAPI server port |
| `MT5_WS_PORT` | `8765` | WebSocket server port |
| `MT5_FRONTEND_PORT` | `3000` | Frontend development server port |

### Environment

| Variable | Default | Description |
|----------|---------|-------------|
| `ENVIRONMENT` | `development` | Environment mode (development/production) |
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG/INFO/WARNING/ERROR) |

### Security

| Variable | Default | Description |
|----------|---------|-------------|
| `MT5_AUTH_TOKEN` | `dashboard_token_2024` | WebSocket authentication token |

### Database

| Variable | Default | Description |
|----------|---------|-------------|
| `MT5_DB_PATH` | `data/mt5_dashboard.db` | SQLite database file path |

### CORS

| Variable | Default | Description |
|----------|---------|-------------|
| `CORS_ORIGINS` | Auto-generated | Comma-separated list of allowed origins |

## Environment Examples

### Development Environment

```bash
# .env for development
ENVIRONMENT=development
MT5_HOST=0.0.0.0
MT5_EXTERNAL_HOST=127.0.0.1
MT5_API_PORT=80
MT5_WS_PORT=8765
MT5_FRONTEND_PORT=3000
MT5_AUTH_TOKEN=dev_token_change_this
LOG_LEVEL=DEBUG
```

### Production Environment

```bash
# .env for production
ENVIRONMENT=production
MT5_HOST=0.0.0.0
MT5_EXTERNAL_HOST=your-server-domain.com
MT5_API_PORT=80
MT5_WS_PORT=8765
MT5_FRONTEND_PORT=3000
MT5_AUTH_TOKEN=very_secure_production_token_here
LOG_LEVEL=INFO
CORS_ORIGINS=https://your-frontend-domain.com,https://api.your-domain.com
```

### Docker Environment

```bash
# .env for Docker
ENVIRONMENT=production
MT5_HOST=0.0.0.0
MT5_EXTERNAL_HOST=localhost
MT5_API_PORT=80
MT5_WS_PORT=8765
MT5_AUTH_TOKEN=docker_secure_token
MT5_DB_PATH=/app/data/mt5_dashboard.db
```

## Migration from Hardcoded Values

### Before (Hardcoded)
```python
# Old hardcoded approach
host = "127.0.0.1"
port = 80
ws_port = 8765
auth_token = "dashboard_token_2024"
```

### After (Configurable)
```python
# New configurable approach
from config.environment import Config

host = Config.get_host()
port = Config.get_api_port()
ws_port = Config.get_ws_port()
auth_token = Config.get_auth_token()
```

## Configuration Priority

Configuration values are resolved in this order (highest to lowest priority):

1. **Command line arguments** (highest priority)
2. **Environment variables**
3. **`.env` file**
4. **Default values** (lowest priority)

## Security Best Practices

### 1. Authentication Tokens

- **Never commit tokens to version control**
- **Use strong, unique tokens for each environment**
- **Rotate tokens regularly**

```bash
# Generate secure token
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 2. Environment Files

- **Add `.env` to `.gitignore`**
- **Use `.env.example` for documentation**
- **Set restrictive file permissions**

```bash
# Secure .env file permissions
chmod 600 .env
```

### 3. Production Deployment

- **Use system environment variables instead of .env files**
- **Use secrets management systems (AWS Secrets Manager, etc.)**
- **Enable HTTPS in production**

## Troubleshooting

### Configuration Not Loading

1. **Check .env file exists and is readable**
```bash
ls -la .env
```

2. **Verify environment variables are set**
```bash
python load_env.py
```

3. **Check configuration values**
```python
from backend.config.environment import Config
print(Config.get_all_config())
```

### Port Conflicts

1. **Check what's using the port**
```bash
netstat -an | grep :80
```

2. **Change port in configuration**
```bash
export MT5_API_PORT=8001
```

### Connection Issues

1. **Verify host binding**
   - Use `0.0.0.0` to bind to all interfaces
   - Use `127.0.0.1` for localhost only

2. **Check firewall settings**
   - Ensure ports are open
   - Verify CORS origins are correct

### Frontend Connection Issues

1. **Check frontend .env file**
```bash
cat frontend/.env
```

2. **Verify API URL matches backend**
```bash
# Should match your backend configuration
REACT_APP_API_URL=http://127.0.0.1:80
REACT_APP_WS_URL=ws://127.0.0.1:8765
```

## Testing Configuration

### Test Environment Loading
```bash
python load_env.py
```

### Test Server Startup
```bash
python backend/start_complete_server.py --help
```

### Test Health Check
```bash
python test_system_health.py
```

## Advanced Configuration

### Custom Configuration Class

You can extend the configuration system:

```python
from backend.config.environment import Config

class CustomConfig(Config):
    @classmethod
    def get_custom_setting(cls):
        return os.getenv("CUSTOM_SETTING", "default_value")
```

### Runtime Configuration Changes

Some settings can be changed at runtime:

```python
import os
os.environ["LOG_LEVEL"] = "DEBUG"

# Restart logging to pick up new level
import logging
logging.getLogger().setLevel(os.getenv("LOG_LEVEL", "INFO"))
```

This configuration system provides flexibility while maintaining security and ease of deployment across different environments.