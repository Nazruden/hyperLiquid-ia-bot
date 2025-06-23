"""
Crypto Configuration API Router
Provides endpoints for managing cryptocurrency configurations
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List, Any
import logging
from pydantic import BaseModel
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from config_manager import ConfigManager

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/api/crypto", tags=["crypto-config"])

# Global config manager instance
config_manager = ConfigManager()

# Pydantic models for request/response validation
class CryptoActivationRequest(BaseModel):
    symbol: str
    topic_id: int

class CryptoDeactivationRequest(BaseModel):
    symbol: str

class BatchUpdateRequest(BaseModel):
    updates: Dict[str, bool]  # {symbol: should_activate}

class CryptoConfigResponse(BaseModel):
    symbol: str
    topic_id: int
    is_active: bool
    availability: str
    hyperliquid_available: bool
    allora_available: bool
    last_price: float = None
    volume_24h: float = None
    updated_at: str

class ApiResponse(BaseModel):
    success: bool
    message: str
    data: Any = None

# Dependency to get config manager
async def get_config_manager() -> ConfigManager:
    return config_manager

@router.get("/available", response_model=Dict[str, Any])
async def get_available_cryptos(manager: ConfigManager = Depends(get_config_manager)):
    """Get list of all available cryptocurrencies across platforms"""
    try:
        # Load latest availability data
        available_cryptos = await manager.load_available_cryptos()
        
        return {
            "success": True,
            "message": "Available cryptocurrencies loaded successfully",
            "data": {
                "total_count": len(available_cryptos),
                "cryptos": list(available_cryptos.values()),
                "last_updated": manager.last_updated if hasattr(manager, 'last_updated') else None
            }
        }
    except Exception as e:
        logger.error(f"Error getting available cryptos: {e}")
        raise HTTPException(status_code=500, detail=f"Error loading available cryptocurrencies: {str(e)}")

@router.get("/active", response_model=Dict[str, Any])
async def get_active_cryptos(manager: ConfigManager = Depends(get_config_manager)):
    """Get list of currently active/monitored cryptocurrencies"""
    try:
        active_cryptos = manager.get_active_cryptos_for_bot()
        
        return {
            "success": True,
            "message": "Active cryptocurrencies retrieved successfully",
            "data": {
                "total_count": len(active_cryptos),
                "active_cryptos": active_cryptos
            }
        }
    except Exception as e:
        logger.error(f"Error getting active cryptos: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving active cryptocurrencies: {str(e)}")

@router.get("/status", response_model=Dict[str, Any])
async def get_crypto_status(manager: ConfigManager = Depends(get_config_manager)):
    """Get complete crypto status including availability breakdown"""
    try:
        status = await manager.get_crypto_status()
        
        return {
            "success": True,
            "message": "Crypto status retrieved successfully",
            "data": status
        }
    except Exception as e:
        logger.error(f"Error getting crypto status: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving crypto status: {str(e)}")

@router.post("/activate", response_model=ApiResponse)
async def activate_crypto(request: CryptoActivationRequest, manager: ConfigManager = Depends(get_config_manager)):
    """Activate a cryptocurrency for monitoring"""
    try:
        result = await manager.activate_crypto(request.symbol)
        
        if result['success']:
            return ApiResponse(
                success=True,
                message=result['message'],
                data={
                    "symbol": request.symbol,
                    "topic_id": result.get('topic_id'),
                    "is_active": True
                }
            )
        else:
            raise HTTPException(status_code=400, detail=result['message'])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error activating crypto {request.symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Error activating cryptocurrency: {str(e)}")

@router.post("/deactivate", response_model=ApiResponse)
async def deactivate_crypto(request: CryptoDeactivationRequest, manager: ConfigManager = Depends(get_config_manager)):
    """Deactivate a cryptocurrency from monitoring"""
    try:
        result = await manager.deactivate_crypto(request.symbol)
        
        if result['success']:
            return ApiResponse(
                success=True,
                message=result['message'],
                data={
                    "symbol": request.symbol,
                    "is_active": False
                }
            )
        else:
            raise HTTPException(status_code=400, detail=result['message'])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deactivating crypto {request.symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Error deactivating cryptocurrency: {str(e)}")

@router.put("/batch-update", response_model=ApiResponse)
async def batch_update_cryptos(request: BatchUpdateRequest, manager: ConfigManager = Depends(get_config_manager)):
    """Batch update multiple cryptocurrency activations"""
    try:
        result = await manager.batch_update_cryptos(request.updates)
        
        return ApiResponse(
            success=result['success'],
            message=f"Batch update completed. Activated: {len(result['activated'])}, Deactivated: {len(result['deactivated'])}, Errors: {len(result['errors'])}",
            data={
                "activated": result['activated'],
                "deactivated": result['deactivated'],
                "errors": result['errors'],
                "total_updated": len(result['activated']) + len(result['deactivated'])
            }
        )
        
    except Exception as e:
        logger.error(f"Error in batch update: {e}")
        raise HTTPException(status_code=500, detail=f"Error in batch update: {str(e)}")

@router.get("/compatibility", response_model=Dict[str, Any])
async def get_compatibility_check(manager: ConfigManager = Depends(get_config_manager)):
    """Check compatibility between HyperLiquid and AlloraNetwork"""
    try:
        compatibility = await manager.get_compatibility_check()
        
        return {
            "success": True,
            "message": "Compatibility check completed",
            "data": compatibility
        }
    except Exception as e:
        logger.error(f"Error in compatibility check: {e}")
        raise HTTPException(status_code=500, detail=f"Error checking compatibility: {str(e)}")

@router.get("/search", response_model=Dict[str, Any])
async def search_cryptos(
    query: str = "",
    availability: str = "all",  # "all", "both", "hyperliquid", "allora"
    active_only: bool = False,
    manager: ConfigManager = Depends(get_config_manager)
):
    """Search and filter cryptocurrencies"""
    try:
        # Get crypto status
        status = await manager.get_crypto_status()
        cryptos = status['cryptos']
        
        # Apply filters
        filtered_cryptos = []
        
        for crypto in cryptos:
            # Query filter (search in symbol)
            if query and query.upper() not in crypto['symbol'].upper():
                continue
            
            # Availability filter
            if availability != "all" and crypto['availability'] != availability:
                continue
            
            # Active filter
            if active_only and not crypto['is_active']:
                continue
            
            filtered_cryptos.append(crypto)
        
        return {
            "success": True,
            "message": f"Found {len(filtered_cryptos)} cryptocurrencies matching criteria",
            "data": {
                "total_found": len(filtered_cryptos),
                "cryptos": filtered_cryptos,
                "filters_applied": {
                    "query": query,
                    "availability": availability,
                    "active_only": active_only
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Error in crypto search: {e}")
        raise HTTPException(status_code=500, detail=f"Error searching cryptocurrencies: {str(e)}")

@router.get("/popular", response_model=Dict[str, Any])
async def get_popular_cryptos(manager: ConfigManager = Depends(get_config_manager)):
    """Get popular/recommended cryptocurrency selections"""
    try:
        # Define popular crypto sets
        popular_sets = {
            "top_market_cap": ["BTC", "ETH", "SOL", "AVAX"],
            "defi_favorites": ["ETH", "UNI", "LINK", "MATIC"],
            "layer1_blockchains": ["BTC", "ETH", "SOL", "ADA", "ATOM", "DOT"],
            "recommended_starter": ["BTC", "ETH", "SOL"]
        }
        
        # Get availability data
        status = await manager.get_crypto_status()
        available_symbols = [crypto['symbol'] for crypto in status['cryptos']]
        
        # Filter popular sets by availability
        filtered_sets = {}
        for set_name, symbols in popular_sets.items():
            available_in_set = [symbol for symbol in symbols if symbol in available_symbols]
            if available_in_set:
                filtered_sets[set_name] = available_in_set
        
        return {
            "success": True,
            "message": "Popular crypto sets retrieved",
            "data": {
                "popular_sets": filtered_sets,
                "total_sets": len(filtered_sets)
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting popular cryptos: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving popular cryptocurrencies: {str(e)}")

@router.post("/quick-actions/activate-popular", response_model=ApiResponse)
async def activate_popular_cryptos(
    set_name: str = "recommended_starter",
    manager: ConfigManager = Depends(get_config_manager)
):
    """Quick action to activate a popular set of cryptocurrencies"""
    try:
        # Get popular sets
        popular_response = await get_popular_cryptos(manager)
        popular_sets = popular_response["data"]["popular_sets"]
        
        if set_name not in popular_sets:
            raise HTTPException(status_code=400, detail=f"Popular set '{set_name}' not found")
        
        symbols = popular_sets[set_name]
        
        # Create batch update request
        updates = {symbol: True for symbol in symbols}
        result = await manager.batch_update_cryptos(updates)
        
        return ApiResponse(
            success=result['success'],
            message=f"Quick activation of {set_name} completed",
            data={
                "set_name": set_name,
                "symbols": symbols,
                "activated": result['activated'],
                "errors": result['errors']
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in quick activation: {e}")
        raise HTTPException(status_code=500, detail=f"Error in quick activation: {str(e)}")

@router.post("/quick-actions/clear-all", response_model=ApiResponse)
async def clear_all_cryptos(manager: ConfigManager = Depends(get_config_manager)):
    """Quick action to deactivate all cryptocurrencies"""
    try:
        # Get currently active cryptos
        active_cryptos = manager.get_active_cryptos_for_bot()
        
        if not active_cryptos:
            return ApiResponse(
                success=True,
                message="No active cryptocurrencies to clear",
                data={"deactivated": []}
            )
        
        # Create batch update request to deactivate all
        updates = {symbol: False for symbol in active_cryptos.keys()}
        result = await manager.batch_update_cryptos(updates)
        
        return ApiResponse(
            success=result['success'],
            message=f"Cleared all active cryptocurrencies",
            data={
                "total_cleared": len(result['deactivated']),
                "deactivated": result['deactivated'],
                "errors": result['errors']
            }
        )
        
    except Exception as e:
        logger.error(f"Error clearing all cryptos: {e}")
        raise HTTPException(status_code=500, detail=f"Error clearing all cryptocurrencies: {str(e)}")

# Health check endpoint
@router.get("/health", response_model=Dict[str, Any])
async def health_check(manager: ConfigManager = Depends(get_config_manager)):
    """Health check for crypto configuration service"""
    try:
        # Test database connection
        configs = manager.db.get_crypto_configs()
        
        return {
            "success": True,
            "message": "Crypto configuration service is healthy",
            "data": {
                "database_connected": True,
                "total_configs": len(configs),
                "service_status": "online"
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "success": False,
            "message": "Crypto configuration service is unhealthy",
            "data": {
                "database_connected": False,
                "error": str(e),
                "service_status": "error"
            }
        } 