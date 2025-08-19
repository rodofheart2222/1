#!/usr/bin/env python3
"""
Simple HTTP Server for MT5 COC Dashboard (No External Dependencies)
Uses only Python built-in modules
"""

import json
import socket
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from datetime import datetime
import uuid

# In-memory storage
ea_data = {
    12345: {
        "instanceUuid": "12345503-9065-115G-BPAU-D17554989642",
        "magicNumber": 12345,
        "symbol": "GBPAUD",
        "strategyTag": "MACD_TREND",
        "status": "active",
        "currentProfit": 125.50,
        "openPositions": 2,
        "lastUpdate": datetime.now().isoformat()
    },
    67890: {
        "instanceUuid": "12345503-9065-115E-URUS-D17554931221", 
        "magicNumber": 67890,
        "symbol": "EURUSD",
        "strategyTag": "RSI_SCALPER",
        "status": "active",
        "currentProfit": -45.20,
        "openPositions": 1,
        "lastUpdate": datetime.now().isoformat()
    }
}

news_events = [
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
]

class CORSHTTPRequestHandler(BaseHTTPRequestHandler):
    def set_cors_headers(self):
        """Set CORS headers for all responses"""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS, PATCH, HEAD')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.send_header('Access-Control-Allow-Credentials', 'true')
        self.send_header('Access-Control-Max-Age', '3600')
    
    def do_OPTIONS(self):
        """Handle preflight OPTIONS requests"""
        self.send_response(200)
        self.set_cors_headers()
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
    
    def do_GET(self):
        """Handle GET requests"""
        try:
            parsed_url = urlparse(self.path)
            path = parsed_url.path
            query_params = parse_qs(parsed_url.query)
            
            print(f"📥 GET {path}")
            
            # Route handling
            if path == '/health':
                self.send_json_response({
                    "status": "healthy", 
                    "service": "mt5-coc-dashboard-simple"
                })
            
            elif path == '/':
                self.send_json_response({
                    "message": "MT5 COC Dashboard Backend (Simple) is running"
                })
            
            elif path == '/api/ea/status/all':
                eas = []
                for magic_number, ea in ea_data.items():
                    eas.append({
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
                
                self.send_json_response({
                    "eas": eas,
                    "count": len(eas),
                    "timestamp": datetime.now().isoformat()
                })
            
            elif path.startswith('/api/ea/status/'):
                # Extract magic number from path
                magic_number = int(path.split('/')[-1])
                if magic_number in ea_data:
                    ea = ea_data[magic_number]
                    self.send_json_response({
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
                    })
                else:
                    self.send_error_response(404, "EA not found")
            
            elif path == '/api/news/events/upcoming':
                hours = 24
                if 'hours' in query_params:
                    hours = int(query_params['hours'][0])
                
                self.send_json_response({
                    "events": news_events,
                    "count": len(news_events),
                    "hours": hours
                })
            
            elif path.startswith('/api/ea/commands/instance/'):
                # Mock response for commands
                self.send_error_response(404, "No pending commands")
            
            elif path == '/favicon.ico':
                self.send_response(204)
                self.set_cors_headers()
                self.end_headers()
            
            else:
                self.send_error_response(404, "Not Found")
                
        except Exception as e:
            print(f"❌ Error handling GET request: {e}")
            self.send_error_response(500, str(e))
    
    def do_POST(self):
        """Handle POST requests"""
        try:
            parsed_url = urlparse(self.path)
            path = parsed_url.path
            query_params = parse_qs(parsed_url.query)
            
            print(f"📥 POST {path}")
            
            if path == '/api/ea/register':
                # Get parameters from query string
                magic_number = int(query_params.get('magic_number', [0])[0])
                symbol = query_params.get('symbol', ['UNKNOWN'])[0]
                strategy_tag = query_params.get('strategy_tag', ['UNKNOWN'])[0]
                instance_uuid = query_params.get('instance_uuid', [None])[0]
                
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
                
                self.send_json_response({
                    "success": True,
                    "message": f"EA {magic_number} registered successfully",
                    "instance_uuid": instance_uuid,
                    "magic_number": magic_number,
                    "ea_id": magic_number
                })
            
            else:
                self.send_error_response(404, "Not Found")
                
        except Exception as e:
            print(f"❌ Error handling POST request: {e}")
            self.send_error_response(500, str(e))
    
    def send_json_response(self, data, status_code=200):
        """Send JSON response with CORS headers"""
        json_data = json.dumps(data, indent=2)
        
        self.send_response(status_code)
        self.set_cors_headers()
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(json_data)))
        self.end_headers()
        self.wfile.write(json_data.encode('utf-8'))
    
    def send_error_response(self, status_code, message):
        """Send error response with CORS headers"""
        error_data = {"detail": message}
        self.send_json_response(error_data, status_code)
    
    def log_message(self, format, *args):
        """Override to customize logging"""
        print(f"📡 {self.address_string()} - {format % args}")

def check_port_available(host, port):
    """Check if port is available"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex((host, port))
        sock.close()
        return result != 0
    except:
        return False

def main():
    host = '127.0.0.1'
    port = 80
    
    print("🚀 MT5 COC Dashboard Simple Server")
    print("=" * 50)
    
    # Check if port is available
    if not check_port_available(host, port):
        print(f"❌ Port {port} is already in use!")
        print("Try killing existing processes or use a different port")
        return
    
    try:
        # Create and start server
        server = HTTPServer((host, port), CORSHTTPRequestHandler)
        
        print(f"✅ Server starting on http://{host}:{port}")
        print(f"📚 Test endpoints:")
        print(f"   Health: http://{host}:{port}/health")
        print(f"   EAs: http://{host}:{port}/api/ea/status/all")
        print(f"   News: http://{host}:{port}/api/news/events/upcoming")
        print("-" * 50)
        print("🎯 Server ready! Press Ctrl+C to stop")
        
        server.serve_forever()
        
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
        server.shutdown()
    except Exception as e:
        print(f"❌ Server error: {e}")

if __name__ == "__main__":
    main()


