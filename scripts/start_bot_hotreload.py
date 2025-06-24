#!/usr/bin/env python3
"""
HyperLiquid AI Trading Bot - Bot Only Hot Reload Development Mode
Starts only the trading bot with jurigged hot reload for strategy development
"""

import subprocess
import sys
import time
import signal
import os
from pathlib import Path
import threading

class BotHotReloadLauncher:
    def __init__(self):
        self.process = None
        self.root_dir = Path(__file__).parent.parent
        
    def print_banner(self):
        """Print startup banner"""
        print("🤖 HyperLiquid AI Trading Bot - HOT RELOAD Development Mode")
        print("=" * 65)
        print("🔥 Jurigged Hot Reload: ENABLED")
        print("📁 Project Directory:", self.root_dir)
        print("🐍 Python Executable:", sys.executable)
        print("⏰ Starting Time:", time.strftime("%Y-%m-%d %H:%M:%S"))
        print("=" * 65)
        print("💡 Benefits:")
        print("   • ⚡ Instant strategy updates without restart")
        print("   • 🔄 Preserves bot state and trading positions")
        print("   • 🧪 Perfect for strategy development and debugging")
        print("   • 📊 Allora predictions and state preserved")
        print("=" * 65)
        
    def check_prerequisites(self):
        """Check if all required files exist"""
        print("🔍 Checking Prerequisites...")
        
        # Check main bot file
        if not (self.root_dir / "main.py").exists():
            print("❌ main.py not found!")
            return False
            
        # Check key directories
        required_dirs = ["strategy", "allora", "core", "database"]
        for dir_name in required_dirs:
            if not (self.root_dir / dir_name).exists():
                print(f"❌ {dir_name}/ directory not found!")
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
        """Start the main trading bot with comprehensive hot reload"""
        print("\n🤖 Starting Trading Bot with Hot Reload...")
        print("   • Command: python -m jurigged -v main.py")
        print("   • Hot Reload: ENABLED")
        print("   • Watch directories: ALL project directories")
        print("   • Working Dir:", self.root_dir)
        
        try:
            # Start with jurigged, watching all relevant directories
            cmd = [
                sys.executable, "-m", "jurigged", 
                "-v",  # Verbose mode to see what's being reloaded
                "-w", "strategy/",      # Watch strategy directory
                "-w", "allora/",        # Watch allora directory
                "-w", "core/",          # Watch core directory
                "-w", "database/",      # Watch database directory
                "-w", "analysis/",      # Watch analysis directory
                "-w", "utils/",         # Watch utils directory
                "-d", "1",              # 1 second debounce
                "main.py"
            ]
            
            self.process = subprocess.Popen(
                cmd,
                cwd=self.root_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            self._start_stream_reader(self.process.stdout, "Bot-HotReload-out")
            self._start_stream_reader(self.process.stderr, "Bot-HotReload-err")
            
            print("✅ Trading Bot with Hot Reload started (PID:", self.process.pid, ")")
            print("   🔥 Code changes will be applied instantly!")
            print("   📊 Dashboard available at: http://localhost:4000")
            return True
        except Exception as e:
            print(f"❌ Failed to start Trading Bot: {e}")
            return False
            
    def show_access_info(self):
        """Show access information"""
        print("\n🤖 Trading Bot Hot Reload Development Environment")
        print("=" * 55)
        print("📊 Dashboard:          http://localhost:4000")
        print("🔌 WebSocket:          ws://localhost:8000/ws (if dashboard running)")
        print("🗄️ Database:           trades.db")
        print("📝 Logs:               logs/ directory")
        print("=" * 55)
        print("\n🔥 Hot Reload Active For:")
        print("   • 📈 Strategy files    → Updates instantly")
        print("   • 🤖 Allora mind       → Updates instantly")
        print("   • ⚙️  Core modules      → Updates instantly")
        print("   • 🗄️ Database modules  → Updates instantly")
        print("   • 📊 Analysis modules  → Updates instantly")
        print("   • 🛠️ Utility modules   → Updates instantly")
        print("=" * 55)
        print("\n🧪 Development Tips:")
        print("   • Edit volatility_strategy.py → Bot uses new strategy instantly")
        print("   • Modify adaptive_thresholds.py → New thresholds applied instantly")
        print("   • Update allora_mind.py → Prediction logic updated instantly")
        print("   • Change custom_strategy.py → Trading logic updated instantly")
        print("   • All trading state and positions are preserved!")
        print("=" * 55)
        print("\n⚠️  Note: Bot running in standalone mode")
        print("   Start dashboard separately for full UI experience")
        print("   Use 'python scripts/start_all_hotreload.py' for complete system")
        print("\n⌨️  Press Ctrl+C to stop the bot")
        
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(sig, frame):
            print("\n\n🛑 Shutdown signal received...")
            self.stop_bot()
            sys.exit(0)
            
        signal.signal(signal.SIGINT, signal_handler)
        if hasattr(signal, 'SIGTERM'):
            signal.signal(signal.SIGTERM, signal_handler)
            
    def stop_bot(self):
        """Stop the trading bot"""
        if self.process:
            print("🔄 Stopping trading bot...")
            try:
                self.process.terminate()
                self.process.wait(timeout=10)
                print("   ✅ Trading bot stopped gracefully")
            except subprocess.TimeoutExpired:
                print("   ⚠️ Force killing trading bot...")
                self.process.kill()
            except Exception as e:
                print(f"   ❌ Error stopping trading bot: {e}")
                
    def wait_for_process(self):
        """Wait for the bot process and monitor it"""
        try:
            while True:
                if self.process and self.process.poll() is not None:
                    print(f"\n⚠️ Trading bot has stopped unexpectedly!")
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
        
        # Start the bot
        if not self.start_trading_bot_hotreload():
            print("❌ Failed to start trading bot")
            return False
            
        self.show_access_info()
        self.wait_for_process()
        
        return True

if __name__ == "__main__":
    launcher = BotHotReloadLauncher()
    try:
        launcher.run()
    except KeyboardInterrupt:
        print("\n⏹️ Trading bot hot reload development cancelled by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        launcher.stop_bot()
    finally:
        sys.exit(0) 