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

#### A₃: OpenRouter AI

- **Purpose**: Secondary AI validation for trade decisions
- **Models**: Support for multiple models including:
  - `anthropic/claude-3-sonnet`
  - `openai/gpt-4`
- **Integration**: REST API with OpenAI-compatible interface
- **Sprint 1.2**: Integrated with weighted validation scoring system

#### A₄: HyperLiquid Exchange

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
├── custom_strategy.py        # Extensible strategy implementation
├── hyperbolic_reviewer.py    # AI-powered trade validation
├── openrouter_reviewer.py    # OpenRouter AI validation
├── adaptive_thresholds.py    # Sprint 1.2: Advanced threshold optimization
└── volatility_strategy.py    # Volatility-based trading logic
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
OPENROUTER_API_KEY=<openrouter_api_key>
OPENROUTER_MODEL=<model_name>

# Trading Parameters
ALLOWED_AMOUNT_PER_TRADE=<usd_amount>
MAX_LEVERAGE=<leverage_multiplier>
PRICE_GAP_THRESHOLD=<percentage>
CHECK_FOR_TRADES_INTERVAL=<seconds>

# AlloraNetwork Topic Mapping
ALLORA_TOPICS=<json_mapping>
# Example: {"BTC": "topic_id_1", "ETH": "topic_id_2"}

# Sprint 1.1 & 1.2: Advanced Validation Configuration
VALIDATION_SCORE_THRESHOLD=<float>         # Base validation threshold (0.0-1.0)
ADAPTIVE_THRESHOLDS=<boolean>              # Enable adaptive threshold system
HYPERBOLIC_BASE_WEIGHT=<float>             # Hyperbolic AI weight (0.0-1.0)
OPENROUTER_BASE_WEIGHT=<float>             # OpenRouter AI weight (0.0-1.0)
VOLATILITY_THRESHOLD_LOW=<float>           # Low volatility threshold
VOLATILITY_THRESHOLD_HIGH=<float>          # High volatility threshold

# Sprint 1.2: Advanced Adaptive Thresholds
ADAPTIVE_MIN_THRESHOLD=<float>             # Minimum threshold bound (0.25)
ADAPTIVE_MAX_THRESHOLD=<float>             # Maximum threshold bound (0.85)
HISTORICAL_PERFORMANCE_WEIGHT=<float>      # Historical performance influence
MARKET_CONDITION_WEIGHT=<float>            # Market condition adjustment weight
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

## 🎯 Sprint 1.2: Advanced Technical Components

### S₁: AdaptiveThresholdCalculator Architecture

```python
class AdaptiveThresholdCalculator:
    """
    Advanced threshold optimization with machine learning-like capabilities
    """
    def __init__(self):
        self.base_threshold = float(os.getenv('VALIDATION_SCORE_THRESHOLD', '0.5'))
        self.min_threshold = 0.25  # Safety lower bound
        self.max_threshold = 0.85  # Safety upper bound
        self.db = DatabaseManager()

    def get_threshold(self, volatility=None, token=None, market_condition='NORMAL'):
        # Multi-factor threshold calculation

    def _adjust_for_volatility(self, base_threshold, volatility):
        # Dynamic volatility-based adjustments

    def _adjust_for_historical_performance(self, base_threshold, token):
        # 7-day performance learning

    def analyze_recent_performance(self, token, days=7):
        # Comprehensive performance analysis
```

### S₂: Enhanced Validation Flow

```python
# Sprint 1.2 Advanced Validation Pipeline
validation_score = calculate_validation_score(hyperbolic_review, openrouter_review, volatility)
adaptive_threshold = adaptive_calculator.get_threshold(volatility, token, market_condition)
decision = validation_score >= adaptive_threshold

# Debugging and transparency
explanation = adaptive_calculator.get_threshold_explanation(volatility, token, market_condition)
```

### S₃: Market Condition Detection

**Supported Market States**:

- `NORMAL`: Standard market conditions
- `HIGH_VOLATILITY`: Increased volatility periods
- `LOW_VOLATILITY`: Calm market periods
- `TRENDING`: Strong directional movement
- `SIDEWAYS`: Range-bound trading

**Threshold Adjustments**:

```python
adjustments = {
    'HIGH_VOLATILITY': -0.1,  # More permissive
    'NORMAL': 0.0,            # No change
    'LOW_VOLATILITY': 0.05,   # More strict
    'TRENDING': -0.05,        # Slightly permissive
    'SIDEWAYS': 0.03          # Slightly strict
}
```

### S₄: Testing Infrastructure

**Test Coverage**: 25 comprehensive unit tests

- **AdaptiveThresholds**: 12 tests (new)
- **ValidationScoring**: 13 tests (updated)

**Test Categories**:

- Volatility adjustment scenarios
- Historical performance simulation
- Market condition responses
- Safety bounds validation
- Integration testing

## 🔄 Integration Patterns

### I₁: Database Integration

- **Engine**: SQLite for local persistence
- **Schema**: Trade history, performance metrics, prediction accuracy
- **Sprint 1.2**: Enhanced with historical performance queries
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
