"""
Bot Mode Controller - Manages bot modes and crypto configuration
Handles STANDBY/ACTIVE mode transitions and crypto management
Extracted from bot_controller.py for better maintainability (≤350 lines)
"""

import logging
from datetime import datetime
from typing import Dict, Any
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from dashboard.backend.config_manager import ConfigManager

logger = logging.getLogger(__name__)

class BotModeController:
    """Controls bot modes (STANDBY/ACTIVE) and crypto configuration"""
    
    def __init__(self, state_sync_service=None):
        # Initialize config manager for crypto management
        self.config_manager = ConfigManager()
        
        # State sync service for WebSocket broadcasting
        self.state_sync_service = state_sync_service
        
        # Extended status cache with mode support
        self.status_cache = {
            "mode": "STANDBY",    # STANDBY, ACTIVE
            "monitoring_enabled": False,
            "active_cryptos": {},
            "last_updated": datetime.now().isoformat()
        }
    
    def set_state_sync_service(self, state_sync_service):
        """Set the state sync service for WebSocket broadcasting"""
        self.state_sync_service = state_sync_service
    
    async def start_monitoring(self) -> Dict[str, Any]:
        """Start bot in monitoring mode (transition from STANDBY to ACTIVE)"""
        try:
            # Check if we have active cryptos to monitor
            active_cryptos = self.config_manager.get_active_cryptos_for_bot()
            
            if not active_cryptos:
                return {
                    "success": False,
                    "message": "Cannot start monitoring: No active cryptocurrencies configured",
                    "status": self.get_status()
                }
            
            # Set mode to ACTIVE and enable monitoring
            self.status_cache.update({
                "mode": "ACTIVE",
                "monitoring_enabled": True,
                "active_cryptos": active_cryptos,
                "last_updated": datetime.now().isoformat()
            })
            
            # Send command to bot to start monitoring
            self.config_manager.db.add_bot_command('SET_MODE_ACTIVE', {
                "active_cryptos": active_cryptos,
                "mode": "ACTIVE"
            })
            
            # Broadcast state change via WebSocket
            if self.state_sync_service:
                await self.state_sync_service.sync_mode_change({
                    "mode": "ACTIVE",
                    "monitoring_enabled": True,
                    "active_cryptos": active_cryptos,
                    "timestamp": datetime.now().isoformat()
                })
            
            logger.info(f"Bot monitoring started with {len(active_cryptos)} cryptocurrencies")
            
            return {
                "success": True,
                "message": f"Monitoring started with {len(active_cryptos)} active cryptocurrencies",
                "status": self.get_status()
            }
            
        except Exception as e:
            logger.error(f"Error starting monitoring: {e}")
            return {
                "success": False,
                "message": f"Error starting monitoring: {str(e)}",
                "status": self.get_status()
            }
    
    async def set_standby_mode(self) -> Dict[str, Any]:
        """Set bot to STANDBY mode (stop monitoring but keep bot running)"""
        try:
            # Update status to STANDBY
            self.status_cache.update({
                "mode": "STANDBY",
                "monitoring_enabled": False,
                "last_updated": datetime.now().isoformat()
            })
            
            # Send command to bot to set standby mode
            self.config_manager.db.add_bot_command('SET_MODE_STANDBY', {
                "mode": "STANDBY"
            })
            
            # Broadcast state change via WebSocket
            if self.state_sync_service:
                await self.state_sync_service.sync_mode_change({
                    "mode": "STANDBY",
                    "monitoring_enabled": False,
                    "timestamp": datetime.now().isoformat()
                })
            
            logger.info("Bot set to STANDBY mode")
            
            return {
                "success": True,
                "message": "Bot set to STANDBY mode - monitoring paused",
                "status": self.get_status()
            }
            
        except Exception as e:
            logger.error(f"Error setting standby mode: {e}")
            return {
                "success": False,
                "message": f"Error setting standby mode: {str(e)}",
                "status": self.get_status()
            }
    
    async def update_crypto_config(self, crypto_updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update crypto configuration and notify bot"""
        try:
            # Update local status cache
            active_cryptos = self.config_manager.get_active_cryptos_for_bot()
            self.status_cache.update({
                "active_cryptos": active_cryptos,
                "last_updated": datetime.now().isoformat()
            })
            
            # Send real-time update to bot
            self.config_manager.db.add_bot_command('UPDATE_CRYPTO_CONFIG', {
                "active_cryptos": active_cryptos,
                "updates": crypto_updates
            })
            
            # Broadcast crypto config change via WebSocket
            if self.state_sync_service:
                await self.state_sync_service.sync_crypto_config_change({
                    "active_cryptos": active_cryptos,
                    "updates": crypto_updates,
                    "timestamp": datetime.now().isoformat()
                })
            
            logger.info(f"Crypto configuration updated: {len(active_cryptos)} active cryptos")
            
            return {
                "success": True,
                "message": f"Crypto configuration updated successfully",
                "active_cryptos": active_cryptos,
                "status": self.get_status()
            }
            
        except Exception as e:
            logger.error(f"Error updating crypto config: {e}")
            return {
                "success": False,
                "message": f"Error updating crypto config: {str(e)}",
                "status": self.get_status()
            }
    
    def get_bot_mode_status(self) -> Dict[str, Any]:
        """Get detailed bot mode and crypto status"""
        try:
            # Update active cryptos from config manager
            active_cryptos = self.config_manager.get_active_cryptos_for_bot()
            self.status_cache["active_cryptos"] = active_cryptos
            
            return {
                "success": True,
                "data": {
                    "mode": self.status_cache["mode"],
                    "monitoring_enabled": self.status_cache["monitoring_enabled"],
                    "active_cryptos": active_cryptos,
                    "crypto_count": len(active_cryptos),
                    "last_updated": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting bot mode status: {e}")
            return {
                "success": False,
                "message": f"Error getting bot mode status: {str(e)}",
                "data": {}
            }
    
    def get_status(self) -> Dict[str, Any]:
        """Get current mode status"""
        return self.status_cache.copy()
    
    async def initialize_with_standby(self) -> Dict[str, Any]:
        """Initialize bot in STANDBY mode (for startup)"""
        try:
            # Set initial mode to STANDBY
            self.status_cache.update({
                "mode": "STANDBY",
                "monitoring_enabled": False,
                "active_cryptos": {},
                "last_updated": datetime.now().isoformat()
            })
            
            logger.info("Bot mode controller initialized in STANDBY mode")
            
            return {
                "success": True,
                "message": "Bot mode controller initialized in STANDBY mode",
                "status": self.get_status()
            }
            
        except Exception as e:
            logger.error(f"Error initializing with standby: {e}")
            return {
                "success": False,
                "message": f"Error initializing: {str(e)}",
                "status": self.get_status()
            }
    
    # ===== CRYPTO MANAGEMENT HELPERS =====
    
    async def activate_crypto(self, symbol: str) -> Dict[str, Any]:
        """Activate a single cryptocurrency"""
        try:
            success = self.config_manager.db.activate_crypto(symbol)
            
            if success:
                # Update active cryptos cache
                active_cryptos = self.config_manager.get_active_cryptos_for_bot()
                self.status_cache["active_cryptos"] = active_cryptos
                
                # Send update to bot if in ACTIVE mode
                if self.status_cache["mode"] == "ACTIVE":
                    self.config_manager.db.add_bot_command('ACTIVATE_CRYPTO', {
                        "symbol": symbol,
                        "topic_id": active_cryptos.get(symbol)
                    })
                
                # Broadcast change via WebSocket
                if self.state_sync_service:
                    await self.state_sync_service.sync_crypto_activation({
                        "symbol": symbol,
                        "action": "ACTIVATED",
                        "active_cryptos": active_cryptos,
                        "timestamp": datetime.now().isoformat()
                    })
                
                return {
                    "success": True,
                    "message": f"Cryptocurrency {symbol} activated successfully",
                    "status": self.get_status()
                }
            else:
                return {
                    "success": False,
                    "message": f"Failed to activate cryptocurrency {symbol}",
                    "status": self.get_status()
                }
                
        except Exception as e:
            logger.error(f"Error activating crypto {symbol}: {e}")
            return {
                "success": False,
                "message": f"Error activating crypto {symbol}: {str(e)}",
                "status": self.get_status()
            }
    
    async def deactivate_crypto(self, symbol: str) -> Dict[str, Any]:
        """Deactivate a single cryptocurrency"""
        try:
            success = self.config_manager.db.deactivate_crypto(symbol)
            
            if success:
                # Update active cryptos cache
                active_cryptos = self.config_manager.get_active_cryptos_for_bot()
                self.status_cache["active_cryptos"] = active_cryptos
                
                # Send update to bot if in ACTIVE mode
                if self.status_cache["mode"] == "ACTIVE":
                    self.config_manager.db.add_bot_command('DEACTIVATE_CRYPTO', {
                        "symbol": symbol
                    })
                
                # Broadcast change via WebSocket
                if self.state_sync_service:
                    await self.state_sync_service.sync_crypto_activation({
                        "symbol": symbol,
                        "action": "DEACTIVATED",
                        "active_cryptos": active_cryptos,
                        "timestamp": datetime.now().isoformat()
                    })
                
                return {
                    "success": True,
                    "message": f"Cryptocurrency {symbol} deactivated successfully",
                    "status": self.get_status()
                }
            else:
                return {
                    "success": False,
                    "message": f"Failed to deactivate cryptocurrency {symbol}",
                    "status": self.get_status()
                }
                
        except Exception as e:
            logger.error(f"Error deactivating crypto {symbol}: {e}")
            return {
                "success": False,
                "message": f"Error deactivating crypto {symbol}: {str(e)}",
                "status": self.get_status()
            }
    
    def get_active_cryptos_summary(self) -> Dict[str, Any]:
        """Get summary of active cryptocurrencies"""
        try:
            active_cryptos = self.config_manager.get_active_cryptos_for_bot()
            all_configs = self.config_manager.db.get_crypto_configs()
            
            return {
                "total_configured": len(all_configs),
                "total_active": len(active_cryptos),
                "active_cryptos": active_cryptos,
                "active_symbols": list(active_cryptos.keys()),
                "monitoring_status": "ACTIVE" if self.status_cache["monitoring_enabled"] else "STANDBY"
            }
            
        except Exception as e:
            logger.error(f"Error getting active cryptos summary: {e}")
            return {
                "total_configured": 0,
                "total_active": 0,
                "active_cryptos": {},
                "active_symbols": [],
                "monitoring_status": "ERROR"
            } 