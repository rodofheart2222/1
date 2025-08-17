# 🚀 MT5 Dashboard - One-Click Startup

## Quick Start

```bash
# Start everything (recommended)
python3 start.py

# Or use the shell script
./start.sh
```

## What You Get

- ✅ **Automatic Database Setup** - SQLite database with all tables and migrations
- ✅ **Backend API Server** - FastAPI server on http://127.0.0.1:8000
- ✅ **Frontend Dashboard** - React app on http://localhost:3000  
- ✅ **Dependency Installation** - All Python and Node.js packages
- ✅ **Environment Configuration** - All environment variables set
- ✅ **Graceful Shutdown** - Ctrl+C stops everything cleanly

## Available Scripts

| File | Description | Best For |
|------|-------------|----------|
| `start.py` | Full-featured Python script with options | Development & Production |
| `start.sh` | Simple bash script | Quick testing |
| `STARTUP_GUIDE.md` | Detailed documentation | Learning all options |

## Common Usage

```bash
# Development (default)
python3 start.py

# Production mode
python3 start.py --prod

# Backend only
python3 start.py --backend-only

# Custom ports
python3 start.py --port 8080 --frontend-port 3001

# See all options
python3 start.py --help
```

## Troubleshooting

1. **Port conflicts**: Use `--port` and `--frontend-port` options
2. **Permission errors**: Run `chmod +x start.py start.sh`
3. **Dependencies fail**: Scripts auto-install, but you can install manually
4. **Database issues**: Delete `data/mt5_dashboard.db` and restart

## System Requirements

- Python 3.8+
- Node.js 16+
- npm

That's it! The scripts handle everything else automatically. 🎉