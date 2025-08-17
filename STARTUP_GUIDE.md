# MT5 Dashboard Comprehensive Startup Guide

## Overview

The `startup.py` script is a comprehensive system launcher that handles the entire lifecycle of the MT5 Dashboard application, including:

- Process cleanup
- Running tests
- Starting backend services (API + WebSocket)
- Starting frontend development server
- Health monitoring with auto-restart
- Graceful shutdown

## Quick Start

### Basic Usage

```bash
# Start everything with defaults
python startup.py

# Skip tests for faster startup
python startup.py --skip-tests

# Use custom ports
python startup.py --backend-port 8080 --frontend-port 3001
```

## Features

### 1. **Automatic Process Cleanup**
- Kills any existing processes on required ports
- Cleans up orphaned Node.js and Python processes
- Ensures a clean slate before starting

### 2. **Test Execution**
- Runs backend tests (pytest)
- Runs frontend tests (npm test)
- Can be skipped with `--skip-tests` flag
- Continues startup even if some tests fail

### 3. **Service Management**
- Starts backend API server (FastAPI)
- Starts WebSocket server (for real-time updates)
- Starts frontend development server (React)
- All services run concurrently

### 4. **Health Monitoring**
- Periodic health checks every 30 seconds
- Displays service status with visual indicators
- Automatic restart on crash (up to 3 attempts)

### 5. **Colored Output**
- Green: Success messages
- Yellow: Warnings
- Red: Errors
- Color-coded service logs for easy monitoring

## Command Line Options

```bash
python startup.py [OPTIONS]

Options:
  --host HOST              Server host (default: 155.138.174.196)
  --backend-port PORT      Backend API port (default: 8000)
  --frontend-port PORT     Frontend dev server port (default: 3000)
  --ws-port PORT          WebSocket server port (default: 8765)
  --skip-tests            Skip running tests before startup
```

## What Happens During Startup

1. **Cleanup Phase**
   - Terminates processes on ports 8000, 3000, 8765
   - Kills related Python/Node processes

2. **Environment Setup**
   - Configures Python paths
   - Sets environment variables
   - Updates frontend .env configuration

3. **Test Phase** (unless skipped)
   - Runs `pytest` in backend/tests
   - Runs `npm test` in frontend
   - Reports test results

4. **Service Startup**
   - Backend server starts first
   - 5-second delay for backend initialization
   - Frontend server starts
   - 10-second wait for full initialization

5. **Monitoring Loop**
   - Health checks every 30 seconds
   - Auto-restart failed services
   - Display health status

## Service URLs

After successful startup, you can access:

- **Frontend**: http://155.138.174.196:3000
- **Backend API**: http://155.138.174.196:8000
- **API Documentation**: http://155.138.174.196:8000/docs
- **Health Check**: http://155.138.174.196:8000/health
- **WebSocket**: ws://155.138.174.196:8765

## Health Status Indicators

```
✅ BACKEND: healthy
✅ FRONTEND: healthy
✅ WEBSOCKET: healthy
⚠️ SERVICE: unhealthy (temporary issue)
❌ SERVICE: crashed (will auto-restart)
🔄 SERVICE: starting
⏹️ SERVICE: stopped
```

## Troubleshooting

### Port Already in Use
The script automatically kills processes on required ports. If issues persist:
```bash
# Check what's using a port
lsof -i :8000
# or
netstat -tulpn | grep 8000
```

### Frontend Not Starting
- Ensure `node_modules` exists: `cd frontend && npm install`
- Check Node.js version: `node --version` (requires v14+)

### Backend Not Starting
- Check Python version: `python --version` (requires 3.8+)
- Install dependencies: `pip install -r backend/requirements.txt`

### Tests Failing
- Run tests individually to debug:
  ```bash
  cd backend && pytest -v
  cd frontend && npm test
  ```

## Stopping the System

Press `Ctrl+C` to initiate graceful shutdown:
- All services will be terminated
- Cleanup will be performed
- Exit code indicates success (0) or failure (1)

## Advanced Usage

### Running in Background
```bash
# Using nohup
nohup python startup.py --skip-tests > startup.log 2>&1 &

# Using screen
screen -S mt5-dashboard
python startup.py
# Detach with Ctrl+A, D
```

### Custom Configuration
Edit the script defaults in the `ComprehensiveSystemRunner` class:
- `max_restarts`: Maximum restart attempts (default: 3)
- `health_check_interval`: Seconds between health checks (default: 30)

## Dependencies

The script will automatically install `aiohttp` if not present (used for health checks).

Other required dependencies:
- Python 3.8+
- Node.js 14+
- All packages in `backend/requirements.txt`
- All packages in `frontend/package.json`

## Development Tips

1. **Fast Iteration**: Use `--skip-tests` during development
2. **Debug Mode**: Check individual service logs in the colored output
3. **Manual Testing**: Access the health endpoint to verify service status
4. **Process Management**: The script handles all process lifecycle automatically

## Error Codes

- `0`: Successful execution
- `1`: Error during startup or runtime
- Signal handling for `SIGINT` and `SIGTERM`