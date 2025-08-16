"""
MT5 COC Dashboard Backend Main Application
"""
import asyncio
import uvicorn
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
# Handle imports for both running from root and from backend directory
try:
    # Try backend.* imports first (when running from root)
    from backend.database.init_db import init_database
    from backend.api.news_routes import router as news_router
    from backend.api.backtest_routes import router as backtest_router
    from backend.api.ea_routes import router as ea_router
    from backend.api.ea_sync_routes import router as ea_sync_router
    from backend.api.simple_backtest_routes import router as simple_backtest_router
    from backend.api.trade_routes import router as trade_router
    from backend.api.mt5_routes import router as mt5_router
except ImportError:
    # Fall back to relative imports (when running from backend directory)
    from database.init_db import init_database
    from api.news_routes import router as news_router
    from api.backtest_routes import router as backtest_router
    from api.ea_routes import router as ea_router
    from api.ea_sync_routes import router as ea_sync_router
    from api.simple_backtest_routes import router as simple_backtest_router
    from api.trade_routes import router as trade_router
    from api.mt5_routes import router as mt5_router

# Initialize FastAPI app
app = FastAPI(
    title="MT5 COC Dashboard API",
    description="Backend API for MT5 Commander-in-Chief Dashboard",
    version="1.0.0"
)

# Include routers
app.include_router(news_router)
app.include_router(backtest_router)
app.include_router(ea_router)
app.include_router(ea_sync_router)
app.include_router(simple_backtest_router)
app.include_router(trade_router)
app.include_router(mt5_router)

# Add CORS middleware
import os
cors_origins = os.getenv("CORS_ORIGINS", "http://155.138.174.196:3000,http://155.138.174.196:8000,http://127.0.0.1:8000").split(",")

# Add Railway domains if in production
if os.getenv("RAILWAY_ENVIRONMENT"):
    cors_origins.extend([
        "https://*.railway.app",
        "https://*.up.railway.app"
    ])

# In development, be more permissive with CORS
if os.getenv("ENVIRONMENT", "development") == "development":
    cors_origins.extend([
        "http://155.138.174.196:3000",
        "http://155.138.174.196:8000", 
        "http://155.138.174.196:80",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
        "http://localhost:3000",
        "http://localhost:8000",
        "file://*",  # For Electron
        "app://*",   # For Electron
    ])

# Always allow all origins in development for easier debugging
allow_all_origins = os.getenv("ENVIRONMENT", "development") == "development"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if allow_all_origins else cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH", "HEAD"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,  # Cache preflight requests for 1 hour
)

@app.on_event("startup")
async def startup_event():
    """Initialize database and services on startup"""
    print("Initializing MT5 COC Dashboard Backend...")
    try:
        # Initialize database
        init_database()
        print(" Database initialized successfully")
        
        # Create necessary directories
        from pathlib import Path
        directories = ["data", "logs", "data/mt5_fallback", "data/mt5_globals"]
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
        print(" Directory structure verified")
        
        # EA tracking is handled via API endpoints, not background services
        print(" EA tracking ready - EAs should POST to /api/ea/status")
        
    except Exception as e:
        print(f"️ Database initialization failed: {e}")
        print(" Continuing without database - using mock data")
    
    print(" Backend startup complete")
    print(f" WebSocket server should be started separately on port {8765}")
    print(f" API documentation available at: http://155.138.174.196:80/docs")

@app.options("/{path:path}")
async def options_handler(path: str):
    """Handle all OPTIONS requests explicitly"""
    return {"message": "OK"}

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "MT5 COC Dashboard Backend is running"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "mt5-coc-dashboard"}

@app.get("/api/system/health")
async def system_health():
    """Comprehensive system health check including EA tracking"""
    try:
        try:
            from backend.database.init_db import verify_database_integrity
        except ImportError:
            from database.init_db import verify_database_integrity
        
        # Check database
        db_healthy = verify_database_integrity()
        
        # Check EA count
        conn = None
        ea_count = 0
        try:
            import sqlite3
            import os
            db_path = os.getenv("DATABASE_PATH", "data/mt5_dashboard.db")
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM eas")
            ea_count = cursor.fetchone()[0]
        except Exception as e:
            print(f"Error checking EA count: {e}")
        finally:
            if conn:
                conn.close()
        
        return {
            "status": "healthy" if db_healthy else "degraded",
            "database_status": "connected" if db_healthy else "error",
            "ea_count": ea_count,
            "api_endpoints": {
                "ea_status": "/api/ea/status",
                "ea_commands": "/api/ea/commands/{magic_number}",
                "ea_command_ack": "/api/ea/command-ack"
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}

if __name__ == "__main__":
    import os
    
    # Get port from environment variable (Railway sets this)
    port = int(os.getenv("PORT", 80))
    host = os.getenv("HOST", "155.138.174.196")  # Railway requires 0.0.0.0
    
    # Disable reload in production
    reload = os.getenv("ENVIRONMENT", "development") == "development"
    
    print(f" Starting server on {host}:{port}")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )