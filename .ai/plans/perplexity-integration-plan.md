# 🎯 Plan d'Implémentation: Intégration Perplexity API

**Project**: HyperLiquid AI Trading Bot  
**Plan Version**: v1.0  
**Created**: 2025-01-08  
**Status**: Ready for Execution  
**Estimated Time**: 14-20 heures

## 🎯 Objectif

Ajouter Perplexity AI comme 3ème service de validation avec recherche temps réel et citations, en s'intégrant au système de scoring adaptatif existant.

## 📊 Vue d'Ensemble du Plan

```
🏗️ Architecture Cible:
AlloraNetwork (Prédictions) → [Hyperbolic + OpenRouter + Perplexity] → Triple Scoring → Décision
```

**Durée Estimée**: 14-20 heures réparties sur 3 phases
**Complexité**: Moyenne (extension d'architecture existante)
**Risque**: Faible (patterns établis, fallback disponible)

## 📋 Phase 1: Foundation & Proof of Concept

**Durée**: 4-6 heures | **Priorité**: Critique

### 1.1 Service Perplexity de Base (2-3h)

**Objectif**: Créer le service suivant les patterns existants

**Livrables**:

- [ ] `strategy/perplexity_reviewer.py` - Service de base
- [ ] Tests unitaires de connectivity
- [ ] Validation format de réponse

**Checklist d'Implémentation**:

```python
# strategy/perplexity_reviewer.py
class PerplexityReviewer:
    def __init__(self, api_key: str, model: str = "sonar-pro"):
        # Configuration API Perplexity

    def review_trade(self, trade_data: Dict) -> Optional[Dict]:
        # Interface standardisée (approval, confidence, risk_score, reasoning)

    def _create_market_research_prompt(self, trade_data: Dict) -> str:
        # Prompt spécialisé pour recherche marché temps réel

    def _analyze_with_sources(self, prompt: str) -> Dict:
        # Appel API avec return_citations=True
```

### 1.2 Configuration Environnement (1h)

**Objectif**: Étendre le système de configuration

**Fichiers Modifiés**:

- [ ] `utils/env_loader.py` - Ajout variables Perplexity
- [ ] `.env.example` - Documentation configuration
- [ ] `utils/setup.py` - Intégration paramètres

**Nouvelles Variables**:

```bash
# Perplexity API Configuration
PERPLEXITY_API_KEY=your_perplexity_api_key
PERPLEXITY_MODEL=sonar-pro
PERPLEXITY_BASE_WEIGHT=0.25
PERPLEXITY_TIMEOUT=15
PERPLEXITY_MAX_TOKENS=2000
```

### 1.3 Tests POC (1-2h)

**Objectif**: Valider connectivity et performance

**Tests à Implémenter**:

- [ ] Test connexion API Perplexity
- [ ] Benchmark latence vs autres services
- [ ] Validation format réponses avec citations
- [ ] Test gestion erreurs et timeouts

## 📋 Phase 2: Intégration Triple Validation

**Durée**: 6-8 heures | **Priorité**: Critique

### 2.1 Mise à Jour AlloraMind (3-4h)

**Objectif**: Intégrer Perplexity dans le système de scoring

**Fichiers Modifiés**:

- [ ] `allora/allora_mind.py` - Logique triple validation
- [ ] Méthode `calculate_validation_score()` étendue
- [ ] Méthode `get_dynamic_weights()` mise à jour

**Nouveau Système de Scoring**:

```python
def calculate_validation_score(self, hyperbolic_review, openrouter_review, perplexity_review, volatility=None):
    weights = self.get_dynamic_weights_triple(volatility)
    # Hyperbolic: 40%, OpenRouter: 35%, Perplexity: 25%
    # Perplexity weight augmente si événements récents détectés
```

### 2.2 Logique de Poids Dynamiques (2h)

**Objectif**: Optimiser les poids selon contexte marché

**Algorithme de Pondération**:

```python
def get_dynamic_weights_triple(self, volatility, market_events=None):
    base_weights = {
        'hyperbolic': 0.40,
        'openrouter': 0.35,
        'perplexity': 0.25
    }

    # Augmenter Perplexity si événements récents
    if market_events and market_events.get('recent_news_impact') > 0.3:
        return {
            'hyperbolic': 0.30,
            'openrouter': 0.30,
            'perplexity': 0.40  # Plus de poids pour données temps réel
        }

    # Ajustement volatilité standard
    # ...
```

### 2.3 Gestion d'Erreurs et Fallback (1-2h)

**Objectif**: Resilience du système triple

**Scenarios de Fallback**:

- [ ] Perplexity indisponible → Mode dual (Hyperbolic + OpenRouter)
- [ ] Timeout Perplexity → Skip avec warning, continuer validation
- [ ] Rate limit → Retry avec backoff exponentiel
- [ ] API error → Log détaillé, graceful degradation

## 📋 Phase 3: Optimisation & Production

**Durée**: 4-6 heures | **Priorité**: Haute

### 3.1 Prompts Spécialisés Trading (2h)

**Objectif**: Optimiser les prompts pour validation trading

**Prompts Templates**:

```python
MARKET_RESEARCH_PROMPT = """
Analyser les facteurs de marché actuels pour {token}:

1. ACTUALITÉS RÉCENTES (24h):
   - Événements réglementaires
   - Annonces corporates
   - Mouvements institutionnels

2. SENTIMENT MARCHÉ:
   - Tendance générale crypto
   - Corrélations macro-économiques
   - Indicateurs on-chain

3. ÉVALUATION RISQUE:
   - Facteurs baissiers immédiats
   - Catalyseurs haussiers potentiels
   - Niveau de conviction (1-10)

Format réponse JSON avec citations sources.
"""
```

### 3.2 Monitoring et Métriques (1-2h)

**Objectif**: Tracking performance triple validation

**Métriques à Suivre**:

- [ ] Latence moyenne par service
- [ ] Taux d'accord entre validateurs
- [ ] Impact Perplexity sur win rate
- [ ] Coût par validation (tokens)
- [ ] Citations sources utilisées

**Dashboard Extensions**:

- [ ] Ajout métriques Perplexity dans interface
- [ ] Graphiques consensus 3 services
- [ ] Logs sources citées par trade

### 3.3 Tests d'Intégration Complets (1-2h)

**Objectif**: Validation end-to-end système

**Suite de Tests**:

- [ ] Test cycle complet trading avec Perplexity
- [ ] Test scenarios de charge (rate limits)
- [ ] Test resilience (pannes partielles)
- [ ] Validation métriques vs baseline

## 🎯 Points de Contrôle et Validation

### Checkpoint 1 (Fin Phase 1)

**Critères de Succès**:

- [ ] ✅ Perplexity API connectivity fonctionnel
- [ ] ✅ Format réponse standardisé
- [ ] ✅ Latence acceptable (<5s médiane)
- [ ] ✅ Citations sources fonctionnelles

### Checkpoint 2 (Fin Phase 2)

**Critères de Succès**:

- [ ] ✅ Triple validation opérationnelle
- [ ] ✅ Fallback graceful testé
- [ ] ✅ Poids dynamiques équilibrés
- [ ] ✅ Aucune régression performance

### Checkpoint 3 (Fin Phase 3)

**Critères de Succès**:

- [ ] ✅ Win rate ≥ baseline actuel
- [ ] ✅ Monitoring complet déployé
- [ ] ✅ Documentation mise à jour
- [ ] ✅ Tests production validés

## 🔧 Configuration Production Recommandée

### Variables d'Environnement Optimales

```bash
# Perplexity Configuration
PERPLEXITY_API_KEY=your_api_key
PERPLEXITY_MODEL=sonar-pro                    # Modèle recherche avancée
PERPLEXITY_BASE_WEIGHT=0.25                   # Poids initial 25%
PERPLEXITY_TIMEOUT=10                         # Timeout 10s
PERPLEXITY_MAX_TOKENS=1500                    # Limite tokens
PERPLEXITY_RETRY_ATTEMPTS=3                   # Tentatives retry
PERPLEXITY_BACKOFF_FACTOR=1.5                 # Facteur backoff

# Seuils Triple Validation
TRIPLE_VALIDATION_THRESHOLD=0.55              # Seuil consensus 3 services
PERPLEXITY_CONFIDENCE_MIN=60                  # Confiance minimum
PERPLEXITY_SOURCE_CITATIONS_MIN=2             # Citations minimum requises
```

### Monitoring KPIs

```bash
# Métriques Performance
TRACK_PERPLEXITY_LATENCY=True
TRACK_CITATION_QUALITY=True
TRACK_CONSENSUS_ACCURACY=True
LOG_SOURCE_ATTRIBUTION=True
```

## 🚨 Risques et Mitigation

| **Risque**                      | **Impact**    | **Probabilité** | **Mitigation**                    |
| ------------------------------- | ------------- | --------------- | --------------------------------- |
| **Latence élevée Perplexity**   | Performance   | Moyen           | Timeout optimal + cache réponses  |
| **Coût tokens élevé**           | Budget        | Faible          | Rate limiting + prompts optimisés |
| **Rate limits API**             | Disponibilité | Moyen           | Retry logic + fallback dual       |
| **Qualité citations variables** | Confiance     | Faible          | Validation sources + scoring      |

## 📚 Livrables Finaux

### Code

- [ ] `strategy/perplexity_reviewer.py` - Service complet
- [ ] `allora/allora_mind.py` - Triple validation intégrée
- [ ] `utils/env_loader.py` - Configuration étendue
- [ ] `tests/test_perplexity_integration.py` - Suite tests

### Documentation

- [ ] Guide configuration Perplexity API
- [ ] Documentation prompts spécialisés
- [ ] Métriques monitoring explained
- [ ] Troubleshooting guide

### Monitoring

- [ ] Dashboard métriques triple validation
- [ ] Alertes rate limits et erreurs
- [ ] Logs performance et consensus
- [ ] Reporting coûts API

## 🚀 Plan d'Exécution Recommandé

**Semaine 1**: Phase 1 (POC)

- Implémentation service de base
- Tests connectivity
- Validation concept

**Semaine 2**: Phase 2 (Intégration)

- Triple validation logic
- Tests intégration
- Fallback scenarios

**Semaine 3**: Phase 3 (Production)

- Optimisation prompts
- Monitoring deployment
- Documentation finale

**Timeline Total**: 3 semaines avec 4-6h/semaine effort soutenu

---

**Status Plan**: ✅ **READY FOR EXECUTION**  
**Risk Level**: **LOW** - Extension d'architecture existante  
**Dependencies**: Clé API Perplexity requise
