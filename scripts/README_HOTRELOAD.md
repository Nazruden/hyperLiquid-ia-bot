# 🔥 Hot Reload Development Scripts

Ce dossier contient des scripts améliorés avec support de **hot reload** utilisant [Jurigged](https://github.com/breuleux/jurigged) pour un développement ultra-rapide.

## 🚀 Scripts Disponibles

### 🔥 Scripts Hot Reload (RECOMMANDÉS pour le développement)

| Script                              | Description                          | Usage                                                    |
| ----------------------------------- | ------------------------------------ | -------------------------------------------------------- |
| `testnet_orchestrator_hotreload.py` | **Orchestrateur TESTNET** hot reload | `python scripts/testnet_orchestrator_hotreload.py --hot` |
| `start_all_hotreload.py`            | **Système complet** avec hot reload  | `python scripts/start_all_hotreload.py`                  |
| `start_dashboard_hotreload.py`      | **Dashboard seul** avec hot reload   | `python scripts/start_dashboard_hotreload.py`            |
| `start_bot_hotreload.py`            | **Bot seul** avec hot reload         | `python scripts/start_bot_hotreload.py`                  |

### 📄 Scripts Standard (Production/tests)

| Script                    | Description                        | Usage                                    |
| ------------------------- | ---------------------------------- | ---------------------------------------- |
| `testnet_orchestrator.py` | **Orchestrateur TESTNET** standard | `python scripts/testnet_orchestrator.py` |
| `start_all.py`            | Système complet standard           | `python scripts/start_all.py`            |
| `start_dashboard.py`      | Dashboard seul standard            | `python scripts/start_dashboard.py`      |

## ⚡ Avantages du Hot Reload

### 🔥 **Jurigged** - Python Hot Patching

- ✅ **Pas de redémarrage** - Les changements s'appliquent instantanément
- ✅ **État préservé** - Positions de trading, connexions WebSocket maintenues
- ✅ **Live patching** - Modifications des fonctions en cours d'exécution
- ✅ **Développement 10x plus rapide**

### 🎨 **Vite HMR** - Frontend Hot Module Replacement

- ✅ **Mise à jour instantanée** des composants React
- ✅ **CSS hot reload** - Styles mis à jour sans refresh
- ✅ **État UI préservé** - Formulaires, navigation maintenus

## 🧪 Cas d'Usage Idéaux

### 📈 **Développement de Stratégies**

```bash
python scripts/start_bot_hotreload.py
# Éditez strategy/volatility_strategy.py → Changements appliqués instantanément
```

### 🖥️ **Développement Dashboard**

```bash
python scripts/start_dashboard_hotreload.py
# Éditez les APIs ou composants React → Mises à jour instantanées
```

### 🔧 **Développement Système Complet**

```bash
python scripts/start_all_hotreload.py
# Développement coordonné bot + dashboard avec hot reload
```

## 📋 Installation & Prérequis

Le hot reload nécessite **jurigged** qui s'installe automatiquement :

```bash
pip install jurigged  # Installation automatique si manquant
```

## 🎯 Exemples Pratiques

### 🤖 Développement Bot avec Hot Reload

```bash
# 1. Lancer le bot avec hot reload
python scripts/start_bot_hotreload.py

# 2. Le bot surveille automatiquement :
#    - strategy/ → Stratégies de trading
#    - allora/ → Logique de prédictions
#    - core/ → Modules principaux
#    - database/ → Gestion base de données

# 3. Éditez un fichier strategy/custom_strategy.py
# 4. BOOM! 🔥 Changements appliqués instantanément
```

### 🖥️ Développement Dashboard avec Hot Reload

```bash
# 1. Lancer le dashboard avec hot reload
python scripts/start_dashboard_hotreload.py

# 2. Accéder au dashboard : http://localhost:5173
# 3. Éditez dashboard/backend/routers/bot_control.py
# 4. Éditez dashboard/frontend/src/components/BotStatus.tsx
# 5. BOOM! 🔥 Les deux se mettent à jour instantanément
```

## 🔧 Options Dashboard Server

Le serveur dashboard principal supporte maintenant le hot reload :

```bash
# Mode standard (redémarrage processus)
python dashboard/start_server.py

# Mode hot reload (live patching)
python dashboard/start_server.py --hot
python dashboard/start_server.py --hotreload
```

## 🧠 Comparaison des Modes

| Mode           | Redémarrage | État Préservé | Vitesse       | Idéal Pour       |
| -------------- | ----------- | ------------- | ------------- | ---------------- |
| **Hot Reload** | ❌ Non      | ✅ Oui        | ⚡ Instantané | Développement    |
| **Standard**   | ✅ Oui      | ❌ Non        | 🐌 5-10s      | Production/Tests |

## 🏆 Recommandations

### 🔥 **Pour le Développement** (RECOMMANDÉ)

```bash
# Système complet avec hot reload
python scripts/start_all_hotreload.py
```

### 🚀 **Pour la Production**

```bash
# Système standard pour la stabilité
python scripts/start_all.py
```

### 🎯 **Pour le Debug Spécialisé**

```bash
# Bot seul pour focus sur stratégies
python scripts/start_bot_hotreload.py

# Dashboard seul pour focus sur UI
python scripts/start_dashboard_hotreload.py
```

## 💡 Conseils de Développement

1. **🔥 Utilisez TOUJOURS le hot reload** pour le développement
2. **📊 État préservé** = pas besoin de refaire les setups
3. **⚡ Feedback instantané** = cycle développement ultra-rapide
4. **🧪 Perfect pour l'expérimentation** de nouvelles stratégies
5. **🚀 10x plus productif** qu'avec les redémarrages

---

**🎉 Bon développement avec le hot reload ! Votre productivité va exploser ! 🚀**
