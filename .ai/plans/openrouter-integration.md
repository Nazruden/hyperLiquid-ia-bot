# 🔗 OpenRouter Integration Plan

**Project**: HyperLiquid AI Trading Bot  
**Plan Version**: v1.0  
**Created**: 2025-01-08  
**Status**: Ready for Execution  
**Estimated Time**: 2-3 hours

## 🎯 Project Overview

**Objective**: Add OpenRouter AI as a third validation layer alongside existing AlloraNetwork (predictions) and Hyperbolic AI (validation) systems.

**Approach**: Minimal, clean integration following established patterns  
**Complexity**: Low - straightforward service addition  
**Timeline**: Single development session (~2-3 hours)

## 📝 Implementation Plan

### **Step 1: Environment Configuration** _(15 minutes)_

**Files to Modify:**

- `utils/env_loader.py`
- `.env` (user configuration)

**Changes:**

```python
# Add to required_vars list
'OPENROUTER_API_KEY'

# Add to config dictionary
"openrouter_api_key": os.getenv('OPENROUTER_API_KEY'),
"openrouter_model": os.getenv('OPENROUTER_MODEL', 'anthropic/claude-3-sonnet'),
```

**Environment Variables:**

```bash
# .env additions
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_MODEL=anthropic/claude-3-sonnet  # Optional, has default
```

### **Step 2: Create OpenRouter Service** _(45 minutes)_

**New File**: `strategy/openrouter_reviewer.py`

**Class Structure** (following `HyperbolicReviewer` pattern):

```python
class OpenRouterReviewer:
    def __init__(self, api_key: str, model: str = "anthropic/claude-3-sonnet"):
        self.api_key = api_key
        self.model = model
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    def review_trade(self, trade_data: Dict) -> Optional[Dict]:
        # Same interface as HyperbolicReviewer
        # Same JSON response format
        # Same error handling pattern

    def _create_review_prompt(self, trade_data: Dict) -> str:
        # Reuse existing prompt format

    def _parse_analysis(self, analysis: str) -> Dict:
        # Reuse existing parsing logic
```

### **Step 3: Update Main Setup** _(15 minutes)_

**File to Modify**: `utils/setup.py`

**Changes:**

```python
def setup():
    # ... existing code ...
    openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
    openrouter_model = config["openrouter_model"]

    # Add to return tuple
    return (..., openrouter_api_key, openrouter_model)
```

### **Step 4: Integrate into AlloraMind** _(30 minutes)_

**File to Modify**: `allora/allora_mind.py`

**Changes:**

```python
from strategy.openrouter_reviewer import OpenRouterReviewer

class AlloraMind:
    def __init__(self, manager, allora_upshot_key, hyperbolic_api_key,
                 openrouter_api_key, openrouter_model, threshold=0.03):
        # ... existing code ...
        self.openrouter_reviewer = OpenRouterReviewer(openrouter_api_key, openrouter_model)

    def open_trade(self):
        # ... existing code until Hyperbolic review ...

        # Add OpenRouter review as secondary validation
        openrouter_review = self.openrouter_reviewer.review_trade(trade_data)

        # Simple AND logic for both validators
        both_approve = (review and review['approval'] and
                       openrouter_review and openrouter_review['approval'])

        if both_approve:
            # Continue with trade execution
        else:
            # Log rejection reasons from both
```

### **Step 5: Update Main Entry Point** _(10 minutes)_

**File to Modify**: `main.py`

**Changes:**

```python
def main():
    (address, info, exchange, vault, allora_upshot_key, hyperbolic_api_key,
     openrouter_api_key, openrouter_model, check_for_trades, price_gap,
     allowed_amount_per_trade, max_leverage, allora_topics) = setup()

    # Update AlloraMind initialization
    allora_mind = AlloraMind(manager, allora_upshot_key, hyperbolic_api_key,
                           openrouter_api_key, openrouter_model, threshold=price_gap)
```

### **Step 6: Testing & Validation** _(30 minutes)_

**Testing Approach:**

1. **Configuration Test**: Verify environment variables load correctly
2. **API Connection Test**: Test OpenRouter API connectivity
3. **Integration Test**: Test trade validation with both AI services
4. **Error Handling Test**: Verify graceful degradation if OpenRouter fails

**Validation Steps:**

```python
# Test script to validate integration
def test_openrouter_integration():
    # 1. Test API key configuration
    # 2. Test OpenRouterReviewer initialization
    # 3. Test review_trade() method
    # 4. Test consensus logic in AlloraMind
```

## 📊 Implementation Checklist

- [ ] **Environment Configuration**

  - [ ] Add `OPENROUTER_API_KEY` to `env_loader.py`
  - [ ] Add `OPENROUTER_MODEL` with default value
  - [ ] Update required_vars validation

- [ ] **Service Implementation**

  - [ ] Create `strategy/openrouter_reviewer.py`
  - [ ] Implement `OpenRouterReviewer` class
  - [ ] Copy and adapt methods from `HyperbolicReviewer`
  - [ ] Update API endpoint and headers

- [ ] **Integration Updates**

  - [ ] Update `utils/setup.py` configuration loading
  - [ ] Modify `allora/allora_mind.py` initialization
  - [ ] Add OpenRouter validation to trade logic
  - [ ] Update `main.py` entry point

- [ ] **Testing & Validation**
  - [ ] Test environment variable loading
  - [ ] Test OpenRouter API connectivity
  - [ ] Test dual-validation logic
  - [ ] Verify error handling and logging

## 🔧 Configuration Management

**New Environment Variables:**

```bash
# Required
OPENROUTER_API_KEY=your_api_key

# Optional (with defaults)
OPENROUTER_MODEL=anthropic/claude-3-sonnet
OPENROUTER_TIMEOUT=30
OPENROUTER_MAX_RETRIES=3
```

**Model Options** (popular choices):

- `anthropic/claude-3-sonnet` (balanced)
- `openai/gpt-4-turbo` (comprehensive)
- `google/gemini-pro` (efficient)
- `meta-llama/llama-3.1-70b` (cost-effective)

## 🎯 Success Criteria

1. ✅ **Functional Integration**: OpenRouter validates trades alongside Hyperbolic
2. ✅ **Error Resilience**: System continues if one AI service fails
3. ✅ **Configuration Flexibility**: Easy model switching via environment
4. ✅ **Consistent Interface**: Same validation format as existing system
5. ✅ **Minimal Code Changes**: Follow existing patterns and architecture

## 📈 Benefits of This Integration

**Immediate Value:**

- **Redundancy**: Backup validation if Hyperbolic fails
- **Consensus**: Higher confidence with dual AI approval
- **Model Diversity**: Access to different AI reasoning approaches
- **Cost Options**: Flexibility to use cost-effective models

**Future Extensibility:**

- Foundation for more complex AI strategies
- Template for additional AI service integrations
- A/B testing framework for model comparison
- Performance monitoring baseline

## 🚀 Execution Notes

**Prerequisites:**

- OpenRouter API key required
- Understanding of existing HyperbolicReviewer pattern
- Access to project environment configuration

**Risk Mitigation:**

- Follow existing error handling patterns
- Maintain backward compatibility
- Test thoroughly before deployment
- Document all changes for future reference

---

**Plan Status**: ✅ **READY FOR EXECUTION**  
**Risk Level**: **LOW** - Following proven patterns  
**Dependencies**: OpenRouter API key required
