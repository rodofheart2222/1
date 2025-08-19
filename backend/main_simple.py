"""
MT5 COC Dashboard Backend - Simplified Version (No Database)
"""
import asyncio
import uvicorn
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List, Any
import json

# Initialize FastAPI app
app = FastAPI(
    title="MT5 COC Dashboard API - Simplified",
    description="Backend API for MT5 Commander-in-Chief Dashboard (No Database)",
    version="1.0.0"
)

# CORS configuration - Allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for now
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH", "HEAD"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

# In-memory storage
ea_data = {}
news_events = []

@app.on_event("startup")
async def startup_event():
    """Initialize with some mock data"""
    print("🚀 Starting MT5 COC Dashboard Backend (Simplified)")
    
    # Add some mock EA data
    mock_eas = [
        {
            "instanceUuid": "12345503-9065-115G-BPAU-D17554989642",
            "magicNumber": 12345,
            "symbol": "GBPAUD",
            "strategyTag": "MACD_TREND", 
            "status": "active",
            "currentProfit": 125.50,
            "openPositions": 2,
            "lastUpdate": datetime.now().isoformat()
        },
        {
            "instanceUuid": "12345503-9065-115E-URUS-D17554931221",
            "magicNumber": 67890,
            "symbol": "EURUSD",
            "strategyTag": "RSI_SCALPER",
            "status": "active", 
            "currentProfit": -45.20,
            "openPositions": 1,
            "lastUpdate": datetime.now().isoformat()
        }
    ]
    
    for ea in mock_eas:
        ea_data[ea["magicNumber"]] = ea
    
    # Add some mock news events
    news_events.extend([
        {
            "event_time": datetime.now().isoformat(),
            "currency": "USD",
            "impact_level": "high", 
            "description": "Federal Reserve Interest Rate Decision"
        },
        {
            "event_time": datetime.now().isoformat(),
            "currency": "EUR",
            "impact_level": "medium",
            "description": "European Central Bank Press Conference"
        }
    ])
    
    print("✅ Mock data initialized")
    print(f"📊 {len(ea_data)} EAs loaded")
    print(f"📰 {len(news_events)} news events loaded")

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
    return {"message": "MT5 COC Dashboard Backend (Simplified) is running"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "mt5-coc-dashboard-simplified"}

@app.get("/api/ea/status/all")
async def get_all_ea_status():
    """Get status of all EAs"""
    try:
        eas = []
        for magic_number, ea in ea_data.items():
            eas.append({
                # Both camelCase and snake_case for compatibility
                "instanceUuid": ea.get("instanceUuid"),
                "instance_uuid": ea.get("instanceUuid"),
                "magicNumber": ea.get("magicNumber"),
                "magic_number": ea.get("magicNumber"),
                "symbol": ea.get("symbol"),
                "strategyTag": ea.get("strategyTag"),
                "strategy_tag": ea.get("strategyTag"),
                "status": ea.get("status"),
                "currentProfit": ea.get("currentProfit", 0.0),
                "current_profit": ea.get("currentProfit", 0.0),
                "openPositions": ea.get("openPositions", 0),
                "open_positions": ea.get("openPositions", 0),
                "slValue": None,
                "sl_value": None,
                "tpValue": None,
                "tp_value": None,
                "trailingActive": False,
                "trailing_active": False,
                "cocOverride": False,
                "coc_override": False,
                "isPaused": False,
                "is_paused": False,
                "lastUpdate": ea.get("lastUpdate"),
                "last_update": ea.get("lastUpdate"),
                "themeData": {
                    "glassEffect": {
                        "background": "rgba(17, 17, 17, 0.88)",
                        "backdropFilter": "blur(18px)",
                        "border": "1px solid #00d4ff40",
                        "borderRadius": "14px"
                    }
                }
            })
        
        return {
            "eas": eas, 
            "count": len(eas),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"❌ Error getting EA status: {e}")
        return {"eas": [], "count": 0}

@app.get("/api/ea/status/{magic_number}")
async def get_ea_status(magic_number: int):
    """Get status of specific EA"""
    try:
        if magic_number in ea_data:
            ea = ea_data[magic_number]
            return {
                "magicNumber": ea.get("magicNumber"),
                "magic_number": ea.get("magicNumber"),
                "symbol": ea.get("symbol"),
                "strategyTag": ea.get("strategyTag"),
                "strategy_tag": ea.get("strategyTag"),
                "currentProfit": ea.get("currentProfit", 0.0),
                "current_profit": ea.get("currentProfit", 0.0),
                "openPositions": ea.get("openPositions", 0),
                "open_positions": ea.get("openPositions", 0),
                "status": ea.get("status"),
                "lastUpdate": ea.get("lastUpdate"),
                "last_update": ea.get("lastUpdate")
            }
        else:
            raise HTTPException(status_code=404, detail="EA not found")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get EA status: {str(e)}")

@app.get("/api/news/events/upcoming")
async def get_upcoming_news(hours: int = 24):
    """Get upcoming news events"""
    try:
        return {
            "events": news_events,
            "count": len(news_events),
            "hours": hours
        }
    except Exception as e:
        print(f"❌ Error getting news events: {e}")
        return {"events": [], "count": 0}

@app.post("/api/ea/register")
async def register_ea(
    magic_number: int,
    symbol: str = "UNKNOWN",
    strategy_tag: str = "UNKNOWN",
    instance_uuid: str = None
):
    """Register EA (simplified - just store in memory)"""
    try:
        import uuid
        if not instance_uuid:
            instance_uuid = str(uuid.uuid4())
        
        ea_data[magic_number] = {
            "instanceUuid": instance_uuid,
            "magicNumber": magic_number,
            "symbol": symbol,
            "strategyTag": strategy_tag,
            "status": "active",
            "currentProfit": 0.0,
            "openPositions": 0,
            "lastUpdate": datetime.now().isoformat()
        }
        
        return {
            "success": True,
            "message": f"EA {magic_number} registered successfully",
            "instance_uuid": instance_uuid,
            "magic_number": magic_number
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@app.get("/api/ea/commands/instance/{instance_uuid}")
async def get_pending_commands_by_uuid(instance_uuid: str):
    """Get pending commands for EA instance (mock response)"""
    raise HTTPException(status_code=404, detail="No pending commands")

@app.get("/favicon.ico")
async def favicon():
    """Handle favicon requests"""
    from fastapi import Response
    return Response(status_code=204)

if __name__ == "__main__":
    import os
    
    host = "127.0.0.1"
    port = 80
    
    print(f"🚀 Starting simplified server on {host}:{port}")
    print(f"📚 API docs: http://{host}:{port}/docs")
    
    uvicorn.run(
        "main_simple:app",
        host=host,
        port=port,
        reload=False,
        log_level="info"
    )


