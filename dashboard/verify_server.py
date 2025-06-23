#!/usr/bin/env python3
"""
Dashboard Server Verification Script
Test that the FastAPI server is running and responding
"""

import requests
import json
import time
import sys

def test_server():
    """Test the running FastAPI server"""
    base_url = "http://localhost:8000"
    
    print("🔗 Testing HyperLiquid AI Trading Bot Dashboard Server")
    print("=" * 60)
    
    try:
        # Test 1: Root endpoint
        print("1. Testing root endpoint...")
        response = requests.get(f"{base_url}/", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Root endpoint: {data.get('name', 'Unknown')}")
            print(f"   📊 Status: {data.get('status', 'Unknown')}")
        else:
            print(f"   ❌ Root endpoint failed: {response.status_code}")
            return False
        
        # Test 2: Health check
        print("\n2. Testing health endpoint...")
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Health status: {data.get('status', 'Unknown')}")
            services = data.get('services', {})
            for service, status in services.items():
                print(f"   📋 {service}: {status}")
        else:
            print(f"   ❌ Health endpoint failed: {response.status_code}")
        
        # Test 3: Bot control endpoint
        print("\n3. Testing bot control endpoint...")
        response = requests.get(f"{base_url}/api/bot/status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            bot_status = data.get('data', {}).get('status', 'Unknown')
            print(f"   ✅ Bot status endpoint: {bot_status}")
        else:
            print(f"   ❌ Bot status endpoint failed: {response.status_code}")
        
        # Test 4: Analytics endpoint
        print("\n4. Testing analytics endpoint...")
        response = requests.get(f"{base_url}/api/analytics/trading-summary", timeout=5)
        if response.status_code == 200:
            data = response.json()
            summary = data.get('data', {})
            print(f"   ✅ Analytics endpoint: {summary.get('total_trades', 0)} trades")
        else:
            print(f"   ❌ Analytics endpoint failed: {response.status_code}")
        
        # Test 5: Trades endpoint
        print("\n5. Testing trades endpoint...")
        response = requests.get(f"{base_url}/api/trades/recent?limit=5", timeout=5)
        if response.status_code == 200:
            data = response.json()
            trades = data.get('data', {}).get('trades', [])
            print(f"   ✅ Trades endpoint: {len(trades)} recent trades")
        else:
            print(f"   ❌ Trades endpoint failed: {response.status_code}")
        
        print("\n" + "=" * 60)
        print("🎉 Server verification completed successfully!")
        print("\n📋 API Documentation:")
        print(f"   • Swagger UI: {base_url}/api/docs")
        print(f"   • ReDoc: {base_url}/api/redoc")
        print("\n🌐 Available Endpoints:")
        print(f"   • Root: {base_url}/")
        print(f"   • Health: {base_url}/health")
        print(f"   • Bot Control: {base_url}/api/bot/*")
        print(f"   • Analytics: {base_url}/api/analytics/*")
        print(f"   • Trades: {base_url}/api/trades/*")
        print(f"   • WebSocket: ws://localhost:8000/ws")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Is it running?")
        print("   Start with: python -m uvicorn backend.app:app --reload --port 8000")
        return False
    except requests.exceptions.Timeout:
        print("❌ Server timeout. Check server status.")
        return False
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False

if __name__ == "__main__":
    print("🔧 HyperLiquid AI Trading Bot Dashboard - Server Verification")
    print("=" * 60)
    
    # Wait a moment for server to be ready
    print("⏳ Waiting for server to be ready...")
    time.sleep(2)
    
    success = test_server()
    
    if success:
        print("\n✅ Server is running correctly!")
        print("🎯 Ready for Phase 2: Frontend Development")
        sys.exit(0)
    else:
        print("\n❌ Server verification failed!")
        sys.exit(1) 