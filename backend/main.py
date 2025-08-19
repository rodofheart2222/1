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

# Add CORS middleware - Configuration loaded from central config.json
import os
try:
    from backend.config.central_config import CORS_ORIGINS, should_allow_all_cors
except ImportError:
    from config.central_config import CORS_ORIGINS, should_allow_all_cors

cors_origins = CORS_ORIGINS
allow_all_origins = should_allow_all_cors()

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
    try:
        from backend.config.central_config import WS_PORT, get_docs_url
    except ImportError:
        from config.central_config import WS_PORT, get_docs_url
    print(f" WebSocket server should be started separately on port {WS_PORT}")
    print(f" API documentation available at: {get_docs_url()}")
    print(" All configuration loaded from central config.json")

@app.options("/{path:path}")
async def options_handler(path: str):
    """Handle all OPTIONS requests explicitly"""
    from fastapi import Response
    response = Response()
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH, HEAD"
    response.headers["Access-Control-Allow-Headers"] = "*"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Max-Age"] = "3600"
    return response

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "MT5 COC Dashboard Backend is running"}

@app.post("/")
async def root_post():
    """Handle POST requests to root endpoint (likely from MT5 EAs)"""
    return {
        "message": "MT5 COC Dashboard Backend is running", 
        "note": "For EA registration, use POST /api/ea/register",
        "endpoints": {
            "ea_register": "/api/ea/register",
            "ea_status": "/api/ea/status",
            "ea_commands": "/api/ea/commands/{magic_number}"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "mt5-coc-dashboard"}

@app.get("/favicon.ico")
async def favicon():
    """Handle favicon requests to prevent 405 errors"""
    from fastapi import Response
    # Return empty 204 response for favicon to prevent errors
    return Response(status_code=204)

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
    
    # Get host and port from central configuration (config.json)
    try:
        from backend.config.central_config import BACKEND_HOST, BACKEND_PORT
    except ImportError:
        from config.central_config import BACKEND_HOST, BACKEND_PORT
    
    host = BACKEND_HOST
    port = BACKEND_PORT
    
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