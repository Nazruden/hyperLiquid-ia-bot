"""
State Synchronization Service - Core solution for dashboard state sync
Handles real-time state synchronization between bot and dashboard via WebSocket
Key component to resolve the "Start Monitoring" button issue
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional
import json
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

logger = logging.getLogger(__name__)

class StateSyncService:
    """Manages state synchronization between bot and dashboard"""
    
    def __init__(self, websocket_manager=None):
        self.websocket_manager = websocket_manager
        
        # State tracking for synchronization
        self.current_state = {
            "bot_process": {
                "status": "stopped",
                "pid": None,
                "uptime": 0
            },
            "bot_mode": {
                "mode": "STANDBY",
                "monitoring_enabled": False,
                "active_cryptos": {}
            },
            "activity_stream": [],
            "last_sync": None
        }
        
        # State change listeners
        self.state_listeners = []
    
    def set_websocket_manager(self, websocket_manager):
        """Set the WebSocket manager for broadcasting"""
        self.websocket_manager = websocket_manager
        logger.info("WebSocket manager set for state sync service")
    
    def add_state_listener(self, listener):
        """Add a state change listener"""
        self.state_listeners.append(listener)
    
    async def sync_mode_change(self, mode_data: Dict[str, Any]):
        """Sync bot mode changes (STANDBY/ACTIVE) to dashboard"""
        try:
            # Update local state
            self.current_state["bot_mode"].update({
                "mode": mode_data.get("mode", "STANDBY"),
                "monitoring_enabled": mode_data.get("monitoring_enabled", False),
                "active_cryptos": mode_data.get("active_cryptos", {}),
                "last_updated": datetime.now().isoformat()
            })
            
            # Prepare WebSocket message
            sync_message = {
                "type": "bot_mode_update",
                "data": {
                    "mode": mode_data.get("mode", "STANDBY"),
                    "monitoring_enabled": mode_data.get("monitoring_enabled", False),
                    "active_cryptos": mode_data.get("active_cryptos", {}),
                    "crypto_count": len(mode_data.get("active_cryptos", {})),
                    "timestamp": datetime.now().isoformat()
                },
                "timestamp": datetime.now().isoformat()
            }
            
            # Broadcast via WebSocket
            if self.websocket_manager:
                await self.websocket_manager.broadcast_to_all(sync_message)
                logger.info(f"Broadcasted mode change: {mode_data.get('mode', 'UNKNOWN')}")
            else:
                logger.warning("WebSocket manager not available - mode change not broadcasted")
            
            # Notify state listeners
            for listener in self.state_listeners:
                try:
                    await listener.on_mode_change(mode_data)
                except Exception as e:
                    logger.error(f"Error notifying state listener: {e}")
            
            # Update sync timestamp
            self.current_state["last_sync"] = datetime.now().isoformat()
            
            return True
            
        except Exception as e:
            logger.error(f"Error syncing mode change: {e}")
            return False
    
    async def sync_process_status_change(self, process_data: Dict[str, Any]):
        """Sync bot process status changes to dashboard"""
        try:
            # Update local state
            self.current_state["bot_process"].update({
                "status": process_data.get("status", "stopped"),
                "pid": process_data.get("pid"),
                "uptime": process_data.get("uptime", 0),
                "external_process": process_data.get("external_process", False),
                "last_updated": datetime.now().isoformat()
            })
            
            # Prepare WebSocket message
            sync_message = {
                "type": "bot_process_update",
                "data": {
                    "status": process_data.get("status", "stopped"),
                    "pid": process_data.get("pid"),
                    "uptime": process_data.get("uptime", 0),
                    "external_process": process_data.get("external_process", False),
                    "restart_count": process_data.get("restart_count", 0),
                    "timestamp": datetime.now().isoformat()
                },
                "timestamp": datetime.now().isoformat()
            }
            
            # Broadcast via WebSocket
            if self.websocket_manager:
                await self.websocket_manager.broadcast_to_all(sync_message)
                logger.info(f"Broadcasted process status change: {process_data.get('status', 'UNKNOWN')}")
            else:
                logger.warning("WebSocket manager not available - process status not broadcasted")
            
            # Update sync timestamp
            self.current_state["last_sync"] = datetime.now().isoformat()
            
            return True
            
        except Exception as e:
            logger.error(f"Error syncing process status change: {e}")
            return False
    
    async def sync_crypto_config_change(self, crypto_data: Dict[str, Any]):
        """Sync crypto configuration changes to dashboard"""
        try:
            # Update local state
            self.current_state["bot_mode"]["active_cryptos"] = crypto_data.get("active_cryptos", {})
            
            # Prepare WebSocket message
            sync_message = {
                "type": "crypto_config_update",
                "data": {
                    "active_cryptos": crypto_data.get("active_cryptos", {}),
                    "crypto_count": len(crypto_data.get("active_cryptos", {})),
                    "updates": crypto_data.get("updates", {}),
                    "timestamp": datetime.now().isoformat()
                },
                "timestamp": datetime.now().isoformat()
            }
            
            # Broadcast via WebSocket
            if self.websocket_manager:
                await self.websocket_manager.broadcast_to_all(sync_message)
                logger.info(f"Broadcasted crypto config change: {len(crypto_data.get('active_cryptos', {}))} active cryptos")
            else:
                logger.warning("WebSocket manager not available - crypto config not broadcasted")
            
            return True
            
        except Exception as e:
            logger.error(f"Error syncing crypto config change: {e}")
            return False
    
    async def sync_crypto_activation(self, activation_data: Dict[str, Any]):
        """Sync individual crypto activation/deactivation"""
        try:
            # Prepare WebSocket message
            sync_message = {
                "type": "crypto_activation_update",
                "data": {
                    "symbol": activation_data.get("symbol"),
                    "action": activation_data.get("action"),  # ACTIVATED or DEACTIVATED
                    "active_cryptos": activation_data.get("active_cryptos", {}),
                    "timestamp": datetime.now().isoformat()
                },
                "timestamp": datetime.now().isoformat()
            }
            
            # Broadcast via WebSocket
            if self.websocket_manager:
                await self.websocket_manager.broadcast_to_all(sync_message)
                logger.info(f"Broadcasted crypto activation: {activation_data.get('symbol')} {activation_data.get('action')}")
            else:
                logger.warning("WebSocket manager not available - crypto activation not broadcasted")
            
            return True
            
        except Exception as e:
            logger.error(f"Error syncing crypto activation: {e}")
            return False
    
    async def sync_activity_update(self, activity_data: Dict[str, Any]):
        """Sync new activity for the activity journal"""
        try:
            # Add to activity stream (maintain last 100 entries)
            self.current_state["activity_stream"].append({
                "id": activity_data.get("id"),
                "timestamp": activity_data.get("timestamp", datetime.now().isoformat()),
                "activity_type": activity_data.get("activity_type"),
                "token": activity_data.get("token"),
                "title": activity_data.get("title"),
                "description": activity_data.get("description"),
                "severity": activity_data.get("severity", "INFO"),
                "data": activity_data.get("data", {})
            })
            
            # Keep only last 100 activities
            if len(self.current_state["activity_stream"]) > 100:
                self.current_state["activity_stream"] = self.current_state["activity_stream"][-100:]
            
            # Prepare WebSocket message
            sync_message = {
                "type": "activity_update",
                "data": {
                    "activity": {
                        "id": activity_data.get("id"),
                        "timestamp": activity_data.get("timestamp", datetime.now().isoformat()),
                        "activity_type": activity_data.get("activity_type"),
                        "token": activity_data.get("token"),
                        "title": activity_data.get("title"),
                        "description": activity_data.get("description"),
                        "severity": activity_data.get("severity", "INFO"),
                        "data": activity_data.get("data", {})
                    },
                    "stream_length": len(self.current_state["activity_stream"])
                },
                "timestamp": datetime.now().isoformat()
            }
            
            # Broadcast via WebSocket
            if self.websocket_manager:
                await self.websocket_manager.broadcast_to_all(sync_message)
                logger.debug(f"Broadcasted activity update: {activity_data.get('title', 'Unknown')}")
            else:
                logger.warning("WebSocket manager not available - activity not broadcasted")
            
            return True
            
        except Exception as e:
            logger.error(f"Error syncing activity update: {e}")
            return False
    
    async def send_full_state_sync(self, client_id: Optional[str] = None):
        """Send complete state synchronization to client(s)"""
        try:
            # Prepare full state message
            full_state = {
                "type": "full_state_sync",
                "data": {
                    "bot_process": self.current_state["bot_process"],
                    "bot_mode": self.current_state["bot_mode"],
                    "activity_stream": self.current_state["activity_stream"][-20:],  # Last 20 activities
                    "sync_timestamp": datetime.now().isoformat()
                },
                "timestamp": datetime.now().isoformat()
            }
            
            # Send to specific client or broadcast to all
            if self.websocket_manager:
                if client_id:
                    await self.websocket_manager.send_to_client(client_id, full_state)
                    logger.info(f"Sent full state sync to client: {client_id}")
                else:
                    await self.websocket_manager.broadcast_to_all(full_state)
                    logger.info("Broadcasted full state sync to all clients")
            else:
                logger.warning("WebSocket manager not available - full state sync not sent")
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending full state sync: {e}")
            return False
    
    def get_current_state(self) -> Dict[str, Any]:
        """Get current synchronized state"""
        return self.current_state.copy()
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on state sync service"""
        try:
            health_status = {
                "service_status": "healthy",
                "websocket_connected": self.websocket_manager is not None,
                "state_listeners_count": len(self.state_listeners),
                "last_sync": self.current_state.get("last_sync"),
                "activity_stream_length": len(self.current_state["activity_stream"]),
                "current_mode": self.current_state["bot_mode"]["mode"],
                "process_status": self.current_state["bot_process"]["status"],
                "timestamp": datetime.now().isoformat()
            }
            
            # Test WebSocket if available
            if self.websocket_manager:
                try:
                    test_message = {
                        "type": "health_check",
                        "data": {"status": "testing"},
                        "timestamp": datetime.now().isoformat()
                    }
                    await self.websocket_manager.broadcast_to_all(test_message)
                    health_status["websocket_test"] = "passed"
                except Exception as e:
                    health_status["websocket_test"] = f"failed: {str(e)}"
                    logger.error(f"WebSocket health check failed: {e}")
            
            return health_status
            
        except Exception as e:
            logger.error(f"Error in health check: {e}")
            return {
                "service_status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def reset_state(self):
        """Reset state to initial values"""
        try:
            self.current_state = {
                "bot_process": {
                    "status": "stopped",
                    "pid": None,
                    "uptime": 0
                },
                "bot_mode": {
                    "mode": "STANDBY",
                    "monitoring_enabled": False,
                    "active_cryptos": {}
                },
                "activity_stream": [],
                "last_sync": None
            }
            
            # Broadcast reset
            if self.websocket_manager:
                reset_message = {
                    "type": "state_reset",
                    "data": self.current_state,
                    "timestamp": datetime.now().isoformat()
                }
                await self.websocket_manager.broadcast_to_all(reset_message)
                logger.info("State reset and broadcasted")
            
            return True
            
        except Exception as e:
            logger.error(f"Error resetting state: {e}")
            return False 