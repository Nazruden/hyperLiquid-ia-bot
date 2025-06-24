from utils.setup import setup
from core.orders import OrderManager
from utils.helpers import display_leverage_info
from hyperliquid.utils import constants
from hyperliquid.exchange import Exchange
from allora.allora_mind import AlloraMind
from analysis.performance_analyzer import PerformanceAnalyzer
import time


def main():
    print("🚀 HyperLiquid AI Trading Bot with Dynamic Crypto Management")
    print("=" * 60)
    
    (address, info, exchange, vault, allora_upshot_key, hyperbolic_api_key, 
     openrouter_api_key, openrouter_model, perplexity_api_key, perplexity_model, check_for_trades, price_gap,
     allowed_amount_per_trade, max_leverage, allora_topics) = setup()

    manager = OrderManager(exchange, vault, allowed_amount_per_trade, max_leverage, info)
    res = manager.get_wallet_summary()
    print(res)
    
    # Initialize AlloraMind with crypto management capabilities (triple validation)
    allora_mind = AlloraMind(manager, allora_upshot_key, hyperbolic_api_key, 
                           openrouter_api_key, openrouter_model, perplexity_api_key, perplexity_model, threshold=price_gap)
    
    # Set legacy topic IDs if no database config exists (backward compatibility)
    if allora_topics:
        print(f"🔄 Setting legacy topic IDs: {allora_topics}")
        allora_mind.set_topic_ids(allora_topics)
    
    print("🟡 Starting bot with STANDBY mode and command listening...")
    print("📱 Use the dashboard to activate cryptocurrencies and start monitoring")
    print("🌐 Dashboard: http://localhost:4000")
    print("=" * 60)
    
    # Start with STANDBY mode - will load active cryptos from database
    allora_mind.start_with_standby(interval=check_for_trades)


def analyze_trading_results():
    analyzer = PerformanceAnalyzer()
    results = analyzer.analyze_results()
    print("\nTrading Analysis Results:")
    print("========================")
    print("\nPerformance by Market Condition:")
    print(results['condition_analysis'])
    print(f"\nVolatility Correlation: {results['volatility_correlation']:.4f}")
    print(f"Allora Prediction Accuracy: {results['prediction_accuracy']:.4f}")


if __name__ == "__main__":
    main()
