#!/usr/bin/env python3
"""
Check what's running on ports
"""

import subprocess
import sys

def check_port(port):
    """Check what's running on a specific port"""
    try:
        # For Windows
        result = subprocess.run(['netstat', '-ano'], capture_output=True, text=True)
        lines = result.stdout.split('\n')
        
        for line in lines:
            if f':{port}' in line and 'LISTENING' in line:
                parts = line.split()
                if len(parts) >= 5:
                    pid = parts[-1]
                    print(f"Port {port} is used by process PID: {pid}")
                    
                    # Get process name
                    try:
                        tasklist_result = subprocess.run(['tasklist', '/FI', f'PID eq {pid}'], 
                                                       capture_output=True, text=True)
                        print(f"Process details:\n{tasklist_result.stdout}")
                    except:
                        pass
                    return True
        
        print(f"Port {port} appears to be free")
        return False
        
    except Exception as e:
        print(f"Error checking port {port}: {e}")
        return False

def main():
    """Check common ports"""
    ports_to_check = [80, 8000, 8080, 3000, 8765]
    
    print("🔍 Checking port usage...")
    print("=" * 50)
    
    for port in ports_to_check:
        print(f"\nChecking port {port}:")
        check_port(port)
    
    print("\n" + "=" * 50)
    print("💡 Recommendations:")
    print("- If port 80 is used by IIS/Apache, you can stop those services")
    print("- Or use port 8000 for development (type 'Y' when prompted)")
    print("- Port 8765 should be free for WebSocket server")

if __name__ == "__main__":
    main()