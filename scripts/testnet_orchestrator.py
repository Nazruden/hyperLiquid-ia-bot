#!/usr/bin/env python3
"""
HyperLiquid AI Trading Bot - TESTNET Orchestrator
Complete deployment orchestration with graceful shutdown
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
    def __init__(self):
        self.root_dir = Path(__file__).parent.parent
        self.processes = {}
        self.running = True
        self.startup_complete = False
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
    def log(self, message, level="INFO"):
        """Enhanced logging with timestamps"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def signal_handler(self, signum, frame):
        """Handle Ctrl+C and graceful shutdown"""
        self.log("🛑 Shutdown signal received", "WARNING")
        self.running = False
        self.shutdown_all_services()
        sys.exit(0)
        
    def start_service(self, name, command, cwd=None, env_vars=None):
        """Start a service and monitor it"""
        self.log(f"🚀 Starting {name}...")
        
        # Prepare environment
        env = os.environ.copy()
        if env_vars:
            env.update(env_vars)
            
        try:
            process = subprocess.Popen(
                command,
                cwd=cwd or self.root_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
                shell=True if isinstance(command, str) else False
            )
            
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
        """Start the dashboard backend"""
        # Use uvicorn directly for better control
        backend_cmd = [
            sys.executable, "-m", "uvicorn",
            "dashboard.backend.app:app",
            "--host", "127.0.0.1",
            "--port", "8000",
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
                "npm install", 
                cwd=frontend_dir
            )
            if npm_install:
                npm_install.wait()  # Wait for installation to complete
                
        # Start the frontend dev server
        frontend_cmd = "npm run dev"
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
        """Start the main trading bot"""
        bot_cmd = [sys.executable, "main.py"]
        process = self.start_service("Trading Bot", bot_cmd)
        
        if process:
            self.log("🤖 Trading Bot started and monitoring markets")
            return True
        return False
        
    def monitor_processes(self):
        """Monitor all processes and restart if needed"""
        while self.running:
            for name, process in list(self.processes.items()):
                if process.poll() is not None:  # Process has terminated
                    self.log(f"⚠️ {name} has stopped unexpectedly", "WARNING")
                    
                    # Try to restart critical services
                    if name == "Trading Bot":
                        self.log("🔄 Restarting Trading Bot...")
                        self.start_trading_bot()
                    elif name == "Dashboard Backend":
                        self.log("🔄 Restarting Dashboard Backend...")
                        self.start_dashboard_backend()
                        
            time.sleep(5)  # Check every 5 seconds
            
    def print_status_dashboard(self):
        """Print current status and URLs"""
        print("\n" + "=" * 60)
        print("🚀 HYPERLIQUID AI TRADING BOT - TESTNET ACTIVE")
        print("=" * 60)
        print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🔧 Mode: TESTNET")
        print(f"🤖 Bot Status: {'✅ Running' if 'Trading Bot' in self.processes else '❌ Stopped'}")
        print(f"📊 Dashboard: {'✅ Ready' if 'Dashboard Backend' in self.processes else '❌ Stopped'}")
        print(f"🖥️ Frontend: {'✅ Ready' if 'Dashboard Frontend' in self.processes else '❌ Stopped'}")
        print("\n🔗 ACCESS URLS:")
        print("   📊 Dashboard: http://localhost:8000")
        print("   🖥️ Frontend:  http://localhost:5173")
        print("   📡 API:       http://localhost:8000/api")
        print("   📈 Metrics:   http://localhost:8000/metrics")
        print("\n📁 LOGS:")
        print("   🤖 Bot:       logs/testnet_bot.log")
        print("   📊 Dashboard: logs/dashboard.log")
        print("   📈 Trading:   trades.db")
        print("\n⚠️ IMPORTANT:")
        print("   • Monitor for at least 1 hour before leaving unattended")
        print("   • Check dashboard for live trading activity")
        print("   • Validate AI predictions are working correctly")
        print("   • Press Ctrl+C to shutdown gracefully")
        print("=" * 60)
        
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
    """Main orchestrator function"""
    print("🚀 HyperLiquid AI Trading Bot - TESTNET Orchestrator")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not Path("main.py").exists():
        print("❌ Error: Please run from the project root directory")
        sys.exit(1)
        
    # Check if .env exists
    if not Path(".env").exists():
        print("❌ Error: .env file not found. Run deploy_testnet.py first.")
        sys.exit(1)
        
    orchestrator = TestnetOrchestrator()
    
    try:
        success = orchestrator.run_deployment()
        if success:
            print("\n✅ Testnet deployment completed successfully")
        else:
            print("\n❌ Testnet deployment failed")
            sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        orchestrator.shutdown_all_services()
        sys.exit(1)
    finally:
        orchestrator.shutdown_all_services()


if __name__ == "__main__":
    main() 