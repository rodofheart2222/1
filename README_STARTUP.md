# MT5 Dashboard Startup

- Backend-only quick start:
  - `./startup.sh` (or `bash startup.sh`)
  - Exposes API at `http://0.0.0.0:8000`

- Full system start (backend + frontend):
  - `python3 start.py --dev`
  - Requires Node.js and npm

- Environment variables (optional):
  - `ENVIRONMENT` (default: development)
  - `HOST` (default: 0.0.0.0)
  - `PORT` (default: 8000)
  - `MT5_API_PORT` (alternative to PORT)