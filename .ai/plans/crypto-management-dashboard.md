# Plan: Gestion Dynamique des Cryptomonnaies & Mode Veille Bot

_Créé: 2025-01-12 | Version: 1.0 | Updated: 2025-01-25_  
_Status: PHASE 2 COMPLETED ✅ | Priorité: HAUTE_

## 🎉 IMPLEMENTATION STATUS: PHASE 2 COMPLETED

### ✅ **Achievements Summary**

- **Phase 1**: Backend Foundation ✅ COMPLETED

  - 13 API endpoints implemented
  - ConfigManager with cross-platform crypto management
  - Database schema with crypto_configs & bot_commands tables
  - Enhanced BotController with STANDBY/ACTIVE modes

- **Phase 2**: Bot Integration ✅ COMPLETED
  - AlloraMind extended with dynamic mode control
  - Real-time command processing (10-second intervals)
  - Dynamic crypto configuration without restarts
  - 15/15 comprehensive tests passing
  - Production-ready command execution system

### 🎯 **Ready for Phase 3**: Frontend Interface Implementation

- CryptoManager.tsx component development
- Real-time dashboard integration
- User interface for crypto toggles and bot control

## 🎯 Objectifs Principaux

### 1. **Dashboard de Gestion des Cryptos**

- Interface web pour activer/désactiver les cryptomonnaies surveillées
- Affichage temps réel des cryptos disponibles sur HyperLiquid + AlloraNetwork
- Gestion par toggles intuitifs avec recherche et filtres

### 2. **Mode Veille du Bot**

- Bot démarre en mode STANDBY (attente d'instructions)
- Activation/désactivation via dashboard
- Pas de trading automatique sans ordre explicite

### 3. **Gestion Dynamique**

- Modification des cryptos surveillées sans redémarrage du bot
- Communication temps réel dashboard ↔ bot
- Persistance des configurations

## 📊 Architecture Proposée

### **Backend Extensions**

#### A. Configuration Manager (`dashboard/backend/config_manager.py`)

```python
class ConfigManager:
    def __init__(self):
        self.active_cryptos = {}  # {token: topic_id}
        self.available_cryptos = {}
        self.db = DatabaseService()

    async def load_available_cryptos(self):
        # Charge HyperLiquid testnet tokens (178 cryptos)
        # Charge AlloraNetwork topic IDs (26 topics)
        # Croise les données pour "both" availability

    async def update_active_cryptos(self, updates):
        # Met à jour la config active
        # Notifie le bot via WebSocket
        # Sauvegarde en base

    async def get_crypto_status(self):
        # Retourne status complet pour dashboard
```

#### B. Crypto Router (`dashboard/backend/routers/crypto_config.py`)

```python
# Nouveaux endpoints:
GET /api/crypto/available         # Liste complète cryptos disponibles
GET /api/crypto/active           # Cryptos actuellement surveillées
POST /api/crypto/activate        # Activer une crypto: {symbol, topic_id}
POST /api/crypto/deactivate      # Désactiver: {symbol}
PUT /api/crypto/batch-update     # Mise à jour multiple
GET /api/crypto/compatibility    # Check HyperLiquid + Allora compat
```

#### C. Bot Controller Extension (`dashboard/backend/bot_controller.py`)

```python
class BotController:
    def __init__(self):
        self.bot_mode = "STANDBY"  # STANDBY, ACTIVE, STOPPED
        self.bot_process = None
        self.config_manager = ConfigManager()

    async def start_monitoring(self):
        # Démarre bot en mode surveillance
        self.bot_mode = "ACTIVE"

    async def set_standby(self):
        # Met bot en veille
        self.bot_mode = "STANDBY"

    async def update_crypto_config(self, config):
        # Envoie nouvelle config au bot via signal/WebSocket
```

### **Bot Core Modifications**

#### A. Standby Mode (`allora/allora_mind.py`)

```python
class AlloraMind:
    def __init__(self):
        self.mode = "STANDBY"  # STANDBY, ACTIVE
        self.topic_ids = {}
        self.command_listener = CommandListener()

    def start_with_standby(self):
        """Démarre en mode veille avec écoute commands"""
        print("🟡 Bot started in STANDBY mode")
        while True:
            if self.mode == "ACTIVE" and self.topic_ids:
                self.run_trading_cycle()
            else:
                self.check_dashboard_commands()
            time.sleep(10)

    def update_cryptos_dynamically(self, new_topics):
        """Met à jour topic_ids sans redémarrage"""
        self.topic_ids = new_topics
        print(f"📡 Updated monitored cryptos: {list(new_topics.keys())}")

    def activate_monitoring(self):
        """Active le mode trading"""
        self.mode = "ACTIVE"
        print("🟢 Bot activated - Starting monitoring")

    def set_standby(self):
        """Retour en mode veille"""
        self.mode = "STANDBY"
        print("🟡 Bot set to STANDBY mode")
```

#### B. Command Interface (`allora/command_listener.py`)

```python
class CommandListener:
    def __init__(self):
        self.websocket_client = None
        self.db_listener = DatabaseListener()

    async def listen_for_commands(self):
        # Écoute WebSocket commands du dashboard
        # Format: {"type": "UPDATE_CRYPTOS", "data": {cryptos}}
        #         {"type": "SET_MODE", "data": "ACTIVE"}

    def check_db_commands(self):
        # Alternative: polling base pour commands
```

### **Frontend Extensions**

#### A. Crypto Manager Component (`dashboard/frontend/src/components/CryptoManager.tsx`)

```typescript
interface CryptoConfig {
  symbol: string;
  topicId: number;
  isActive: boolean;
  availability: "both" | "hyperliquid" | "allora";
  price?: number;
  volume24h?: number;
}

const CryptoManager: React.FC = () => {
  const [availableCryptos, setAvailableCryptos] = useState<CryptoConfig[]>([]);
  const [activeCryptos, setActiveCryptos] = useState<CryptoConfig[]>([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [filterBy, setFilterBy] = useState<
    "all" | "both" | "hyperliquid" | "allora"
  >("all");

  const handleToggleCrypto = async (symbol: string, activate: boolean) => {
    // Call API to activate/deactivate
    // Update local state
    // Show notification
  };

  const handleBatchUpdate = async (updates: CryptoConfig[]) => {
    // Bulk operations for multiple cryptos
  };

  return (
    <div className="crypto-manager">
      <SearchAndFilter />
      <CryptoGrid cryptos={filteredCryptos} onToggle={handleToggleCrypto} />
      <QuickActions />
    </div>
  );
};
```

#### B. Enhanced Bot Control (`dashboard/frontend/src/components/BotControl.tsx`)

```typescript
const BotControl: React.FC = () => {
  const [botMode, setBotMode] = useState<"STANDBY" | "ACTIVE" | "STOPPED">(
    "STANDBY"
  );
  const [activeCryptos, setActiveCryptos] = useState<string[]>([]);

  const handleStartMonitoring = async () => {
    if (activeCryptos.length === 0) {
      alert("Please activate at least one cryptocurrency first");
      return;
    }
    await apiService.startBotMonitoring();
  };

  return (
    <div className="bot-control">
      <BotModeIndicator mode={botMode} />
      <ActiveCryptosSummary cryptos={activeCryptos} />
      <ControlButtons />
    </div>
  );
};
```

## 🔄 Flux de Données

### Activation d'une Crypto

```
User Dashboard → Frontend → Backend API → ConfigManager → WebSocket → Bot
     ↓                                                                ↓
Confirmation ← Frontend ← Backend API ← ConfigManager ← WebSocket ← Bot ACK
```

### Démarrage du Mode Surveillance

```
User "Start" → Frontend → Backend → BotController → Bot Process
                                         ↓
                              Signal: SET_MODE=ACTIVE
                                         ↓
                            Bot: mode="ACTIVE" + start trading
```

## 📋 Plan d'Implémentation

### **Phase 1: Backend Foundation** ✅ COMPLETED

- [x] `ConfigManager` class avec gestion crypto ✅
- [x] `crypto_config.py` router avec tous endpoints ✅ (13 endpoints)
- [x] Extension `BotController` pour modes STANDBY/ACTIVE ✅
- [x] Database schema pour config cryptos ✅
- [x] Tests API endpoints ✅

### **Phase 2: Bot Integration** ✅ COMPLETED

- [x] Modification `allora_mind.py` pour mode STANDBY ✅
- [x] Command system pour communication dashboard ✅ (DB polling)
- [x] Real-time command processing (10s intervals) ✅
- [x] Dynamic `topic_ids` update sans redémarrage ✅
- [x] Tests mode veille et activation ✅ (15/15 tests passing)

### **Phase 3: Frontend Interface** (Jour 3-4)

- [ ] `CryptoManager.tsx` component principal
- [ ] Search, filter, et toggle controls
- [ ] Enhanced `BotControl.tsx` avec modes
- [ ] Dashboard tab pour "Crypto Configuration"
- [ ] Real-time updates via WebSocket

### **Phase 4: Integration & Testing** (Jour 4-5)

- [ ] End-to-end workflow testing
- [ ] Error handling et edge cases
- [ ] Performance optimization
- [ ] User experience refinement
- [ ] Documentation utilisateur

## 🗄️ Database Schema

```sql
-- Table configuration cryptos
CREATE TABLE crypto_configs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT UNIQUE NOT NULL,           -- 'BTC', 'ETH', etc.
    topic_id INTEGER NOT NULL,             -- AlloraNetwork topic ID
    is_active BOOLEAN DEFAULT FALSE,       -- Actuellement surveillée
    availability TEXT NOT NULL,            -- 'both', 'hyperliquid', 'allora'
    hyperliquid_available BOOLEAN DEFAULT FALSE,
    allora_available BOOLEAN DEFAULT FALSE,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_price REAL,                       -- Cache du dernier prix
    volume_24h REAL                        -- Cache volume 24h
);

-- Table commandes bot
CREATE TABLE bot_commands (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    command_type TEXT NOT NULL,            -- 'UPDATE_CRYPTOS', 'SET_MODE', etc.
    command_data TEXT,                     -- JSON data
    status TEXT DEFAULT 'PENDING',         -- 'PENDING', 'EXECUTED', 'FAILED'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    executed_at TIMESTAMP,
    error_message TEXT
);
```

## 🎛️ Interface Utilisateur

### Crypto Management Dashboard

```
┌─────────────────────────────────────────────────────────────────────┐
│ 🚀 HyperLiquid AI Trading Bot - Crypto Configuration              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│ 🔍 [Search cryptocurrencies...]     📊 Filter: [Both Platforms ▼] │
│                                                                     │
│ Active Cryptocurrencies (2/178)              🟢 Bot: STANDBY       │
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │ ✅ BTC  Topic 1   $100,822   Vol: $2.1B    [🟢●●●] [Deactivate]│ │
│ │ ✅ ETH  Topic 2   $2,227     Vol: $891M    [🟢●●●] [Deactivate]│ │
│ └─────────────────────────────────────────────────────────────────┘ │
│                                                                     │
│ Available Cryptocurrencies                                          │
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │ ⚪ SOL   Topic 3   $133      Vol: $156M    [⚪●●●] [Activate]   │ │
│ │ ⚪ AVAX  Topic 7   $16.41    Vol: $89M     [⚪●●●] [Activate]   │ │
│ │ ⚪ MATIC Topic 9   $0.168    Vol: $45M     [⚪●●●] [Activate]   │ │
│ │ ⚪ ATOM  Topic 13  $3.79     Vol: $23M     [⚪●●●] [Activate]   │ │
│ └─────────────────────────────────────────────────────────────────┘ │
│                                                                     │
│ 📊 Quick Actions: [Select Popular (BTC,ETH,SOL,AVAX)] [Clear All]  │
│                                                                     │
│ Bot Control:                                                        │
│ [🚀 Start Monitoring] [⏸️ Set Standby] [🛑 Stop Bot]              │
└─────────────────────────────────────────────────────────────────────┘
```

## ⚙️ Configuration Updates

### Environment Variables (.env.testnet)

```bash
# Bot Mode Configuration
BOT_DEFAULT_MODE=STANDBY
CONFIG_UPDATE_INTERVAL=10
WEBSOCKET_COMMAND_ENABLED=true
WEBSOCKET_COMMAND_CHANNEL=bot_commands

# Default Active Cryptocurrencies (optional)
DEFAULT_ACTIVE_CRYPTOS=BTC:1,ETH:2

# Command Interface
BOT_COMMAND_DB_POLLING=true
BOT_COMMAND_WEBSOCKET=true
```

## 🎯 Avantages de Cette Architecture

### ✅ **Avantages Utilisateur**

- **🎛️ Contrôle Total**: Gestion intuitive des cryptos via interface web
- **⚡ Temps Réel**: Changements instantanés sans redémarrage
- **🛡️ Sécurité**: Mode veille par défaut, activation manuelle requise
- **📊 Visibilité**: Status en temps réel de toutes les cryptos et du bot

### ✅ **Avantages Techniques**

- **🔄 Hot Reload**: Modification config sans arrêt du bot
- **📡 Communication**: WebSocket temps réel dashboard ↔ bot
- **💾 Persistance**: Sauvegarde config en base de données
- **🧪 Testabilité**: Architecture modulaire facile à tester

### ✅ **Avantages Opérationnels**

- **🚀 Déploiement**: Zero-downtime configuration changes
- **📈 Scalabilité**: Ajout facile de nouvelles cryptos
- **🔧 Maintenance**: Gestion centralisée des configurations
- **📋 Audit**: Historique complet des changements

## 🚨 Considérations & Risques

### ⚠️ **Risques Identifiés**

- **Latence WebSocket**: Commands peuvent être perdues → Fallback DB polling
- **État Incohérent**: Bot et dashboard désynchronisés → Heartbeat system
- **Charge CPU**: Polling trop fréquent → Optimisation intervales
- **Erreurs Réseau**: Perte connexion AlloraNetwork → Retry logic

### 🛡️ **Mitigation Strategies**

- **Double Communication**: WebSocket + DB polling comme backup
- **Health Checks**: Vérification périodique cohérence état
- **Circuit Breaker**: Arrêt automatique si trop d'erreurs
- **Graceful Degradation**: Mode dégradé si services externes down

## 📚 Documentation Utilisateur

### Guide d'Utilisation

1. **Démarrage**: Bot lance automatiquement en mode STANDBY
2. **Configuration**: Aller dans l'onglet "Crypto Configuration"
3. **Activation**: Toggle les cryptos désirées (BTC, ETH, SOL...)
4. **Monitoring**: Cliquer "Start Monitoring" pour activer le bot
5. **Gestion**: Modifier les cryptos à tout moment, même pendant trading

### Workflow Recommandé

```
STANDBY → Configure Cryptos → Activate Monitoring →
Monitor Performance → Adjust Cryptos → Continue Trading
```

Cette architecture fournit une base solide pour une gestion flexible et professionnelle du bot de trading, tout en conservant la robustesse et les optimizations existantes.
