"""
Data Service Layer for Dashboard
Provides access to trading data, analytics, and dashboard snapshots
"""

import sqlite3
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import json
import sys
import asyncio

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from dashboard.backend.bot_controller import BotController

logger = logging.getLogger(__name__)

class DataService:
    """Service layer for accessing trading data and analytics"""
    
    def __init__(self):
        self.db_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
            "trades.db"
        )
        self.cache = {}
        self.cache_timeout = 30  # Cache timeout in seconds
        
        # Initialize bot controller for status information
        self.bot_controller = BotController()
    
    async def initialize(self):
        """Initialize the data service"""
        try:
            # Verify database exists
            if not os.path.exists(self.db_path):
                logger.warning(f"Database not found at {self.db_path}")
                # Create empty database structure if needed
                await self._create_database_structure()
            
            # Test connection
            await self.health_check()
            logger.info(f"✅ Data service initialized with database: {self.db_path}")
            
        except Exception as e:
            logger.error(f"Failed to initialize data service: {e}")
            raise
    
    async def health_check(self) -> bool:
        """Check database connectivity"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    async def _create_database_structure(self):
        """Create basic database structure if it doesn't exist"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create trades table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS trades (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT,
                        coin TEXT,
                        side TEXT,
                        size REAL,
                        price REAL,
                        pnl REAL,
                        prediction_confidence REAL,
                        ai_reasoning TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create positions table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS positions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        coin TEXT,
                        size REAL,
                        entry_price REAL,
                        current_price REAL,
                        unrealized_pnl REAL,
                        leverage REAL,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # OPTIMIZATION: Add indexes to improve query performance
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_trades_timestamp ON trades (timestamp)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_trades_coin_timestamp ON trades (coin, timestamp)")
                
                conn.commit()
                logger.info("Database structure created/verified with indexes")
                
        except Exception as e:
            logger.error(f"Failed to create database structure: {e}")
            raise
    
    async def get_dashboard_snapshot(self) -> Dict[str, Any]:
        """Get complete dashboard data snapshot"""
        cache_key = "dashboard_snapshot"
        
        # Check cache
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]["data"]
        
        try:
            # Get real bot status from bot controller
            bot_status = self.bot_controller.get_status()
            
            # ✅ FIX: Get mode status with active_cryptos from mode_controller directly
            # This ensures the snapshot contains the correct active_cryptos data
            mode_status_response = self.bot_controller.mode_controller.get_bot_mode_status()
            mode_status = mode_status_response.get("data", {}) if mode_status_response.get("success") else {}
            
            # Merge mode status into bot_status to ensure active_cryptos are included
            # Force refresh from cache to get the most recent mode status
            if mode_status:
                bot_status.update({
                    "active_cryptos": mode_status.get("active_cryptos", {}),
                    "crypto_count": mode_status.get("crypto_count", 0),
                    "mode": mode_status.get("mode", "STANDBY"),
                    "monitoring_enabled": mode_status.get("monitoring_enabled", False),
                    "last_mode_update": mode_status.get("last_updated")
                })
                logger.info(f"📊 Dashboard snapshot - Bot mode: {bot_status.get('mode')}, Monitoring: {bot_status.get('monitoring_enabled')}")
            
            # OPTIMIZATION: Run database queries concurrently
            results = await asyncio.gather(
                self.get_trading_summary(),
                self.get_recent_trades(limit=10),
                self.get_current_positions(),
                self.get_analytics_summary()
            )
            
            trading_summary, recent_trades, current_positions, analytics_summary = results
            
            snapshot = {
                "bot_status": bot_status,
                "trading_summary": trading_summary,
                "recent_trades": recent_trades,
                "current_positions": current_positions,
                "analytics": analytics_summary,
                "timestamp": datetime.now().isoformat()
            }
            
            # Cache the result
            self._cache_data(cache_key, snapshot)
            
            return snapshot
            
        except Exception as e:
            logger.error(f"Error getting dashboard snapshot: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def get_trading_summary(self) -> Dict[str, Any]:
        """Get trading summary statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get basic statistics
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_trades,
                        SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as winning_trades,
                        SUM(CASE WHEN pnl < 0 THEN 1 ELSE 0 END) as losing_trades,
                        SUM(pnl) as total_pnl,
                        AVG(pnl) as avg_pnl,
                        MAX(pnl) as max_profit,
                        MIN(pnl) as max_loss,
                        AVG(prediction_confidence) as avg_confidence
                    FROM trades
                    WHERE timestamp >= datetime('now', '-7 days')
                """)
                
                result = cursor.fetchone()
                
                if result and result[0] > 0:
                    total_trades, winning_trades, losing_trades, total_pnl, avg_pnl, max_profit, max_loss, avg_confidence = result
                    
                    return {
                        "total_trades": total_trades or 0,
                        "winning_trades": winning_trades or 0,
                        "losing_trades": losing_trades or 0,
                        "win_rate": round((winning_trades / total_trades) * 100, 2) if total_trades > 0 else 0,
                        "total_pnl": round(total_pnl or 0, 2),
                        "avg_pnl": round(avg_pnl or 0, 2),
                        "max_profit": round(max_profit or 0, 2),
                        "max_loss": round(max_loss or 0, 2),
                        "avg_confidence": round(avg_confidence or 0, 2),
                        "period": "7 days"
                    }
                else:
                    return {
                        "total_trades": 0,
                        "winning_trades": 0,
                        "losing_trades": 0,
                        "win_rate": 0,
                        "total_pnl": 0,
                        "avg_pnl": 0,
                        "max_profit": 0,
                        "max_loss": 0,
                        "avg_confidence": 0,
                        "period": "7 days"
                    }
                    
        except Exception as e:
            logger.error(f"Error getting trading summary: {e}")
            return {"error": str(e)}
    
    async def get_recent_trades(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent trades"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT 
                        id, timestamp, coin, side, size, price, pnl, 
                        prediction_confidence, ai_reasoning, created_at
                    FROM trades
                    ORDER BY created_at DESC
                    LIMIT ?
                """, (limit,))
                
                trades = []
                for row in cursor.fetchall():
                    trades.append({
                        "id": row[0],
                        "timestamp": row[1],
                        "coin": row[2],
                        "side": row[3],
                        "size": row[4],
                        "price": row[5],
                        "pnl": row[6],
                        "prediction_confidence": row[7],
                        "ai_reasoning": row[8],
                        "created_at": row[9]
                    })
                
                return trades
                
        except Exception as e:
            logger.error(f"Error getting recent trades: {e}")
            return []
    
    async def get_current_positions(self) -> List[Dict[str, Any]]:
        """Get current positions"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT 
                        id, coin, size, entry_price, current_price, 
                        unrealized_pnl, leverage, created_at, updated_at
                    FROM positions
                    WHERE size != 0
                    ORDER BY updated_at DESC
                """)
                
                positions = []
                for row in cursor.fetchall():
                    positions.append({
                        "id": row[0],
                        "coin": row[1],
                        "size": row[2],
                        "entry_price": row[3],
                        "current_price": row[4],
                        "unrealized_pnl": row[5],
                        "leverage": row[6],
                        "created_at": row[7],
                        "updated_at": row[8]
                    })
                
                return positions
                
        except Exception as e:
            logger.error(f"Error getting current positions: {e}")
            return []
    
    async def get_analytics_summary(self) -> Dict[str, Any]:
        """Get analytics summary"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get daily PnL for the last 30 days
                cursor.execute("""
                    SELECT 
                        DATE(timestamp) as date,
                        SUM(pnl) as daily_pnl,
                        COUNT(*) as daily_trades
                    FROM trades
                    WHERE timestamp >= datetime('now', '-30 days')
                    GROUP BY DATE(timestamp)
                    ORDER BY date DESC
                """)
                
                daily_data = []
                for row in cursor.fetchall():
                    daily_data.append({
                        "date": row[0],
                        "pnl": round(row[1], 2),
                        "trades": row[2]
                    })
                
                # Get coin performance
                cursor.execute("""
                    SELECT 
                        coin,
                        COUNT(*) as trades,
                        SUM(pnl) as total_pnl,
                        AVG(prediction_confidence) as avg_confidence
                    FROM trades
                    WHERE timestamp >= datetime('now', '-7 days')
                    GROUP BY coin
                    ORDER BY total_pnl DESC
                """)
                
                coin_performance = []
                for row in cursor.fetchall():
                    coin_performance.append({
                        "coin": row[0],
                        "trades": row[1],
                        "total_pnl": round(row[2], 2),
                        "avg_confidence": round(row[3], 2)
                    })
                
                return {
                    "daily_pnl": daily_data,
                    "coin_performance": coin_performance,
                    "updated_at": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error getting analytics summary: {e}")
            return {"error": str(e)}
    
    def _is_cache_valid(self, key: str) -> bool:
        """Check if cached data is still valid"""
        if key not in self.cache:
            return False
        
        cached_time = self.cache[key]["timestamp"]
        return (datetime.now() - cached_time).seconds < self.cache_timeout
    
    def _cache_data(self, key: str, data: Any):
        """Cache data with timestamp"""
        self.cache[key] = {
            "data": data,
            "timestamp": datetime.now()
        } 