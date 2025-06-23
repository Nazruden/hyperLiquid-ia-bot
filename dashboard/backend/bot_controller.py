"""
Bot Controller for Managing Trading Bot Lifecycle
Handles start, stop, restart, and status operations with STANDBY/ACTIVE modes
"""

import subprocess
import psutil
import logging
import json
import os
import signal
from datetime import datetime
from typing import Dict, Any, Optional
import asyncio
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from config_manager import ConfigManager

logger = logging.getLogger(__name__)

class BotController:
    """Controls the trading bot process lifecycle with crypto management modes"""
    
    def __init__(self):
        self.bot_process: Optional[subprocess.Popen] = None
        self.bot_pid: Optional[int] = None
        self.bot_script_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
            "main.py"
        )
        
        # Initialize config manager for crypto management
        self.config_manager = ConfigManager()
        
        # Extended status cache with mode support
        self.status_cache = {
            "status": "stopped",  # stopped, running
            "mode": "STANDBY",    # STANDBY, ACTIVE
            "last_updated": datetime.now().isoformat(),
            "uptime": 0,
            "restart_count": 0,
            "active_cryptos": {},
            "monitoring_enabled": False
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get current bot status"""
        try:
            if self.bot_process and self.bot_process.poll() is None:
                # Bot is running
                self.status_cache.update({
                    "status": "running",
                    "pid": self.bot_process.pid,
                    "last_updated": datetime.now().isoformat()
                })
            elif self.bot_process and self.bot_process.poll() is not None:
                # Bot process ended
                self.status_cache.update({
                    "status": "stopped",
                    "pid": None,
                    "last_updated": datetime.now().isoformat(),
                    "exit_code": self.bot_process.returncode
                })
                self.bot_process = None
            else:
                # No bot process
                self.status_cache.update({
                    "status": "stopped",
                    "pid": None,
                    "last_updated": datetime.now().isoformat()
                })
                
            return self.status_cache.copy()
            
        except Exception as e:
            logger.error(f"Error getting bot status: {e}")
            return {
                "status": "error",
                "error": str(e),
                "last_updated": datetime.now().isoformat()
            }
    
    async def start_bot(self) -> Dict[str, Any]:
        """Start the trading bot"""
        try:
            # Check if bot is already running
            current_status = self.get_status()
            if current_status["status"] == "running":
                return {
                    "success": False,
                    "message": "Bot is already running",
                    "status": current_status
                }
            
            # Verify bot script exists
            if not os.path.exists(self.bot_script_path):
                return {
                    "success": False,
                    "message": f"Bot script not found: {self.bot_script_path}",
                    "status": current_status
                }
            
            # Start the bot process
            logger.info(f"Starting bot: {self.bot_script_path}")
            
            self.bot_process = subprocess.Popen(
                [sys.executable, self.bot_script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=os.path.dirname(self.bot_script_path)
            )
            
            self.bot_pid = self.bot_process.pid
            
            # Wait a moment to check if it started successfully
            await asyncio.sleep(2)
            
            if self.bot_process.poll() is None:
                # Bot started successfully
                self.status_cache["restart_count"] += 1
                logger.info(f"Bot started successfully with PID: {self.bot_pid}")
                
                return {
                    "success": True,
                    "message": f"Bot started successfully with PID: {self.bot_pid}",
                    "status": self.get_status()
                }
            else:
                # Bot failed to start
                stdout, stderr = self.bot_process.communicate()
                error_msg = f"Bot failed to start. Exit code: {self.bot_process.returncode}"
                
                logger.error(f"{error_msg}\nStdout: {stdout}\nStderr: {stderr}")
                
                return {
                    "success": False,
                    "message": error_msg,
                    "stdout": stdout,
                    "stderr": stderr,
                    "status": self.get_status()
                }
                
        except Exception as e:
            logger.error(f"Error starting bot: {e}")
            return {
                "success": False,
                "message": f"Error starting bot: {str(e)}",
                "status": self.get_status()
            }
    
    async def stop_bot(self) -> Dict[str, Any]:
        """Stop the trading bot"""
        try:
            current_status = self.get_status()
            
            if current_status["status"] != "running":
                return {
                    "success": False,
                    "message": "Bot is not running",
                    "status": current_status
                }
            
            if not self.bot_process:
                return {
                    "success": False,
                    "message": "No bot process found",
                    "status": current_status
                }
            
            logger.info(f"Stopping bot with PID: {self.bot_pid}")
            
            # Try graceful shutdown first
            self.bot_process.terminate()
            
            # Wait for graceful shutdown
            try:
                await asyncio.wait_for(
                    asyncio.create_task(self._wait_for_process_end()), 
                    timeout=10.0
                )
                logger.info("Bot stopped gracefully")
                
            except asyncio.TimeoutError:
                # Force kill if graceful shutdown failed
                logger.warning("Bot didn't stop gracefully, forcing shutdown")
                self.bot_process.kill()
                await asyncio.create_task(self._wait_for_process_end())
                logger.info("Bot force stopped")
            
            self.bot_process = None
            self.bot_pid = None
            
            return {
                "success": True,
                "message": "Bot stopped successfully",
                "status": self.get_status()
            }
            
        except Exception as e:
            logger.error(f"Error stopping bot: {e}")
            return {
                "success": False,
                "message": f"Error stopping bot: {str(e)}",
                "status": self.get_status()
            }
    
    async def restart_bot(self) -> Dict[str, Any]:
        """Restart the trading bot"""
        try:
            logger.info("Restarting bot...")
            
            # Stop the bot first
            stop_result = await self.stop_bot()
            if not stop_result["success"] and "not running" not in stop_result["message"]:
                return {
                    "success": False,
                    "message": f"Failed to stop bot during restart: {stop_result['message']}",
                    "status": self.get_status()
                }
            
            # Wait a moment before starting
            await asyncio.sleep(2)
            
            # Start the bot
            start_result = await self.start_bot()
            
            if start_result["success"]:
                return {
                    "success": True,
                    "message": "Bot restarted successfully",
                    "status": self.get_status()
                }
            else:
                return {
                    "success": False,
                    "message": f"Failed to start bot during restart: {start_result['message']}",
                    "status": self.get_status()
                }
                
        except Exception as e:
            logger.error(f"Error restarting bot: {e}")
            return {
                "success": False,
                "message": f"Error restarting bot: {str(e)}",
                "status": self.get_status()
            }
    
    async def get_bot_logs(self, lines: int = 50) -> Dict[str, Any]:
        """Get recent bot logs"""
        try:
            if not self.bot_process:
                return {
                    "success": False,
                    "message": "Bot is not running",
                    "logs": []
                }
            
            # This is a simplified version - in production you'd want to read from log files
            return {
                "success": True,
                "message": "Logs retrieved (simplified - implement log file reading)",
                "logs": [
                    "Log reading not implemented - check bot console output",
                    f"Bot PID: {self.bot_pid}",
                    f"Status: {self.get_status()['status']}"
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting bot logs: {e}")
            return {
                "success": False,
                "message": f"Error getting logs: {str(e)}",
                "logs": []
            }
    
    async def _wait_for_process_end(self):
        """Wait for the bot process to end"""
        while self.bot_process and self.bot_process.poll() is None:
            await asyncio.sleep(0.1)
    
    def get_system_resources(self) -> Dict[str, Any]:
        """Get system resource usage"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_used_gb": round(memory.used / (1024**3), 2),
                "memory_total_gb": round(memory.total / (1024**3), 2),
                "disk_percent": disk.percent,
                "disk_used_gb": round(disk.used / (1024**3), 2),
                "disk_total_gb": round(disk.total / (1024**3), 2)
            }
            
        except Exception as e:
            logger.error(f"Error getting system resources: {e}")
            return {
                "error": str(e)
            }

    # ===== CRYPTO MANAGEMENT & MODE CONTROL =====
    
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
            
            # Start the bot if not already running
            if self.get_status()["status"] != "running":
                start_result = await self.start_bot()
                if not start_result["success"]:
                    return {
                        "success": False,
                        "message": f"Failed to start bot: {start_result['message']}",
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
            
            # Get bot process status
            process_status = self.get_status()
            
            return {
                "success": True,
                "data": {
                    "bot_status": process_status["status"],
                    "bot_mode": self.status_cache["mode"],
                    "monitoring_enabled": self.status_cache["monitoring_enabled"],
                    "active_cryptos": active_cryptos,
                    "active_crypto_count": len(active_cryptos),
                    "pid": process_status.get("pid"),
                    "uptime": process_status.get("uptime", 0),
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
            
            logger.info("Bot controller initialized in STANDBY mode")
            
            return {
                "success": True,
                "message": "Bot controller initialized in STANDBY mode",
                "status": self.get_status()
            }
            
        except Exception as e:
            logger.error(f"Error initializing with standby: {e}")
            return {
                "success": False,
                "message": f"Error initializing: {str(e)}",
                "status": self.get_status()
            } 