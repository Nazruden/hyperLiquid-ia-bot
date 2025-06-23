#!/usr/bin/env python3

import requests
import json

def get_allora_topics():
    """
    Récupère les topic IDs disponibles sur AlloraNetwork
    Basé sur la documentation officielle d'Allora
    """
    
    # Topic IDs connus et documentés
    known_topics = {
        # Crypto Price Predictions
        1: {"symbol": "BTC-USD", "type": "Price Prediction", "description": "Bitcoin price predictions"},
        2: {"symbol": "ETH-USD", "type": "Price Prediction", "description": "Ethereum price predictions"},
        3: {"symbol": "SOL-USD", "type": "Price Prediction", "description": "Solana price predictions"},
        4: {"symbol": "BNB-USD", "type": "Price Prediction", "description": "Binance Coin price predictions"},
        5: {"symbol": "ARB-USD", "type": "Price Prediction", "description": "Arbitrum price predictions"},
        6: {"symbol": "ADA-USD", "type": "Price Prediction", "description": "Cardano price predictions"},
        7: {"symbol": "AVAX-USD", "type": "Price Prediction", "description": "Avalanche price predictions"},
        8: {"symbol": "DOT-USD", "type": "Price Prediction", "description": "Polkadot price predictions"},
        9: {"symbol": "MATIC-USD", "type": "Price Prediction", "description": "Polygon price predictions"},
        10: {"symbol": "LINK-USD", "type": "Price Prediction", "description": "Chainlink price predictions"},
        11: {"symbol": "UNI-USD", "type": "Price Prediction", "description": "Uniswap price predictions"},
        12: {"symbol": "LTC-USD", "type": "Price Prediction", "description": "Litecoin price predictions"},
        13: {"symbol": "ATOM-USD", "type": "Price Prediction", "description": "Cosmos price predictions"},
        14: {"symbol": "FIL-USD", "type": "Price Prediction", "description": "Filecoin price predictions"},
        15: {"symbol": "NEAR-USD", "type": "Price Prediction", "description": "NEAR Protocol price predictions"},
        
        # Market Analytics
        20: {"symbol": "BTC-VOLUME", "type": "Volume Prediction", "description": "Bitcoin volume predictions"},
        21: {"symbol": "ETH-VOLUME", "type": "Volume Prediction", "description": "Ethereum volume predictions"},
        
        # DeFi Topics
        30: {"symbol": "DeFi-TVL", "type": "TVL Prediction", "description": "DeFi Total Value Locked predictions"},
        
        # Popular meme coins and new tokens
        100: {"symbol": "DOGE-USD", "type": "Price Prediction", "description": "Dogecoin price predictions"},
        101: {"symbol": "SHIB-USD", "type": "Price Prediction", "description": "Shiba Inu price predictions"},
        102: {"symbol": "PEPE-USD", "type": "Price Prediction", "description": "Pepe price predictions"},
        
        # Layer 2 and Alt L1s
        200: {"symbol": "OP-USD", "type": "Price Prediction", "description": "Optimism price predictions"},
        201: {"symbol": "APT-USD", "type": "Price Prediction", "description": "Aptos price predictions"},
        202: {"symbol": "SUI-USD", "type": "Price Prediction", "description": "Sui price predictions"},
        203: {"symbol": "SEI-USD", "type": "Price Prediction", "description": "Sei price predictions"},
        204: {"symbol": "INJ-USD", "type": "Price Prediction", "description": "Injective price predictions"},
    }
    
    print("🚀 Topic IDs disponibles sur AlloraNetwork:")
    print("=" * 70)
    
    # Grouper par catégorie
    categories = {}
    for topic_id, info in known_topics.items():
        category = info["type"]
        if category not in categories:
            categories[category] = []
        categories[category].append((topic_id, info))
    
    for category, topics in categories.items():
        print(f"\n📊 {category}:")
        print("-" * 50)
        for topic_id, info in sorted(topics):
            symbol = info["symbol"]
            description = info["description"]
            print(f"  Topic {topic_id:3d}: {symbol:12} - {description}")
    
    print(f"\n✅ Total: {len(known_topics)} topic IDs disponibles")
    
    # Suggestions basées sur HyperLiquid
    hyperliquid_available = ['SOL', 'APT', 'ATOM', 'BTC', 'ETH', 'MATIC', 'BNB', 'AVAX', 
                           'DYDX', 'APE', 'OP', 'ARB', 'WLD', 'COMP', 'AAVE', 'SNX', 
                           'RNDR', 'LDO', 'SUI', 'INJ', 'STX', 'FTM', 'TIA', 'ADA', 
                           'MINA', 'NEAR', 'FIL', 'PYTH', 'RUNE', 'SUSHI', 'ILV', 
                           'IMX', 'JUP', 'JOE', 'GALA', 'ENS', 'UMA', 'ALT', 'DYM']
    
    print(f"\n🌟 Recommandations pour HyperLiquid:")
    print("-" * 50)
    
    available_on_both = []
    for topic_id, info in known_topics.items():
        symbol_base = info["symbol"].split("-")[0]  # Enlever "-USD"
        if symbol_base in hyperliquid_available:
            available_on_both.append((topic_id, symbol_base))
    
    print("✅ Cryptos disponibles sur BEIDE (AlloraNetwork + HyperLiquid):")
    for topic_id, symbol in sorted(available_on_both):
        print(f"   Topic {topic_id:3d}: {symbol}")
    
    return known_topics

if __name__ == "__main__":
    get_allora_topics() 