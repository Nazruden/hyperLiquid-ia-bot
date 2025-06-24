#!/usr/bin/env python3
"""
Direct trading cycle test - Force the bot to execute a single trading cycle
to see what actions it performs.
"""

import os
import sys
import time

# Set testnet environment
os.environ['DB_PATH'] = 'testnet_trades.db'
os.environ['MAINNET'] = 'False'

def test_single_trading_cycle():
    """Test a single trading cycle to see bot actions"""
    print("🧪 Testing Single Trading Cycle")
    print("=" * 50)
    
    try:
        from utils.setup import setup
        from core.orders import OrderManager
        from allora.allora_mind import AlloraMind
        
        # Initialize components
        print("🔧 Initializing bot components...")
        (address, info, exchange, vault, allora_upshot_key, hyperbolic_api_key, 
         openrouter_api_key, openrouter_model, check_for_trades, price_gap,
         allowed_amount_per_trade, max_leverage, allora_topics) = setup()

        manager = OrderManager(exchange, vault, allowed_amount_per_trade, max_leverage, info)
        res = manager.get_wallet_summary()
        print(f"💰 Wallet: {res}")
        
        # Initialize AlloraMind
        allora_mind = AlloraMind(manager, allora_upshot_key, hyperbolic_api_key, 
                               openrouter_api_key, openrouter_model, threshold=price_gap)
        
        # Set topic IDs
        allora_mind.topic_ids = {'BTC': 1, 'ETH': 2}
        allora_mind.mode = "ACTIVE"
        allora_mind.monitoring_enabled = True
        
        print(f"🟢 Bot configured for ACTIVE mode")
        print(f"📈 Active cryptocurrencies: {list(allora_mind.topic_ids.keys())}")
        
        print("\n" + "=" * 50)
        print("🚀 EXECUTING TRADING CYCLE")
        print("=" * 50)
        
        # Force a trading cycle
        print("\n📊 Step 1: Open Trade Analysis")
        allora_mind.open_trade()
        
        print("\n📈 Step 2: Position Monitoring")
        allora_mind.monitor_positions()
        
        print("\n" + "=" * 50)
        print("✅ Trading cycle completed!")
        print("=" * 50)
        
    except Exception as e:
        print(f"❌ Error during trading cycle: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_single_trading_cycle()