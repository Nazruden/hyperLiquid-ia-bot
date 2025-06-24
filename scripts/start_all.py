#!/usr/bin/env python3
"""
HyperLiquid AI Trading Bot - Complete System Startup
Starts trading bot + dashboard backend + frontend in parallel
"""

import subprocess
import sys
import time
import threading
import signal
import os
from pathlib import Path

class SystemLauncher:
    def __init__(self):
        self.processes = []
        self.root_dir = Path(__file__).parent.parent
        
    def print_banner(self):
        """Print startup banner"""
        print("🚀 HyperLiquid AI Trading Bot - Complete System Launcher")
        print("=" * 65)
        print("📁 Project Directory:", self.root_dir)
        print("🐍 Python Executable:", sys.executable)
        print("⏰ Starting Time:", time.strftime("%Y-%m-%d %H:%M:%S"))
        print("=" * 65)
        
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
            
        # Check dashboard frontend
        if not (self.root_dir / "dashboard" / "frontend" / "package.json").exists():
            print("❌ Dashboard frontend not found!")
            return False
            
        # Check if npm is available
        try:
            subprocess.run(["npm", "--version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("❌ npm not found! Please install Node.js")
            return False
            
        print("✅ All prerequisites found")
        return True
        
    def start_trading_bot(self):
        """Start the main trading bot"""
        print("\n🤖 Starting Trading Bot...")
        print("   • Command: python main.py")
        print("   • Working Dir:", self.root_dir)
        
        try:
            # Redirect stdout and stderr and set encoding to utf-8 to prevent UnicodeEncodeError
            process = subprocess.Popen(
                [sys.executable, "-u", "main.py"], # -u for unbuffered output
                cwd=self.root_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='replace' # Replace characters that can't be decoded
            )

            # Start threads to read stdout and stderr in a non-blocking way
            self._start_stream_reader(process.stdout, "Bot-out")
            self._start_stream_reader(process.stderr, "Bot-err")

            self.processes.append(("Trading Bot", process))
            print("✅ Trading Bot started (PID:", process.pid, ")")
            return True
        except Exception as e:
            print(f"❌ Failed to start Trading Bot: {e}")
            return False
            
    def _start_stream_reader(self, stream, prefix):
        """Starts a thread to read and print from a stream."""
        def reader_thread():
            for line in iter(stream.readline, ''):
                print(f"[{prefix}] {line}", end='')
            stream.close()
        
        thread = threading.Thread(target=reader_thread)
        thread.daemon = True
        thread.start()
            
    def start_dashboard_backend(self):
        """Start FastAPI dashboard backend"""
        print("\n⚙️ Starting Dashboard Backend...")
        print("   • URL: http://localhost:8000")
        print("   • API Docs: http://localhost:8000/api/docs")
        print("   • WebSocket: ws://localhost:8000/ws")
        
        try:
            process = subprocess.Popen([
                sys.executable, "-m", "uvicorn", 
                "dashboard.backend.app:app",
                "--host", "127.0.0.1", 
                "--port", "8000", 
                "--reload"
            ], cwd=self.root_dir)
            
            self.processes.append(("Dashboard Backend", process))
            print("✅ Dashboard Backend started (PID:", process.pid, ")")
            return True
        except Exception as e:
            print(f"❌ Failed to start Dashboard Backend: {e}")
            return False
            
    def start_dashboard_frontend(self):
        """Start React frontend development server"""
        print("\n🎨 Starting Dashboard Frontend...")
        print("   • URL: http://localhost:5173")
        print("   • Hot Reload: Enabled")
        
        frontend_dir = self.root_dir / "dashboard" / "frontend"
        
        try:
            # Check if node_modules exists, install if not
            if not (frontend_dir / "node_modules").exists():
                print("📦 Installing frontend dependencies...")
                subprocess.run(["npm", "install"], cwd=frontend_dir, check=True)
                
            process = subprocess.Popen(
                ["npm", "run", "dev"],
                cwd=frontend_dir
            )
            
            self.processes.append(("Dashboard Frontend", process))
            print("✅ Dashboard Frontend started (PID:", process.pid, ")")
            return True
        except Exception as e:
            print(f"❌ Failed to start Dashboard Frontend: {e}")
            return False
            
    def show_access_info(self):
        """Show access information"""
        print("\n🌐 Access Information")
        print("=" * 40)
        print("📊 Main Dashboard:     http://localhost:5173")
        print("🔧 API Documentation:  http://localhost:8000/api/docs")
        print("💓 Health Check:       http://localhost:8000/health")
        print("🔌 WebSocket:          ws://localhost:8000/ws")
        print("=" * 40)
        print("\n⌨️  Press Ctrl+C to stop all services")
        print("🔄 Services will auto-reload on code changes")
        
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
        print("🔄 Stopping all services...")
        
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
        success &= self.start_trading_bot()
        time.sleep(2)
        
        success &= self.start_dashboard_backend()
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
    launcher = SystemLauncher()
    try:
        launcher.run()
    except KeyboardInterrupt:
        print("\n⏹️ Startup cancelled by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        launcher.stop_all_processes()
    finally:
        sys.exit(0) 