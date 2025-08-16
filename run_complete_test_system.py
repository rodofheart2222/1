#!/usr/bin/env python3
"""
Complete Test System Runner

This script orchestrates the complete MT5 trading workflow test:
1. Starts the backend server
2. Starts the EA simulator
3. Runs the workflow tests
4. Generates comprehensive reports

Usage:
    python run_complete_test_system.py [--ea-magic 12345] [--symbol EURUSD]
"""

import asyncio
import subprocess
import time
import signal
import sys
import logging
import argparse
import json
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestSystemOrchestrator:
    """Orchestrates the complete test system"""
    
    def __init__(self, ea_magic: int = 12345, symbol: str = "EURUSD", host: str = "155.138.174.196"):
        self.ea_magic = ea_magic
        self.symbol = symbol
        self.host = host
        
        self.processes = []
        self.running = False
        
    async def start_backend_server(self):
        """Start the backend server"""
        logger.info("🚀 Starting backend server...")
        
        try:
            # Try to start the complete server
            process = subprocess.Popen([
                sys.executable, "backend/start_complete_server.py",
                "--host", self.host,
                "--port", "80",
                "--ws-port", "8765"
            ], cwd=".", stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            self.processes.append(("backend_server", process))
            
            # Wait a moment for server to start
            await asyncio.sleep(5)
            
            # Check if process is still running
            if process.poll() is None:
                logger.info("✅ Backend server started successfully")
                return True
            else:
                stdout, stderr = process.communicate()
                logger.error(f"❌ Backend server failed to start: {stderr.decode()}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to start backend server: {e}")
            return False
    
    async def start_ea_simulator(self):
        """Start the EA simulator"""
        logger.info("🤖 Starting EA simulator...")
        
        try:
            process = subprocess.Popen([
                sys.executable, "simulate_ea_responses.py",
                "--magic", str(self.ea_magic),
                "--symbol", self.symbol,
                "--host", self.host,
                "--port", "80"
            ], cwd=".", stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            self.processes.append(("ea_simulator", process))
            
            # Wait a moment for simulator to start
            await asyncio.sleep(3)
            
            # Check if process is still running
            if process.poll() is None:
                logger.info("✅ EA simulator started successfully")
                return True
            else:
                stdout, stderr = process.communicate()
                logger.error(f"❌ EA simulator failed to start: {stderr.decode()}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to start EA simulator: {e}")
            return False
    
    async def run_workflow_tests(self):
        """Run the complete workflow tests"""
        logger.info("🧪 Running workflow tests...")
        
        try:
            process = subprocess.Popen([
                sys.executable, "test_complete_trading_workflow.py",
                "--ea-magic", str(self.ea_magic),
                "--symbol", self.symbol,
                "--host", self.host,
                "--port", "80",
                "--ws-port", "8765"
            ], cwd=".", stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            # Wait for tests to complete
            stdout, stderr = process.communicate()
            
            # Log test output
            if stdout:
                logger.info("Test Output:")
                for line in stdout.split('\n'):
                    if line.strip():
                        logger.info(f"  {line}")
            
            if stderr:
                logger.error("Test Errors:")
                for line in stderr.split('\n'):
                    if line.strip():
                        logger.error(f"  {line}")
            
            return process.returncode == 0
            
        except Exception as e:
            logger.error(f"❌ Failed to run workflow tests: {e}")
            return False
    
    def stop_all_processes(self):
        """Stop all running processes"""
        logger.info("🛑 Stopping all processes...")
        
        for name, process in self.processes:
            try:
                if process.poll() is None:  # Process is still running
                    logger.info(f"Stopping {name}...")
                    process.terminate()
                    
                    # Wait for graceful shutdown
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        logger.warning(f"Force killing {name}...")
                        process.kill()
                        process.wait()
                    
                    logger.info(f"✅ {name} stopped")
                else:
                    logger.info(f"✅ {name} already stopped")
                    
            except Exception as e:
                logger.error(f"Error stopping {name}: {e}")
        
        self.processes.clear()
    
    async def run_complete_test_cycle(self):
        """Run the complete test cycle"""
        logger.info("=" * 80)
        logger.info("🎯 STARTING COMPLETE MT5 TRADING WORKFLOW TEST SYSTEM")
        logger.info("=" * 80)
        logger.info(f"EA Magic: {self.ea_magic}")
        logger.info(f"Symbol: {self.symbol}")
        logger.info(f"Host: {self.host}")
        logger.info("=" * 80)
        
        self.running = True
        success = False
        
        try:
            # Step 1: Start backend server
            if not await self.start_backend_server():
                logger.error("❌ Failed to start backend server")
                return False
            
            # Step 2: Start EA simulator
            if not await self.start_ea_simulator():
                logger.error("❌ Failed to start EA simulator")
                return False
            
            # Step 3: Wait for systems to stabilize
            logger.info("⏳ Waiting for systems to stabilize...")
            await asyncio.sleep(5)
            
            # Step 4: Run workflow tests
            success = await self.run_workflow_tests()
            
            if success:
                logger.info("🎉 All tests completed successfully!")
            else:
                logger.error("💥 Some tests failed!")
            
            return success
            
        except KeyboardInterrupt:
            logger.info("🛑 Test interrupted by user")
            return False
        except Exception as e:
            logger.error(f"❌ Test system error: {e}")
            return False
        finally:
            self.running = False
            self.stop_all_processes()
    
    def generate_final_report(self):
        """Generate final test report"""
        logger.info("📊 Generating final test report...")
        
        # Find the latest test files
        log_files = list(Path(".").glob("trading_workflow_*.json"))
        if not log_files:
            logger.warning("No test result files found")
            return
        
        latest_file = max(log_files, key=lambda p: p.stat().st_mtime)
        
        try:
            with open(latest_file, 'r') as f:
                test_data = json.load(f)
            
            # Generate summary report
            report = {
                "test_session": test_data.get("test_session", {}),
                "system_config": {
                    "ea_magic": self.ea_magic,
                    "symbol": self.symbol,
                    "host": self.host
                },
                "results_summary": test_data.get("results", {}),
                "latency_summary": test_data.get("latency_summary", {}),
                "test_details": test_data.get("test_details", []),
                "recommendations": self._generate_recommendations(test_data)
            }
            
            # Save final report
            report_filename = f"final_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_filename, 'w') as f:
                json.dump(report, f, indent=2)
            
            # Print summary
            self._print_final_summary(report)
            
            logger.info(f"📄 Final report saved to {report_filename}")
            
        except Exception as e:
            logger.error(f"Failed to generate final report: {e}")
    
    def _generate_recommendations(self, test_data: dict) -> list:
        """Generate recommendations based on test results"""
        recommendations = []
        
        results = test_data.get("results", {})
        latency = test_data.get("latency_summary", {})
        
        # Check success rate
        success_rate = results.get("success_rate", 0)
        if success_rate < 100:
            recommendations.append({
                "category": "reliability",
                "priority": "high",
                "issue": f"Test success rate is {success_rate}%",
                "recommendation": "Investigate failed tests and improve error handling"
            })
        
        # Check latency
        avg_latency = latency.get("avg_latency_ms", 0)
        if avg_latency > 500:
            recommendations.append({
                "category": "performance",
                "priority": "medium",
                "issue": f"Average latency is {avg_latency:.1f}ms",
                "recommendation": "Optimize API response times and WebSocket communication"
            })
        
        # Check specific test failures
        test_details = test_data.get("test_details", [])
        for test in test_details:
            if test.get("status") == "FAIL":
                recommendations.append({
                    "category": "functionality",
                    "priority": "high",
                    "issue": f"{test.get('test_name')} failed",
                    "recommendation": f"Fix: {test.get('details', 'Unknown error')}"
                })
        
        if not recommendations:
            recommendations.append({
                "category": "system",
                "priority": "info",
                "issue": "All tests passed",
                "recommendation": "System is performing well. Consider load testing for production readiness."
            })
        
        return recommendations
    
    def _print_final_summary(self, report: dict):
        """Print final test summary"""
        logger.info("=" * 80)
        logger.info("📊 FINAL TEST REPORT SUMMARY")
        logger.info("=" * 80)
        
        results = report.get("results_summary", {})
        logger.info(f"Total Tests: {results.get('total_tests', 0)}")
        logger.info(f"✅ Passed: {results.get('passed', 0)}")
        logger.info(f"❌ Failed: {results.get('failed', 0)}")
        logger.info(f"📈 Success Rate: {results.get('success_rate', 0)}%")
        
        latency = report.get("latency_summary", {})
        logger.info(f"⚡ Avg Latency: {latency.get('avg_latency_ms', 0):.2f}ms")
        logger.info(f"🔄 Total Operations: {latency.get('total_operations', 0)}")
        
        recommendations = report.get("recommendations", [])
        if recommendations:
            logger.info("\n🔍 RECOMMENDATIONS:")
            for i, rec in enumerate(recommendations, 1):
                priority_emoji = "🔴" if rec["priority"] == "high" else "🟡" if rec["priority"] == "medium" else "🔵"
                logger.info(f"{i}. {priority_emoji} [{rec['category'].upper()}] {rec['issue']}")
                logger.info(f"   💡 {rec['recommendation']}")
        
        logger.info("=" * 80)


def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}, shutting down...")
    sys.exit(0)


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Complete MT5 Trading Workflow Test System')
    parser.add_argument('--ea-magic', type=int, default=12345, help='EA Magic Number')
    parser.add_argument('--symbol', default='EURUSD', help='Trading Symbol')
    parser.add_argument('--host', default='155.138.174.196', help='Server Host')
    parser.add_argument('--no-report', action='store_true', help='Skip final report generation')
    
    args = parser.parse_args()
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    orchestrator = TestSystemOrchestrator(args.ea_magic, args.symbol, args.host)
    
    try:
        success = await orchestrator.run_complete_test_cycle()
        
        if not args.no_report:
            orchestrator.generate_final_report()
        
        if success:
            logger.info("🎉 Complete test system finished successfully!")
            return 0
        else:
            logger.error("💥 Complete test system finished with errors!")
            return 1
            
    except Exception as e:
        logger.error(f"Test system error: {e}")
        return 1
    finally:
        orchestrator.stop_all_processes()


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("Test system interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)