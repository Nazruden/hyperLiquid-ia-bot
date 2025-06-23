#!/usr/bin/env python3

import requests
import json

def get_hyperliquid_tokens():
    """Récupère la liste des tokens disponibles sur HyperLiquid testnet"""
    try:
        response = requests.post(
            'https://api.hyperliquid-testnet.xyz/info',
            json={'type': 'meta'}
        )
        response.raise_for_status()
        
        data = response.json()
        universe = data.get('universe', [])
        
        print("🚀 Cryptomonnaies disponibles sur HyperLiquid testnet:")
        print("=" * 60)
        
        for i, token in enumerate(universe, 1):
            name = token.get('name', 'N/A')
            print(f"{i:2d}. {name}")
        
        print(f"\n✅ Total: {len(universe)} tokens disponibles")
        
        # Suggérer quelques tokens populaires pour AlloraNetwork
        popular_tokens = ['BTC-USD', 'ETH-USD', 'SOL-USD', 'AVAX-USD', 'MATIC-USD', 'DOT-USD', 'LINK-USD', 'UNI-USD']
        available_popular = [token['name'] for token in universe if token.get('name') in popular_tokens]
        
        if available_popular:
            print(f"\n🌟 Tokens populaires disponibles:")
            for token in available_popular:
                print(f"   - {token}")
                
        return universe
        
    except Exception as e:
        print(f"❌ Erreur lors de la récupération des tokens: {e}")
        return []

if __name__ == "__main__":
    get_hyperliquid_tokens() 