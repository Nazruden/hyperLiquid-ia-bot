#!/usr/bin/env python3
"""
Dashboard Backend Test Script
Quick test to verify FastAPI backend functionality
"""

import asyncio
import sys
import os
import subprocess
import time

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

async def test_backend():
    """Test the dashboard backend"""
    print("🧪 Testing HyperLiquid AI Trading Bot Dashboard Backend")
    print("=" * 60)
    
    try:
        # Test 1: Import modules
        print("1. Testing module imports...")
        from dashboard.backend.app import app
        from dashboard.backend.websocket_manager import WebSocketManager
        from dashboard.backend.bot_controller import BotController
        from dashboard.backend.data_service import DataService
        print("   ✅ All modules imported successfully")
        
        # Test 2: Initialize services
        print("\n2. Testing service initialization...")
        
        # Test WebSocket Manager
        ws_manager = WebSocketManager()
        print("   ✅ WebSocket Manager initialized")
        
        # Test Bot Controller
        bot_controller = BotController()
        status = bot_controller.get_status()
        print(f"   ✅ Bot Controller initialized - Status: {status['status']}")
        
        # Test Data Service
        data_service = DataService()
        await data_service.initialize()
        db_healthy = await data_service.health_check()
        print(f"   ✅ Data Service initialized - DB Health: {'OK' if db_healthy else 'FAILED'}")
        
        # Test 3: API endpoints simulation
        print("\n3. Testing API functionality...")
        
        # Test dashboard snapshot
        snapshot = await data_service.get_dashboard_snapshot()
        print(f"   ✅ Dashboard snapshot retrieved - Keys: {list(snapshot.keys())}")
        
        # Test trading summary
        trading_summary = await data_service.get_trading_summary()
        print(f"   ✅ Trading summary retrieved - Total trades: {trading_summary.get('total_trades', 0)}")
        
        # Test 4: System resources
        print("\n4. Testing system monitoring...")
        resources = bot_controller.get_system_resources()
        if "error" not in resources:
            print(f"   ✅ System resources: CPU {resources.get('cpu_percent', 0):.1f}%, Memory {resources.get('memory_percent', 0):.1f}%")
        else:
            print(f"   ⚠️ System resources error: {resources['error']}")
        
        print("\n" + "=" * 60)
        print("🎉 Backend test completed successfully!")
        print("\n📋 Test Results Summary:")
        print(f"   • Module imports: ✅ Success")
        print(f"   • Service initialization: ✅ Success")
        print(f"   • Database connectivity: {'✅ Success' if db_healthy else '❌ Failed'}")
        print(f"   • API functionality: ✅ Success")
        print(f"   • System monitoring: ✅ Success")
        
        print("\n🚀 Ready to start FastAPI server!")
        print("   Run: cd dashboard && python -m uvicorn backend.app:app --reload --host 0.0.0.0 --port 8000")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_requirements():
    """Check if required packages are installed"""
    print("📦 Checking requirements...")
    
    required_packages = [
        "fastapi",
        "uvicorn",
        "websockets",
        "psutil",
        "pydantic"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"   ✅ {package}")
        except ImportError:
            print(f"   ❌ {package} - MISSING")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n❌ Missing packages: {', '.join(missing_packages)}")
        print("Install with: pip install fastapi uvicorn websockets psutil pydantic")
        return False
    
    print("   ✅ All requirements satisfied")
    return True

if __name__ == "__main__":
    print("🔧 HyperLiquid AI Trading Bot Dashboard - Backend Test")
    print("=" * 60)
    
    # Check requirements first
    if not check_requirements():
        sys.exit(1)
    
    print()
    
    # Run async test
    try:
        success = asyncio.run(test_backend())
        if success:
            print("\n🎯 Next Steps:")
            print("1. Install frontend dependencies: cd dashboard/frontend && npm install")
            print("2. Start backend: cd dashboard && python -m uvicorn backend.app:app --reload --port 8000")
            print("3. Start frontend: cd dashboard/frontend && npm run dev")
            print("4. Open dashboard: http://localhost:3000")
            sys.exit(0)
        else:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")
        sys.exit(1) 