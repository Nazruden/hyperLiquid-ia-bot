# 🚀 Bot Launcher - Guide d'utilisation

Le script `launch_bot.py` permet de lancer le bot HyperLiquid avec des paramètres flexibles.

## ⚡ Utilisation rapide

```bash
# Lancer avec les paramètres par défaut (testnet, BTC/ETH/SOL, monitoring auto)
python launch_bot.py

# Test rapide 60 secondes en testnet
python launch_bot.py --duration 60

# Trading mainnet BTC seulement, 5 minutes, sans monitoring auto
python launch_bot.py --env mainnet --cryptos BTC --duration 300 --no-auto-monitor
```

## 📋 Paramètres disponibles

### `--env / --environment`

**Environnement de trading**

- `testnet` (défaut) : Mode test sans argent réel
- `mainnet` : Mode production avec argent réel ⚠️

```bash
python launch_bot.py --env testnet    # Mode test
python launch_bot.py --env mainnet    # Mode production
```

### `--duration / -d`

**Durée d'exécution en secondes**

- Par défaut : Infini (arrêt avec Ctrl+C)
- Nombre entier : Durée en secondes

```bash
python launch_bot.py --duration 60     # 1 minute
python launch_bot.py --duration 300    # 5 minutes
python launch_bot.py --duration 3600   # 1 heure
python launch_bot.py                   # Infini
```

### `--cryptos / --currencies`

**Cryptomonnaies à activer**

- Par défaut : `BTC,ETH,SOL`
- Format : Liste séparée par des virgules
- Supportées : BTC, ETH, SOL, AVAX, DOGE, MATIC, ADA, DOT, LINK, UNI

```bash
python launch_bot.py --cryptos BTC,ETH,SOL     # Défaut
python launch_bot.py --cryptos BTC             # Bitcoin seulement
python launch_bot.py --cryptos BTC,ETH         # Bitcoin et Ethereum
python launch_bot.py --cryptos SOL,AVAX,DOGE   # Altcoins
```

### `--auto-monitor` / `--no-auto-monitor`

**Activation automatique du monitoring**

- Par défaut : `--auto-monitor` (activé)
- `--no-auto-monitor` : Mode STANDBY, activation manuelle via dashboard

```bash
python launch_bot.py --auto-monitor        # Démarre en mode ACTIVE
python launch_bot.py --no-auto-monitor     # Démarre en mode STANDBY
```

### `--db-path`

**Chemin personnalisé pour la base de données**

- Optionnel : Permet de spécifier une DB custom

```bash
python launch_bot.py --db-path custom_trades.db
```

### `--hot-reload`

**Mode hot reload pour développement**

- Expérimental : Rechargement à chaud du code
- Recommandé : Utiliser `scripts/start_bot_hotreload.py` à la place

```bash
python launch_bot.py --hot-reload
```

## 🎯 Exemples d'utilisation

### Développement et tests

```bash
# Test rapide 30 secondes avec BTC en testnet
python launch_bot.py --duration 30 --cryptos BTC

# Test complet 5 minutes avec toutes les cryptos
python launch_bot.py --duration 300 --cryptos BTC,ETH,SOL,AVAX

# Mode STANDBY pour tester l'activation manuelle
python launch_bot.py --no-auto-monitor --duration 60
```

### Production mainnet

```bash
# BTC trading 1 heure
python launch_bot.py --env mainnet --cryptos BTC --duration 3600

# Multi-crypto trading infini
python launch_bot.py --env mainnet --cryptos BTC,ETH,SOL

# Mode conservateur : pas d'auto-monitoring
python launch_bot.py --env mainnet --cryptos BTC --no-auto-monitor
```

### Cas spéciaux

```bash
# Base de données personnalisée
python launch_bot.py --db-path my_strategy.db --cryptos BTC,ETH

# Test de nouvelles cryptos
python launch_bot.py --cryptos AVAX,DOGE,MATIC --duration 120
```

## ⚠️ Sécurité

- **Mainnet** : Confirmation manuelle requise (`Type 'YES' to confirm`)
- **Testnet** : Aucune confirmation, argent virtuel
- **Database** : Sauvegarde automatique des configurations

## 🆘 Aide

```bash
python launch_bot.py --help    # Affiche l'aide complète
```

## 🔗 Scripts connexes

- `scripts/start_bot_hotreload.py` : Hot reload stable pour développement
- `scripts/start_all_hotreload.py` : Bot + Dashboard avec hot reload
- `scripts/testnet_orchestrator_hotreload.py` : Orchestrateur complet testnet
