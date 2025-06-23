"""
HyperLiquid AI Trading Bot Dashboard - FastAPI Backend
Main application entry point with WebSocket support and API routing
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from dashboard.backend.websocket_manager import WebSocketManager
from dashboard.backend.bot_controller import BotController
from dashboard.backend.data_service import DataService
from dashboard.backend.routers import bot_control, analytics, trades

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI application
app = FastAPI(
    title="HyperLiquid AI Trading Bot Dashboard",
    description="Real-time dashboard for monitoring and controlling the HyperLiquid AI Trading Bot",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Configure CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:4000"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize managers and services
websocket_manager = WebSocketManager()
bot_controller = BotController()
data_service = DataService()

# Include API routers
app.include_router(bot_control.router, prefix="/api/bot", tags=["Bot Control"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(trades.router, prefix="/api/trades", tags=["Trades"])

@app.on_event("startup")
async def startup_event():
    """Initialize services on application startup"""
    logger.info("🚀 Dashboard backend starting up...")
    
    # Initialize data service
    await data_service.initialize()
    
    # Start background tasks
    asyncio.create_task(websocket_manager.broadcast_loop())
    
    logger.info("✅ Dashboard backend initialized successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown"""
    logger.info("🛑 Dashboard backend shutting down...")
    
    # Cleanup WebSocket connections
    await websocket_manager.disconnect_all()
    
    logger.info("✅ Dashboard backend shutdown complete")

@app.get("/")
async def root():
    """Root endpoint with basic API information"""
    return {
        "name": "HyperLiquid AI Trading Bot Dashboard API",
        "version": "1.0.0",
        "status": "operational",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "health": "/health",
            "websocket": "/ws",
            "bot_control": "/api/bot",
            "analytics": "/api/analytics",
            "trades": "/api/trades",
            "docs": "/api/docs"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    try:
        # Check data service connectivity
        db_status = await data_service.health_check()
        
        # Check bot controller status
        bot_status = bot_controller.get_status()
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "services": {
                "database": "operational" if db_status else "error",
                "bot_controller": bot_status["status"],
                "websocket_connections": len(websocket_manager.active_connections)
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
        )

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time data streaming"""
    client_id = await websocket_manager.connect(websocket)
    logger.info(f"🔌 WebSocket client connected: {client_id}")
    
    try:
        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connection",
            "status": "connected",
            "client_id": client_id,
            "timestamp": datetime.now().isoformat()
        })
        
        # Send initial data snapshot
        initial_data = await data_service.get_dashboard_snapshot()
        await websocket.send_json({
            "type": "snapshot",
            "data": initial_data,
            "timestamp": datetime.now().isoformat()
        })
        
        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Wait for client messages (ping/pong for keep-alive)
                data = await websocket.receive_text()
                message = json.loads(data)
                
                if message.get("type") == "ping":
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": datetime.now().isoformat()
                    })
                
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"WebSocket message handling error: {e}")
                await websocket.send_json({
                    "type": "error",
                    "message": str(e),
                    "timestamp": datetime.now().isoformat()
                })
                
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
    finally:
        websocket_manager.disconnect(client_id)
        logger.info(f"🔌 WebSocket client disconnected: {client_id}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 