#!/usr/bin/env python3
"""
Test script for HyperLiquid AI Trading Bot Dashboard
Verifies that both backend and frontend are working correctly
"""

import requests
import time
import websocket
import json
import threading
from colorama import init, Fore, Style

# Initialize colorama for colored output
init()

def print_status(message, status="INFO"):
    colors = {
        "INFO": Fore.BLUE,
        "SUCCESS": Fore.GREEN,
        "ERROR": Fore.RED,
        "WARNING": Fore.YELLOW
    }
    print(f"{colors.get(status, Fore.WHITE)}[{status}] {message}{Style.RESET_ALL}")

def test_backend_health():
    """Test backend health endpoint"""
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_status(f"Backend health check: {data['status']}", "SUCCESS")
            return True
        else:
            print_status(f"Backend health check failed: {response.status_code}", "ERROR")
            return False
    except Exception as e:
        print_status(f"Backend health check failed: {e}", "ERROR")
        return False

def test_api_endpoints():
    """Test key API endpoints"""
    endpoints = [
        "/api/analytics/dashboard-metrics",
        "/api/analytics/summary",
        "/api/bot/status",
        "/api/trades"
    ]
    
    success_count = 0
    for endpoint in endpoints:
        try:
            response = requests.get(f"http://localhost:8000{endpoint}", timeout=5)
            if response.status_code == 200:
                print_status(f"✓ {endpoint}", "SUCCESS")
                success_count += 1
            else:
                print_status(f"✗ {endpoint} - Status: {response.status_code}", "ERROR")
        except Exception as e:
            print_status(f"✗ {endpoint} - Error: {e}", "ERROR")
    
    print_status(f"API endpoints: {success_count}/{len(endpoints)} working", "INFO")
    return success_count == len(endpoints)

def test_websocket():
    """Test WebSocket connection"""
    ws_connected = False
    ws_error = None
    
    def on_message(ws, message):
        print_status(f"WebSocket message received: {message[:100]}...", "SUCCESS")
    
    def on_error(ws, error):
        nonlocal ws_error
        ws_error = str(error)
    
    def on_open(ws):
        nonlocal ws_connected
        ws_connected = True
        print_status("WebSocket connection established", "SUCCESS")
        # Send a test ping
        ws.send(json.dumps({"type": "ping"}))
        time.sleep(1)
        ws.close()
    
    def on_close(ws, close_status_code, close_msg):
        print_status("WebSocket connection closed", "INFO")
    
    try:
        ws = websocket.WebSocketApp(
            "ws://localhost:8000/ws",
            on_open=on_open,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close
        )
        
        # Run WebSocket in a separate thread with timeout
        ws_thread = threading.Thread(target=ws.run_forever)
        ws_thread.daemon = True
        ws_thread.start()
        ws_thread.join(timeout=5)
        
        if ws_connected:
            return True
        elif ws_error:
            print_status(f"WebSocket connection failed: {ws_error}", "ERROR")
            return False
        else:
            print_status("WebSocket connection timeout", "WARNING")
            return False
            
    except Exception as e:
        print_status(f"WebSocket test failed: {e}", "ERROR")
        return False

def test_frontend():
    """Test if frontend is accessible"""
    try:
        response = requests.get("http://localhost:5173", timeout=5)
        if response.status_code == 200:
            print_status("Frontend is accessible", "SUCCESS")
            return True
        else:
            print_status(f"Frontend not accessible: {response.status_code}", "WARNING")
            return False
    except Exception as e:
        print_status(f"Frontend test failed: {e}", "WARNING")
        return False

def main():
    """Run all tests"""
    print_status("=== HyperLiquid AI Trading Bot Dashboard Tests ===", "INFO")
    print()
    
    # Test backend
    print_status("Testing Backend...", "INFO")
    backend_ok = test_backend_health()
    
    if backend_ok:
        api_ok = test_api_endpoints()
        ws_ok = test_websocket()
    else:
        api_ok = False
        ws_ok = False
    
    print()
    
    # Test frontend
    print_status("Testing Frontend...", "INFO")
    frontend_ok = test_frontend()
    
    print()
    
    # Summary
    print_status("=== Test Summary ===", "INFO")
    print_status(f"Backend Health: {'✓' if backend_ok else '✗'}", "SUCCESS" if backend_ok else "ERROR")
    print_status(f"API Endpoints: {'✓' if api_ok else '✗'}", "SUCCESS" if api_ok else "ERROR")
    print_status(f"WebSocket: {'✓' if ws_ok else '✗'}", "SUCCESS" if ws_ok else "ERROR")
    print_status(f"Frontend: {'✓' if frontend_ok else '✗'}", "SUCCESS" if frontend_ok else "WARNING")
    
    if backend_ok and api_ok:
        print()
        print_status("🎉 Dashboard is ready!", "SUCCESS")
        print_status("Backend running at: http://localhost:8000", "INFO")
        print_status("Frontend running at: http://localhost:5173", "INFO")
        print_status("API docs at: http://localhost:8000/api/docs", "INFO")
    else:
        print()
        print_status("⚠️  Some issues found. Please check the logs above.", "WARNING")

if __name__ == "__main__":
    main() 