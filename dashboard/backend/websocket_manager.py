"""
Enhanced WebSocket Manager for Real-time Dashboard State Sync
Handles client connections and broadcasts live trading data with state synchronization
Enhanced for Phase 2 - State Sync Integration
"""

from fastapi import WebSocket, WebSocketDisconnect
import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

logger = logging.getLogger(__name__)

class WebSocketManager:
    """Enhanced WebSocket manager with state synchronization support"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.client_metadata: Dict[str, Dict[str, Any]] = {}  # Track client info
        self.broadcast_queue: asyncio.Queue = asyncio.Queue()
        self._running = False
        
        # State sync integration
        self.state_sync_service = None
        
        # Message stats for monitoring
        self.message_stats = {
            "total_sent": 0,
            "total_received": 0,
            "errors": 0,
            "last_activity": None
        }
    
    def set_state_sync_service(self, state_sync_service):
        """Set the state sync service for integration"""
        self.state_sync_service = state_sync_service
        logger.info("State sync service integrated with WebSocket manager")
    
    async def connect(self, websocket: WebSocket, client_info: Dict[str, Any] = None) -> str:
        """Accept a new WebSocket connection with optional client metadata"""
        await websocket.accept()
        client_id = str(uuid.uuid4())
        self.active_connections[client_id] = websocket
        
        # Store client metadata
        self.client_metadata[client_id] = {
            "connected_at": datetime.now().isoformat(),
            "user_agent": client_info.get("user_agent") if client_info else None,
            "ip_address": client_info.get("ip_address") if client_info else None,
            "last_activity": datetime.now().isoformat()
        }
        
        logger.info(f"WebSocket client connected: {client_id} (Total: {len(self.active_connections)})")
        
        # Send full state sync to new client
        if self.state_sync_service:
            await self.state_sync_service.send_full_state_sync(client_id)
        
        return client_id
    
    def disconnect(self, client_id: str):
        """Remove a WebSocket connection"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            
        if client_id in self.client_metadata:
            del self.client_metadata[client_id]
            
        logger.info(f"WebSocket client disconnected: {client_id} (Remaining: {len(self.active_connections)})")
    
    async def disconnect_all(self):
        """Disconnect all active WebSocket connections"""
        for client_id in list(self.active_connections.keys()):
            try:
                websocket = self.active_connections[client_id]
                await websocket.close()
            except Exception as e:
                logger.error(f"Error closing WebSocket {client_id}: {e}")
            finally:
                self.disconnect(client_id)
    
    async def send_to_client(self, client_id: str, message: dict):
        """Send a message to a specific client (enhanced method name)"""
        if client_id in self.active_connections:
            try:
                websocket = self.active_connections[client_id]
                await websocket.send_json(message)
                
                # Update stats and client activity
                self.message_stats["total_sent"] += 1
                self.message_stats["last_activity"] = datetime.now().isoformat()
                
                if client_id in self.client_metadata:
                    self.client_metadata[client_id]["last_activity"] = datetime.now().isoformat()
                    
            except WebSocketDisconnect:
                self.disconnect(client_id)
            except Exception as e:
                logger.error(f"Error sending message to {client_id}: {e}")
                self.message_stats["errors"] += 1
                self.disconnect(client_id)
    
    async def send_personal_message(self, message: dict, client_id: str):
        """Send a message to a specific client (legacy method for compatibility)"""
        await self.send_to_client(client_id, message)
    
    async def broadcast_to_all(self, message: dict):
        """Broadcast a message to all connected clients (enhanced method name)"""
        if not self.active_connections:
            return
        
        disconnected_clients = []
        successful_sends = 0
        
        for client_id, websocket in self.active_connections.items():
            try:
                await websocket.send_json(message)
                successful_sends += 1
                
                # Update client activity
                if client_id in self.client_metadata:
                    self.client_metadata[client_id]["last_activity"] = datetime.now().isoformat()
                    
            except WebSocketDisconnect:
                disconnected_clients.append(client_id)
            except Exception as e:
                logger.error(f"Error broadcasting to {client_id}: {e}")
                disconnected_clients.append(client_id)
                self.message_stats["errors"] += 1
        
        # Update stats
        self.message_stats["total_sent"] += successful_sends
        self.message_stats["last_activity"] = datetime.now().isoformat()
        
        # Clean up disconnected clients
        for client_id in disconnected_clients:
            self.disconnect(client_id)
        
        if successful_sends > 0:
            logger.debug(f"Broadcasted message to {successful_sends} clients")
    
    async def broadcast_message(self, message: dict):
        """Broadcast a message to all connected clients (legacy method for compatibility)"""
        await self.broadcast_to_all(message)
    
    # ===== STATE SYNC INTEGRATION METHODS =====
    
    async def broadcast_state_sync(self, sync_type: str, data: Any):
        """Broadcast state synchronization messages"""
        message = {
            "type": f"state_sync_{sync_type}",
            "data": data,
            "timestamp": datetime.now().isoformat(),
            "source": "state_sync_service"
        }
        await self.broadcast_to_all(message)
        logger.debug(f"Broadcasted state sync: {sync_type}")
    
    async def broadcast_mode_change(self, mode_data: Dict[str, Any]):
        """Broadcast bot mode changes (STANDBY/ACTIVE)"""
        await self.broadcast_state_sync("mode_change", mode_data)
    
    async def broadcast_process_status(self, process_data: Dict[str, Any]):
        """Broadcast bot process status changes"""
        await self.broadcast_state_sync("process_status", process_data)
    
    async def broadcast_crypto_config(self, crypto_data: Dict[str, Any]):
        """Broadcast crypto configuration changes"""
        await self.broadcast_state_sync("crypto_config", crypto_data)
    
    async def broadcast_activity_stream(self, activity_data: Dict[str, Any]):
        """Broadcast new activity for the journal"""
        message = {
            "type": "activity_update",
            "data": activity_data,
            "timestamp": datetime.now().isoformat(),
            "source": "activity_logger"
        }
        await self.broadcast_to_all(message)
    
    # ===== ENHANCED BROADCASTING METHODS =====
    
    async def queue_broadcast(self, message_type: str, data: Any, priority: str = "normal"):
        """Queue a message for broadcasting with priority support"""
        message = {
            "type": message_type,
            "data": data,
            "timestamp": datetime.now().isoformat(),
            "priority": priority
        }
        await self.broadcast_queue.put(message)
    
    async def broadcast_loop(self):
        """Enhanced background task to process broadcast queue"""
        self._running = True
        logger.info("🔄 Enhanced WebSocket broadcast loop started")
        
        heartbeat_interval = 30  # seconds
        last_heartbeat = datetime.now()
        
        while self._running:
            try:
                # Process queued messages
                try:
                    message = await asyncio.wait_for(
                        self.broadcast_queue.get(), 
                        timeout=1.0
                    )
                    await self.broadcast_to_all(message)
                except asyncio.TimeoutError:
                    # Timeout is expected, continue loop
                    pass
                
                # Send periodic heartbeat if we have connections
                now = datetime.now()
                if (self.active_connections and 
                    (now - last_heartbeat).seconds >= heartbeat_interval):
                    await self.broadcast_heartbeat()
                    last_heartbeat = now
                    
            except Exception as e:
                logger.error(f"Error in enhanced broadcast loop: {e}")
                await asyncio.sleep(1)
    
    async def broadcast_heartbeat(self):
        """Enhanced heartbeat with connection stats"""
        heartbeat_message = {
            "type": "heartbeat",
            "timestamp": datetime.now().isoformat(),
            "data": {
                "connections": len(self.active_connections),
                "total_messages_sent": self.message_stats["total_sent"],
                "total_errors": self.message_stats["errors"],
                "last_activity": self.message_stats["last_activity"]
            }
        }
        await self.broadcast_to_all(heartbeat_message)
    
    # ===== LEGACY TRADING BROADCAST METHODS (for compatibility) =====
    
    async def broadcast_bot_status(self, status: dict):
        """Broadcast bot status update"""
        await self.queue_broadcast("bot_status", status)
    
    async def broadcast_new_trade(self, trade: dict):
        """Broadcast new trade information"""
        await self.queue_broadcast("new_trade", trade, priority="high")
    
    async def broadcast_position_update(self, position: dict):
        """Broadcast position update"""
        await self.queue_broadcast("position_update", position)
    
    async def broadcast_market_data(self, market_data: dict):
        """Broadcast market data update"""
        await self.queue_broadcast("market_data", market_data)
    
    async def broadcast_analytics_update(self, analytics: dict):
        """Broadcast analytics update"""
        await self.queue_broadcast("analytics", analytics)
    
    async def broadcast_error(self, error: str, details: dict = None):
        """Broadcast error information"""
        error_data = {
            "message": error,
            "details": details or {},
            "timestamp": datetime.now().isoformat()
        }
        await self.queue_broadcast("error", error_data, priority="high")
    
    # ===== MONITORING AND STATS METHODS =====
    
    def get_connection_count(self) -> int:
        """Get the number of active connections"""
        return len(self.active_connections)
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get detailed connection statistics"""
        return {
            "active_connections": len(self.active_connections),
            "client_metadata": self.client_metadata,
            "message_stats": self.message_stats,
            "queue_size": self.broadcast_queue.qsize(),
            "is_running": self._running
        }
    
    def get_client_info(self, client_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific client"""
        return self.client_metadata.get(client_id)
    
    async def ping_client(self, client_id: str) -> bool:
        """Ping a specific client to test connection"""
        try:
            ping_message = {
                "type": "ping",
                "timestamp": datetime.now().isoformat(),
                "client_id": client_id
            }
            await self.send_to_client(client_id, ping_message)
            return True
        except Exception as e:
            logger.error(f"Failed to ping client {client_id}: {e}")
            return False
    
    def stop_broadcast_loop(self):
        """Stop the broadcast loop"""
        self._running = False
        logger.info("🛑 Enhanced WebSocket broadcast loop stopped") 