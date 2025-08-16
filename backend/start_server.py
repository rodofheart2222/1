#!/usr/bin/env python3
"""
Simple startup script for the MT5 COC Dashboard Backend
This avoids import issues by creating a minimal FastAPI server
"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Initialize FastAPI app
app = FastAPI(
    title="MT5 COC Dashboard API",
    description="Backend API for MT5 Commander-in-Chief Dashboard",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://155.138.174.196:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "MT5 COC Dashboard Backend is running"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "mt5-coc-dashboard"}

# Simple news endpoints for testing
@app.get("/api/news/events/today")
async def get_todays_events():
    """Mock endpoint for today's news events"""
    return {
        'success': True,
        'events': [
            {
                'id': 1,
                'event_time': '2024-12-08T14:30:00Z',
                'currency': 'USD',
                'impact_level': 'high',
                'description': 'Non-Farm Payrolls',
                'pre_minutes': 60,
                'post_minutes': 60,
                'is_active': False
            },
            {
                'id': 2,
                'event_time': '2024-12-08T16:00:00Z',
                'currency': 'EUR',
                'impact_level': 'medium',
                'description': 'ECB Interest Rate Decision',
                'pre_minutes': 30,
                'post_minutes': 30,
                'is_active': False
            }
        ],
        'count': 2,
        'date': '2024-12-08'
    }

@app.get("/api/news/blackout/status")
async def get_blackout_status(symbols: str = "EURUSD,GBPUSD,USDJPY,XAUUSD"):
    """Mock endpoint for blackout status"""
    symbols_list = symbols.split(',')
    results = {}
    
    for symbol in symbols_list:
        results[symbol.strip()] = {
            'trading_allowed': True,
            'active_restrictions': [],
            'highest_impact_level': None
        }
    
    return {
        'success': True,
        'blackout_status': results,
        'check_time': '2024-12-08T12:00:00Z'
    }

@app.get("/api/news/config/impact-levels")
async def get_impact_level_config():
    """Mock endpoint for impact level configuration"""
    return {
        'success': True,
        'impact_level_config': {
            'high': {'pre': 60, 'post': 60},
            'medium': {'pre': 30, 'post': 30},
            'low': {'pre': 15, 'post': 15}
        },
        'description': {
            'high': 'High impact events (NFP, Interest Rate Decisions)',
            'medium': 'Medium impact events (GDP, Inflation)',
            'low': 'Low impact events (PMI, Consumer Confidence)'
        }
    }

@app.post("/api/news/sync")
async def sync_news_events():
    """Mock endpoint for news sync"""
    return {
        'success': True,
        'message': 'News events synchronized successfully',
        'sync_result': {'stored': 5, 'deleted': 2}
    }

if __name__ == "__main__":
    print(" Starting MT5 COC Dashboard Backend...")
    print(" News Event Management Interface is ready!")
    print(" Server will be available at: http://155.138.174.196:80")
    print(" API docs available at: http://155.138.174.196:80/docs")
    print()
    
    uvicorn.run(
        "start_server:app",
        host="155.138.174.196",
        port=80,
        reload=True,
        log_level="info"
    )