#!/usr/bin/env python3
"""
HyperLiquid AI Trading Bot - Dashboard Hot Reload Development Mode
Starts only the dashboard (backend + frontend) with hot reload for rapid UI development
"""

import subprocess
import sys
import time
import signal
import os
from pathlib import Path
import threading

class DashboardHotReloadLauncher:
    def __init__(self):
        self.processes = []
        self.root_dir = Path(__file__).parent.parent
        
    def print_banner(self):
        """Print startup banner"""
        print("🖥️ HyperLiquid Dashboard - HOT RELOAD Development Mode")
        print("=" * 60)
        print("🔥 Jurigged Hot Reload: ENABLED (Backend)")
        print("🔥 Vite HMR: ENABLED (Frontend)")
        print("📁 Project Directory:", self.root_dir)
        print("🐍 Python Executable:", sys.executable)
        print("⏰ Starting Time:", time.strftime("%Y-%m-%d %H:%M:%S"))
        print("=" * 60)
        print("💡 Benefits:")
        print("   • ⚡ Instant API updates without restart")
        print("   • 🔄 Preserves WebSocket connections")
        print("   • 🎨 Instant React component updates")
        print("   • 🧪 Perfect for dashboard development")
        print("=" * 60)
        
    def check_prerequisites(self):
        """Check if dashboard components exist"""
        print("🔍 Checking Dashboard Prerequisites...")
        
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
            
        print("✅ Dashboard prerequisites found")
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
        
    def start_dashboard_backend_hotreload(self):
        """Start FastAPI dashboard backend with jurigged hot reload"""
        print("\n⚙️ Starting Dashboard Backend with Hot Reload...")
        print("   • URL: http://localhost:8000")
        print("   • API Docs: http://localhost:8000/api/docs")
        print("   • WebSocket: ws://localhost:8000/ws")
        print("   • Hot Reload: ENABLED")
        
        try:
            # Use jurigged for the dashboard backend with comprehensive watching
            cmd = [
                sys.executable, "-m", "jurigged",
                "-v",  # Verbose mode to see reloads
                "-w", "dashboard/backend/",      # Watch backend directory
                "-w", "dashboard/backend/routers/",    # Watch routers
                "-w", "dashboard/backend/controllers/", # Watch controllers
                "-w", "dashboard/backend/services/",    # Watch services
                "-d", "1",  # 1 second debounce
                "-m", "uvicorn",  # Run uvicorn as module
                "dashboard.backend.app:app",
                "--host", "127.0.0.1",
                "--port", "8000",
                "--reload"  # Keep uvicorn's reload as backup
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
            print("   🔥 API endpoints will update instantly!")
            print("   🔥 WebSocket handlers will update instantly!")
            print("   🔥 Controllers and services will update instantly!")
            return True
        except Exception as e:
            print(f"❌ Failed to start Dashboard Backend: {e}")
            return False
            
    def start_dashboard_frontend(self):
        """Start React frontend development server with native hot reload"""
        print("\n🎨 Starting Dashboard Frontend with Hot Reload...")
        print("   • URL: http://localhost:5173")
        print("   • Hot Reload: Native Vite HMR")
        print("   • WebSocket to Backend: ws://localhost:8000/ws")
        
        frontend_dir = self.root_dir / "dashboard" / "frontend"
        
        try:
            # Check if node_modules exists, install if not
            if not (frontend_dir / "node_modules").exists():
                print("📦 Installing frontend dependencies...")
                subprocess.run(["npm", "install"], cwd=frontend_dir, check=True)
                
            # Start Vite dev server with hot reload
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
            
            self.processes.append(("Dashboard Frontend (HMR)", process))
            print("✅ Dashboard Frontend started (PID:", process.pid, ")")
            print("   🔥 React components will update instantly!")
            print("   🔥 CSS/Tailwind changes will update instantly!")
            print("   🔥 TypeScript changes will update instantly!")
            return True
        except Exception as e:
            print(f"❌ Failed to start Dashboard Frontend: {e}")
            return False
            
    def show_access_info(self):
        """Show access information"""
        print("\n🌐 Dashboard Hot Reload Development Environment")
        print("=" * 55)
        print("📊 Main Dashboard:     http://localhost:5173")
        print("🔧 API Documentation:  http://localhost:8000/api/docs")
        print("💓 Health Check:       http://localhost:8000/health")
        print("🔌 WebSocket:          ws://localhost:8000/ws")
        print("=" * 55)
        print("\n🔥 Hot Reload Status:")
        print("   • ⚙️  Backend API:    Jurigged (Python hot patching)")
        print("   • 🎨 Frontend:       Vite HMR (React/TypeScript)")
        print("=" * 55)
        print("\n🧪 Development Tips:")
        print("   • Edit API routes → Backend updates instantly")
        print("   • Modify WebSocket handlers → Updates instantly")
        print("   • Change React components → Frontend updates instantly")
        print("   • Update CSS/Tailwind → Styles update instantly")
        print("   • All WebSocket connections are preserved!")
        print("=" * 55)
        print("\n⚠️  Note: Dashboard running in standalone mode")
        print("   Trading bot data will only show if bot is running separately")
        print("   Use 'python scripts/start_all_hotreload.py' for full system")
        print("\n⌨️  Press Ctrl+C to stop dashboard services")
        
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
        print("🔄 Stopping dashboard hot reload services...")
        
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
                
        print("✅ Dashboard services stopped")
        
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
                    print("❌ All dashboard services have stopped. Exiting...")
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
        
        # Start dashboard services with hot reload
        success = True
        success &= self.start_dashboard_backend_hotreload()
        time.sleep(3)
        
        success &= self.start_dashboard_frontend()
        
        if not success:
            print("❌ Failed to start dashboard services")
            self.stop_all_processes()
            return False
            
        self.show_access_info()
        self.wait_for_processes()
        
        return True

if __name__ == "__main__":
    launcher = DashboardHotReloadLauncher()
    try:
        launcher.run()
    except KeyboardInterrupt:
        print("\n⏹️ Dashboard hot reload development cancelled by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        launcher.stop_all_processes()
    finally:
        sys.exit(0) 