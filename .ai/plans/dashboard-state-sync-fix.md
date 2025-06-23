# 📊 Dashboard State Sync & Activity Journal - Implementation Plan

_Version 1.0 | Created: 2024-12-20 | Phase: Π₃ | Mode: Ω₃_

## 🎯 Executive Summary

This plan addresses two critical dashboard issues:

1. **State Synchronization Problem**: "Start Monitoring" button activates bot but dashboard state remains "STANDBY"
2. **Missing Activity Journal**: No real-time logging of AI decisions, Allora predictions, and trading actions

### 📋 Success Criteria

- ✅ Real-time state synchronization between bot and dashboard
- ✅ Live activity journal with AI decisions and trading actions
- ✅ All files maintain ≤350 lines for maintainability
- ✅ Zero breaking changes to existing functionality

---

## 📐 Architecture Overview

### Current State Analysis

```
File Size Analysis (from investigation):
- dashboard/backend/bot_controller.py: 559 lines ❌ (>350)
- dashboard/backend/websocket_manager.py: 166 lines ✅
- dashboard/backend/data_service.py: 338 lines ✅
- dashboard/backend/routers/bot_control.py: 258 lines ✅
- allora/allora_mind.py: 682 lines ❌ (>350)
- database/db_manager.py: 368 lines ❌ (>350)
```

### Target Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    DASHBOARD FRONTEND                       │
├─────────────────┬─────────────────┬─────────────────────────┤
│   BotStatus     │  ActivityLog    │      LiveMetrics        │
│   Component     │   Component     │       Component         │
└─────────────────┴─────────────────┴─────────────────────────┘
                            │
                    WebSocket Connection
                            │
┌─────────────────────────────────────────────────────────────┐
│                   BACKEND SERVICES                          │
├─────────────────┬─────────────────┬─────────────────────────┤
│  BotController  │ ActivityLogger  │   WebSocketManager      │
│   (≤350 lines)  │  (≤350 lines)   │     (≤350 lines)        │
├─────────────────┼─────────────────┼─────────────────────────┤
│  StateSync      │  LogsAPI        │   DatabaseManager       │
│   Service       │   Service       │      (≤350 lines)      │
└─────────────────┴─────────────────┴─────────────────────────┘
                            │
                      Command Queue
                            │
┌─────────────────────────────────────────────────────────────┐
│                     BOT CORE                                │
├─────────────────┬─────────────────┬─────────────────────────┤
│  AlloraMind     │ CommandProcessor│   ActivityReporter      │
│   (≤350 lines)  │   (≤350 lines)  │     (≤350 lines)        │
└─────────────────┴─────────────────┴─────────────────────────┘
```

---

## 🗂️ File Refactoring Plan

### Phase 1: File Size Optimization

#### 1.1 Split BotController (559 → 3×~200 lines)

**Target Files:**

- `dashboard/backend/controllers/bot_process_controller.py` (~200 lines)
- `dashboard/backend/controllers/bot_mode_controller.py` (~200 lines)
- `dashboard/backend/services/state_sync_service.py` (~159 lines)

**Responsibilities:**

```python
# bot_process_controller.py - Process lifecycle management
class BotProcessController:
    - start_bot(), stop_bot(), restart_bot()
    - get_status(), _find_running_bot_process()
    - get_system_resources(), get_bot_logs()

# bot_mode_controller.py - Mode & crypto management
class BotModeController:
    - start_monitoring(), set_standby_mode()
    - get_bot_mode_status(), update_crypto_config()
    - initialize_with_standby()

# state_sync_service.py - WebSocket integration
class StateSyncService:
    - broadcast_state_change()
    - periodic_status_sync()
    - handle_bot_status_updates()
```

#### 1.2 Split DatabaseManager (368 → 2×~190 lines)

**Target Files:**

- `database/db_manager.py` (~190 lines) - Core DB operations
- `database/activity_logger.py` (~178 lines) - Activity & log management

#### 1.3 Split AlloraMind (682 → 3×~230 lines)

**Target Files:**

- `allora/allora_mind.py` (~230 lines) - Core prediction logic
- `allora/command_processor.py` (~230 lines) - Dashboard command handling
- `allora/activity_reporter.py` (~222 lines) - Real-time activity reporting

---

## 🔧 Implementation Phases

### 🎯 Phase 1: Foundation Refactoring (Est. 4 hours)

#### Sprint 1.1: Database Layer Split

**Duration:** 1 hour
**Files to modify:**

- Split `database/db_manager.py` → `db_manager.py` + `activity_logger.py`
- Update all imports across the project

**Key Changes:**

```python
# database/activity_logger.py
class ActivityLogger:
    def log_ai_decision(self, token, provider, decision, confidence, reasoning)
    def log_allora_prediction(self, token, prediction, metadata)
    def log_trade_signal(self, token, signal, price, reasoning)
    def get_recent_activity(self, limit=50, filters=None)
    def get_activity_stream(self, since_timestamp)
```

#### Sprint 1.2: BotController Refactoring

**Duration:** 2 hours
**Files to create:**

- `dashboard/backend/controllers/bot_process_controller.py`
- `dashboard/backend/controllers/bot_mode_controller.py`
- `dashboard/backend/services/state_sync_service.py`

**Key Changes:**

```python
# state_sync_service.py
class StateSyncService:
    def __init__(self, websocket_manager):
        self.ws_manager = websocket_manager

    async def sync_bot_status(self, status_data):
        await self.ws_manager.broadcast_bot_status(status_data)

    async def sync_mode_change(self, mode_data):
        await self.ws_manager.queue_broadcast("mode_status", mode_data)
```

#### Sprint 1.3: AlloraMind Refactoring

**Duration:** 1 hour  
**Files to create:**

- `allora/command_processor.py`
- `allora/activity_reporter.py`
- Update `allora/allora_mind.py`

### 🎯 Phase 2: State Synchronization Fix (Est. 3 hours)

#### Sprint 2.1: WebSocket State Broadcasting

**Duration:** 1 hour
**Files to modify:**

- `dashboard/backend/controllers/bot_mode_controller.py`
- `dashboard/backend/services/state_sync_service.py`
- `dashboard/backend/websocket_manager.py`

**Implementation:**

```python
# In bot_mode_controller.py
async def start_monitoring(self):
    # ... existing logic ...

    # NEW: Broadcast state change via WebSocket
    await self.state_sync_service.sync_mode_change({
        "mode": "ACTIVE",
        "monitoring_enabled": True,
        "active_cryptos": active_cryptos,
        "timestamp": datetime.now().isoformat()
    })
```

#### Sprint 2.2: Frontend WebSocket Integration

**Duration:** 1 hour
**Files to modify:**

- `dashboard/frontend/src/hooks/useWebSocket.ts`
- `dashboard/frontend/src/components/BotStatus.tsx`

**Key Changes:**

```typescript
// In useWebSocket.ts - Add new message handler
case "mode_status":
    setModeStatus(message.data);
    break;

// In BotStatus.tsx - Listen to WebSocket updates
useEffect(() => {
    if (lastMessage?.type === "mode_status") {
        setModeStatus(lastMessage.data);
    }
}, [lastMessage]);
```

#### Sprint 2.3: Periodic Status Sync

**Duration:** 1 hour
**Files to create:**

- `dashboard/backend/services/status_monitor.py`

**Implementation:**

```python
# status_monitor.py
class StatusMonitor:
    async def start_monitoring(self):
        while True:
            try:
                # Check bot status every 10 seconds
                status = await self.get_comprehensive_status()
                await self.state_sync_service.sync_status(status)
                await asyncio.sleep(10)
            except Exception as e:
                logger.error(f"Status monitoring error: {e}")
                await asyncio.sleep(5)
```

### 🎯 Phase 3: Activity Journal Implementation (Est. 4 hours)

#### Sprint 3.1: Activity Logging API

**Duration:** 1.5 hours
**Files to create:**

- `dashboard/backend/routers/activity_logs.py`
- `dashboard/backend/services/activity_service.py`

**New Endpoints:**

```python
@router.get("/activity/recent")
async def get_recent_activity(limit: int = 50):
    # Get recent AI decisions, predictions, signals

@router.get("/activity/stream")
async def get_activity_stream(since: str = None):
    # Get activity since timestamp for real-time updates

@router.get("/activity/ai-decisions")
async def get_ai_decisions(provider: str = None):
    # Get AI provider decisions (Hyperbolic, OpenRouter)
```

#### Sprint 3.2: Real-time Activity Broadcasting

**Duration:** 1.5 hours
**Files to modify:**

- `allora/activity_reporter.py`
- `dashboard/backend/websocket_manager.py`

**Key Implementation:**

```python
# In activity_reporter.py
class ActivityReporter:
    def __init__(self, websocket_manager):
        self.ws_manager = websocket_manager

    async def report_ai_decision(self, provider, token, decision_data):
        await self.ws_manager.queue_broadcast("ai_insight", {
            "type": "ai_decision",
            "provider": provider,
            "token": token,
            "data": decision_data,
            "timestamp": datetime.now().isoformat()
        })

    async def report_allora_prediction(self, token, prediction_data):
        await self.ws_manager.queue_broadcast("ai_insight", {
            "type": "allora_prediction",
            "token": token,
            "data": prediction_data,
            "timestamp": datetime.now().isoformat()
        })
```

#### Sprint 3.3: Activity Log Frontend Component

**Duration:** 1 hour
**Files to create:**

- `dashboard/frontend/src/components/ActivityLog.tsx`
- `dashboard/frontend/src/types/activity.ts`

**Component Features:**

- Real-time activity feed
- Filtering by type (AI decisions, predictions, signals)
- Auto-scroll and pause functionality
- Activity details modal

### 🎯 Phase 4: Integration & Testing (Est. 2 hours)

#### Sprint 4.1: End-to-End Integration

**Duration:** 1 hour
**Tasks:**

- Update main dashboard to include ActivityLog component
- Ensure all WebSocket message types are handled
- Test state synchronization flow

#### Sprint 4.2: Testing & Validation

**Duration:** 1 hour  
**Test Scenarios:**

- ✅ Start Monitoring button updates dashboard state immediately
- ✅ Set Standby button updates dashboard state immediately
- ✅ AI decisions appear in activity log in real-time
- ✅ Allora predictions logged and displayed
- ✅ All files ≤350 lines

---

## 📊 Implementation Timeline

```
Week 1 - Foundation
├── Day 1: Phase 1 (Refactoring) - 4 hours
├── Day 2: Phase 2 (State Sync) - 3 hours
├── Day 3: Phase 3 (Activity Journal) - 4 hours
└── Day 4: Phase 4 (Integration) - 2 hours

Total Estimated Effort: 13 hours
```

---

## 🧪 Testing Strategy

### Unit Tests

- `test_state_sync_service.py` - State synchronization logic
- `test_activity_logger.py` - Activity logging functionality
- `test_websocket_integration.py` - WebSocket message handling

### Integration Tests

- State sync flow: Dashboard → Backend → Bot → Dashboard
- Activity logging flow: Bot → Database → WebSocket → Dashboard
- Error handling and resilience

### Manual Testing Checklist

- [ ] Start Monitoring button updates dashboard state immediately
- [ ] Set Standby button updates dashboard state immediately
- [ ] AI decisions appear in activity log in real-time
- [ ] Allora predictions logged and displayed correctly
- [ ] No breaking changes to existing functionality
- [ ] All files maintain ≤350 lines

---

## 🔒 Risk Mitigation

### Technical Risks

1. **WebSocket Connection Reliability**

   - _Mitigation_: Implement reconnection with exponential backoff
   - _Fallback_: Periodic API polling for state updates

2. **Database Performance Impact**

   - _Mitigation_: Index on timestamp columns, implement log retention
   - _Fallback_: Async logging with queue buffering

3. **File Refactoring Complexity**
   - _Mitigation_: Incremental refactoring with comprehensive testing
   - _Fallback_: Feature flags to enable/disable new functionality

### Business Risks

1. **Development Time Overrun**

   - _Mitigation_: Phased approach allows for partial delivery
   - _Contingency_: Core state sync (Phase 2) can be delivered independently

2. **User Experience Disruption**
   - _Mitigation_: Backward compatibility maintained throughout
   - _Rollback_: All changes are additive, easy to revert

---

## 📈 Success Metrics

### Performance Metrics

- State synchronization latency: <500ms
- Activity log update frequency: Real-time (<1s)
- WebSocket connection uptime: >99%
- File size compliance: 100% ≤350 lines

### User Experience Metrics

- Dashboard state accuracy: 100%
- Activity log completeness: >95% of events logged
- No functional regressions: 0 breaking changes

---

## 🎯 Next Steps

1. **Immediate**: Begin Phase 1 refactoring with database layer
2. **Day 1**: Complete BotController split and test imports
3. **Day 2**: Implement state synchronization WebSocket integration
4. **Day 3**: Add activity journal with real-time updates
5. **Day 4**: End-to-end testing and documentation

This plan ensures a systematic approach to resolving both dashboard issues while maintaining code quality through the 350-line constraint and providing comprehensive real-time monitoring capabilities.
