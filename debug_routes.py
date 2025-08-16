#!/usr/bin/env python3
"""
Debug script to check what routes are registered in the FastAPI app
"""
import sys
import os

# Add the backend directory to the path
sys.path.insert(0, 'backend')

try:
    from main import app
    
    print("🔍 Debugging FastAPI Routes")
    print("=" * 50)
    
    print(f"App title: {app.title}")
    print(f"App version: {app.version}")
    print()
    
    print("Registered Routes:")
    print("-" * 30)
    
    for route in app.routes:
        if hasattr(route, 'path') and hasattr(route, 'methods'):
            methods = ', '.join(route.methods) if route.methods else 'N/A'
            print(f"{methods:15} {route.path}")
        elif hasattr(route, 'path'):
            print(f"{'MOUNT':15} {route.path}")
    
    print()
    print("Looking for EA routes specifically:")
    print("-" * 30)
    
    ea_routes = [route for route in app.routes if hasattr(route, 'path') and '/api/ea' in route.path]
    if ea_routes:
        print(f"✅ Found {len(ea_routes)} EA routes:")
        for route in ea_routes:
            methods = ', '.join(route.methods) if hasattr(route, 'methods') and route.methods else 'N/A'
            print(f"  {methods:15} {route.path}")
    else:
        print("❌ No EA routes found!")
    
    print()
    print("Looking for backtest routes:")
    print("-" * 30)
    
    backtest_routes = [route for route in app.routes if hasattr(route, 'path') and '/api/backtest' in route.path]
    if backtest_routes:
        print(f"✅ Found {len(backtest_routes)} backtest routes:")
        for route in backtest_routes:
            methods = ', '.join(route.methods) if hasattr(route, 'methods') and route.methods else 'N/A'
            print(f"  {methods:15} {route.path}")
    else:
        print("❌ No backtest routes found!")
    
    print()
    print("Looking for simple-backtest routes:")
    print("-" * 30)
    
    simple_backtest_routes = [route for route in app.routes if hasattr(route, 'path') and '/api/simple-backtest' in route.path]
    if simple_backtest_routes:
        print(f"✅ Found {len(simple_backtest_routes)} simple-backtest routes:")
        for route in simple_backtest_routes:
            methods = ', '.join(route.methods) if hasattr(route, 'methods') and route.methods else 'N/A'
            print(f"  {methods:15} {route.path}")
    else:
        print("❌ No simple-backtest routes found!")

except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running this from the project root directory")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()