"""
Analytics API Router
Endpoints for trading analytics and performance metrics
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Dict, Any, Optional
import logging
from datetime import datetime, timedelta
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

@router.get("/summary")
async def get_analytics_summary(
    data_service: DataService = Depends(get_data_service)
):
    """Get comprehensive analytics summary"""
    try:
        summary = await data_service.get_analytics_summary()
        
        if "error" in summary:
            return {
                "success": False,
                "message": "Failed to get analytics summary",
                "error": summary["error"]
            }
        
        return {
            "success": True,
            "data": summary
        }
        
    except Exception as e:
        logger.error(f"Error getting analytics summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/trading-summary")
async def get_trading_summary(
    data_service: DataService = Depends(get_data_service)
):
    """Get trading performance summary"""
    try:
        summary = await data_service.get_trading_summary()
        
        if "error" in summary:
            return {
                "success": False,
                "message": "Failed to get trading summary",
                "error": summary["error"]
            }
        
        return {
            "success": True,
            "data": summary
        }
        
    except Exception as e:
        logger.error(f"Error getting trading summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/performance")
async def get_performance_metrics(
    period: Optional[str] = Query("7d", description="Period: 1d, 7d, 30d, 90d"),
    coin: Optional[str] = Query(None, description="Filter by specific coin"),
    data_service: DataService = Depends(get_data_service)
):
    """Get detailed performance metrics"""
    try:
        # Validate period parameter
        valid_periods = ["1d", "7d", "30d", "90d"]
        if period not in valid_periods:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid period. Must be one of: {', '.join(valid_periods)}"
            )
        
        # Get trading summary (which includes 7-day data by default)
        trading_summary = await data_service.get_trading_summary()
        analytics_summary = await data_service.get_analytics_summary()
        
        # Calculate additional metrics based on the data
        performance_data = {
            "period": period,
            "coin_filter": coin,
            "trading_metrics": trading_summary,
            "analytics": analytics_summary,
            "calculated_at": datetime.now().isoformat()
        }
        
        # Filter by coin if specified
        if coin and "coin_performance" in analytics_summary:
            coin_data = [
                item for item in analytics_summary["coin_performance"] 
                if item["coin"].upper() == coin.upper()
            ]
            performance_data["coin_specific"] = coin_data[0] if coin_data else None
        
        return {
            "success": True,
            "data": performance_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting performance metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/daily-pnl")
async def get_daily_pnl(
    days: int = Query(30, ge=1, le=365, description="Number of days to retrieve"),
    data_service: DataService = Depends(get_data_service)
):
    """Get daily PnL data for charting"""
    try:
        analytics = await data_service.get_analytics_summary()
        
        if "error" in analytics:
            return {
                "success": False,
                "message": "Failed to get daily PnL data",
                "error": analytics["error"]
            }
        
        # Get daily PnL data (limited by requested days)
        daily_pnl = analytics.get("daily_pnl", [])[:days]
        
        # Calculate cumulative PnL
        cumulative_pnl = 0
        for day_data in reversed(daily_pnl):
            cumulative_pnl += day_data["pnl"]
            day_data["cumulative_pnl"] = round(cumulative_pnl, 2)
        
        # Reverse back to chronological order
        daily_pnl = list(reversed(daily_pnl))
        
        return {
            "success": True,
            "data": {
                "daily_pnl": daily_pnl,
                "days_requested": days,
                "total_days": len(daily_pnl),
                "period_summary": {
                    "total_pnl": sum(day["pnl"] for day in daily_pnl),
                    "total_trades": sum(day["trades"] for day in daily_pnl),
                    "profitable_days": len([day for day in daily_pnl if day["pnl"] > 0]),
                    "losing_days": len([day for day in daily_pnl if day["pnl"] < 0])
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting daily PnL: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/coin-performance")
async def get_coin_performance(
    data_service: DataService = Depends(get_data_service)
):
    """Get performance breakdown by coin"""
    try:
        analytics = await data_service.get_analytics_summary()
        
        if "error" in analytics:
            return {
                "success": False,
                "message": "Failed to get coin performance data",
                "error": analytics["error"]
            }
        
        coin_performance = analytics.get("coin_performance", [])
        
        # Calculate additional metrics
        total_trades = sum(coin["trades"] for coin in coin_performance)
        total_pnl = sum(coin["total_pnl"] for coin in coin_performance)
        
        for coin in coin_performance:
            coin["trade_percentage"] = round(
                (coin["trades"] / total_trades) * 100, 2
            ) if total_trades > 0 else 0
            
            coin["pnl_contribution"] = round(
                (coin["total_pnl"] / total_pnl) * 100, 2
            ) if total_pnl != 0 else 0
        
        return {
            "success": True,
            "data": {
                "coin_performance": coin_performance,
                "summary": {
                    "total_coins_traded": len(coin_performance),
                    "total_trades": total_trades,
                    "total_pnl": round(total_pnl, 2),
                    "best_performer": max(coin_performance, key=lambda x: x["total_pnl"])["coin"] if coin_performance else None,
                    "worst_performer": min(coin_performance, key=lambda x: x["total_pnl"])["coin"] if coin_performance else None
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting coin performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/dashboard-metrics")
async def get_dashboard_metrics(
    data_service: DataService = Depends(get_data_service)
):
    """Get key metrics for dashboard display"""
    try:
        # Get comprehensive data
        trading_summary = await data_service.get_trading_summary()
        analytics_summary = await data_service.get_analytics_summary()
        recent_trades = await data_service.get_recent_trades(limit=5)
        current_positions = await data_service.get_current_positions()
        
        # Calculate additional dashboard metrics
        dashboard_data = {
            "key_metrics": {
                "total_trades": trading_summary.get("total_trades", 0),
                "win_rate": trading_summary.get("win_rate", 0),
                "total_pnl": trading_summary.get("total_pnl", 0),
                "avg_confidence": trading_summary.get("avg_confidence", 0)
            },
            "quick_stats": {
                "active_positions": len(current_positions),
                "recent_trades_count": len(recent_trades),
                "last_trade_time": recent_trades[0]["timestamp"] if recent_trades else None,
                "coins_traded": len(analytics_summary.get("coin_performance", []))
            },
            "performance_indicators": {
                "profitable_trades": trading_summary.get("winning_trades", 0),
                "losing_trades": trading_summary.get("losing_trades", 0),
                "max_profit": trading_summary.get("max_profit", 0),
                "max_loss": trading_summary.get("max_loss", 0)
            },
            "updated_at": datetime.now().isoformat()
        }
        
        return {
            "success": True,
            "data": dashboard_data
        }
        
    except Exception as e:
        logger.error(f"Error getting dashboard metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def analytics_health_check(
    data_service: DataService = Depends(get_data_service)
):
    """Health check for analytics service"""
    try:
        # Test database connectivity
        db_healthy = await data_service.health_check()
        
        return {
            "success": True,
            "data": {
                "database_connection": "healthy" if db_healthy else "unhealthy",
                "analytics_service": "operational",
                "last_check": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Analytics health check failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "service_status": "unhealthy"
        } 