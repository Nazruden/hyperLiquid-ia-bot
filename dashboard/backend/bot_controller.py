"""
Refactored Bot Controller - Orchestrates bot process and mode management
Uses modular controllers for better maintainability (≤350 lines)
Key component for resolving dashboard state sync issues
"""

import logging
from datetime import datetime
from typing import Dict, Any
import asyncio
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from dashboard.backend.controllers.bot_process_controller import BotProcessController
from dashboard.backend.controllers.bot_mode_controller import BotModeController
from dashboard.backend.services.state_sync_service import StateSyncService
from database.activity_logger import ActivityLogger

logger = logging.getLogger(__name__)

class BotController:
    """
    Orchestrates bot operations using modular controllers
    Handles both process lifecycle and mode management with state synchronization
    """
    
    def __init__(self, websocket_manager=None):
        # Initialize specialized controllers
        self.process_controller = BotProcessController()
        self.mode_controller = BotModeController()
        
        # Initialize state sync service (key component for fixing sync issues)
        self.state_sync_service = StateSyncService(websocket_manager)
        
        # Connect WebSocket manager with state sync service (bidirectional)
        if websocket_manager:
            websocket_manager.set_state_sync_service(self.state_sync_service)
            self.state_sync_service.set_websocket_manager(websocket_manager)
        
        # Connect mode controller to state sync
        self.mode_controller.set_state_sync_service(self.state_sync_service)
        
        # Initialize activity logger for journal functionality
        self.activity_logger = ActivityLogger()
        
        # Combined status cache
        self.status_cache = {
            "last_updated": datetime.now().isoformat(),
            "initialization_complete": True
        }
        
        logger.info("BotController initialized with enhanced WebSocket integration")
    
    def set_websocket_manager(self, websocket_manager):
        """Set WebSocket manager for real-time state synchronization"""
        self.state_sync_service.set_websocket_manager(websocket_manager)
        logger.info("WebSocket manager configured for bot controller")
    
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive bot status from all controllers"""
        try:
            # Get status from process controller
            process_status = self.process_controller.get_status()
            
            # Get status from mode controller
            mode_status = self.mode_controller.get_status()
            
            # Combine statuses
            combined_status = {
                **process_status,
                **mode_status,
                "last_updated": datetime.now().isoformat(),
                "controllers": {
                    "process": "healthy",
                    "mode": "healthy",
                    "sync": "healthy" if self.state_sync_service else "unavailable"
                }
            }
            
            return combined_status
            
        except Exception as e:
            logger.error(f"Error getting bot status: {e}")
            return {
                "status": "error",
                "error": str(e),
                "last_updated": datetime.now().isoformat()
            }
    
    # ===== BOT PROCESS LIFECYCLE METHODS =====
    
    async def start_bot(self) -> Dict[str, Any]:
        """Start the trading bot process"""
        try:
            result = await self.process_controller.start_bot()
            
            # Sync process status change
            if self.state_sync_service and result.get("success"):
                await self.state_sync_service.sync_process_status_change(
                    result["status"]
                )
            
            # Log activity
            if result.get("success"):
                await self._log_activity(
                    activity_type="BOT_PROCESS",
                    title="Bot Process Started",
                    description=f"Bot started successfully with PID: {result['status'].get('pid')}",
                    severity="SUCCESS"
                )
            
            return result
            
        except Exception as e:
            logger.error(f"Error in start_bot: {e}")
            return {
                "success": False,
                "message": f"Error starting bot: {str(e)}",
                "status": self.get_status()
            }
    
    async def stop_bot(self) -> Dict[str, Any]:
        """Stop the trading bot process"""
        try:
            result = await self.process_controller.stop_bot()
            
            # Sync process status change
            if self.state_sync_service:
                await self.state_sync_service.sync_process_status_change(
                    result["status"]
                )
            
            # Log activity
            if result.get("success"):
                await self._log_activity(
                    activity_type="BOT_PROCESS",
                    title="Bot Process Stopped",
                    description="Bot process stopped successfully",
                    severity="INFO"
                )
            
            return result
            
        except Exception as e:
            logger.error(f"Error in stop_bot: {e}")
            return {
                "success": False,
                "message": f"Error stopping bot: {str(e)}",
                "status": self.get_status()
            }
    
    async def restart_bot(self) -> Dict[str, Any]:
        """Restart the trading bot process"""
        try:
            result = await self.process_controller.restart_bot()
            
            # Sync process status change
            if self.state_sync_service:
                await self.state_sync_service.sync_process_status_change(
                    result["status"]
                )
            
            # Log activity
            if result.get("success"):
                await self._log_activity(
                    activity_type="BOT_PROCESS",
                    title="Bot Process Restarted",
                    description="Bot process restarted successfully",
                    severity="SUCCESS"
                )
            
            return result
            
        except Exception as e:
            logger.error(f"Error in restart_bot: {e}")
            return {
                "success": False,
                "message": f"Error restarting bot: {str(e)}",
                "status": self.get_status()
            }
    
    async def get_bot_logs(self, lines: int = 50) -> Dict[str, Any]:
        """Get recent bot logs"""
        return await self.process_controller.get_bot_logs(lines)
    
    def get_system_resources(self) -> Dict[str, Any]:
        """Get system resource usage"""
        return self.process_controller.get_system_resources()
    
    # ===== BOT MODE MANAGEMENT METHODS =====
    
    async def start_monitoring(self) -> Dict[str, Any]:
        """Start bot monitoring (STANDBY -> ACTIVE)"""
        try:
            # This is the key fix for the dashboard sync issue
            result = await self.mode_controller.start_monitoring()
            
            # The mode controller already handles WebSocket sync via state_sync_service
            # Log activity for journal
            if result.get("success"):
                await self._log_activity(
                    activity_type="MODE_CHANGE",
                    title="Monitoring Started",
                    description=f"Bot monitoring activated with {len(result['status'].get('active_cryptos', {}))} cryptocurrencies",
                    severity="SUCCESS"
                )
            
            return result
            
        except Exception as e:
            logger.error(f"Error in start_monitoring: {e}")
            return {
                "success": False,
                "message": f"Error starting monitoring: {str(e)}",
                "status": self.get_status()
            }
    
    async def set_standby_mode(self) -> Dict[str, Any]:
        """Set bot to STANDBY mode"""
        try:
            result = await self.mode_controller.set_standby_mode()
            
            # Log activity
            if result.get("success"):
                await self._log_activity(
                    activity_type="MODE_CHANGE",
                    title="Standby Mode Set",
                    description="Bot set to STANDBY mode - monitoring paused",
                    severity="INFO"
                )
            
            return result
            
        except Exception as e:
            logger.error(f"Error in set_standby_mode: {e}")
            return {
                "success": False,
                "message": f"Error setting standby mode: {str(e)}",
                "status": self.get_status()
            }
    
    async def update_crypto_config(self, crypto_updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update crypto configuration"""
        try:
            result = await self.mode_controller.update_crypto_config(crypto_updates)
            
            # Log activity
            if result.get("success"):
                await self._log_activity(
                    activity_type="CONFIG_CHANGE",
                    title="Crypto Configuration Updated",
                    description=f"Configuration updated for {len(result.get('active_cryptos', {}))} cryptocurrencies",
                    severity="INFO"
                )
            
            return result
            
        except Exception as e:
            logger.error(f"Error in update_crypto_config: {e}")
            return {
                "success": False,
                "message": f"Error updating crypto config: {str(e)}",
                "status": self.get_status()
            }
    
    def get_bot_mode_status(self) -> Dict[str, Any]:
        """Get detailed bot mode and crypto status"""
        return self.mode_controller.get_bot_mode_status()
    
    async def initialize_with_standby(self) -> Dict[str, Any]:
        """Initialize bot in STANDBY mode"""
        try:
            result = await self.mode_controller.initialize_with_standby()
            
            # Log initialization
            await self._log_activity(
                activity_type="SYSTEM",
                title="Bot Controller Initialized",
                description="Bot controller initialized in STANDBY mode with modular architecture",
                severity="INFO"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error in initialize_with_standby: {e}")
            return {
                "success": False,
                "message": f"Error initializing: {str(e)}",
                "status": self.get_status()
            }
    
    # ===== CRYPTO MANAGEMENT HELPERS =====
    
    async def activate_crypto(self, symbol: str) -> Dict[str, Any]:
        """Activate a single cryptocurrency"""
        result = await self.mode_controller.activate_crypto(symbol)
        
        if result.get("success"):
            await self._log_activity(
                activity_type="CRYPTO_MANAGEMENT",
                title=f"Crypto Activated",
                description=f"Cryptocurrency {symbol} activated for monitoring",
                severity="SUCCESS"
            )
        
        return result
    
    async def deactivate_crypto(self, symbol: str) -> Dict[str, Any]:
        """Deactivate a single cryptocurrency"""
        result = await self.mode_controller.deactivate_crypto(symbol)
        
        if result.get("success"):
            await self._log_activity(
                activity_type="CRYPTO_MANAGEMENT",
                title=f"Crypto Deactivated",
                description=f"Cryptocurrency {symbol} deactivated from monitoring",
                severity="INFO"
            )
        
        return result
    
    def get_active_cryptos_summary(self) -> Dict[str, Any]:
        """Get summary of active cryptocurrencies"""
        return self.mode_controller.get_active_cryptos_summary()
    
    # ===== ACTIVITY LOGGING & SYNCHRONIZATION =====
    
    async def _log_activity(self, activity_type: str, title: str, description: str, 
                          severity: str = "INFO", token: str = None, data: Dict[str, Any] = None):
        """Internal method to log activity and sync to dashboard"""
        try:
            activity_data = {
                "id": f"{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat(),
                "activity_type": activity_type,
                "token": token,
                "title": title,
                "description": description,
                "severity": severity,
                "data": data or {}
            }
            
            # Sync to dashboard via WebSocket
            if self.state_sync_service:
                await self.state_sync_service.sync_activity_update(activity_data)
            
        except Exception as e:
            logger.error(f"Error logging activity: {e}")
    
    async def get_recent_activity(self, limit: int = 50, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Get recent activity for dashboard journal"""
        try:
            activities = self.activity_logger.get_recent_activity(limit, filters)
            
            return {
                "success": True,
                "data": activities,
                "count": len(activities)
            }
            
        except Exception as e:
            logger.error(f"Error getting recent activity: {e}")
            return {
                "success": False,
                "message": f"Error getting recent activity: {str(e)}",
                "data": []
            }
    
    # ===== STATE SYNCHRONIZATION METHODS =====
    
    async def send_full_state_sync(self, client_id: str = None):
        """Send full state sync to dashboard client(s)"""
        if self.state_sync_service:
            return await self.state_sync_service.send_full_state_sync(client_id)
        return False
    
    def get_sync_service_status(self) -> Dict[str, Any]:
        """Get state sync service health status"""
        if self.state_sync_service:
            return asyncio.run(self.state_sync_service.health_check())
        return {"service_status": "unavailable"}
    
    # ===== BACKWARD COMPATIBILITY METHODS =====
    
    async def get_status_with_crypto_info(self) -> Dict[str, Any]:
        """Backward compatibility method for combined status"""
        status = self.get_status()
        crypto_summary = self.get_active_cryptos_summary()
        
        return {
            **status,
            "crypto_summary": crypto_summary
        } 