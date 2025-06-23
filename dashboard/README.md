# 🖥️ HyperLiquid AI Trading Bot Dashboard

Professional web interface for monitoring and controlling your AI trading bot with real-time data streaming and modern UI.

## 🎯 Overview

The HyperLiquid Dashboard provides a comprehensive web-based interface for:

- **🔄 Real-time Monitoring**: Live metrics via WebSocket streaming
- **🤖 Bot Lifecycle Control**: Start, stop, restart your trading bot
- **📊 Performance Analytics**: Interactive charts and trend analysis
- **📋 Trade Management**: Complete transaction history with filtering
- **📱 Mobile-First Design**: Responsive interface for all devices
- **🌙 Modern UI**: Dark/light themes with TailwindCSS v4.1

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                 HyperLiquid Dashboard System                 │
├─────────────────┬─────────────────┬─────────────────────────┤
│   Trading Bot   │  FastAPI Backend │     React Frontend      │
│   (main.py)     │    (Port 8000)   │      (Port 5173)        │
│                 │                  │                         │
│ ✓ AI Trading    │ ✓ WebSocket Hub  │ ✓ Real-time UI          │
│ ✓ Risk Mgmt     │ ✓ Bot Controls   │ ✓ Interactive Charts    │
│ ✓ SQLite DB     │ ✓ Data Service   │ ✓ Mobile Responsive     │
│ ✓ Predictions   │ ✓ Health Checks  │ ✓ Modern Design         │
│ ✓ Strategies    │ ✓ 15+ Endpoints  │ ✓ Theme System          │
└─────────────────┴─────────────────┴─────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+** with the trading bot configured
- **Node.js 18+** with npm
- **Active Trading Bot** (main.py) for data source

### One-Command Startup

```bash
# From project root - starts everything
python scripts/start_all.py
```

### Manual Startup

```bash
# Terminal 1: Backend API
cd dashboard
python start_server.py

# Terminal 2: Frontend UI
cd dashboard/frontend
npm install  # First time only
npm run dev

# Terminal 3: Trading Bot (data source)
cd ../..
python main.py
```

### Access Points

Once running:

- **📊 Main Dashboard**: http://localhost:5173
- **🔧 API Documentation**: http://localhost:8000/api/docs
- **💓 Health Check**: http://localhost:8000/health
- **🔌 WebSocket Test**: ws://localhost:8000/ws

## 📊 Dashboard Features

### 🤖 Bot Control Panel

- **Status Monitoring**: Real-time bot state (running/stopped/error)
- **Lifecycle Management**: Start, stop, restart controls with confirmations
- **Uptime Tracking**: Monitor how long the bot has been running
- **Last Activity**: Timestamp of most recent bot action

### 📈 Live Metrics Grid

Real-time cards displaying:

- **💰 Account Balance**: Current USD value with trend indicators
- **🎯 Active Positions**: Number of open positions and exposure
- **📊 24h P&L**: Profit/loss with percentage change and trend arrows
- **🧠 AI Accuracy**: Prediction accuracy percentage from AI models

### 📊 Performance Charts

Interactive visualizations:

- **P&L Timeline**: Line chart showing profit/loss over time with zoom/pan
- **Prediction Accuracy**: AI model performance trends
- **Volatility Analysis**: Market volatility correlation charts
- **Volume Distribution**: Trading volume by time periods

### 📋 Trade History

Comprehensive transaction table:

- **Sortable Columns**: Timestamp, symbol, side, price, quantity, P&L
- **Advanced Filtering**: Date range, symbol, trade type, minimum P&L
- **Real-time Search**: Text search across all trade data
- **Smart Pagination**: Efficient handling of large datasets
- **Export Options**: CSV download of filtered results

### 🧠 AI Insights

Intelligence analytics:

- **Recent Predictions**: AlloraNetwork forecasts vs actual outcomes
- **Model Performance**: Hyperbolic AI validation accuracy metrics
- **Risk Assessment**: Current position risk analysis
- **Strategy Effectiveness**: Performance breakdown by strategy type

## 🔧 Technical Specifications

### Backend (FastAPI)

```yaml
Framework: FastAPI 0.104+
WebSocket: Real-time bidirectional communication
Database: SQLite (read-only access to trades.db)
Authentication: API key based (configurable)
CORS: Configured for development and production
Logging: Structured logging with multiple levels
```

### Frontend (React)

```yaml
Framework: React 19.1 + TypeScript
Build Tool: Vite 6.3.5 (ultra-fast builds)
Styling: TailwindCSS v4.1.10 (latest with Oxide engine)
Charts: Recharts 2.15.4 (responsive trading charts)
Icons: Lucide React 0.522.0 (modern icon set)
HTTP Client: Axios 1.10.0 (API communication)
```

### API Endpoints

The dashboard provides 15+ RESTful endpoints:

```bash
# Bot Control
POST /api/bot/start          # Start trading bot
POST /api/bot/stop           # Stop trading bot
POST /api/bot/restart        # Restart trading bot
GET  /api/bot/status         # Get current bot status

# Trading Data
GET  /api/trades             # Get trade history with pagination
GET  /api/positions          # Get current positions
GET  /api/balance            # Get account balance
GET  /api/performance        # Get performance metrics

# Analytics
GET  /api/analytics/summary      # Overall performance summary
GET  /api/analytics/predictions  # AI prediction accuracy
GET  /api/analytics/volatility   # Volatility analysis
GET  /api/analytics/correlation  # Price correlation metrics

# System
GET  /health                 # System health check
GET  /                       # API information
```

### WebSocket Events

Real-time streaming events:

```json
{
  "type": "bot_status",
  "data": {
    "status": "running",
    "uptime": 3600,
    "last_trade": "2025-06-23T12:30:00Z"
  }
}

{
  "type": "live_metrics",
  "data": {
    "balance": 12450.67,
    "positions": 3,
    "pnl_24h": 245.67,
    "accuracy": 73.2
  }
}

{
  "type": "new_trade",
  "data": {
    "id": "trade_123",
    "symbol": "BTC",
    "side": "buy",
    "price": 45230.50,
    "quantity": 0.1,
    "timestamp": "2025-06-23T12:30:00Z"
  }
}
```

## 🛠️ Development

### Development Setup

```bash
# Backend development
cd dashboard/backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r ../requirements.txt
uvicorn app:app --reload --port 8000

# Frontend development
cd dashboard/frontend
npm install
npm run dev  # Starts on port 5173 with hot reload
```

### Build for Production

```bash
# Frontend production build
cd dashboard/frontend
npm run build
npm run preview  # Test production build

# Backend production
uvicorn dashboard.backend.app:app --host 0.0.0.0 --port 8000 --workers 4
```

### Code Quality

```bash
# Frontend linting and type checking
npm run lint
npm run build  # Includes TypeScript compilation

# Backend testing
python -m pytest dashboard/backend/tests/
```

## 🔒 Security & Configuration

### Environment Variables

Add to your `.env` file:

```bash
# Dashboard Configuration (optional)
DASHBOARD_ENABLED=True
DASHBOARD_HOST=localhost
DASHBOARD_PORT=8000
FRONTEND_PORT=5173
ENABLE_WEBSOCKET=True
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

### Security Features

- **Read-Only Database**: Dashboard cannot modify trading data
- **CORS Protection**: Configurable cross-origin policies
- **Input Validation**: All user inputs sanitized
- **Process Isolation**: Dashboard failures don't affect trading
- **Audit Logging**: All bot control actions logged

## 🐛 Troubleshooting

### Common Issues

**Frontend not connecting to backend:**

```bash
# Check if backend is running
curl http://localhost:8000/health

# Check WebSocket connection
wscat -c ws://localhost:8000/ws
```

**PostCSS warning (non-critical):**

```
A PostCSS plugin did not pass the 'from' option to postcss.parse
```

This is a known issue with TailwindCSS v4.1 and doesn't affect functionality.

**Port conflicts:**

```bash
# Check what's using ports
netstat -ano | findstr :8000
netstat -ano | findstr :5173

# Kill processes if needed
taskkill /PID <pid> /F
```

### Performance Optimization

- **WebSocket Connections**: Limited to prevent resource exhaustion
- **Database Queries**: Optimized with indexing and pagination
- **Frontend Bundle**: Code splitting and lazy loading implemented
- **Memory Usage**: Efficient data structures and cleanup

## 📚 Additional Resources

- **[API Documentation](http://localhost:8000/api/docs)**: Interactive API explorer
- **[User Guide](USER_GUIDE.md)**: Step-by-step usage instructions
- **[Deployment Guide](DEPLOYMENT.md)**: Production deployment instructions
- **[Troubleshooting](TROUBLESHOOTING.md)**: Common issues and solutions

## 🎯 Performance Metrics

Current dashboard performance targets:

- **Page Load Time**: < 2 seconds initial load
- **WebSocket Latency**: < 500ms for real-time updates
- **API Response Time**: < 200ms for data queries
- **Build Time**: < 5 seconds with TailwindCSS v4.1
- **Memory Usage**: < 100MB for frontend, < 200MB for backend

---

_Built with ❤️ for the HyperLiquid AI Trading Bot ecosystem_
