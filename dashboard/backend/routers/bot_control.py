"""
Bot Control API Router
Endpoints for managing the trading bot lifecycle
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
import logging
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from dashboard.backend.bot_controller import BotController

router = APIRouter()
logger = logging.getLogger(__name__)

# Dependency to get bot controller instance
async def get_bot_controller():
    return BotController()

@router.get("/status")
async def get_bot_status(bot_controller: BotController = Depends(get_bot_controller)):
    """Get current bot status and information"""
    try:
        status = bot_controller.get_status()
        return {
            "success": True,
            "data": status
        }
    except Exception as e:
        logger.error(f"Error getting bot status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/start")
async def start_bot(bot_controller: BotController = Depends(get_bot_controller)):
    """Start the trading bot"""
    try:
        result = await bot_controller.start_bot()
        
        if result["success"]:
            return {
                "success": True,
                "message": result["message"],
                "data": result["status"]
            }
        else:
            return {
                "success": False,
                "message": result["message"],
                "data": result.get("status", {}),
                "details": {
                    "stdout": result.get("stdout"),
                    "stderr": result.get("stderr")
                }
            }
            
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stop")
async def stop_bot(bot_controller: BotController = Depends(get_bot_controller)):
    """Stop the trading bot"""
    try:
        result = await bot_controller.stop_bot()
        
        return {
            "success": result["success"],
            "message": result["message"],
            "data": result["status"]
        }
        
    except Exception as e:
        logger.error(f"Error stopping bot: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/restart")
async def restart_bot(bot_controller: BotController = Depends(get_bot_controller)):
    """Restart the trading bot"""
    try:
        result = await bot_controller.restart_bot()
        
        return {
            "success": result["success"],
            "message": result["message"],
            "data": result["status"]
        }
        
    except Exception as e:
        logger.error(f"Error restarting bot: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/logs")
async def get_bot_logs(
    lines: int = 50,
    bot_controller: BotController = Depends(get_bot_controller)
):
    """Get recent bot logs"""
    try:
        if lines < 1 or lines > 1000:
            raise HTTPException(
                status_code=400, 
                detail="Lines parameter must be between 1 and 1000"
            )
        
        result = await bot_controller.get_bot_logs(lines=lines)
        
        return {
            "success": result["success"],
            "message": result["message"],
            "data": {
                "logs": result["logs"],
                "lines_requested": lines
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting bot logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/system")
async def get_system_info(bot_controller: BotController = Depends(get_bot_controller)):
    """Get system resource information"""
    try:
        resources = bot_controller.get_system_resources()
        
        if "error" in resources:
            return {
                "success": False,
                "message": "Failed to get system resources",
                "error": resources["error"]
            }
        
        return {
            "success": True,
            "data": resources
        }
        
    except Exception as e:
        logger.error(f"Error getting system info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def bot_health_check(bot_controller: BotController = Depends(get_bot_controller)):
    """Health check endpoint for bot controller"""
    try:
        status = bot_controller.get_status()
        system = bot_controller.get_system_resources()
        
        return {
            "success": True,
            "data": {
                "bot_status": status,
                "system_resources": system,
                "controller_healthy": True
            }
        }
        
    except Exception as e:
        logger.error(f"Bot controller health check failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "controller_healthy": False
        }

# ===== CRYPTO MANAGEMENT & MODE CONTROL ENDPOINTS =====

@router.post("/start-monitoring")
async def start_monitoring(bot_controller: BotController = Depends(get_bot_controller)):
    """Start bot monitoring mode (STANDBY → ACTIVE)"""
    try:
        result = await bot_controller.start_monitoring()
        
        return {
            "success": result["success"],
            "message": result["message"],
            "data": result["status"]
        }
        
    except Exception as e:
        logger.error(f"Error starting monitoring: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/set-standby")
async def set_standby_mode(bot_controller: BotController = Depends(get_bot_controller)):
    """Set bot to STANDBY mode (pause monitoring)"""
    try:
        result = await bot_controller.set_standby_mode()
        
        return {
            "success": result["success"],
            "message": result["message"],
            "data": result["status"]
        }
        
    except Exception as e:
        logger.error(f"Error setting standby mode: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/mode-status")
async def get_bot_mode_status(bot_controller: BotController = Depends(get_bot_controller)):
    """Get detailed bot mode and crypto monitoring status"""
    try:
        result = bot_controller.get_bot_mode_status()
        
        return {
            "success": result["success"],
            "message": result.get("message", "Bot mode status retrieved"),
            "data": result["data"]
        }
        
    except Exception as e:
        logger.error(f"Error getting bot mode status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/update-crypto-config")
async def update_crypto_config(
    crypto_updates: Dict[str, Any],
    bot_controller: BotController = Depends(get_bot_controller)
):
    """Update crypto configuration and notify bot in real-time"""
    try:
        result = await bot_controller.update_crypto_config(crypto_updates)
        
        return {
            "success": result["success"],
            "message": result["message"],
            "data": {
                "active_cryptos": result["active_cryptos"],
                "status": result["status"]
            }
        }
        
    except Exception as e:
        logger.error(f"Error updating crypto config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/initialize-standby")
async def initialize_with_standby(bot_controller: BotController = Depends(get_bot_controller)):
    """Initialize bot controller in STANDBY mode"""
    try:
        result = await bot_controller.initialize_with_standby()
        
        return {
            "success": result["success"],
            "message": result["message"],
            "data": result["status"]
        }
        
    except Exception as e:
        logger.error(f"Error initializing with standby: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 