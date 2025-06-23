import os
from dotenv import load_dotenv

class EnvLoader:
    def __init__(self):
        # Explicitly reload environment variables from .env file
        load_dotenv(override=True)
        
    def get_config(self):
        """
        Load configuration from environment variables with validation
        """
        required_vars = [
            'HL_SECRET_KEY',
            'ALLORA_UPSHOT_KEY'
        ]
        
        # AI services are now optional - at least one must be provided
        ai_services = {
            'HYPERBOLIC_API_KEY': os.getenv('HYPERBOLIC_API_KEY'),
            'OPENROUTER_API_KEY': os.getenv('OPENROUTER_API_KEY')
        }
        
        # Check for required variables
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        # Validate at least one AI service is configured
        available_ai_services = [name for name, key in ai_services.items() if key]
        if not available_ai_services:
            raise ValueError("At least one AI service must be configured: HYPERBOLIC_API_KEY or OPENROUTER_API_KEY")
        
        print(f"Available AI services: {', '.join(available_ai_services)}")
            
        # Trading parameters with defaults
        config = {
            "secret_key": os.getenv('HL_SECRET_KEY'),
            "account_address": os.getenv('HL_ACCOUNT_ADDRESS'),
            "hl_master_address": os.getenv('HL_MASTER_ADDRESS'),
            "vault": os.getenv('HL_VAULT', ''),
            "allora_upshot_key": os.getenv('ALLORA_UPSHOT_KEY'),
            "price_gap": float(os.getenv('PRICE_GAP', '0.25')),
            "allowed_amount_per_trade": float(os.getenv('ALLOWED_AMOUNT_PER_TRADE', '500')),
            "max_leverage": int(os.getenv('MAX_LEVERAGE', '5')),
            "check_for_trades": int(os.getenv('CHECK_FOR_TRADES', '300')),
            "volatility_threshold": float(os.getenv('VOLATILITY_THRESHOLD', '0.02')),
            "db_path": os.getenv('DB_PATH', 'trading_logs.db'),
            "mainnet": os.getenv('MAINNET', "False"),
            "allora_topics": {
                "BTC": int(os.getenv('BTC_TOPIC_ID', '14')),
                "ETH": int(os.getenv('ETH_TOPIC_ID', '13'))
            },
            "openrouter_api_key": os.getenv('OPENROUTER_API_KEY'),
            "openrouter_model": os.getenv('OPENROUTER_MODEL', 'anthropic/claude-3-sonnet'),
            # Sprint 1.1: Nouvelle logique de validation adaptative
            "validation_score_threshold": float(os.getenv('VALIDATION_SCORE_THRESHOLD', '0.5')),
            "adaptive_thresholds": os.getenv('ADAPTIVE_THRESHOLDS', 'True').lower() == 'true',
            "volatility_threshold_low": float(os.getenv('VOLATILITY_THRESHOLD_LOW', '0.015')),
            "volatility_threshold_high": float(os.getenv('VOLATILITY_THRESHOLD_HIGH', '0.04')),
            "hyperbolic_base_weight": float(os.getenv('HYPERBOLIC_BASE_WEIGHT', '0.6')),
            "openrouter_base_weight": float(os.getenv('OPENROUTER_BASE_WEIGHT', '0.4')),
            # Sprint 1.2: Adaptive thresholds avancés  
            "adaptive_min_threshold": float(os.getenv('ADAPTIVE_MIN_THRESHOLD', '0.25')),
            "adaptive_max_threshold": float(os.getenv('ADAPTIVE_MAX_THRESHOLD', '0.85')),
            "historical_performance_weight": float(os.getenv('HISTORICAL_PERFORMANCE_WEIGHT', '0.05')),
            "market_condition_weight": float(os.getenv('MARKET_CONDITION_WEIGHT', '0.03'))
        }
        
        return config
