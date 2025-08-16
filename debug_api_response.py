#!/usr/bin/env python3
"""
Debug script to check what the API is actually returning
"""

import requests
import json
import sys
from pathlib import Path

def test_api_response():
    """Test what the API is actually returning"""
    
    print("Debugging API Response")
    print("=" * 50)
    
    base_url = "http://155.138.174.196:80"  # Adjust if needed
    
    try:
        # Test benchmarks endpoint
        print("1. Testing /api/backtest/benchmarks endpoint...")
        response = requests.get(f"{base_url}/api/backtest/benchmarks", timeout=10)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Response keys: {list(data.keys())}")
            print(f"   Success: {data.get('success')}")
            print(f"   Source: {data.get('source')}")
            
            benchmarks = data.get('benchmarks', [])
            print(f"   Benchmarks count: {len(benchmarks)}")
            
            if benchmarks:
                print("   Benchmarks:")
                for i, benchmark in enumerate(benchmarks):
                    print(f"     {i+1}. EA {benchmark.get('ea_id')}: PF={benchmark.get('profit_factor')}, WR={benchmark.get('win_rate')}%")
            else:
                print("   No benchmarks found")
                
            summary = data.get('summary', {})
            print(f"   Summary: {summary}")
        else:
            print(f"   Error: {response.text}")
        
        # Test health endpoint
        print("\n2. Testing /api/backtest/health endpoint...")
        response = requests.get(f"{base_url}/api/backtest/health", timeout=10)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Health data: {json.dumps(data, indent=2)}")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to API server")
        print(f"   Make sure the server is running on {base_url}")
        return False
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False

def test_database_directly():
    """Test the database directly to see what's stored"""
    
    print("\n" + "=" * 50)
    print("Testing Database Directly")
    print("=" * 50)
    
    try:
        # Add backend to path
        backend_path = Path(__file__).parent / "backend"
        if str(backend_path) not in sys.path:
            sys.path.insert(0, str(backend_path))
        
        import sqlite3
        import os
        
        # Check database file
        db_path = "data/mt5_dashboard.db"
        if not os.path.exists(db_path):
            print(f"❌ Database file not found: {db_path}")
            return False
        
        print(f"✅ Database file found: {db_path}")
        
        # Connect and query
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='backtest_benchmarks'
        """)
        
        if not cursor.fetchone():
            print("❌ backtest_benchmarks table does not exist")
            conn.close()
            return False
        
        print("✅ backtest_benchmarks table exists")
        
        # Get all records
        cursor.execute("""
            SELECT ea_id, profit_factor, expected_payoff, drawdown, 
                   win_rate, trade_count, upload_date
            FROM backtest_benchmarks 
            ORDER BY upload_date DESC
        """)
        
        rows = cursor.fetchall()
        print(f"📊 Found {len(rows)} records in database:")
        
        for i, row in enumerate(rows):
            print(f"   {i+1}. EA {row[0]}: PF={row[1]}, EP={row[2]}, DD={row[3]}%, WR={row[4]}%, Trades={row[5]}")
        
        conn.close()
        return len(rows) > 0
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_backtest_service():
    """Test the BacktestService directly"""
    
    print("\n" + "=" * 50)
    print("Testing BacktestService Directly")
    print("=" * 50)
    
    try:
        # Add backend to path
        backend_path = Path(__file__).parent / "backend"
        if str(backend_path) not in sys.path:
            sys.path.insert(0, str(backend_path))
        
        from database.connection import DatabaseManager
        from services.backtest_service import BacktestService
        
        # Initialize service
        db_manager = DatabaseManager("sqlite:///data/mt5_dashboard.db")
        backtest_service = BacktestService(db_manager)
        
        # Test getting benchmarks using service
        print("1. Testing BacktestService.get_benchmark_summary()...")
        summary = backtest_service.get_benchmark_summary()
        print(f"   Summary: {summary}")
        
        # Test getting EAs with benchmarks
        print("\n2. Testing BacktestService._get_eas_with_benchmarks()...")
        ea_ids = backtest_service._get_eas_with_benchmarks()
        print(f"   EAs with benchmarks: {ea_ids}")
        
        # Test getting specific benchmarks
        for ea_id in ea_ids[:3]:  # Test first 3
            print(f"\n3. Testing BacktestService.get_backtest_benchmark({ea_id})...")
            benchmark = backtest_service.get_backtest_benchmark(ea_id)
            if benchmark:
                print(f"   EA {ea_id}: PF={benchmark.profit_factor}, WR={benchmark.win_rate}%")
            else:
                print(f"   No benchmark found for EA {ea_id}")
        
        return True
        
    except Exception as e:
        print(f"❌ BacktestService test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("API Response Debug Tool")
    print("=" * 60)
    
    # Test in order
    api_test = test_api_response()
    db_test = test_database_directly()
    service_test = test_backtest_service()
    
    print("\n" + "=" * 60)
    print("DEBUG RESULTS:")
    print(f"API Test: {'✅ PASSED' if api_test else '❌ FAILED'}")
    print(f"Database Test: {'✅ PASSED' if db_test else '❌ FAILED'}")
    print(f"Service Test: {'✅ PASSED' if service_test else '❌ FAILED'}")
    
    if not db_test:
        print("\n💡 ISSUE: No data in database - upload a backtest first")
    elif not service_test:
        print("\n💡 ISSUE: BacktestService not working properly")
    elif not api_test:
        print("\n💡 ISSUE: API not returning data correctly")
    else:
        print("\n🎉 Everything looks good - check frontend console for errors")