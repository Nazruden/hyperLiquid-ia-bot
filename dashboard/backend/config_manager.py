"""
Configuration Manager for Dynamic Crypto Management
Handles crypto activation/deactivation and cross-platform availability
"""

import asyncio
import logging
import json
import requests
from datetime import datetime
from typing import Dict, List, Any, Optional
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from database.db_manager import DatabaseManager
from scripts.check_allora_topics import get_allora_topics

logger = logging.getLogger(__name__)

class ConfigManager:
    """Manages cryptocurrency configuration and availability"""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.active_cryptos = {}  # {symbol: topic_id}
        self.available_cryptos = {}  # Complete availability data
        self.hyperliquid_info = None
        
        # Initialize with existing active cryptos from database
        self._load_active_cryptos()
        
        # Known Allora topics (from check_allora_topics.py)
        self.allora_topics = {
            1: {"symbol": "BTC", "category": "crypto", "description": "Bitcoin Price Prediction"},
            2: {"symbol": "ETH", "category": "crypto", "description": "Ethereum Price Prediction"},
            3: {"symbol": "SOL", "category": "crypto", "description": "Solana Price Prediction"},
            7: {"symbol": "AVAX", "category": "crypto", "description": "Avalanche Price Prediction"},
            9: {"symbol": "MATIC", "category": "crypto", "description": "Polygon Price Prediction"},
            13: {"symbol": "ATOM", "category": "crypto", "description": "Cosmos Price Prediction"},
            14: {"symbol": "DOT", "category": "crypto", "description": "Polkadot Price Prediction"},
            18: {"symbol": "LINK", "category": "crypto", "description": "Chainlink Price Prediction"},
            22: {"symbol": "ADA", "category": "crypto", "description": "Cardano Price Prediction"},
            26: {"symbol": "UNI", "category": "crypto", "description": "Uniswap Price Prediction"}
        }
    
    def _load_active_cryptos(self):
        """Load active cryptos from database"""
        try:
            self.active_cryptos = self.db.get_active_cryptos()
            logger.info(f"Loaded {len(self.active_cryptos)} active cryptos from database")
        except Exception as e:
            logger.error(f"Error loading active cryptos: {e}")
            self.active_cryptos = {}
    
    async def load_available_cryptos(self) -> Dict[str, Any]:
        """Load and cross-reference crypto availability from HyperLiquid and Allora"""
        try:
            # Load HyperLiquid tokens
            hyperliquid_tokens = await self._get_hyperliquid_tokens()
            
            # Load Allora topics
            allora_tokens = self._get_allora_tokens()
            
            # Cross-reference availability
            self.available_cryptos = self._cross_reference_availability(
                hyperliquid_tokens, allora_tokens
            )
            
            # Update database with availability data
            await self._update_availability_in_db()
            
            logger.info(f"Loaded {len(self.available_cryptos)} available cryptos")
            return self.available_cryptos
            
        except Exception as e:
            logger.error(f"Error loading available cryptos: {e}")
            return {}
    
    async def _get_hyperliquid_tokens(self) -> List[str]:
        """Get available tokens from HyperLiquid testnet"""
        try:
            # Import HyperLiquid info class
            from hyperliquid.info import Info
            
            if not self.hyperliquid_info:
                self.hyperliquid_info = Info(base_url="https://api.hyperliquid-testnet.xyz")
            
            # Get all available symbols
            meta = self.hyperliquid_info.meta()
            
            if meta and 'universe' in meta:
                tokens = []
                for asset in meta['universe']:
                    if 'name' in asset:
                        # Extract base symbol (remove -USD suffix if present)
                        symbol = asset['name'].replace('-USD', '')
                        tokens.append(symbol)
                
                logger.info(f"Found {len(tokens)} tokens on HyperLiquid testnet")
                return tokens
            else:
                logger.warning("No universe data from HyperLiquid")
                return []
                
        except Exception as e:
            logger.error(f"Error fetching HyperLiquid tokens: {e}")
            # Fallback to known tokens
            return ["BTC", "ETH", "SOL", "AVAX", "MATIC", "ATOM", "DOT", "LINK", "ADA", "UNI"]
    
    def _get_allora_tokens(self) -> Dict[str, int]:
        """Get available tokens from Allora topics"""
        try:
            # Convert topic data to symbol -> topic_id mapping
            allora_tokens = {}
            for topic_id, info in self.allora_topics.items():
                if info['category'] == 'crypto':
                    symbol = info['symbol']
                    allora_tokens[symbol] = topic_id
            
            logger.info(f"Found {len(allora_tokens)} tokens on AlloraNetwork")
            return allora_tokens
            
        except Exception as e:
            logger.error(f"Error getting Allora tokens: {e}")
            return {}
    
    def _cross_reference_availability(self, hyperliquid_tokens: List[str], 
                                    allora_tokens: Dict[str, int]) -> Dict[str, Dict]:
        """Cross-reference crypto availability between platforms"""
        all_symbols = set(hyperliquid_tokens + list(allora_tokens.keys()))
        availability_data = {}
        
        for symbol in all_symbols:
            hyperliquid_available = symbol in hyperliquid_tokens
            allora_available = symbol in allora_tokens
            
            # Determine availability category
            if hyperliquid_available and allora_available:
                availability = "both"
            elif hyperliquid_available:
                availability = "hyperliquid"
            elif allora_available:
                availability = "allora"
            else:
                continue  # Skip if not available on either platform
            
            availability_data[symbol] = {
                'symbol': symbol,
                'topic_id': allora_tokens.get(symbol, None),
                'availability': availability,
                'hyperliquid_available': hyperliquid_available,
                'allora_available': allora_available,
                'is_active': symbol in self.active_cryptos,
                'last_price': None,
                'volume_24h': None
            }
        
        return availability_data
    
    async def _update_availability_in_db(self):
        """Update crypto availability data in database"""
        for symbol, data in self.available_cryptos.items():
            try:
                self.db.update_crypto_config(
                    symbol=symbol,
                    topic_id=data['topic_id'] or 0,
                    is_active=data['is_active'],
                    availability=data['availability'],
                    hyperliquid_available=data['hyperliquid_available'],
                    allora_available=data['allora_available']
                )
            except Exception as e:
                logger.error(f"Error updating DB for {symbol}: {e}")
    
    async def get_crypto_status(self) -> Dict[str, Any]:
        """Get complete crypto status for dashboard"""
        if not self.available_cryptos:
            await self.load_available_cryptos()
        
        # Get latest data from database
        db_configs = self.db.get_crypto_configs()
        
        # Merge with availability data
        status = {
            'total_available': len(self.available_cryptos),
            'total_active': len([c for c in db_configs if c['is_active']]),
            'availability_breakdown': {
                'both': len([c for c in self.available_cryptos.values() if c['availability'] == 'both']),
                'hyperliquid_only': len([c for c in self.available_cryptos.values() if c['availability'] == 'hyperliquid']),
                'allora_only': len([c for c in self.available_cryptos.values() if c['availability'] == 'allora'])
            },
            'cryptos': db_configs,
            'last_updated': datetime.now().isoformat()
        }
        
        return status
    
    async def activate_crypto(self, symbol: str) -> Dict[str, Any]:
        """Activate a cryptocurrency for monitoring"""
        try:
            # Validate crypto exists and is available
            if symbol not in self.available_cryptos:
                return {
                    'success': False,
                    'message': f"Crypto {symbol} not available on any platform"
                }
            
            crypto_data = self.available_cryptos[symbol]
            
            # Check if it has Allora topic ID for trading
            if not crypto_data['allora_available']:
                return {
                    'success': False,
                    'message': f"Crypto {symbol} not available on AlloraNetwork (no trading predictions)"
                }
            
            # Activate in database
            success = self.db.activate_crypto(symbol)
            
            if success:
                # Update local cache
                self.active_cryptos[symbol] = crypto_data['topic_id']
                
                # Add bot command for real-time update
                self.db.add_bot_command('ACTIVATE_CRYPTO', {'symbol': symbol, 'topic_id': crypto_data['topic_id']})
                
                return {
                    'success': True,
                    'message': f"Crypto {symbol} activated successfully",
                    'symbol': symbol,
                    'topic_id': crypto_data['topic_id']
                }
            else:
                return {
                    'success': False,
                    'message': f"Failed to activate crypto {symbol}"
                }
                
        except Exception as e:
            logger.error(f"Error activating crypto {symbol}: {e}")
            return {
                'success': False,
                'message': f"Error activating crypto {symbol}: {str(e)}"
            }
    
    async def deactivate_crypto(self, symbol: str) -> Dict[str, Any]:
        """Deactivate a cryptocurrency from monitoring"""
        try:
            # Check if crypto is currently active
            if symbol not in self.active_cryptos:
                return {
                    'success': False,
                    'message': f"Crypto {symbol} is not currently active"
                }
            
            # Deactivate in database
            success = self.db.deactivate_crypto(symbol)
            
            if success:
                # Remove from local cache
                topic_id = self.active_cryptos.pop(symbol, None)
                
                # Add bot command for real-time update
                self.db.add_bot_command('DEACTIVATE_CRYPTO', {'symbol': symbol})
                
                return {
                    'success': True,
                    'message': f"Crypto {symbol} deactivated successfully",
                    'symbol': symbol
                }
            else:
                return {
                    'success': False,
                    'message': f"Failed to deactivate crypto {symbol}"
                }
                
        except Exception as e:
            logger.error(f"Error deactivating crypto {symbol}: {e}")
            return {
                'success': False,
                'message': f"Error deactivating crypto {symbol}: {str(e)}"
            }
    
    async def batch_update_cryptos(self, updates: Dict[str, bool]) -> Dict[str, Any]:
        """Batch update multiple crypto activations"""
        results = {
            'success': True,
            'activated': [],
            'deactivated': [],
            'errors': []
        }
        
        for symbol, should_activate in updates.items():
            try:
                if should_activate:
                    result = await self.activate_crypto(symbol)
                    if result['success']:
                        results['activated'].append(symbol)
                    else:
                        results['errors'].append(f"{symbol}: {result['message']}")
                        results['success'] = False
                else:
                    result = await self.deactivate_crypto(symbol)
                    if result['success']:
                        results['deactivated'].append(symbol)
                    else:
                        results['errors'].append(f"{symbol}: {result['message']}")
                        results['success'] = False
                        
            except Exception as e:
                results['errors'].append(f"{symbol}: {str(e)}")
                results['success'] = False
        
        # Add batch command for bot
        if results['activated'] or results['deactivated']:
            self.db.add_bot_command('BATCH_UPDATE_CRYPTOS', {
                'activated': results['activated'],
                'deactivated': results['deactivated']
            })
        
        return results
    
    def get_active_cryptos_for_bot(self) -> Dict[str, int]:
        """Get active cryptos in format expected by AlloraMind (symbol -> topic_id)"""
        return self.active_cryptos.copy()
    
    async def get_compatibility_check(self) -> Dict[str, Any]:
        """Check compatibility between HyperLiquid and Allora"""
        if not self.available_cryptos:
            await self.load_available_cryptos()
        
        both_platforms = [symbol for symbol, data in self.available_cryptos.items() 
                         if data['availability'] == 'both']
        
        return {
            'total_cryptos': len(self.available_cryptos),
            'both_platforms': len(both_platforms),
            'compatibility_rate': len(both_platforms) / len(self.available_cryptos) * 100 if self.available_cryptos else 0,
            'compatible_cryptos': both_platforms,
            'last_checked': datetime.now().isoformat()
        } 