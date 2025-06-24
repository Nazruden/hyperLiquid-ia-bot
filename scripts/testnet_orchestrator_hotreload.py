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
import concurrent.futures
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

class TestnetOrchestrator:
    def __init__(self, hot_reload=True):
        self.root_dir = Path(__file__).parent.parent
        self.processes = {}
        self.running = True
        self.startup_complete = False
        self.hot_reload = hot_reload
        self.startup_time = time.time()
        
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
        
    def await_services_ready(self, services_to_check: List[Dict[str, Any]]) -> bool:
        """
        Performs health checks for multiple services concurrently.
        Returns True if all services are healthy, False otherwise.
        """
        self.log("📡 Performing concurrent health checks...")
        services_with_health_checks = [s for s in services_to_check if s.get("health_check_url")]
        
        if not services_with_health_checks:
            self.log("ℹ️ No services require a health check.", "INFO")
            return True

        with concurrent.futures.ThreadPoolExecutor(max_workers=len(services_with_health_checks)) as executor:
            future_to_service = {
                executor.submit(self.wait_for_service, service['name'], service['health_check_url'], service['max_wait']): service
                for service in services_with_health_checks
            }
            
            all_healthy = True
            for future in concurrent.futures.as_completed(future_to_service):
                service = future_to_service[future]
                try:
                    is_healthy = future.result()
                    if not is_healthy:
                        all_healthy = False
                        self.log(f"💔 Health check failed for {service['name']}", "ERROR")
                except Exception as exc:
                    all_healthy = False
                    self.log(f"💥 Health check for {service['name']} generated an exception: {exc}", "CRITICAL")
        
        return all_healthy

    def start_dashboard_backend(self) -> Optional[Dict[str, Any]]:
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
            return {
                "name": "Dashboard Backend",
                "process": process,
                "health_check_url": "http://localhost:8000/health",
                "max_wait": 45
            }
        return None
        
    def start_dashboard_frontend(self) -> Optional[Dict[str, Any]]:
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
                    return None
                
        # Start the frontend dev server
        frontend_cmd = ["npm", "run", "dev"]
        if sys.platform == "win32":
            frontend_cmd = ["npm.cmd", "run", "dev"]

        process = self.start_service("Dashboard Frontend", frontend_cmd, cwd=frontend_dir)
        
        if process:
            return {
                "name": "Dashboard Frontend",
                "process": process,
                "health_check_url": "http://localhost:5173",
                "max_wait": 15
            }
        return None
        
    def start_trading_bot(self) -> Optional[Dict[str, Any]]:
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
            return {
                "name": "Trading Bot",
                "process": process,
                "health_check_url": None
            }
        return None
        
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
            
        self.log("Main monitoring loop has ended. Shutting down remaining services...")
        self.shutdown_all_services()

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
        
        uptime = time.time() - self.startup_time
        self.log(f"🕒 Orchestrator uptime: {int(uptime)}s", "STATUS")
        self.log("="*60, "STATUS")

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
        self.running = False
        
    def run_deployment(self):
        """Launches all services concurrently and waits for them to be healthy."""
        self.log("🚀 Orchestrator starting parallel deployment...")
        launched_services = []

        # --- STEP 1: Launch all services concurrently ---
        self.log("STEP 1: Launching all services...")
        
        backend_service = self.start_dashboard_backend()
        if backend_service:
            launched_services.append(backend_service)
            
        frontend_service = self.start_dashboard_frontend()
        if frontend_service:
            launched_services.append(frontend_service)
            
        bot_service = self.start_trading_bot()
        if bot_service:
            launched_services.append(bot_service)
            
        # --- CRITICAL CHECK: Ensure essential services were launched ---
        essential_services = {"Dashboard Backend", "Trading Bot"}
        launched_names = {s['name'] for s in launched_services}
        if not essential_services.issubset(launched_names):
            self.log("❌ CRITICAL: Failed to launch one or more essential services. Shutting down.", "CRITICAL")
            self.running = False
            self.shutdown_all_services()
            return

        # --- STEP 2: Perform concurrent health checks ---
        self.log("STEP 2: Awaiting service health checks...")
        all_systems_go = self.await_services_ready(launched_services)
        
        if not all_systems_go:
            self.log("❌ One or more services failed the health check. Initiating shutdown.", "CRITICAL")
            self.running = False
            self.shutdown_all_services()
            return
            
        # --- STEP 3: Finalization ---
        self.log("✅ All services are up, running, and healthy.", "SUCCESS")
        self.startup_complete = True
        
        self.print_status_dashboard()
        
        # Start monitoring loop
        self.monitor_processes()


def main():
    """Main entry point for the orchestrator script."""
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