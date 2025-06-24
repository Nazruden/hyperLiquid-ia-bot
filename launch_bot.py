#!/usr/bin/env python3
"""
🚀 HyperLiquid Bot Launcher
===========================
Flexible bot launcher with configurable parameters

Usage:
  python launch_bot.py --env testnet --duration 60 --cryptos BTC,ETH,SOL --auto-monitor
  python launch_bot.py --env mainnet --duration 300 --cryptos BTC --no-auto-monitor
  python launch_bot.py  # Use defaults
"""
import argparse
import os
import sys
import time
import sqlite3
import json
from datetime import datetime
from typing import List, Optional

def setup_environment(env: str, db_path: str):
    """Setup environment variables for specified environment"""
    print(f"🌐 Setting up {env.upper()} environment")
    
    if env == "testnet":
        os.environ['MAINNET'] = 'False'
        os.environ['DB_PATH'] = db_path or 'testnet_trades.db'
        print(f"   • Mode: TESTNET")
        print(f"   • Database: {os.environ['DB_PATH']}")
    elif env == "mainnet":
        os.environ['MAINNET'] = 'True'
        os.environ['DB_PATH'] = db_path or 'trading_logs.db'
        print(f"   • Mode: MAINNET")
        print(f"   • Database: {os.environ['DB_PATH']}")
        print(f"   ⚠️  WARNING: REAL MONEY TRADING!")
    
    return os.environ['DB_PATH']

def initialize_database(db_path: str, cryptos: List[str]):
    """Initialize database with crypto configurations"""
    print(f"\n🗄️ Initializing database: {db_path}")
    
    # Topic ID mapping (can be extended)
    topic_mapping = {
        'BTC': 1,
        'ETH': 2, 
        'SOL': 3,
        'AVAX': 4,
        'DOGE': 5,
        'MATIC': 6,
        'ADA': 7,
        'DOT': 8,
        'LINK': 9,
        'UNI': 10
    }
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create tables if they don't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS crypto_configs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT UNIQUE NOT NULL,
                topic_id INTEGER NOT NULL,
                is_active BOOLEAN DEFAULT FALSE,
                availability TEXT DEFAULT 'BOTH',
                hyperliquid_available BOOLEAN DEFAULT TRUE,
                allora_available BOOLEAN DEFAULT TRUE,
                last_price REAL,
                volume_24h REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bot_commands (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                command_type TEXT NOT NULL,
                command_data TEXT,
                status TEXT DEFAULT 'PENDING',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                executed_at TIMESTAMP,
                error_message TEXT
            )
        """)
        
        # Add/activate requested cryptos
        activated_count = 0
        for symbol in cryptos:
            symbol = symbol.upper()
            topic_id = topic_mapping.get(symbol)
            
            if not topic_id:
                print(f"   ⚠️ Unknown crypto: {symbol} - skipping")
                continue
            
            # Insert or update crypto config
            cursor.execute("""
                INSERT OR REPLACE INTO crypto_configs 
                (symbol, topic_id, is_active, availability, hyperliquid_available, allora_available, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (symbol, topic_id, True, 'BOTH', True, True, datetime.now(), datetime.now()))
            
            print(f"   ✅ Activated {symbol} (Topic {topic_id})")
            activated_count += 1
        
        conn.commit()
        conn.close()
        
        print(f"   📊 {activated_count} cryptocurrencies activated")
        return activated_count > 0
        
    except Exception as e:
        print(f"   ❌ Database error: {e}")
        return False

def add_monitoring_command(db_path: str):
    """Add SET_MODE_ACTIVE command to automatically start monitoring"""
    print(f"\n📡 Adding automatic monitoring activation...")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Clear any existing pending commands
        cursor.execute("DELETE FROM bot_commands WHERE status = 'PENDING'")
        
        # Get active cryptos from database to include in activation command
        cursor.execute("SELECT symbol, topic_id FROM crypto_configs WHERE is_active = TRUE")
        active_cryptos = {}
        for symbol, topic_id in cursor.fetchall():
            active_cryptos[symbol] = topic_id
        
        print(f"   📊 Found {len(active_cryptos)} active cryptos: {list(active_cryptos.keys())}")
        
        # Add SET_MODE_ACTIVE command with active_cryptos data
        command_data = {
            "mode": "ACTIVE",
            "active_cryptos": active_cryptos
        }
        
        cursor.execute("""
            INSERT INTO bot_commands (command_type, command_data, status, created_at)
            VALUES (?, ?, 'PENDING', ?)
        """, ('SET_MODE_ACTIVE', json.dumps(command_data), datetime.now()))
        
        command_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        print(f"   ✅ Monitoring activation command added (ID: {command_id})")
        return True
        
    except Exception as e:
        print(f"   ❌ Error adding monitoring command: {e}")
        return False

def run_bot(duration: Optional[int], trading_interval: int):
    """Run the bot for specified duration"""
    print(f"\n🚀 Starting HyperLiquid Bot...")
    
    if duration:
        print(f"⏱️ Duration: {duration} seconds")
    else:
        print(f"⏱️ Duration: Infinite (press Ctrl+C to stop)")
    
    print("=" * 60)
    
    # Import components after environment is set
    try:
        from utils.setup import setup
        from core.orders import OrderManager
        from allora.allora_mind import AlloraMind
        
        # Initialize bot components
        (address, info, exchange, vault, allora_upshot_key, hyperbolic_api_key, 
         openrouter_api_key, openrouter_model, check_for_trades, price_gap,
         allowed_amount_per_trade, max_leverage, allora_topics) = setup()

        manager = OrderManager(exchange, vault, allowed_amount_per_trade, max_leverage, info)
        res = manager.get_wallet_summary()
        print(f"Wallet: {res}")
        
        # Initialize AlloraMind
        allora_mind = AlloraMind(manager, allora_upshot_key, hyperbolic_api_key, 
                               openrouter_api_key, openrouter_model, threshold=price_gap)
        
        # Set legacy topic IDs if available
        if allora_topics:
            print(f"🔄 Setting legacy topic IDs: {allora_topics}")
            allora_mind.set_topic_ids(allora_topics)
        
        print("🟡 Bot initialized and ready!")
        
        # Start the bot with specified trading interval
        if duration:
            # For timed runs, use a simplified monitoring loop
            start_time = time.time()
            cycle_count = 0
            
            try:
                while True:
                    cycle_count += 1
                    elapsed = time.time() - start_time
                    
                    # Check duration limit
                    if elapsed >= duration:
                        print(f"\n⏰ Duration limit reached ({duration}s)")
                        break
                    
                    if cycle_count % 5 == 1:  # Show status every 5 cycles
                        print(f"\n🔄 Cycle {cycle_count} - {elapsed:.1f}s elapsed")
                    
                    # Check for dashboard commands
                    allora_mind.check_dashboard_commands()
                    
                    # Show status periodically
                    if cycle_count % 20 == 1:  # Every 20 cycles
                        print(f"   🔍 Mode: {allora_mind.mode} | Monitoring: {allora_mind.monitoring_enabled}")
                        
                        if allora_mind.mode == "ACTIVE":
                            active_cryptos = allora_mind.db.get_active_cryptos()
                            print(f"   📈 Active: {list(active_cryptos.keys())}")
                    
                    # Wait between cycles (command checking interval)
                    time.sleep(3)
                    
            except KeyboardInterrupt:
                print(f"\n⏹️ Bot stopped by user (Ctrl+C)")
            except Exception as e:
                print(f"\n❌ Bot error: {e}")
                import traceback
                traceback.print_exc()
            
            print(f"\n✅ Bot session completed:")
            print(f"   • Duration: {time.time() - start_time:.1f} seconds")
            print(f"   • Cycles: {cycle_count}")
            print(f"   • Final mode: {allora_mind.mode}")
        else:
            # For infinite runs, use the built-in AlloraMind loop with custom interval
            allora_mind.start_with_standby(interval=trading_interval)
        
    except Exception as e:
        print(f"❌ Failed to start bot: {e}")
        import traceback
        traceback.print_exc()

def parse_crypto_list(crypto_string: str) -> List[str]:
    """Parse comma-separated crypto list"""
    if not crypto_string:
        return []
    return [crypto.strip().upper() for crypto in crypto_string.split(',')]

def main():
    parser = argparse.ArgumentParser(
        description='🚀 HyperLiquid Bot Launcher',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --env testnet --duration 60 --cryptos BTC,ETH,SOL --auto-monitor
  %(prog)s --env mainnet --duration 300 --cryptos BTC --no-auto-monitor
  %(prog)s --cryptos BTC,ETH  # Use testnet, infinite duration, auto-monitor
  %(prog)s  # Use all defaults
        """
    )
    
    # Environment selection
    parser.add_argument(
        '--env', '--environment',
        choices=['testnet', 'mainnet'],
        default='testnet',
        help='Trading environment (default: testnet)'
    )
    
    # Duration
    parser.add_argument(
        '--duration', '-d',
        type=int,
        help='Duration in seconds (default: infinite, use Ctrl+C to stop)'
    )
    
    # Cryptocurrencies
    parser.add_argument(
        '--cryptos', '--currencies',
        type=str,
        default='BTC,ETH,SOL',
        help='Comma-separated list of cryptocurrencies (default: BTC,ETH,SOL)'
    )
    
    # Auto-monitoring
    parser.add_argument(
        '--auto-monitor',
        action='store_true',
        default=True,
        help='Automatically start monitoring (default: enabled)'
    )
    
    parser.add_argument(
        '--no-auto-monitor',
        action='store_true',
        help='Do not start monitoring automatically'
    )
    
    # Database path override
    parser.add_argument(
        '--db-path',
        type=str,
        help='Custom database path (optional)'
    )
    
    # Hot reload mode
    parser.add_argument(
        '--hot-reload',
        action='store_true',
        help='Enable hot reload for development (experimental)'
    )
    
    # Trading interval
    parser.add_argument(
        '--trading-interval', '--interval',
        type=int,
        default=180,
        help='Trading cycle interval in seconds (default: 180)'
    )
    
    args = parser.parse_args()
    
    # Handle auto-monitor logic
    auto_monitor = args.auto_monitor and not args.no_auto_monitor
    
    # Parse crypto list
    cryptos = parse_crypto_list(args.cryptos)
    
    # Display configuration
    print("🚀 HyperLiquid Bot Launcher")
    print("=" * 60)
    print(f"📋 Configuration:")
    print(f"   • Environment: {args.env.upper()}")
    print(f"   • Duration: {args.duration if args.duration else 'Infinite'} seconds")
    print(f"   • Cryptocurrencies: {', '.join(cryptos)}")
    print(f"   • Auto-monitor: {'Yes' if auto_monitor else 'No'}")
    print(f"   • Trading interval: {args.trading_interval} seconds")
    if args.db_path:
        print(f"   • Database: {args.db_path}")
    if args.hot_reload:
        print(f"   • Hot reload: Enabled")
    
    # Confirmation for mainnet
    if args.env == 'mainnet':
        print(f"\n⚠️  WARNING: You are about to start MAINNET trading with REAL MONEY!")
        confirm = input("Type 'YES' to confirm: ")
        if confirm != 'YES':
            print("❌ Mainnet launch cancelled")
            return
    
    # Setup environment
    db_path = setup_environment(args.env, args.db_path)
    
    # Initialize database with cryptos
    if not initialize_database(db_path, cryptos):
        print("❌ Failed to initialize database")
        return
    
    # Add monitoring command if requested
    if auto_monitor:
        if not add_monitoring_command(db_path):
            print("❌ Failed to add monitoring command")
            return
    
    # Run the bot
    if args.hot_reload:
        print("\n🔥 Hot reload mode is experimental. Use scripts/start_bot_hotreload.py for stable hot reload.")
    
    run_bot(args.duration, args.trading_interval)

if __name__ == "__main__":
    main() 