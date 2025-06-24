#!/usr/bin/env python3
"""
HyperLiquid AI Trading Bot - Hot Reload Development Mode
Starts trading bot + dashboard backend with jurigged hot reload for rapid development
"""

import subprocess
import sys
import time
import threading
import signal
import os
from pathlib import Path

class HotReloadLauncher:
    def __init__(self):
        self.processes = []
        self.root_dir = Path(__file__).parent.parent
        
    def print_banner(self):
        """Print startup banner"""
        print("🚀 HyperLiquid AI Trading Bot - HOT RELOAD Development Mode")
        print("=" * 70)
        print("🔥 Jurigged Hot Reload: ENABLED")
        print("📁 Project Directory:", self.root_dir)
        print("🐍 Python Executable:", sys.executable)
        print("⏰ Starting Time:", time.strftime("%Y-%m-%d %H:%M:%S"))
        print("=" * 70)
        print("💡 Benefits:")
        print("   • ⚡ Instant code updates without restart")
        print("   • 🔄 Preserves bot state and WebSocket connections")
        print("   • 🧪 Perfect for strategy development and debugging")
        print("=" * 70)
        
    def check_prerequisites(self):
        """Check if all required files and dependencies exist"""
        print("🔍 Checking Prerequisites...")
        
        # Check main bot file
        if not (self.root_dir / "main.py").exists():
            print("❌ main.py not found!")
            return False
            
        # Check dashboard backend
        if not (self.root_dir / "dashboard" / "backend" / "app.py").exists():
            print("❌ Dashboard backend not found!")
            return False
            
        # Check jurigged installation
        try:
            subprocess.run([sys.executable, "-m", "jurigged", "--version"], 
                         capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("❌ jurigged not found! Installing...")
            try:
                subprocess.run([sys.executable, "-m", "pip", "install", "jurigged"], check=True)
                print("✅ jurigged installed successfully")
            except subprocess.CalledProcessError:
                print("❌ Failed to install jurigged. Please install manually: pip install jurigged")
                return False
            
        print("✅ All prerequisites found")
        return True
        
    def _start_stream_reader(self, stream, prefix):
        """Starts a thread to read and print from a stream."""
        def reader_thread():
            for line in iter(stream.readline, ''):
                print(f"[{prefix}] {line}", end='')
            stream.close()
        
        thread = threading.Thread(target=reader_thread)
        thread.daemon = True
        thread.start()
        
    def start_trading_bot_hotreload(self):
        """Start the main trading bot with jurigged hot reload"""
        print("\n🤖 Starting Trading Bot with Hot Reload...")
        print("   • Command: python -m jurigged -v main.py")
        print("   • Hot Reload: ENABLED")
        print("   • Watch directories: strategy/, allora/, core/, database/")
        print("   • Working Dir:", self.root_dir)
        
        try:
            # Start with jurigged, watching key directories for changes
            cmd = [
                sys.executable, "-m", "jurigged", 
                "-v",  # Verbose mode to see what's being reloaded
                "-w", "strategy/",  # Watch strategy directory
                "-w", "allora/",    # Watch allora directory
                "-w", "core/",      # Watch core directory
                "-w", "database/",  # Watch database directory
                "-w", "analysis/",  # Watch analysis directory
                "-d", "1",          # 1 second debounce
                "main.py"
            ]
            
            process = subprocess.Popen(
                cmd,
                cwd=self.root_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            self._start_stream_reader(process.stdout, "Bot-HotReload-out")
            self._start_stream_reader(process.stderr, "Bot-HotReload-err")

            self.processes.append(("Trading Bot (Hot Reload)", process))
            print("✅ Trading Bot with Hot Reload started (PID:", process.pid, ")")
            print("   🔥 Code changes will be applied instantly!")
            return True
        except Exception as e:
            print(f"❌ Failed to start Trading Bot: {e}")
            return False
            
    def start_dashboard_backend_hotreload(self):
        """Start FastAPI dashboard backend with jurigged hot reload"""
        print("\n⚙️ Starting Dashboard Backend with Hot Reload...")
        print("   • URL: http://localhost:8000")
        print("   • API Docs: http://localhost:8000/api/docs")
        print("   • WebSocket: ws://localhost:8000/ws")
        print("   • Hot Reload: ENABLED")
        
        try:
            # Use jurigged for the dashboard backend as well
            cmd = [
                sys.executable, "-m", "jurigged",
                "-v",  # Verbose mode
                "-w", "dashboard/backend/",  # Watch backend directory
                "-d", "1",  # 1 second debounce
                "-m", "uvicorn",  # Run uvicorn as module
                "dashboard.backend.app:app",
                "--host", "127.0.0.1",
                "--port", "8000",
                "--reload"  # Keep uvicorn's reload for file watching
            ]
            
            process = subprocess.Popen(
                cmd, 
                cwd=self.root_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            self._start_stream_reader(process.stdout, "Backend-HotReload-out")
            self._start_stream_reader(process.stderr, "Backend-HotReload-err")
            
            self.processes.append(("Dashboard Backend (Hot Reload)", process))
            print("✅ Dashboard Backend with Hot Reload started (PID:", process.pid, ")")
            print("   🔥 Backend changes will be applied instantly!")
            return True
        except Exception as e:
            print(f"❌ Failed to start Dashboard Backend: {e}")
            return False
            
    def start_dashboard_frontend(self):
        """Start React frontend development server (already has hot reload)"""
        print("\n🎨 Starting Dashboard Frontend...")
        print("   • URL: http://localhost:5173")
        print("   • Hot Reload: Native Vite HMR")
        
        frontend_dir = self.root_dir / "dashboard" / "frontend"
        
        try:
            # Check if node_modules exists, install if not
            if not (frontend_dir / "node_modules").exists():
                print("📦 Installing frontend dependencies...")
                subprocess.run(["npm", "install"], cwd=frontend_dir, check=True)
                
            process = subprocess.Popen(
                ["npm", "run", "dev"],
                cwd=frontend_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            self._start_stream_reader(process.stdout, "Frontend-out")
            self._start_stream_reader(process.stderr, "Frontend-err")
            
            self.processes.append(("Dashboard Frontend", process))
            print("✅ Dashboard Frontend started (PID:", process.pid, ")")
            print("   🔥 Frontend already has native hot reload!")
            return True
        except Exception as e:
            print(f"❌ Failed to start Dashboard Frontend: {e}")
            return False
            
    def show_access_info(self):
        """Show access information"""
        print("\n🌐 Hot Reload Development Environment")
        print("=" * 50)
        print("📊 Main Dashboard:     http://localhost:5173")
        print("🔧 API Documentation:  http://localhost:8000/api/docs")
        print("💓 Health Check:       http://localhost:8000/health")
        print("🔌 WebSocket:          ws://localhost:8000/ws")
        print("=" * 50)
        print("\n🔥 Hot Reload Status:")
        print("   • 🤖 Trading Bot:    Jurigged (Python hot patching)")
        print("   • ⚙️  Backend API:    Jurigged + Uvicorn")
        print("   • 🎨 Frontend:       Vite HMR (native)")
        print("=" * 50)
        print("\n🧪 Development Tips:")
        print("   • Edit strategy files → Bot updates instantly")
        print("   • Modify API endpoints → Backend updates instantly")
        print("   • Change React components → Frontend updates instantly")
        print("   • All state is preserved during updates!")
        print("\n⌨️  Press Ctrl+C to stop all services")
        
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(sig, frame):
            print("\n\n🛑 Shutdown signal received...")
            self.stop_all_processes()
            sys.exit(0)
            
        signal.signal(signal.SIGINT, signal_handler)
        if hasattr(signal, 'SIGTERM'):
            signal.signal(signal.SIGTERM, signal_handler)
            
    def stop_all_processes(self):
        """Stop all running processes"""
        print("🔄 Stopping all hot reload services...")
        
        for name, process in self.processes:
            try:
                print(f"   • Stopping {name}...")
                process.terminate()
                process.wait(timeout=5)
                print(f"   ✅ {name} stopped")
            except subprocess.TimeoutExpired:
                print(f"   ⚠️ Force killing {name}...")
                process.kill()
            except Exception as e:
                print(f"   ❌ Error stopping {name}: {e}")
                
        print("✅ All services stopped")
        
    def wait_for_processes(self):
        """Wait for all processes and monitor them"""
        try:
            while True:
                # Check if any process has died
                for name, process in self.processes[:]:
                    if process.poll() is not None:
                        print(f"\n⚠️ {name} has stopped unexpectedly!")
                        self.processes.remove((name, process))
                        
                if not self.processes:
                    print("❌ All processes have stopped. Exiting...")
                    break
                    
                time.sleep(1)
                
        except KeyboardInterrupt:
            pass
            
    def run(self):
        """Main execution method"""
        self.print_banner()
        
        if not self.check_prerequisites():
            print("❌ Prerequisites check failed. Exiting...")
            return False
            
        self.setup_signal_handlers()
        
        # Start services in sequence with delays
        success = True
        success &= self.start_trading_bot_hotreload()
        time.sleep(3)
        
        success &= self.start_dashboard_backend_hotreload()
        time.sleep(3)
        
        success &= self.start_dashboard_frontend()
        
        if not success:
            print("❌ Failed to start all services")
            self.stop_all_processes()
            return False
            
        self.show_access_info()
        self.wait_for_processes()
        
        return True

if __name__ == "__main__":
    launcher = HotReloadLauncher()
    try:
        launcher.run()
    except KeyboardInterrupt:
        print("\n⏹️ Hot reload development cancelled by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        launcher.stop_all_processes()
    finally:
        sys.exit(0) 