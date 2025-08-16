#!/usr/bin/env python3
"""
Quick Server Test for Port 8000

Simple test to check if the server is responding on port 8000
"""

import asyncio
import aiohttp
import sys

async def quick_test():
    """Quick test of server responsiveness"""
    host = "155.138.174.196"
    port = 8000  # Changed to port 8000
    url = f"http://{host}:{port}/health"
    
    print(f"Testing server at {url}...")
    
    try:
        timeout = aiohttp.ClientTimeout(total=5)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Server is responding: {data}")
                    return True
                else:
                    print(f"❌ Server returned status {response.status}")
                    return False
    except asyncio.TimeoutError:
        print("❌ Server timeout - not responding")
        return False
    except aiohttp.ClientConnectorError:
        print("❌ Connection refused - server not running")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(quick_test())
    sys.exit(0 if success else 1)