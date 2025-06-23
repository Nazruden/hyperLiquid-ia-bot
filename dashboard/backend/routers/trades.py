"""
Trades API Router
Endpoints for trade history, positions, and trade-related data
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from dashboard.backend.data_service import DataService

router = APIRouter()
logger = logging.getLogger(__name__)

# Dependency to get data service instance
async def get_data_service():
    data_service = DataService()
    await data_service.initialize()
    return data_service

@router.get("")
async def get_trades(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Number of trades per page"),
    sort_by: str = Query("timestamp", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order: asc or desc"),
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    side: Optional[str] = Query(None, description="Filter by side (buy/sell)"),
    data_service: DataService = Depends(get_data_service)
):
    """Get trades with pagination - main endpoint for frontend"""
    try:
        # Calculate offset from page
        offset = (page - 1) * limit
        
        # Get recent trades (basic implementation)
        trades = await data_service.get_recent_trades(limit=500)  # Get more for filtering
        
        # Apply filters
        if symbol:
            trades = [t for t in trades if t["coin"].upper() == symbol.upper()]
        
        if side:
            trades = [t for t in trades if t["side"].upper() == side.upper()]
        
        # Sort trades
        reverse_sort = sort_order.lower() == "desc"
        if sort_by == "timestamp":
            trades.sort(key=lambda x: x.get("timestamp", ""), reverse=reverse_sort)
        elif sort_by == "pnl":
            trades.sort(key=lambda x: x.get("pnl", 0), reverse=reverse_sort)
        elif sort_by == "size":
            trades.sort(key=lambda x: x.get("size", 0), reverse=reverse_sort)
        
        # Apply pagination
        total_count = len(trades)
        paginated_trades = trades[offset:offset + limit]
        
        return {
            "success": True,
            "data": {
                "trades": paginated_trades,
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total_pages": (total_count + limit - 1) // limit,
                    "total_count": total_count,
                    "has_next": offset + limit < total_count,
                    "has_prev": page > 1
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting trades: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history")
async def get_trade_history(
    limit: int = Query(50, ge=1, le=500, description="Number of trades to retrieve"),
    offset: int = Query(0, ge=0, description="Number of trades to skip"),
    coin: Optional[str] = Query(None, description="Filter by coin"),
    side: Optional[str] = Query(None, description="Filter by side (buy/sell)"),
    data_service: DataService = Depends(get_data_service)
):
    """Get trade history with filtering and pagination"""
    try:
        # Get recent trades (basic implementation)
        trades = await data_service.get_recent_trades(limit=limit + offset)
        
        # Apply offset
        if offset > 0:
            trades = trades[offset:]
        
        # Apply limit after offset
        trades = trades[:limit]
        
        # Apply filters
        if coin:
            trades = [t for t in trades if t["coin"].upper() == coin.upper()]
        
        if side:
            trades = [t for t in trades if t["side"].upper() == side.upper()]
        
        # Calculate summary statistics for filtered results
        total_trades = len(trades)
        total_pnl = sum(trade.get("pnl", 0) for trade in trades)
        winning_trades = len([t for t in trades if t.get("pnl", 0) > 0])
        
        return {
            "success": True,
            "data": {
                "trades": trades,
                "pagination": {
                    "limit": limit,
                    "offset": offset,
                    "total_returned": len(trades)
                },
                "filters": {
                    "coin": coin,
                    "side": side
                },
                "summary": {
                    "total_trades": total_trades,
                    "total_pnl": round(total_pnl, 2),
                    "winning_trades": winning_trades,
                    "win_rate": round((winning_trades / total_trades) * 100, 2) if total_trades > 0 else 0
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting trade history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/recent")
async def get_recent_trades(
    limit: int = Query(10, ge=1, le=100, description="Number of recent trades"),
    data_service: DataService = Depends(get_data_service)
):
    """Get most recent trades"""
    try:
        trades = await data_service.get_recent_trades(limit=limit)
        
        return {
            "success": True,
            "data": {
                "trades": trades,
                "count": len(trades),
                "last_updated": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting recent trades: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/positions")
async def get_current_positions(
    data_service: DataService = Depends(get_data_service)
):
    """Get current open positions"""
    try:
        positions = await data_service.get_current_positions()
        
        # Calculate position summary
        total_positions = len(positions)
        total_unrealized_pnl = sum(pos.get("unrealized_pnl", 0) for pos in positions)
        long_positions = len([p for p in positions if p.get("size", 0) > 0])
        short_positions = len([p for p in positions if p.get("size", 0) < 0])
        
        return {
            "success": True,
            "data": {
                "positions": positions,
                "summary": {
                    "total_positions": total_positions,
                    "long_positions": long_positions,
                    "short_positions": short_positions,
                    "total_unrealized_pnl": round(total_unrealized_pnl, 2)
                },
                "last_updated": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting current positions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/trade/{trade_id}")
async def get_trade_details(
    trade_id: int,
    data_service: DataService = Depends(get_data_service)
):
    """Get details for a specific trade"""
    try:
        # Get all recent trades and find the specific one
        # This is a simple implementation - could be optimized with direct DB query
        trades = await data_service.get_recent_trades(limit=1000)
        
        trade = next((t for t in trades if t["id"] == trade_id), None)
        
        if not trade:
            raise HTTPException(status_code=404, detail=f"Trade {trade_id} not found")
        
        return {
            "success": True,
            "data": trade
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting trade details: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/statistics")
async def get_trade_statistics(
    period: Optional[str] = Query("7d", description="Statistics period: 1d, 7d, 30d"),
    data_service: DataService = Depends(get_data_service)
):
    """Get comprehensive trade statistics"""
    try:
        # Validate period
        valid_periods = ["1d", "7d", "30d"]
        if period not in valid_periods:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid period. Must be one of: {', '.join(valid_periods)}"
            )
        
        # Get data
        trading_summary = await data_service.get_trading_summary()
        analytics_summary = await data_service.get_analytics_summary()
        recent_trades = await data_service.get_recent_trades(limit=100)
        
        # Calculate additional statistics
        if recent_trades:
            trade_sizes = [t.get("size", 0) for t in recent_trades]
            trade_prices = [t.get("price", 0) for t in recent_trades]
            
            avg_trade_size = sum(trade_sizes) / len(trade_sizes) if trade_sizes else 0
            avg_trade_price = sum(trade_prices) / len(trade_prices) if trade_prices else 0
            
            confidence_scores = [t.get("prediction_confidence", 0) for t in recent_trades if t.get("prediction_confidence")]
            avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
        else:
            avg_trade_size = 0
            avg_trade_price = 0
            avg_confidence = 0
        
        statistics = {
            "period": period,
            "trading_summary": trading_summary,
            "detailed_stats": {
                "average_trade_size": round(avg_trade_size, 4),
                "average_trade_price": round(avg_trade_price, 2),
                "average_confidence": round(avg_confidence, 2),
                "total_volume": sum(t.get("size", 0) * t.get("price", 0) for t in recent_trades)
            },
            "coin_breakdown": analytics_summary.get("coin_performance", []),
            "calculated_at": datetime.now().isoformat()
        }
        
        return {
            "success": True,
            "data": statistics
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting trade statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search")
async def search_trades(
    query: str = Query(..., description="Search query"),
    field: Optional[str] = Query("all", description="Field to search: coin, side, ai_reasoning, all"),
    limit: int = Query(50, ge=1, le=200, description="Max results"),
    data_service: DataService = Depends(get_data_service)
):
    """Search trades by various criteria"""
    try:
        # Get trades to search through
        trades = await data_service.get_recent_trades(limit=500)
        
        # Filter based on search criteria
        filtered_trades = []
        query_lower = query.lower()
        
        for trade in trades:
            match_found = False
            
            if field == "all" or field == "coin":
                if query_lower in trade.get("coin", "").lower():
                    match_found = True
            
            if field == "all" or field == "side":
                if query_lower in trade.get("side", "").lower():
                    match_found = True
            
            if field == "all" or field == "ai_reasoning":
                ai_reasoning = trade.get("ai_reasoning", "") or ""
                if query_lower in ai_reasoning.lower():
                    match_found = True
            
            if match_found:
                filtered_trades.append(trade)
        
        # Limit results
        filtered_trades = filtered_trades[:limit]
        
        return {
            "success": True,
            "data": {
                "trades": filtered_trades,
                "search_params": {
                    "query": query,
                    "field": field,
                    "limit": limit
                },
                "results": {
                    "total_found": len(filtered_trades),
                    "searched_field": field
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Error searching trades: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def trades_health_check(
    data_service: DataService = Depends(get_data_service)
):
    """Health check for trades service"""
    try:
        # Test basic functionality
        db_healthy = await data_service.health_check()
        recent_trades = await data_service.get_recent_trades(limit=1)
        
        return {
            "success": True,
            "data": {
                "database_connection": "healthy" if db_healthy else "unhealthy",
                "trades_service": "operational",
                "sample_data_available": len(recent_trades) > 0,
                "last_check": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Trades health check failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "service_status": "unhealthy"
        } 