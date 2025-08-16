"""
WebSocket Integration Example

This module demonstrates how to integrate the WebSocket server with existing
services like EA data collection, command dispatching, and other components
to provide real-time updates to the dashboard.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any

try:
    from .websocket_server import WebSocketServer, get_websocket_server
    from .ea_data_collector import EADataCollector
    from .command_dispatcher import CommandDispatcher
except ImportError:
    # Fallback for direct execution
    from websocket_server import WebSocketServer, get_websocket_server
    try:
        from ea_data_collector import EADataCollector
        from command_dispatcher import CommandDispatcher
    except ImportError:
        # Mock classes for testing when dependencies aren't available
        class EADataCollector:
            async def collect_all_ea_data(self):
                return []
            async def get_disconnected_eas(self):
                return []
        
        class CommandDispatcher:
            async def get_completed_commands(self):
                return []


logger = logging.getLogger(__name__)


class DashboardIntegrationService:
    """
    Service that integrates WebSocket server with other backend services
    to provide real-time dashboard updates.
    """
    
    def __init__(self, websocket_server: WebSocketServer):
        self.websocket_server = websocket_server
        self.ea_collector = EADataCollector()
        self.command_dispatcher = CommandDispatcher()
        self.running = False
        
        # Data update intervals (seconds)
        self.ea_update_interval = 5
        self.portfolio_update_interval = 10
        
    async def start(self):
        """Start the integration service"""
        self.running = True
        logger.info("Starting Dashboard Integration Service")
        
        # Start background tasks
        asyncio.create_task(self.ea_data_monitor())
        asyncio.create_task(self.portfolio_monitor())
        asyncio.create_task(self.command_monitor())
        
    async def stop(self):
        """Stop the integration service"""
        self.running = False
        logger.info("Stopping Dashboard Integration Service")
    
    async def ea_data_monitor(self):
        """Monitor EA data and broadcast updates"""
        logger.info("Starting EA data monitoring")
        
        while self.running:
            try:
                # Collect EA data
                ea_reports = await self.ea_collector.collect_all_ea_data()
                
                # Broadcast individual EA updates
                for ea_report in ea_reports:
                    ea_data = self.format_ea_data(ea_report)
                    await self.websocket_server.broadcast_ea_update(ea_data)
                
                # Check for disconnected EAs
                disconnected_eas = await self.ea_collector.get_disconnected_eas()
                for ea_id in disconnected_eas:
                    await self.websocket_server.broadcast_alert({
                        "type": "ea_disconnected",
                        "ea_id": ea_id,
                        "message": f"EA {ea_id} has disconnected",
                        "timestamp": datetime.now().isoformat()
                    })
                
                await asyncio.sleep(self.ea_update_interval)
                
            except Exception as e:
                logger.error(f"Error in EA data monitoring: {e}")
                await asyncio.sleep(5)  # Brief pause before retry
    
    async def portfolio_monitor(self):
        """Monitor portfolio statistics and broadcast updates"""
        logger.info("Starting portfolio monitoring")
        
        while self.running:
            try:
                # Calculate portfolio metrics
                portfolio_data = await self.calculate_portfolio_metrics()
                
                # Broadcast portfolio update
                await self.websocket_server.broadcast_portfolio_update(portfolio_data)
                
                await asyncio.sleep(self.portfolio_update_interval)
                
            except Exception as e:
                logger.error(f"Error in portfolio monitoring: {e}")
                await asyncio.sleep(5)
    
    async def command_monitor(self):
        """Monitor command execution and broadcast updates"""
        logger.info("Starting command monitoring")
        
        while self.running:
            try:
                # Check for completed commands
                completed_commands = await self.command_dispatcher.get_completed_commands()
                
                for command in completed_commands:
                    command_data = {
                        "command_id": command.get("id"),
                        "command_type": command.get("command_type"),
                        "ea_id": command.get("ea_id"),
                        "status": command.get("status"),
                        "result": command.get("result"),
                        "timestamp": command.get("completed_at")
                    }
                    
                    await self.websocket_server.broadcast_command_update(command_data)
                
                await asyncio.sleep(2)  # Check commands frequently
                
            except Exception as e:
                logger.error(f"Error in command monitoring: {e}")
                await asyncio.sleep(5)
    
    def format_ea_data(self, ea_report: Dict) -> Dict:
        """Format EA report data for WebSocket transmission"""
        return {
            "ea_id": ea_report.get("magic_number"),
            "symbol": ea_report.get("symbol"),
            "strategy_tag": ea_report.get("strategy_tag"),
            "status": ea_report.get("status", "unknown"),
            "current_profit": ea_report.get("current_profit", 0.0),
            "open_positions": ea_report.get("open_positions", 0),
            "sl_value": ea_report.get("sl_value"),
            "tp_value": ea_report.get("tp_value"),
            "trailing_active": ea_report.get("trailing_active", False),
            "module_status": ea_report.get("module_status", {}),
            "performance_metrics": {
                "total_profit": ea_report.get("total_profit", 0.0),
                "profit_factor": ea_report.get("profit_factor", 0.0),
                "expected_payoff": ea_report.get("expected_payoff", 0.0),
                "drawdown": ea_report.get("drawdown", 0.0),
                "z_score": ea_report.get("z_score", 0.0)
            },
            "last_trades": ea_report.get("last_trades", []),
            "coc_override": ea_report.get("coc_override", False),
            "last_update": ea_report.get("last_update", datetime.now().isoformat())
        }
    
    async def calculate_portfolio_metrics(self) -> Dict:
        """Calculate and format portfolio metrics"""
        try:
            # Get all EA data
            ea_reports = await self.ea_collector.collect_all_ea_data()
            
            # Calculate aggregated metrics
            total_profit = sum(ea.get("current_profit", 0) for ea in ea_reports)
            active_eas = len([ea for ea in ea_reports if ea.get("status") == "active"])
            total_eas = len(ea_reports)
            total_positions = sum(ea.get("open_positions", 0) for ea in ea_reports)
            
            # Calculate portfolio drawdown (simplified)
            profits = [ea.get("current_profit", 0) for ea in ea_reports]
            max_profit = max(profits) if profits else 0
            current_profit = sum(profits)
            drawdown_pct = ((max_profit - current_profit) / max_profit * 100) if max_profit > 0 else 0
            
            # Group by symbol and strategy
            symbol_breakdown = {}
            strategy_breakdown = {}
            
            for ea in ea_reports:
                symbol = ea.get("symbol", "Unknown")
                strategy = ea.get("strategy_tag", "Unknown")
                profit = ea.get("current_profit", 0)
                
                if symbol not in symbol_breakdown:
                    symbol_breakdown[symbol] = {"profit": 0, "count": 0}
                symbol_breakdown[symbol]["profit"] += profit
                symbol_breakdown[symbol]["count"] += 1
                
                if strategy not in strategy_breakdown:
                    strategy_breakdown[strategy] = {"profit": 0, "count": 0}
                strategy_breakdown[strategy]["profit"] += profit
                strategy_breakdown[strategy]["count"] += 1
            
            return {
                "total_profit": round(total_profit, 2),
                "drawdown_pct": round(drawdown_pct, 2),
                "active_eas": active_eas,
                "total_eas": total_eas,
                "total_positions": total_positions,
                "symbol_breakdown": symbol_breakdown,
                "strategy_breakdown": strategy_breakdown,
                "last_update": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error calculating portfolio metrics: {e}")
            return {
                "total_profit": 0.0,
                "drawdown_pct": 0.0,
                "active_eas": 0,
                "total_eas": 0,
                "total_positions": 0,
                "symbol_breakdown": {},
                "strategy_breakdown": {},
                "last_update": datetime.now().isoformat(),
                "error": str(e)
            }
    
    async def handle_new_trade(self, trade_data: Dict):
        """Handle new trade notification"""
        formatted_trade = {
            "trade_id": trade_data.get("id"),
            "ea_id": trade_data.get("ea_id"),
            "symbol": trade_data.get("symbol"),
            "order_type": trade_data.get("order_type"),
            "volume": trade_data.get("volume"),
            "price": trade_data.get("price"),
            "profit": trade_data.get("profit"),
            "timestamp": trade_data.get("timestamp", datetime.now().isoformat())
        }
        
        await self.websocket_server.broadcast_trade_update(formatted_trade)
    
    async def handle_news_event(self, news_data: Dict):
        """Handle news event notification"""
        formatted_news = {
            "event_id": news_data.get("id"),
            "event_time": news_data.get("event_time"),
            "currency": news_data.get("currency"),
            "impact_level": news_data.get("impact_level"),
            "description": news_data.get("description"),
            "trading_blocked": news_data.get("trading_blocked", False),
            "timestamp": datetime.now().isoformat()
        }
        
        await self.websocket_server.broadcast_news_update(formatted_news)
    
    async def handle_performance_alert(self, alert_data: Dict):
        """Handle performance alert"""
        formatted_alert = {
            "alert_type": "performance",
            "ea_id": alert_data.get("ea_id"),
            "level": alert_data.get("level", "warning"),
            "message": alert_data.get("message"),
            "metrics": alert_data.get("metrics", {}),
            "timestamp": datetime.now().isoformat()
        }
        
        await self.websocket_server.broadcast_alert(formatted_alert)


async def run_integrated_dashboard():
    """
    Example function showing how to run the complete integrated dashboard system
    """
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    try:
        # Start WebSocket server
        websocket_server = WebSocketServer(
            host="155.138.174.196",
            port=8765,
            auth_token="dashboard_token_2024"
        )
        await websocket_server.start_server()
        
        # Start integration service
        integration_service = DashboardIntegrationService(websocket_server)
        await integration_service.start()
        
        logger.info("Integrated dashboard system started successfully")
        logger.info("WebSocket server running on ws://155.138.174.196:8765")
        logger.info("Use auth token: dashboard_token_2024")
        
        # Keep running
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Shutting down integrated dashboard system")
    except Exception as e:
        logger.error(f"Error running integrated dashboard: {e}")
    finally:
        # Cleanup
        if 'integration_service' in locals():
            await integration_service.stop()
        if 'websocket_server' in locals():
            await websocket_server.stop_server()


async def test_websocket_with_mock_data():
    """
    Test function that demonstrates WebSocket functionality with mock data
    """
    logging.basicConfig(level=logging.INFO)
    
    # Start WebSocket server
    websocket_server = WebSocketServer(host="155.138.174.196", port=8765)
    await websocket_server.start_server()
    
    try:
        # Simulate sending various types of updates
        await asyncio.sleep(2)  # Wait for server to be ready
        
        # Mock EA update
        ea_data = {
            "ea_id": 12345,
            "symbol": "EURUSD",
            "strategy_tag": "Compression_v1",
            "status": "active",
            "current_profit": 150.75,
            "open_positions": 2,
            "performance_metrics": {
                "profit_factor": 1.45,
                "drawdown": 5.2
            }
        }
        await websocket_server.broadcast_ea_update(ea_data)
        
        # Mock portfolio update
        portfolio_data = {
            "total_profit": 2450.30,
            "active_eas": 15,
            "total_eas": 20,
            "drawdown_pct": 3.8
        }
        await websocket_server.broadcast_portfolio_update(portfolio_data)
        
        # Mock trade update
        trade_data = {
            "trade_id": 789,
            "ea_id": 12345,
            "symbol": "EURUSD",
            "order_type": "BUY",
            "volume": 0.1,
            "profit": 25.50
        }
        await websocket_server.broadcast_trade_update(trade_data)
        
        # Mock alert
        alert_data = {
            "level": "warning",
            "message": "EA 12345 drawdown exceeds 10%",
            "ea_id": 12345
        }
        await websocket_server.broadcast_alert(alert_data)
        
        logger.info("Mock data sent successfully")
        
        # Keep server running for testing
        await asyncio.sleep(30)
        
    finally:
        await websocket_server.stop_server()


if __name__ == "__main__":
    # Run the test with mock data
    asyncio.run(test_websocket_with_mock_data())