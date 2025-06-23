# HyperLiquid AI Trading Bot

## Overview

An advanced AI-powered trading bot for the HyperLiquid decentralized exchange. The bot leverages predictions from AlloraNetwork's AI models and validates trades using flexible AI validation services (Hyperbolic AI and/or OpenRouter) for intelligent, automated trading decisions.

## ✨ Key Features

- **🤖 AI Predictions**: Uses AlloraNetwork for market predictions
- **🛡️ Flexible AI Validation**: Choose between Hyperbolic AI, OpenRouter, or both
- **🎯 Dual Validation Mode**: Enhanced safety with consensus validation when both AI services are configured
- **📊 Custom Strategies**: Supports user-defined trading strategies
- **💾 Database Logging**: Complete trade history in local SQLite database
- **⚙️ Environment Configuration**: Easy setup via `.env` file
- **🔒 Risk Management**: Multiple layers of position and leverage protection
- **🖥️ Web Dashboard**: Professional real-time monitoring interface with charts and controls

## 🎛️ AI Validation Modes

### Single AI Service Mode

Configure **either** Hyperbolic AI **or** OpenRouter:

- ✅ **Cost-effective**: Use only one AI service
- ⚡ **Faster decisions**: Single validation step
- 🎯 **Flexible**: Choose your preferred AI provider

### Dual AI Consensus Mode

Configure **both** Hyperbolic AI **and** OpenRouter:

- 🛡️ **Enhanced safety**: Both AIs must approve trades
- 🤝 **Consensus validation**: Higher confidence in decisions
- 🔄 **Redundancy**: Backup if one service fails
- 📊 **Comparative analysis**: See reasoning from both AIs

## 🔧 Requirements

- **Python**: 3.10 or higher
- **HyperLiquid Account**: Testnet or mainnet account with funds
- **API Keys**: AlloraNetwork (required) + at least one AI service

## 🚀 Quick Setup

### 1. Clone and Install

```bash
git clone <repository-url>
cd hyperLiquid-ia-bot
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy the example configuration
cp .env.example .env

# Edit .env with your API keys and settings
nano .env  # or use your preferred editor
```

### 3. Start Trading Bot + Dashboard

```bash
# Option A: Complete system (Bot + Dashboard)
python scripts/start_all.py

# Option B: Just the trading bot
python main.py

# Option C: Just the dashboard
cd dashboard && python start_server.py
cd dashboard/frontend && npm run dev
```

### 4. Required Configuration

#### 🔑 Essential API Keys

```bash
# HyperLiquid (Required)
HL_SECRET_KEY=your_ethereum_private_key_here
ALLORA_UPSHOT_KEY=your_allora_api_key_here

# AI Validation (At least one required)
HYPERBOLIC_API_KEY=your_hyperbolic_api_key_here    # Optional
OPENROUTER_API_KEY=your_openrouter_api_key_here    # Optional
```

#### 🛡️ Safety Settings

```bash
# Start with testnet for testing
MAINNET=False

# Conservative trading parameters
ALLOWED_AMOUNT_PER_TRADE=500  # $500 per trade
MAX_LEVERAGE=5                # 5x maximum leverage
PRICE_GAP=0.25               # 0.25% minimum price difference
```

### 5. Access Your Dashboard

Once started, access the web interface:

- **🖥️ Dashboard**: http://localhost:5173
- **📊 API Documentation**: http://localhost:8000/api/docs
- **🔍 Health Check**: http://localhost:8000/health

### 6. Run the Bot

```bash
python main.py
```

## 🖥️ Web Dashboard Interface

### Overview

Professional web interface for real-time monitoring and control of your HyperLiquid AI Trading Bot. Built with FastAPI backend and React frontend for optimal performance.

### Key Dashboard Features

- **📊 Real-time Metrics**: Live account balance, P&L, positions, and AI prediction accuracy
- **🤖 Bot Control**: Start, stop, restart your trading bot from the web interface
- **📈 Performance Charts**: Interactive charts showing trading performance over time
- **📋 Trade History**: Complete trade log with filtering and search capabilities
- **🔔 Live Updates**: WebSocket-powered real-time data streaming
- **📱 Mobile Responsive**: Full functionality on desktop, tablet, and mobile
- **🌙 Dark/Light Theme**: Modern UI with automatic theme switching
- **⚡ TailwindCSS v4.1**: Latest styling framework for optimal performance

### Dashboard Architecture

```
┌─────────────────────────────────────────────────────────┐
│                 HyperLiquid Dashboard                    │
├─────────────────┬─────────────────┬─────────────────────┤
│   Trading Bot   │  FastAPI Backend │  React Frontend     │
│   (main.py)     │    (Port 8000)   │   (Port 5173)       │
│                 │                  │                     │
│ ✓ AI Trading    │ ✓ WebSocket API  │ ✓ Real-time UI      │
│ ✓ Risk Mgmt     │ ✓ Bot Controls   │ ✓ Interactive Charts│
│ ✓ SQLite DB     │ ✓ Data Service   │ ✓ Mobile Ready      │
│ ✓ Predictions   │ ✓ Health Checks  │ ✓ Modern Design     │
└─────────────────┴─────────────────┴─────────────────────┘
```

### Quick Dashboard Setup

```bash
# Prerequisites (first time only)
cd dashboard/frontend
npm install

# Start complete system
python scripts/start_all.py

# Or start components separately
# Terminal 1: Backend
cd dashboard && python start_server.py

# Terminal 2: Frontend
cd dashboard/frontend && npm run dev

# Terminal 3: Trading Bot
python main.py
```

### Dashboard URLs

- **Main Dashboard**: http://localhost:5173
- **API Documentation**: http://localhost:8000/api/docs
- **WebSocket Endpoint**: ws://localhost:8000/ws
- **Health Check**: http://localhost:8000/health

### Dashboard Screenshots

The dashboard provides:

- **Bot Status Panel**: Control and monitor bot lifecycle
- **Live Metrics Grid**: Real-time trading performance
- **Performance Charts**: Visual analytics and trends
- **Trade History Table**: Complete transaction log
- **AI Insights**: Prediction accuracy and model performance

📚 **Detailed Documentation**: See [Dashboard Guide](dashboard/README.md) for complete setup and usage instructions.

## 📋 Complete Configuration Guide

### 🏦 HyperLiquid Exchange Setup

```bash
# Required: Your Ethereum private key
HL_SECRET_KEY=your_private_key_without_0x_prefix

# Optional: Account addresses (auto-derived if not specified)
HL_ACCOUNT_ADDRESS=0x1234567890123456789012345678901234567890
HL_MASTER_ADDRESS=0x1234567890123456789012345678901234567890

# Optional: Vault for fund management
HL_VAULT=0x1234567890123456789012345678901234567890

# Network selection
MAINNET=False  # Use True for live trading (start with False!)
```

### 🤖 AI Services Configuration

#### AlloraNetwork (Required)

```bash
ALLORA_UPSHOT_KEY=your_allora_api_key
BTC_TOPIC_ID=14  # Bitcoin predictions
ETH_TOPIC_ID=13  # Ethereum predictions
```

#### Hyperbolic AI (Optional)

```bash
HYPERBOLIC_API_KEY=your_hyperbolic_api_key
# Supports models: deepseek-ai/DeepSeek-R1, deepseek-ai/DeepSeek-V3-0324
```

#### OpenRouter (Optional)

```bash
OPENROUTER_API_KEY=your_openrouter_api_key
OPENROUTER_MODEL=anthropic/claude-3-sonnet  # Default model

# Popular model options:
# - anthropic/claude-3-sonnet    (balanced performance)
# - openai/gpt-4-turbo          (comprehensive analysis)
# - google/gemini-pro           (efficient)
# - meta-llama/llama-3.1-70b    (cost-effective)
```

### ⚙️ Trading Parameters

```bash
# Risk management
PRICE_GAP=0.25                    # Minimum 0.25% price difference
ALLOWED_AMOUNT_PER_TRADE=500      # $500 maximum per trade
MAX_LEVERAGE=5                    # 5x maximum leverage

# Timing
CHECK_FOR_TRADES=300              # Check every 5 minutes
VOLATILITY_THRESHOLD=0.02         # 2% volatility threshold

# Advanced thresholds
CONFIDENCE_THRESHOLD=70           # 70% minimum AI confidence
MAXIMUM_RISK_THRESHOLD=4          # Maximum risk score 4/10
```

## 🔗 Getting API Keys

### HyperLiquid

1. Visit [HyperLiquid](https://app.hyperliquid.xyz/)
2. Create account and complete verification
3. Generate Ethereum private key for trading
4. **Start with testnet** for safe testing

### AlloraNetwork

1. Access AlloraNetwork dashboard
2. Generate API key for predictions
3. Note topic IDs for your desired tokens

### Hyperbolic AI (Optional)

1. Sign up at [Hyperbolic](https://hyperbolic.xyz/)
2. Generate API key
3. Choose from available DeepSeek models

### OpenRouter (Optional)

1. Register at [OpenRouter](https://openrouter.ai/)
2. Create API key
3. Select preferred AI model

## 🛡️ Safety Recommendations

### 🚦 Testing Phase

- ✅ **Start with testnet**: Set `MAINNET=False`
- ✅ **Small amounts**: Use minimal `ALLOWED_AMOUNT_PER_TRADE`
- ✅ **Low leverage**: Start with `MAX_LEVERAGE=2` or `3`
- ✅ **Monitor closely**: Watch first few trades manually

### 🔒 Production Safety

- ✅ **Gradual scaling**: Increase amounts slowly
- ✅ **Regular monitoring**: Check bot performance daily
- ✅ **Backup strategy**: Have manual override procedures
- ✅ **API limits**: Monitor rate limits on AI services

## 📊 Validation Logic

### Single AI Service

When only one AI service is configured:

```
AlloraNetwork Prediction → Single AI Validation → Trade Execution
```

### Dual AI Consensus

When both AI services are configured:

```
AlloraNetwork Prediction → Hyperbolic AI + OpenRouter → Consensus Required → Trade Execution
```

**Consensus Rules:**

- ✅ **Both approve**: Trade executes
- ❌ **Either rejects**: Trade rejected
- ❌ **Both fail**: No trade execution
- 📊 **Individual reasoning**: See each AI's analysis

## 📈 Supported Features

### Trading

- **Multi-token support**: BTC, ETH (easily extensible)
- **Automated position management**: Entry, profit targets, stop-loss
- **Real-time monitoring**: Continuous position tracking
- **Risk controls**: Leverage limits, position sizing

### Analytics

- **Performance tracking**: Trade history and analysis
- **Prediction accuracy**: AI model performance metrics
- **Volatility correlation**: Market condition analysis
- **Database logging**: Complete audit trail

### Strategy Framework

- **Custom strategies**: Extensible strategy system
- **Signal confirmation**: Multi-layer validation
- **Market condition filters**: Volatility-based filtering

## 🚀 Quick Commands Reference

### System Management

```bash
# Complete System (Recommended)
python scripts/start_all.py          # Start bot + dashboard

# Individual Components
python main.py                       # Trading bot only
python scripts/start_dashboard.py    # Dashboard only
python scripts/health_check.py       # System diagnostics

# Dashboard Development
cd dashboard/frontend && npm run dev  # Frontend dev server
cd dashboard && python start_server.py  # Backend dev server
```

### First Time Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt
cd dashboard/frontend && npm install

# 2. Configure environment
cp .env.example .env
# Edit .env with your API keys

# 3. Run health check
python scripts/health_check.py

# 4. Start everything
python scripts/start_all.py
```

### Access Points

Once running, access these URLs:

- **🖥️ Main Dashboard**: http://localhost:5173
- **📊 Trading Performance**: Real-time charts and metrics
- **🤖 Bot Controls**: Start/stop/restart from web interface
- **📋 Trade History**: Complete transaction log with filters
- **🔧 API Documentation**: http://localhost:8000/api/docs

## 🔄 Future Roadmap

- **Node.js Migration**: Backend transition for enhanced performance
- **IPFS Integration**: Decentralized database storage
- **Smart Contracts**: HyperLiquid EVM blockchain integration
- **React DApp**: Modern web interface development

## 📝 License

This project is licensed under the MIT License.

## 🤝 Contributing

Contributions welcome! Please fork the repository and submit a pull request.

## 📞 Support

For questions or support, please contact the project maintainer or open an issue.

---

**⚠️ Disclaimer**: Trading cryptocurrencies involves substantial risk. This bot is for educational and research purposes. Always test thoroughly and never trade with funds you cannot afford to lose.
