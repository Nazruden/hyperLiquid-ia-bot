"""
Bot Process Controller - Manages bot process lifecycle
Handles start, stop, restart, and status operations
Extracted from bot_controller.py for better maintainability (≤350 lines)
"""

import subprocess
import psutil
import logging
import os
import signal
import sys
from datetime import datetime
from typing import Dict, Any, Optional
import asyncio

logger = logging.getLogger(__name__)

class BotProcessController:
    """Controls the trading bot process lifecycle"""
    
    def __init__(self):
        self.bot_process: Optional[subprocess.Popen] = None
        self.bot_pid: Optional[int] = None
        self.bot_script_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 
            "main.py"
        )
        
        # Process status cache
        self.status_cache = {
            "status": "stopped",  # stopped, running, starting, stopping, error
            "pid": None,
            "last_updated": datetime.now().isoformat(),
            "uptime": 0,
            "restart_count": 0,
            "external_process": False
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get current bot process status"""
        try:
            # First check if we have a tracked process
            if self.bot_process and self.bot_process.poll() is None:
                # Bot is running (started by dashboard)
                self.status_cache.update({
                    "status": "running",
                    "pid": self.bot_process.pid,
                    "last_updated": datetime.now().isoformat(),
                    "external_process": False
                })
            elif self.bot_process and self.bot_process.poll() is not None:
                # Bot process ended
                self.status_cache.update({
                    "status": "stopped",
                    "pid": None,
                    "last_updated": datetime.now().isoformat(),
                    "exit_code": self.bot_process.returncode,
                    "external_process": False
                })
                self.bot_process = None
            else:
                # No tracked process - check for existing bot processes
                running_bot_pid = self._find_running_bot_process()
                if running_bot_pid:
                    self.status_cache.update({
                        "status": "running",
                        "pid": running_bot_pid,
                        "last_updated": datetime.now().isoformat(),
                        "external_process": True  # Flag to indicate we didn't start this
                    })
                else:
                    self.status_cache.update({
                        "status": "stopped",
                        "pid": None,
                        "last_updated": datetime.now().isoformat(),
                        "external_process": False
                    })
                
            return self.status_cache.copy()
            
        except Exception as e:
            logger.error(f"Error getting bot status: {e}")
            return {
                "status": "error",
                "error": str(e),
                "last_updated": datetime.now().isoformat()
            }
    
    def _find_running_bot_process(self) -> Optional[int]:
        """Find already-running bot processes (main.py)"""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cwd']):
                try:
                    # Check if this is a Python process running main.py
                    if proc.info['name'] and 'python' in proc.info['name'].lower():
                        cmdline = proc.info['cmdline']
                        if cmdline and any('main.py' in arg for arg in cmdline):
                            # Get the working directory of the process
                            cwd = proc.info.get('cwd', '')
                            
                            # Check if this is our bot's main.py by looking at:
                            # 1. Working directory contains 'hyperLiquid-ia-bot'
                            # 2. Full path contains our script path
                            # 3. Command line contains main.py
                            if (any('hyperLiquid-ia-bot' in str(arg) for arg in cmdline) or
                                'hyperLiquid-ia-bot' in cwd or
                                any(self.bot_script_path in str(arg) for arg in cmdline)):
                                logger.info(f"Found existing bot process: PID {proc.info['pid']}")
                                logger.debug(f"Command line: {' '.join(cmdline)}")
                                logger.debug(f"Working directory: {cwd}")
                                return proc.info['pid']
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            
            logger.debug("No existing bot process found")
            return None
        except Exception as e:
            logger.error(f"Error finding running bot process: {e}")
            return None
    
    async def start_bot(self) -> Dict[str, Any]:
        """Start the trading bot process"""
        try:
            # Check if bot is already running
            current_status = self.get_status()
            if current_status["status"] == "running":
                external_process = current_status.get("external_process", False)
                pid = current_status.get("pid")
                message = f"Bot is already running (PID: {pid})"
                if external_process:
                    message += " - started externally"
                return {
                    "success": False,
                    "message": message,
                    "status": current_status
                }
            
            # Verify bot script exists
            if not os.path.exists(self.bot_script_path):
                return {
                    "success": False,
                    "message": f"Bot script not found: {self.bot_script_path}",
                    "status": current_status
                }
            
            # Update status to starting
            self.status_cache["status"] = "starting"
            
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
        """Stop the trading bot process"""
        try:
            current_status = self.get_status()
            if current_status["status"] != "running":
                return {
                    "success": False,
                    "message": "Bot is not running",
                    "status": current_status
                }
            
            # Update status to stopping
            self.status_cache["status"] = "stopping"
            
            pid = current_status.get("pid")
            external_process = current_status.get("external_process", False)
            
            if external_process:
                # Handle external process
                try:
                    process = psutil.Process(pid)
                    process.terminate()
                    
                    # Wait for graceful termination
                    try:
                        process.wait(timeout=10)
                    except psutil.TimeoutExpired:
                        logger.warning(f"Process {pid} didn't terminate gracefully, forcing kill")
                        process.kill()
                        process.wait(timeout=5)
                    
                    logger.info(f"External bot process {pid} stopped successfully")
                    
                except psutil.NoSuchProcess:
                    logger.warning(f"Process {pid} already terminated")
                except Exception as e:
                    logger.error(f"Error stopping external process {pid}: {e}")
                    return {
                        "success": False,
                        "message": f"Error stopping external process: {str(e)}",
                        "status": self.get_status()
                    }
            else:
                # Handle our own process
                if self.bot_process:
                    try:
                        self.bot_process.terminate()
                        
                        # Wait for graceful termination
                        try:
                            self.bot_process.wait(timeout=10)
                        except subprocess.TimeoutExpired:
                            logger.warning("Bot process didn't terminate gracefully, forcing kill")
                            self.bot_process.kill()
                            self.bot_process.wait(timeout=5)
                        
                        logger.info("Bot process stopped successfully")
                        
                    except Exception as e:
                        logger.error(f"Error stopping bot process: {e}")
                        return {
                            "success": False,
                            "message": f"Error stopping bot process: {str(e)}",
                            "status": self.get_status()
                        }
                    finally:
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
        """Restart the trading bot process"""
        try:
            logger.info("Restarting bot...")
            
            # Stop the bot first
            stop_result = await self.stop_bot()
            if not stop_result["success"]:
                return {
                    "success": False,
                    "message": f"Failed to stop bot for restart: {stop_result['message']}",
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
                    "message": f"Failed to start bot after stop: {start_result['message']}",
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
            # For now, return a placeholder. In a real implementation,
            # this would read from log files or capture stdout/stderr
            return {
                "success": True,
                "message": "Bot logs retrieved",
                "logs": [
                    f"[{datetime.now().isoformat()}] Bot process status: {self.get_status()['status']}",
                    f"[{datetime.now().isoformat()}] Requested {lines} lines of logs",
                    # Add more log parsing logic here
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting bot logs: {e}")
            return {
                "success": False,
                "message": f"Error getting bot logs: {str(e)}",
                "logs": []
            }
    
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