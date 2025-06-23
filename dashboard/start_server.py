#!/usr/bin/env python3
"""
Dashboard Server Startup Script
Ensures the FastAPI server starts correctly with proper error handling
"""

import sys
import os
import subprocess
import time
import signal

def start_server():
    """Start the FastAPI server with proper configuration"""
    print("🚀 Starting HyperLiquid AI Trading Bot Dashboard Server")
    print("=" * 60)
    
    try:
        # Ensure we're in the right directory
        os.chdir(os.path.dirname(__file__))
        
        print(f"📁 Working directory: {os.getcwd()}")
        print(f"🐍 Python executable: {sys.executable}")
        
        # Check if the app module exists
        if not os.path.exists("backend/app.py"):
            print("❌ backend/app.py not found!")
            return False
        
        print("✅ FastAPI app module found")
        
        # Start the server
        print("\n🔧 Starting FastAPI server...")
        print("   Host: 127.0.0.1")
        print("   Port: 8000")
        print("   Auto-reload: Enabled")
        print("   Log level: info")
        print("\n📡 Server will be available at:")
        print("   • Main API: http://localhost:8000")
        print("   • Swagger UI: http://localhost:8000/api/docs")
        print("   • Health Check: http://localhost:8000/health")
        print("\n⌨️ Press Ctrl+C to stop the server")
        print("=" * 60)
        
        # Start uvicorn with explicit configuration
        cmd = [
            sys.executable, "-m", "uvicorn",
            "backend.app:app",
            "--host", "127.0.0.1",
            "--port", "8000",
            "--reload",
            "--log-level", "info",
            "--access-log"
        ]
        
        process = subprocess.Popen(cmd)
        
        # Handle Ctrl+C gracefully
        def signal_handler(sig, frame):
            print("\n🛑 Stopping server...")
            process.terminate()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        
        # Wait for the process
        process.wait()
        
        return True
        
    except FileNotFoundError as e:
        print(f"❌ Command not found: {e}")
        print("💡 Make sure uvicorn is installed: pip install uvicorn")
        return False
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        return False

if __name__ == "__main__":
    try:
        start_server()
    except KeyboardInterrupt:
        print("\n⏹️ Server startup cancelled by user")
        sys.exit(0) 