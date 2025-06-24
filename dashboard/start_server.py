#!/usr/bin/env python3
"""
Dashboard Server Startup Script
Ensures the FastAPI server starts correctly with proper error handling
Supports both regular and hot reload modes
"""

import sys
import os
import subprocess
import time
import signal
import argparse

def start_server(hot_reload=False):
    """Start the FastAPI server with proper configuration"""
    mode = "Hot Reload" if hot_reload else "Standard"
    print(f"🚀 Starting HyperLiquid AI Trading Bot Dashboard Server ({mode} Mode)")
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
        
        if hot_reload:
            # Check if jurigged is available
            try:
                subprocess.run([sys.executable, "-m", "jurigged", "--version"], 
                             capture_output=True, check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                print("❌ jurigged not found! Installing...")
                try:
                    subprocess.run([sys.executable, "-m", "pip", "install", "jurigged"], check=True)
                    print("✅ jurigged installed successfully")
                except subprocess.CalledProcessError:
                    print("❌ Failed to install jurigged. Falling back to standard mode...")
                    hot_reload = False
        
        # Start the server
        print(f"\n🔧 Starting FastAPI server in {mode} mode...")
        print("   Host: 127.0.0.1")
        print("   Port: 8000")
        print("   Auto-reload: Enabled")
        print("   Log level: info")
        
        if hot_reload:
            print("   🔥 Hot reload: Jurigged (Python hot patching)")
        else:
            print("   🔄 Hot reload: Uvicorn (process restart)")
            
        print("\n📡 Server will be available at:")
        print("   • Main API: http://localhost:8000")
        print("   • Swagger UI: http://localhost:8000/api/docs")
        print("   • Health Check: http://localhost:8000/health")
        print("\n⌨️ Press Ctrl+C to stop the server")
        print("=" * 60)
        
        if hot_reload:
            # Start with jurigged for hot patching
            cmd = [
                sys.executable, "-m", "jurigged",
                "-v",  # Verbose mode
                "-w", "backend/",           # Watch backend directory
                "-w", "backend/routers/",   # Watch routers
                "-w", "backend/controllers/", # Watch controllers
                "-w", "backend/services/",    # Watch services
                "-d", "1",  # 1 second debounce
                "-m", "uvicorn",  # Run uvicorn as module
                "backend.app:app",
                "--host", "127.0.0.1",
                "--port", "8000",
                "--reload",  # Keep uvicorn's reload as backup
                "--log-level", "info",
                "--access-log"
            ]
        else:
            # Standard uvicorn with restart-based reload
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
        if hot_reload:
            print("💡 For hot reload: pip install jurigged")
        return False
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        return False

def main():
    """Main entry point with argument parsing"""
    parser = argparse.ArgumentParser(
        description="HyperLiquid Dashboard Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python start_server.py           # Standard mode with uvicorn reload
  python start_server.py --hot     # Hot reload mode with jurigged
  python start_server.py --hotreload  # Alternative flag for hot reload
        """
    )
    
    parser.add_argument(
        "--hot", "--hotreload", 
        action="store_true",
        help="Enable hot reload mode with jurigged (instant code updates)"
    )
    
    args = parser.parse_args()
    
    try:
        start_server(hot_reload=args.hot)
    except KeyboardInterrupt:
        print("\n⏹️ Server startup cancelled by user")
        sys.exit(0)

if __name__ == "__main__":
    main() 