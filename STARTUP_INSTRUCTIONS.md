# MT5 Dashboard Startup Instructions

## Quick Start

The MT5 Dashboard now includes easy-to-use startup scripts that handle all the setup and dependencies for you.

### Option 1: Python Startup Script (Recommended)

```bash
python3 startup.py
```

This will:
1. Check Python and Node.js installations
2. Install all required dependencies
3. Set up the database
4. Start both backend and frontend servers
5. Open the dashboard at http://localhost:3000

**Additional Options:**
- `python3 startup.py --skip-deps` - Skip dependency installation (faster if already installed)
- `python3 startup.py --backend-only` - Start only the backend server
- `python3 startup.py --frontend-only` - Start only the frontend server
- `python3 startup.py --port 8080` - Use a different backend port
- `python3 startup.py --host 0.0.0.0` - Specify backend host
- `python3 startup.py --help` - Show all available options

### Option 2: Bash Startup Script

```bash
./startup.sh
```

Or for backend-only mode:
```bash
./startup.sh --backend-only
```

### Manual Start (Advanced Users)

If you prefer to start components manually:

1. **Install Dependencies:**
   ```bash
   # Python dependencies
   pip3 install --user -r backend/requirements.txt
   
   # Node.js dependencies
   cd frontend && npm install && cd ..
   ```

2. **Set up Database:**
   ```bash
   python3 fix_database_schema.py
   python3 populate_ea_database.py
   ```

3. **Start Backend:**
   ```bash
   python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
   ```

4. **Start Frontend (in a new terminal):**
   ```bash
   cd frontend
   npm start
   ```

## Requirements

- **Python 3.8+** - Required for backend
- **Node.js 14+** - Required for frontend (optional if using --backend-only)
- **pip3** - Python package manager

## Troubleshooting

### Python Dependencies Installation Issues

If you encounter "externally-managed-environment" errors:
- The startup scripts will automatically try different installation methods
- You can manually install with: `pip3 install --user <package>`

### Missing System Libraries

If lxml or other packages fail to install:
```bash
# For Ubuntu/Debian:
sudo apt-get install python3-dev libxml2-dev libxslt1-dev

# For macOS:
brew install libxml2 libxslt
```

### Port Already in Use

If ports 8000 or 3000 are already in use:
- Use `python3 startup.py --port 8080` to change the backend port
- Edit `frontend/.env` to change the frontend port

### Database Issues

If the database setup fails:
1. Delete the existing database: `rm data/*.db`
2. Run the setup scripts again: `python3 fix_database_schema.py`

## Features

The startup scripts provide:
- ✅ Automatic dependency installation
- ✅ Database initialization and migration
- ✅ Process management with graceful shutdown
- ✅ Colored terminal output for easy reading
- ✅ Automatic error handling and recovery
- ✅ Support for different deployment modes

## Stopping the Services

Press `Ctrl+C` in the terminal where you started the services. The scripts will gracefully shut down all components.

## Development Mode

The servers start in development mode by default with hot-reloading enabled:
- Backend changes are automatically detected
- Frontend changes trigger automatic browser refresh

## Production Deployment

For production deployment, consider:
1. Using a process manager like PM2 or systemd
2. Setting up proper environment variables
3. Using a reverse proxy like Nginx
4. Enabling HTTPS
5. Setting up proper logging

## Need Help?

Check the following files for more information:
- `README.md` - General project information
- `CONFIGURATION.md` - Configuration options
- `backend/README.md` - Backend-specific details
- `frontend/README.md` - Frontend-specific details