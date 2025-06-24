#!/usr/bin/env python3
"""
HyperLiquid AI Trading Bot - TESTNET Orchestrator with Hot Reload
Complete deployment orchestration with hot reload for ultra-fast development
"""

import os
import sys
import time
import signal
import subprocess
import threading
import requests
from pathlib import Path
from datetime import datetime

class TestnetOrchestrator:
    def __init__(self, hot_reload=True):
        self.root_dir = Path(__file__).parent.parent
        self.processes = {}
        self.running = True
        self.startup_complete = False
        self.hot_reload = hot_reload
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
    def log(self, message, level="INFO"):
        """Enhanced logging with timestamps"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        mode_indicator = "🔥" if self.hot_reload else "🔄"
        print(f"[{timestamp}] {mode_indicator} {level}: {message}")
        
    def signal_handler(self, signum, frame):
        """Handle Ctrl+C and graceful shutdown by setting a flag."""
        if self.running:
            self.log("🛑 Shutdown signal received, initiating graceful shutdown...", "WARNING")
            self.running = False
        # Do not call shutdown_all_services() here, let the main loop handle it.
        
    def _start_stream_reader(self, stream, prefix):
        """Starts a thread to read and print from a stream."""
        def reader_thread():
            # Use self.log for consistent output formatting
            for line in iter(stream.readline, ''):
                self.log(f"[{prefix}] {line.strip()}", "PROCESS")
            stream.close()
        
        thread = threading.Thread(target=reader_thread)
        thread.daemon = True
        thread.start()
        
    def start_service(self, name, command, cwd=None, env_vars=None):
        """Start a service securely and robustly, capturing its output."""
        self.log(f"🚀 Starting {name}...")
        
        # Prepare environment
        env = os.environ.copy()
        if env_vars:
            env.update(env_vars)

        # Force Python to use UTF-8 for its standard streams
        if sys.platform == "win32" and "python" in command[0]:
            env['PYTHONIOENCODING'] = 'utf-8'
            
        try:
            # Consistent, secure, and robust process startup for all services
            process = subprocess.Popen(
                command,
                cwd=cwd or self.root_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='replace',
                env=env
            )

            # Start stream readers for long-running services to capture output
            if name in ["Trading Bot", "Dashboard Backend", "Dashboard Frontend"]:
                self._start_stream_reader(process.stdout, f"{name}-out")
                self._start_stream_reader(process.stderr, f"{name}-err")
            
            self.processes[name] = process
            self.log(f"✅ {name} started (PID: {process.pid})")
            return process
            
        except Exception as e:
            self.log(f"❌ Failed to start {name}: {e}", "ERROR")
            return None
            
    def check_service_health(self, name, url, timeout=5):
        """Check if a service is healthy"""
        try:
            response = requests.get(url, timeout=timeout)
            if response.status_code == 200:
                self.log(f"✅ {name} is healthy")
                return True
            else:
                self.log(f"⚠️ {name} responded with status {response.status_code}", "WARNING")
                return False
        except requests.RequestException as e:
            self.log(f"❌ {name} health check failed: {e}", "ERROR")
            return False
            
    def wait_for_service(self, name, url, max_wait=30):
        """Wait for a service to become available"""
        self.log(f"⏳ Waiting for {name} to be ready...")
        
        for attempt in range(max_wait):
            if self.check_service_health(name, url):
                return True
            time.sleep(1)
            
        self.log(f"❌ {name} failed to become ready within {max_wait}s", "ERROR")
        return False
        
    def start_dashboard_backend(self):
        """Start the dashboard backend with optional hot reload"""
        if self.hot_reload:
            # Check if jurigged is available
            try:
                subprocess.run([sys.executable, "-m", "jurigged", "--version"], 
                             capture_output=True, check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                self.log("⚡ Installing jurigged for hot reload...")
                try:
                    subprocess.run([sys.executable, "-m", "pip", "install", "jurigged"], 
                                 check=True, capture_output=True)
                    self.log("✅ jurigged installed successfully")
                except subprocess.CalledProcessError:
                    self.log("❌ Failed to install jurigged. Falling back to standard mode...", "WARNING")
                    self.hot_reload = False
            
            # Use jurigged for hot patching
            backend_cmd = [
                sys.executable, "-m", "jurigged",
                "-v",  # Verbose mode
                "-w", "dashboard/backend/",      # Watch backend directory
                "-w", "dashboard/backend/routers/",    # Watch routers
                "-w", "dashboard/backend/controllers/", # Watch controllers
                "-w", "dashboard/backend/services/",    # Watch services
                "-d", "0.5",  # Fast debounce
                "-m", "uvicorn",  # Run uvicorn as module
                "dashboard.backend.app:app",
                "--host", "127.0.0.1",
                "--port", "8000",
                "--reload",  # Keep uvicorn's reload as backup
                "--log-level", "info"
            ]
        else:
            # Use uvicorn directly for better control
            backend_cmd = [
                sys.executable, "-m", "uvicorn",
                "dashboard.backend.app:app",
                "--host", "127.0.0.1",
                "--port", "8000",
                "--reload",
                "--log-level", "info"
            ]
        process = self.start_service("Dashboard Backend", backend_cmd)
        
        if process:
            # Give more time for backend to start
            time.sleep(5)
            # Wait for backend to be ready with longer timeout
            if self.wait_for_service("Dashboard Backend", "http://localhost:8000/health", max_wait=45):
                self.log("🎯 Dashboard Backend ready at http://localhost:8000")
                return True
            else:
                self.log("❌ Dashboard Backend failed to start properly", "ERROR")
                return False
        return False
        
    def start_dashboard_frontend(self):
        """Start the dashboard frontend"""
        frontend_dir = self.root_dir / "dashboard" / "frontend"
        
        # Check if node_modules exists
        if not (frontend_dir / "node_modules").exists():
            self.log("📦 Installing frontend dependencies...")
            npm_install = self.start_service(
                "NPM Install", 
                ["npm", "install"],
                cwd=frontend_dir
            )
            if npm_install:
                exit_code = npm_install.wait()  # Wait for installation to complete
                if exit_code != 0:
                    self.log(f"❌ NPM Install failed with exit code {exit_code}", "ERROR")
                    return False
                
        # Start the frontend dev server
        frontend_cmd = ["npm", "run", "dev"]
        if sys.platform == "win32":
            frontend_cmd = ["npm.cmd", "run", "dev"]

        process = self.start_service("Dashboard Frontend", frontend_cmd, cwd=frontend_dir)
        
        if process:
            # Wait for frontend to be ready
            time.sleep(3)  # Give Vite some time to start
            if self.wait_for_service("Dashboard Frontend", "http://localhost:5173", max_wait=15):
                self.log("🎯 Dashboard Frontend ready at http://localhost:5173")
                return True
            else:
                self.log("⚠️ Frontend may still be starting...", "WARNING")
                return True  # Don't fail deployment for frontend issues
        return False
        
    def start_trading_bot(self):
        """Start the main trading bot with optional hot reload"""
        if self.hot_reload:
            # Start with jurigged, watching all relevant directories
            # The -u flag must come after python and before -m
            bot_cmd = [
                sys.executable, "-u", "-m", "jurigged", 
                "-v",  # Verbose mode to see what's being reloaded
                "-w", "strategy/",      # Watch strategy directory
                "-w", "allora/",        # Watch allora directory
                "-w", "core/",          # Watch core directory
                "-w", "database/",      # Watch database directory
                "-w", "analysis/",      # Watch analysis directory
                "-w", "utils/",         # Watch utils directory
                "-d", "0.5",            # Fast debounce
                "main.py"
            ]
        else:
            bot_cmd = [sys.executable, "-u", "main.py"] # Unbuffered output
            
        process = self.start_service("Trading Bot", bot_cmd)
        
        if process:
            reload_info = " with Hot Reload" if self.hot_reload else ""
            self.log(f"🤖 Trading Bot started{reload_info} and monitoring markets")
            return True
        return False
        
    def monitor_processes(self):
        """Monitor all processes and handle termination"""
        while self.running:
            for name, process in list(self.processes.items()):
                if process.poll() is not None:  # Process has terminated
                    exit_code = process.returncode
                    self.log(f"ℹ️ {name} has stopped with exit code: {exit_code}", "WARNING")
                    
                    # Log any remaining output from the process streams
                    # This is now handled by the continuously running reader threads
                    
                    # Remove from processes list. The user can decide to restart the orchestrator.
                    del self.processes[name]
                        
            time.sleep(5)  # Check every 5 seconds
            
    def print_status_dashboard(self):
        """Print current status and URLs"""
        mode_info = "🔥 HOT RELOAD" if self.hot_reload else "STANDARD"
        print("\n" + "=" * 65)
        print(f"🚀 HYPERLIQUID AI TRADING BOT - TESTNET ACTIVE ({mode_info})")
        print("=" * 65)
        print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🔧 Mode: TESTNET")
        print(f"🔥 Hot Reload: {'✅ ENABLED' if self.hot_reload else '❌ DISABLED'}")
        print(f"🤖 Bot Status: {'✅ Running' if 'Trading Bot' in self.processes else '❌ Stopped'}")
        print(f"📊 Dashboard: {'✅ Ready' if 'Dashboard Backend' in self.processes else '❌ Stopped'}")
        print(f"🖥️ Frontend: {'✅ Ready' if 'Dashboard Frontend' in self.processes else '❌ Stopped'}")
        print("\n🔗 ACCESS URLS:")
        print("   📊 Dashboard: http://localhost:5173")
        print("   🔧 API:       http://localhost:8000/api/docs")
        print("   💓 Health:    http://localhost:8000/health")
        print("   🔌 WebSocket: ws://localhost:8000/ws")
        
        if self.hot_reload:
            print("\n🔥 HOT RELOAD ACTIVE:")
            print("   • 🤖 Bot:        Strategy files update instantly")
            print("   • ⚙️  Backend:    API endpoints update instantly")  
            print("   • 🎨 Frontend:   React components update instantly")
            print("   • 🚀 Development: 10x faster iteration!")
        
        print("\n📁 LOGS:")
        print("   🤖 Bot:       Console output")
        print("   📊 Dashboard: Console output")
        print("   📈 Trading:   trades.db")
        print("\n💡 DEVELOPMENT TIPS:")
        if self.hot_reload:
            print("   • Edit strategy files → Bot updates instantly")
            print("   • Modify API endpoints → Backend updates instantly")
            print("   • Change React components → Frontend updates instantly")
            print("   • All state is preserved during updates!")
        print("   • Monitor for at least 1 hour before leaving unattended")
        print("   • Check dashboard for live trading activity")
        print("   • Press Ctrl+C to shutdown gracefully")
        print("=" * 65)
        
    def shutdown_all_services(self):
        """Gracefully shutdown all services"""
        if not self.processes:
            return
            
        self.log("🛑 Initiating graceful shutdown...")
        
        # Stop processes in reverse order (bot first, then dashboard)
        shutdown_order = ["Trading Bot", "Dashboard Frontend", "Dashboard Backend"]
        
        for name in shutdown_order:
            if name in self.processes:
                process = self.processes[name]
                self.log(f"🛑 Stopping {name}...")
                
                try:
                    # Try graceful shutdown first
                    process.terminate()
                    
                    # Wait up to 5 seconds for graceful shutdown
                    try:
                        process.wait(timeout=5)
                        self.log(f"✅ {name} stopped gracefully")
                    except subprocess.TimeoutExpired:
                        # Force kill if necessary
                        self.log(f"⚡ Force killing {name}...")
                        process.kill()
                        process.wait()
                        self.log(f"✅ {name} force stopped")
                        
                except Exception as e:
                    self.log(f"⚠️ Error stopping {name}: {e}", "WARNING")
                    
        self.log("✅ All services stopped")
        
    def run_deployment(self):
        """Run complete testnet deployment"""
        self.log("🚀 Starting HyperLiquid AI Trading Bot - TESTNET Deployment")
        self.log("=" * 60)
        
        # Step 1: Start Dashboard Backend
        if not self.start_dashboard_backend():
            self.log("❌ Critical: Dashboard Backend failed to start", "ERROR")
            return False
            
        # Step 2: Start Dashboard Frontend
        if not self.start_dashboard_frontend():
            self.log("⚠️ Frontend startup issues - continuing anyway", "WARNING")
            
        # Step 3: Start Trading Bot
        if not self.start_trading_bot():
            self.log("❌ Critical: Trading Bot failed to start", "ERROR")
            return False
            
        # Mark startup as complete
        self.startup_complete = True
        
        # Show status dashboard
        self.print_status_dashboard()
        
        # Start monitoring thread
        monitor_thread = threading.Thread(target=self.monitor_processes, daemon=True)
        monitor_thread.start()
        
        # Main loop - keep running until shutdown
        self.log("✅ All services started - Bot is now active!")
        self.log("📊 Monitor dashboard: http://localhost:8000")
        self.log("🛑 Press Ctrl+C to shutdown gracefully")
        
        try:
            # Status updates every 30 seconds
            last_status = time.time()
            
            while self.running:
                current_time = time.time()
                
                # Print status update every 30 seconds
                if current_time - last_status > 30:
                    active_processes = len([p for p in self.processes.values() if p.poll() is None])
                    self.log(f"📊 Status: {active_processes}/{len(self.processes)} services running")
                    last_status = current_time
                    
                time.sleep(1)
                
        except KeyboardInterrupt:
            self.log("🛑 Keyboard interrupt received", "WARNING")
            
        return True


def main():
    """Main function to run the orchestrator with argument parsing"""
    import argparse
    parser = argparse.ArgumentParser(
        description="HyperLiquid AI Trading Bot - Testnet Orchestrator with Hot Reload",
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    parser.add_argument(
        '--no-hot-reload',
        action='store_true',
        help="Run without hot reloading features (standard mode)."
    )
    
    args = parser.parse_args()
    
    # Hot reload is on by default, turned off by the flag
    hot_reload_enabled = not args.no_hot_reload
    
    orchestrator = TestnetOrchestrator(hot_reload=hot_reload_enabled)
    try:
        orchestrator.run_deployment()
    except KeyboardInterrupt:
        print() # Newline after Ctrl+C
        orchestrator.log("Deployment cancelled by user.", "INFO")
    except Exception as e:
        orchestrator.log(f"An unexpected error occurred: {e}", "CRITICAL")
    finally:
        orchestrator.shutdown_all_services()
        orchestrator.log("Orchestrator has shut down.", "INFO")
        sys.exit(1)


if __name__ == "__main__":
    main() 