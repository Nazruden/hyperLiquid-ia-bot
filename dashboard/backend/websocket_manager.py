"""
WebSocket Manager for Real-time Dashboard Updates
Handles client connections and broadcasts live trading data
"""

from fastapi import WebSocket, WebSocketDisconnect
import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Any
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

logger = logging.getLogger(__name__)

class WebSocketManager:
    """Manages WebSocket connections and real-time data broadcasting"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.broadcast_queue: asyncio.Queue = asyncio.Queue()
        self._running = False
    
    async def connect(self, websocket: WebSocket) -> str:
        """Accept a new WebSocket connection"""
        await websocket.accept()
        client_id = str(uuid.uuid4())
        self.active_connections[client_id] = websocket
        logger.info(f"WebSocket client connected: {client_id}")
        return client_id
    
    def disconnect(self, client_id: str):
        """Remove a WebSocket connection"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"WebSocket client disconnected: {client_id}")
    
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
    
    async def send_personal_message(self, message: dict, client_id: str):
        """Send a message to a specific client"""
        if client_id in self.active_connections:
            try:
                websocket = self.active_connections[client_id]
                await websocket.send_json(message)
            except WebSocketDisconnect:
                self.disconnect(client_id)
            except Exception as e:
                logger.error(f"Error sending message to {client_id}: {e}")
                self.disconnect(client_id)
    
    async def broadcast_message(self, message: dict):
        """Broadcast a message to all connected clients"""
        if not self.active_connections:
            return
        
        disconnected_clients = []
        
        for client_id, websocket in self.active_connections.items():
            try:
                await websocket.send_json(message)
            except WebSocketDisconnect:
                disconnected_clients.append(client_id)
            except Exception as e:
                logger.error(f"Error broadcasting to {client_id}: {e}")
                disconnected_clients.append(client_id)
        
        # Clean up disconnected clients
        for client_id in disconnected_clients:
            self.disconnect(client_id)
    
    async def queue_broadcast(self, message_type: str, data: Any):
        """Queue a message for broadcasting"""
        message = {
            "type": message_type,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        await self.broadcast_queue.put(message)
    
    async def broadcast_loop(self):
        """Background task to process broadcast queue"""
        self._running = True
        logger.info("🔄 WebSocket broadcast loop started")
        
        while self._running:
            try:
                # Wait for messages in the queue
                try:
                    message = await asyncio.wait_for(
                        self.broadcast_queue.get(), 
                        timeout=1.0
                    )
                    await self.broadcast_message(message)
                except asyncio.TimeoutError:
                    # Timeout is expected, continue loop
                    continue
                    
                # Send periodic heartbeat if we have connections
                if self.active_connections:
                    await self.broadcast_heartbeat()
                    
            except Exception as e:
                logger.error(f"Error in broadcast loop: {e}")
                await asyncio.sleep(1)
    
    async def broadcast_heartbeat(self):
        """Send periodic heartbeat to maintain connections"""
        heartbeat_message = {
            "type": "heartbeat",
            "timestamp": datetime.now().isoformat(),
            "connections": len(self.active_connections)
        }
        await self.broadcast_message(heartbeat_message)
    
    async def broadcast_bot_status(self, status: dict):
        """Broadcast bot status update"""
        await self.queue_broadcast("bot_status", status)
    
    async def broadcast_new_trade(self, trade: dict):
        """Broadcast new trade information"""
        await self.queue_broadcast("new_trade", trade)
    
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
        await self.queue_broadcast("error", error_data)
    
    def get_connection_count(self) -> int:
        """Get the number of active connections"""
        return len(self.active_connections)
    
    def stop_broadcast_loop(self):
        """Stop the broadcast loop"""
        self._running = False
        logger.info("🛑 WebSocket broadcast loop stopped") 