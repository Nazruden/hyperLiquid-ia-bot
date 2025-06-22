# σ₃: Technical Context

_v1.0 | Created: 2025-01-08 19:27:00 | Updated: 2025-01-08 19:27:00_
_Π: INITIALIZING | Ω: PLAN_

## 🛠️ Technology Stack

### 🐍 Backend Runtime

- **Python**: 3.10+
- **Runtime Environment**: Standard Python interpreter
- **Package Management**: pip with requirements.txt
- **Virtual Environment**: Recommended (venv/conda)

### 📦 Core Dependencies

```python
# Trading & Blockchain
eth-account==0.10.0          # Ethereum account management
hyperliquid-python-sdk==0.9.0 # HyperLiquid exchange integration

# Configuration & Environment
python-dotenv==1.0.0         # Environment variable management

# Data Analysis & Processing
pandas==2.1.4                # Data manipulation and analysis
numpy==1.26.2                # Numerical computing

# Build Tools
setuptools==69.1.1           # Package building
wheel==0.42.0                # Package distribution
```

### 🔗 External APIs & Services

#### A₁: AlloraNetwork AI

- **Purpose**: Market prediction and inference
- **Endpoint**: `https://api.allora.network/ethereum-11155111`
- **Authentication**: API Key (`x-api-key` header)
- **Rate Limits**: Configurable timeout (default: 5s)
- **Data Format**: JSON with `network_inference_normalized` predictions

#### A₂: Hyperbolic AI

- **Purpose**: Trade validation and risk assessment
- **Models**: Support for various models including:
  - `deepseek-ai/DeepSeek-R1`
  - `deepseek-ai/DeepSeek-V3-0324`
- **Integration**: REST API for trade decision validation
- **Response**: Confidence scores, risk assessment, reasoning

#### A₃: HyperLiquid Exchange

- **SDK**: `hyperliquid-python-sdk==0.9.0`
- **Functions**: Trading, position management, market data
- **Network**: Mainnet/Testnet configurable
- **Authentication**: Ethereum account-based

## 🏗️ Architecture Components

### C₁: Core Trading Engine

```
core/
├── __init__.py
├── exchange.py         # ExchangeWrapper - HyperLiquid SDK abstraction
└── orders.py          # OrderManager - Trade execution and management
```

### C₂: AI Decision System

```
allora/
├── __init__.py
└── allora_mind.py     # AlloraMind - Main AI coordination engine
```

### C₃: Strategy Framework

```
strategy/
├── custom_strategy.py      # Extensible strategy implementation
├── hyperbolic_reviewer.py  # AI-powered trade validation
└── volatility_strategy.py  # Volatility-based trading logic
```

### C₄: Data & Analytics

```
database/
└── db_manager.py      # DatabaseManager - SQLite operations

analysis/
└── performance_analyzer.py # Real-time performance tracking
```

### C₅: Utilities & Configuration

```
utils/
├── __init__.py
├── constants.py       # System constants and configurations
├── env_loader.py      # Environment variable management
├── helpers.py         # Utility functions (pricing, rounding)
└── setup.py          # System initialization and configuration
```

## ⚙️ Environment Configuration

### 🔑 Required Environment Variables

```bash
# HyperLiquid Configuration
HYPERLIQUID_PRIVATE_KEY=<ethereum_private_key>
HYPERLIQUID_VAULT_ADDRESS=<vault_address>
HYPERLIQUID_BASE_URL=<api_endpoint>

# AI Service APIs
ALLORA_UPSHOT_KEY=<allora_api_key>
HYPERBOLIC_API_KEY=<hyperbolic_api_key>

# Trading Parameters
ALLOWED_AMOUNT_PER_TRADE=<usd_amount>
MAX_LEVERAGE=<leverage_multiplier>
PRICE_GAP_THRESHOLD=<percentage>
CHECK_FOR_TRADES_INTERVAL=<seconds>

# AlloraNetwork Topic Mapping
ALLORA_TOPICS=<json_mapping>
# Example: {"BTC": "topic_id_1", "ETH": "topic_id_2"}
```

### 📁 File Structure Standards

```
hyperLiquid-ia-bot/
├── main.py                    # Application entry point
├── requirements.txt           # Dependencies specification
├── README.md                  # Project documentation
├── .env                      # Environment configuration (not tracked)
├── memory-bank/              # RIPER framework memory system
│   ├── backups/             # Automated backups
│   ├── projectbrief.md      # σ₁: Requirements and overview
│   ├── systemPatterns.md    # σ₂: Architecture patterns
│   ├── techContext.md       # σ₃: Technical context (this file)
│   ├── activeContext.md     # σ₄: Current focus and context
│   ├── progress.md          # σ₅: Progress tracking
│   └── protection.md        # σ₆: Protection registry
├── core/                     # Core trading functionality
├── allora/                   # AI prediction system
├── strategy/                 # Trading strategies
├── database/                 # Data persistence
├── analysis/                 # Performance analytics
└── utils/                   # Utilities and helpers
```

## 🔧 Development Environment

### 🐳 Local Setup

```bash
# Clone and setup
git clone <repository>
cd hyperLiquid-ia-bot
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configuration
cp .env.example .env
# Edit .env with your API keys and settings

# Run
python main.py
```

### 🚀 Production Considerations

- **Security**: Environment-based API key management
- **Monitoring**: Database logging for all trades and decisions
- **Resilience**: Retry mechanisms for API failures
- **Performance**: Optimized for real-time trading operations

## 🔄 Integration Patterns

### I₁: Database Integration

- **Engine**: SQLite for local persistence
- **Schema**: Trade history, performance metrics, prediction accuracy
- **Future**: IPFS migration planned for decentralization

### I₂: API Integration Architecture

```python
# Pattern: Retry with exponential backoff
max_retries = 3
for attempt in range(max_retries):
    try:
        response = api_call()
        break
    except Exception as e:
        if attempt < max_retries - 1:
            time.sleep(2 ** attempt)
        else:
            handle_failure()
```

### I₃: Error Handling Strategy

- **API Failures**: Graceful degradation with logging
- **Network Issues**: Automatic retry with backoff
- **Data Validation**: Input validation at all integration points
- **State Recovery**: Automated position reconciliation

## 📊 Performance Characteristics

### ⚡ Response Times

- **AI Prediction**: < 5 seconds (AlloraNetwork API)
- **Trade Validation**: < 3 seconds (Hyperbolic AI)
- **Order Execution**: < 2 seconds (HyperLiquid)
- **Position Updates**: Real-time via SDK

### 📈 Scalability

- **Concurrent Tokens**: Optimized for 3-10 simultaneous tokens
- **API Rate Limits**: Respectful of service limitations
- **Memory Usage**: Efficient data structures for real-time operation
- **Database Growth**: Managed via periodic cleanup routines

## 🛡️ Security & Compliance

### 🔐 Security Measures

- **Private Key Management**: Environment-based, never logged
- **API Key Rotation**: Support for key updates without restart
- **Transaction Logging**: Complete audit trail
- **Error Sanitization**: Sensitive data removed from logs

### 📋 Compliance Considerations

- **Financial Regulations**: User responsibility for compliance
- **Data Privacy**: Local data storage, minimal external sharing
- **Risk Disclosure**: Clear documentation of trading risks
- **Audit Trail**: Complete transaction and decision history
