"""
WebSocket Server Startup Script

This script provides a simple way to start the WebSocket server for development
and testing purposes.
"""

import asyncio
import logging
import signal
import sys
from typing import Optional

try:
    from .websocket_server import WebSocketServer
    from .websocket_integration_example import DashboardIntegrationService
except ImportError:
    # Fallback for direct execution
    from websocket_server import WebSocketServer
    from websocket_integration_example import DashboardIntegrationService


# Global server instance for cleanup
server_instance: Optional[WebSocketServer] = None
integration_service: Optional[DashboardIntegrationService] = None


def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print(f"\nReceived signal {signum}, shutting down gracefully...")
    if server_instance:
        asyncio.create_task(cleanup())


async def cleanup():
    """Cleanup resources on shutdown"""
    global server_instance, integration_service
    
    try:
        if integration_service:
            await integration_service.stop()
            print("Integration service stopped")
        
        if server_instance:
            await server_instance.stop_server()
            print("WebSocket server stopped")
    
    except Exception as e:
        print(f"Error during cleanup: {e}")
    
    # Exit the event loop
    loop = asyncio.get_event_loop()
    loop.stop()


async def start_websocket_server_only(host: str = "155.138.174.196", port: int = 8765, auth_token: str = "dashboard_token"):
    """Start only the WebSocket server without integration services"""
    global server_instance
    
    try:
        server_instance = WebSocketServer(host=host, port=port, auth_token=auth_token)
        await server_instance.start_server()
        
        print(f"WebSocket server started successfully!")
        print(f"Server: ws://{host}:{port}")
        print(f"Auth token: {auth_token}")
        print("Press Ctrl+C to stop the server")
        
        # Keep the server running
        while server_instance.running:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        print("\nShutdown requested by user")
    except Exception as e:
        print(f"Error starting WebSocket server: {e}")
        sys.exit(1)
    finally:
        await cleanup()


async def start_integrated_system(host: str = "155.138.174.196", port: int = 8765, auth_token: str = "dashboard_token"):
    """Start WebSocket server with full integration services"""
    global server_instance, integration_service
    
    try:
        # Start WebSocket server
        server_instance = WebSocketServer(host=host, port=port, auth_token=auth_token)
        await server_instance.start_server()
        
        # Start integration service
        integration_service = DashboardIntegrationService(server_instance)
        await integration_service.start()
        
        print(f"Integrated dashboard system started successfully!")
        print(f"WebSocket server: ws://{host}:{port}")
        print(f"Auth token: {auth_token}")
        print("Services running:")
        print("  - WebSocket server")
        print("  - EA data monitoring")
        print("  - Portfolio monitoring")
        print("  - Command monitoring")
        print("Press Ctrl+C to stop all services")
        
        # Keep the system running
        while server_instance.running:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        print("\nShutdown requested by user")
    except Exception as e:
        print(f"Error starting integrated system: {e}")
        sys.exit(1)
    finally:
        await cleanup()


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Start WebSocket server for MT5 Dashboard")
    parser.add_argument("--host", default="155.138.174.196", help="Server host (default: 155.138.174.196)")
    parser.add_argument("--port", type=int, default=8765, help="Server port (default: 8765)")
    parser.add_argument("--auth-token", default="dashboard_token", help="Authentication token")
    parser.add_argument("--integrated", action="store_true", help="Start with full integration services")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"], 
                       help="Logging level")
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start the appropriate system
    try:
        if args.integrated:
            asyncio.run(start_integrated_system(args.host, args.port, args.auth_token))
        else:
            asyncio.run(start_websocket_server_only(args.host, args.port, args.auth_token))
    except KeyboardInterrupt:
        print("\nShutdown complete")
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()