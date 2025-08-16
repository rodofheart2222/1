#!/usr/bin/env python3
"""
Debug script for backtest upload issues
"""
import requests
import os
import sys

def test_server_connection():
    """Test if server is running"""
    try:
        response = requests.get("http://155.138.174.196:8000/health", timeout=5)
        print(f"Server health check: {response.status_code}")
        if response.status_code == 200:
            print("✅ Server is running")
            return True
        else:
            print(f"❌ Server error: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        print("Please check if server is running on 155.138.174.196:8000")
        return False

def test_file_exists():
    """Test if the HTML file exists"""
    html_file_path = "backend/services/ReportTester-10007209416.html"
    if os.path.exists(html_file_path):
        file_size = os.path.getsize(html_file_path)
        print(f"✅ HTML file found: {html_file_path} ({file_size} bytes)")
        return html_file_path
    else:
        print(f"❌ HTML file not found: {html_file_path}")
        return None

def test_backtest_upload(html_file_path):
    """Test the actual upload"""
    url = "http://155.138.174.196:8000/api/ea/backtest/upload"
    magic_number = 777777
    
    try:
        with open(html_file_path, 'rb') as f:
            files = {'file': ('ReportTester-10007209416.html', f, 'text/html')}
            data = {'magic_number': magic_number}
            
            print(f"Uploading to: {url}")
            print(f"Magic number: {magic_number}")
            
            response = requests.post(url, files=files, data=data, timeout=30)
            
            print(f"Response status: {response.status_code}")
            print(f"Response headers: {dict(response.headers)}")
            print(f"Response body: {response.text}")
            
            if response.status_code == 200:
                print("✅ Upload successful!")
                return True
            else:
                print("❌ Upload failed!")
                return False
                
    except Exception as e:
        print(f"❌ Upload error: {e}")
        return False

def test_database_check():
    """Check if data was stored in database"""
    try:
        # Try to get the benchmark back
        url = "http://155.138.174.196:8000/api/ea/backtest/benchmark/777777"
        response = requests.get(url, timeout=10)
        
        print(f"Database check status: {response.status_code}")
        print(f"Database check response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Data found in database!")
            return True
        else:
            print("❌ Data not found in database")
            return False
            
    except Exception as e:
        print(f"❌ Database check error: {e}")
        return False

def main():
    print("🔍 Debugging Backtest Upload Issues")
    print("=" * 50)
    
    # Step 1: Check server
    if not test_server_connection():
        return
    
    # Step 2: Check file
    html_file = test_file_exists()
    if not html_file:
        return
    
    # Step 3: Test upload
    if not test_backtest_upload(html_file):
        return
    
    # Step 4: Check database
    test_database_check()
    
    print("\n🎉 All tests completed!")

if __name__ == "__main__":
    main()