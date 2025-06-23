# σ₂: System Patterns

_v1.0 | Created: 2025-01-08 19:27:00 | Updated: 2025-01-08 19:27:00_
_Π: INITIALIZING | Ω: PLAN_

## 🏛️ Architecture Overview

### Core Architecture Pattern: **Layered AI-Trading System**

```
┌─────────────────┐
│   UI Layer      │ (Future: React DApp)
├─────────────────┤
│ Strategy Layer  │ ← AlloraNetwork + Hyperbolic AI
├─────────────────┤
│ Trading Layer   │ ← OrderManager + ExchangeWrapper
├─────────────────┤
│ Data Layer      │ ← DatabaseManager + Analytics
├─────────────────┤
│ Infrastructure  │ ← HyperLiquid SDK + Environment
└─────────────────┘
```

## 🧩 Component Architecture

### A₁: AI Decision Engine (`AlloraMind`)

**Pattern**: Strategy + Observer + Command

- **Primary**: Coordinates AI predictions and trade decisions
- **Dependencies**: OrderManager, DatabaseManager, HyperbolicReviewer
- **Key Methods**: `generate_signal()`, `open_trade()`, `monitor_positions()`
- **Decision Flow**: Prediction → Validation → Execution

### A₂: Order Management (`OrderManager`)

**Pattern**: Facade + Factory

- **Primary**: Abstracts HyperLiquid exchange operations
- **Responsibilities**: Order creation, position management, risk controls
- **Size Management**: Coin-specific precision handling
- **Risk Controls**: Leverage limits, minimum order values

### A₃: Trade Validation (`HyperbolicReviewer` + `AdaptiveThresholdCalculator`)

**Pattern**: Validator + Chain of Responsibility + Strategy

- **Primary**: Multi-AI validation with adaptive threshold optimization
- **Validation Systems**: Hyperbolic AI + OpenRouter AI with weighted scoring
- **Adaptive Logic**: Historical performance learning + market condition awareness
- **Threshold Management**: Dynamic thresholds (0.25-0.85) with safety bounds
- **Sprint 1.2 Enhancement**: Advanced threshold calculation with 7-day performance analysis

### A₄: Strategy Framework (`custom_strategy`)

**Pattern**: Strategy + Template Method

- **Primary**: Extensible trading strategy implementation
- **Current**: Basic signal confirmation and enhancement
- **Future**: Multi-strategy portfolio management

### A₅: Performance Analytics (`PerformanceAnalyzer`)

**Pattern**: Observer + Decorator

- **Primary**: Real-time performance tracking and analysis
- **Metrics**: Volatility correlation, prediction accuracy
- **Reporting**: Condition-based analysis and market insights

## 🔗 Integration Patterns

### I₁: AI Integration Pattern

```
AlloraNetwork API → Signal Generation → Multi-AI Validation → Adaptive Threshold → Trade Execution
                                      ↗ Hyperbolic AI ↘
                                                       → Weighted Score → Historical Adjustment
                                      ↗ OpenRouter AI ↗                → Market Condition Adjustment
```

- **Reliability**: Retry mechanisms, fallback strategies, dual AI redundancy
- **Validation**: Sprint 1.2 weighted scoring system with adaptive thresholds
- **Learning**: Historical performance analysis (7-day lookback)
- **Adaptation**: Market condition awareness (5 states: NORMAL, HIGH_VOLATILITY, TRENDING, etc.)
- **Safety**: Bounded thresholds (0.25-0.85) with comprehensive testing

### I₂: Data Flow Pattern

```
Market Data → AI Prediction → Strategy Filter → Risk Assessment → Order Execution → Performance Tracking
```

- **Persistence**: SQLite for trade history and analysis
- **Real-time**: Continuous position monitoring
- **Analytics**: Post-trade performance correlation

### I₃: Error Handling Pattern

**Pattern**: Circuit Breaker + Retry + Graceful Degradation

- **API Failures**: Max 3 retries with exponential backoff
- **Position Safety**: Automatic position monitoring on failures
- **Data Integrity**: Database transaction safety

## 🏗️ Design Decisions

### D₁: **Adaptive AI Architecture**

**Decision**: Separate prediction (Allora) and multi-AI validation (Hyperbolic + OpenRouter)
**Enhancement (Sprint 1.2)**: Added adaptive threshold optimization with historical learning
**Rationale**: Risk reduction, validation redundancy, performance-based optimization, market awareness
**Trade-offs**: Increased complexity vs. significantly improved decision quality
**Results**: Expected +150% execution rate improvement with maintained quality

### D₂: **HyperLiquid SDK Integration**

**Decision**: Direct SDK usage vs. custom exchange abstraction
**Implementation**: Thin wrapper (`ExchangeWrapper`) over HyperLiquid SDK
**Benefits**: Full feature access, reduced maintenance overhead

### D₃: **SQLite for Data Persistence**

**Decision**: Local SQLite vs. cloud database
**Rationale**: Performance, privacy, future IPFS migration readiness
**Evolution**: Planned migration to decentralized storage

### D₄: **Real-time Position Monitoring**

**Decision**: Continuous monitoring vs. interval-based checks
**Implementation**: Hybrid approach - continuous for critical operations
**Performance**: Balanced responsiveness with API rate limits

## 🔄 Architectural Evolution

### Phase 1: Python Foundation ✅

- Core trading functionality
- AI integration framework
- Risk management basics

### Phase 2: Enhanced Analytics 🔧

- Advanced performance tracking
- Multi-strategy support
- Improved risk modeling

### Phase 3: Platform Migration 🚧

- Node.js backend transition
- React DApp development
- HyperLiquid EVM integration

### Phase 4: Decentralization 🌟

- IPFS data layer
- Smart contract automation
- Distributed governance

## 🎯 Sprint 1.2: Advanced Patterns

### P₁: **Adaptive Threshold Pattern**

**Pattern**: Strategy + Observer + Historical Analysis

```
Current Trade Request → AdaptiveThresholdCalculator
                     ↗ Volatility Analysis
                     ↗ Historical Performance (7-day)
                     ↗ Market Condition Assessment
                     ↘ Dynamic Threshold (0.25-0.85)
```

**Components**:

- `AdaptiveThresholdCalculator`: Core threshold computation engine
- `analyze_recent_performance()`: Historical data analysis
- `get_threshold_explanation()`: Debugging and transparency
- Safety bounds and market condition mapping

### P₂: **Weighted Validation Pattern**

**Pattern**: Composite + Strategy + Chain of Responsibility

```
Validation Request → Dynamic Weight Calculator → Weighted Score
                  ↗ Hyperbolic AI (weight: 0.4-0.6)
                  ↗ OpenRouter AI (weight: 0.4-0.6)
                  ↘ Combined Score (0.0-1.0) vs Adaptive Threshold
```

**Benefits**:

- Flexible single/dual AI operation
- Performance-based weight adjustment
- Volatility-aware threshold adaptation

### P₃: **Historical Learning Pattern**

**Pattern**: Observer + Repository + Strategy

- **Data Collection**: 7-day trade performance tracking
- **Analysis**: Win rate, average P&L, token-specific performance
- **Adaptation**: Threshold adjustment (-0.05 to +0.1 range)
- **Safety**: Bounded adjustment with minimum trade count requirements

## 📐 Quality Attributes

### Reliability

- **AI Validation**: Multi-layer validation with adaptive thresholds
- **Error Recovery**: Comprehensive error handling and retry mechanisms
- **Data Integrity**: Transactional safety for all operations
- **Historical Robustness**: Performance-based threshold learning with safety bounds

### Performance

- **Response Time**: < 5s for AI prediction processing (+ threshold calculation)
- **Throughput**: Support for multiple concurrent token analysis
- **Scalability**: Modular design for easy horizontal scaling
- **Optimization**: Expected +150% execution rate with Sprint 1.2 enhancements

### Security

- **API Key Management**: Environment-based secure configuration
- **Risk Controls**: Multi-layer position and leverage protection with adaptive thresholds
- **Audit Trail**: Complete trade history and decision logging with threshold explanations
- **Bounded Safety**: Hard limits (0.25-0.85) prevent extreme threshold values
