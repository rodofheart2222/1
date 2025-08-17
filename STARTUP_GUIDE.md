# 🚀 MT5 Dashboard Startup Guide

This guide explains how to start the MT5 Dashboard system using the provided startup scripts.

## 📋 Prerequisites

Before running the startup scripts, ensure you have the following installed:

- **Python 3.8+** - for the backend API server
- **Node.js 16+** - for the frontend React application  
- **npm** - for managing frontend dependencies

## 🎯 Quick Start

### Option 1: Python Startup Script (Recommended)

The Python script provides the most features and robust error handling:

```bash
# Start everything in development mode
python3 start.py

# Start everything in production mode
python3 start.py --prod

# Start only the backend
python3 start.py --backend-only

# Start only the frontend
python3 start.py --frontend-only

# Custom ports
python3 start.py --port 8080 --frontend-port 3001

# Don't open browser automatically
python3 start.py --no-browser
```

### Option 2: Shell Script (Simple)

For a simpler approach, use the bash script:

```bash
# Start everything with default settings
./start.sh

# With environment variables
BACKEND_PORT=8080 FRONTEND_PORT=3001 ./start.sh

# Production mode
MODE=prod ./start.sh
```

## 📚 Startup Script Features

### What the Scripts Do

1. **🔍 Dependency Check** - Verifies Python, Node.js, and npm are installed
2. **🔧 Environment Setup** - Configures environment variables
3. **🗄️ Database Initialization** - Creates SQLite database and applies migrations
4. **📦 Dependency Installation** - Installs Python and Node.js packages
5. **🚀 Service Startup** - Launches backend and frontend servers
6. **🌐 Browser Launch** - Opens the dashboard in your default browser
7. **🛑 Graceful Shutdown** - Handles Ctrl+C to stop all services cleanly

### Default Configuration

- **Backend**: http://127.0.0.1:8000
- **Frontend**: http://localhost:3000
- **Database**: SQLite at `data/mt5_dashboard.db`
- **Mode**: Development

## 🔧 Command Line Options

### Python Script Options

| Option | Description | Default |
|--------|-------------|---------|
| `--dev` | Development mode (hot reload) | ✅ Default |
| `--prod` | Production mode (optimized build) | |
| `--backend-only` | Start only backend server | |
| `--frontend-only` | Start only frontend server | |
| `--port PORT` | Backend server port | 8000 |
| `--frontend-port PORT` | Frontend server port | 3000 |
| `--host HOST` | Backend server host | 127.0.0.1 |
| `--no-browser` | Don't open browser automatically | |
| `--help` | Show help message | |

### Shell Script Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `BACKEND_PORT` | Backend server port | 8000 |
| `FRONTEND_PORT` | Frontend server port | 3000 |
| `HOST` | Backend server host | 127.0.0.1 |
| `MODE` | Development or production mode | dev |

## 📖 Usage Examples

### Development Workflow

```bash
# Standard development startup
python3 start.py

# Backend development only (if working on API)
python3 start.py --backend-only

# Frontend development only (if backend is running elsewhere)
python3 start.py --frontend-only --host 192.168.1.100
```

### Production Deployment

```bash
# Production mode with custom ports
python3 start.py --prod --port 80 --frontend-port 80 --host 0.0.0.0

# Or with shell script
MODE=prod BACKEND_PORT=80 HOST=0.0.0.0 ./start.sh
```

### Testing Different Configurations

```bash
# Test with different ports to avoid conflicts
python3 start.py --port 8080 --frontend-port 3001

# Headless mode (no browser)
python3 start.py --no-browser
```

## 🌐 Accessing the Dashboard

Once started, you can access:

- **🌐 Frontend Dashboard**: http://localhost:3000
- **🔧 Backend API**: http://127.0.0.1:8000
- **📊 API Documentation**: http://127.0.0.1:8000/docs
- **🔍 API Schema**: http://127.0.0.1:8000/redoc

## 🛠️ Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   python3 start.py --port 8080 --frontend-port 3001
   ```

2. **Permission Errors**
   ```bash
   chmod +x start.py start.sh
   ```

3. **Missing Dependencies**
   - The script will install them automatically
   - If it fails, install manually:
   ```bash
   pip3 install --break-system-packages fastapi uvicorn sqlalchemy
   cd frontend && npm install --legacy-peer-deps
   ```

4. **Database Issues**
   - Delete `data/mt5_dashboard.db` and restart
   - The script will recreate it automatically

5. **Frontend Build Fails**
   ```bash
   cd frontend
   rm -rf node_modules package-lock.json
   npm install --legacy-peer-deps
   ```

### Logs and Debugging

The Python script provides detailed logging with timestamps and colors:
- 🔍 Info messages in cyan
- ✅ Success messages in green  
- ⚠️ Warnings in yellow
- ❌ Errors in red

### Manual Startup (If Scripts Fail)

Backend only:
```bash
cd backend
python3 main.py
```

Frontend only:
```bash
cd frontend
npm run dev
```

## 🔄 Stopping the Services

- Press **Ctrl+C** in the terminal where the script is running
- The script will gracefully shutdown both services
- All processes will be terminated cleanly

## 📁 File Structure

```
MT5-Dashboard/
├── start.py          # Main Python startup script
├── start.sh           # Simple bash startup script
├── backend/           # Python FastAPI backend
│   ├── main.py        # Backend entry point
│   └── database/      # Database schemas and migrations
├── frontend/          # React frontend
│   ├── package.json   # Frontend dependencies
│   └── src/           # Frontend source code
└── data/              # Database and data files
    └── mt5_dashboard.db
```

## 🎉 Success!

When everything starts correctly, you should see:

```
🎉 MT5 Dashboard is running!

  🔧 Backend API: http://127.0.0.1:8000
  📊 API Docs: http://127.0.0.1:8000/docs
  🌐 Frontend: http://localhost:3000

Press Ctrl+C to stop all services
```

Your browser should automatically open to the dashboard, and you're ready to start trading! 📈