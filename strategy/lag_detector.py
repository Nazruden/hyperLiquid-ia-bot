import time
import os
from typing import Dict, Optional, Tuple

class LagDetector:
    """
    Détecteur de lag pour les prédictions AI
    Rejette les prédictions obsolètes selon des critères configurables
    """
    
    def __init__(self):
        # Configuration depuis les variables d'environnement
        self.max_prediction_age = float(os.getenv('MAX_PREDICTION_AGE_SECONDS', '30'))
        self.max_api_latency = float(os.getenv('MAX_API_LATENCY_SECONDS', '5'))
        self.lag_warning_threshold = float(os.getenv('LAG_WARNING_THRESHOLD_SECONDS', '15'))
        
        # Compteurs pour monitoring
        self.total_predictions = 0
        self.rejected_by_age = 0
        self.rejected_by_latency = 0
        self.warnings_issued = 0
        
        print(f"LagDetector initialized:")
        print(f"  Max prediction age: {self.max_prediction_age}s")
        print(f"  Max API latency: {self.max_api_latency}s") 
        print(f"  Warning threshold: {self.lag_warning_threshold}s")
    
    def check_prediction_freshness(self, prediction_data: Dict) -> Tuple[bool, str, Dict]:
        """
        Vérifie si une prédiction est suffisamment fraîche pour être utilisée
        
        Args:
            prediction_data: Dictionnaire contenant timestamp, api_latency, etc.
            
        Returns:
            Tuple[bool, str, Dict]: (is_valid, rejection_reason, metrics)
        """
        self.total_predictions += 1
        current_time = time.time()
        
        # Extraire les métadonnées temporelles
        prediction_timestamp = prediction_data.get('timestamp', current_time)
        api_latency = prediction_data.get('api_latency', 0)
        request_time = prediction_data.get('request_time', current_time)
        
        # Calculer l'âge de la prédiction
        prediction_age = current_time - prediction_timestamp
        
        # Métriques pour retour
        metrics = {
            'prediction_age_seconds': prediction_age,
            'api_latency_seconds': api_latency,
            'current_time': current_time,
            'prediction_timestamp': prediction_timestamp,
            'is_stale': False,
            'is_slow_api': False,
            'warning': False
        }
        
        # Vérification 1: Age de la prédiction
        if prediction_age > self.max_prediction_age:
            self.rejected_by_age += 1
            metrics['is_stale'] = True
            reason = f"Prediction too old: {prediction_age:.1f}s > {self.max_prediction_age}s"
            print(f"⚠️ LAG REJECTION: {reason}")
            return False, reason, metrics
        
        # Vérification 2: Latence API excessive
        if api_latency > self.max_api_latency:
            self.rejected_by_latency += 1
            metrics['is_slow_api'] = True
            reason = f"API latency too high: {api_latency:.1f}s > {self.max_api_latency}s"
            print(f"⚠️ LAG REJECTION: {reason}")
            return False, reason, metrics
        
        # Avertissement pour latence élevée mais acceptable
        if prediction_age > self.lag_warning_threshold or api_latency > (self.max_api_latency * 0.7):
            self.warnings_issued += 1
            metrics['warning'] = True
            print(f"⚡ LAG WARNING: Age={prediction_age:.1f}s, Latency={api_latency:.1f}s")
        
        # Prédiction acceptée
        return True, "Fresh prediction", metrics
    
    def get_lag_statistics(self) -> Dict:
        """
        Retourne les statistiques de performance du détecteur de lag
        """
        rejection_rate = 0
        if self.total_predictions > 0:
            rejection_rate = ((self.rejected_by_age + self.rejected_by_latency) / self.total_predictions) * 100
        
        return {
            'total_predictions_checked': self.total_predictions,
            'rejected_by_age': self.rejected_by_age,
            'rejected_by_latency': self.rejected_by_latency,
            'total_rejections': self.rejected_by_age + self.rejected_by_latency,
            'warnings_issued': self.warnings_issued,
            'rejection_rate_percent': round(rejection_rate, 2),
            'configuration': {
                'max_prediction_age_seconds': self.max_prediction_age,
                'max_api_latency_seconds': self.max_api_latency,
                'lag_warning_threshold_seconds': self.lag_warning_threshold
            }
        }
    
    def reset_statistics(self):
        """
        Remet à zéro les compteurs statistiques
        """
        self.total_predictions = 0
        self.rejected_by_age = 0
        self.rejected_by_latency = 0
        self.warnings_issued = 0
        print("Lag detection statistics reset")
    
    def is_prediction_too_old(self, prediction_timestamp: float) -> bool:
        """
        Méthode utilitaire pour vérifier uniquement l'âge
        """
        age = time.time() - prediction_timestamp
        return age > self.max_prediction_age
    
    def calculate_freshness_score(self, prediction_data: Dict) -> float:
        """
        Calcule un score de fraîcheur (0.0-1.0) pour la prédiction
        Plus le score est élevé, plus la prédiction est fraîche
        """
        current_time = time.time()
        prediction_timestamp = prediction_data.get('timestamp', current_time)
        api_latency = prediction_data.get('api_latency', 0)
        
        prediction_age = current_time - prediction_timestamp
        
        # Score basé sur l'âge (0.0 = max_age, 1.0 = fraîche)
        age_score = max(0.0, 1.0 - (prediction_age / self.max_prediction_age))
        
        # Score basé sur la latence API (0.0 = max_latency, 1.0 = instantané)
        latency_score = max(0.0, 1.0 - (api_latency / self.max_api_latency))
        
        # Score composite (moyenne pondérée)
        freshness_score = (age_score * 0.7) + (latency_score * 0.3)
        
        return min(1.0, max(0.0, freshness_score))
    
    def log_prediction_timing(self, token: str, prediction_data: Dict, decision: str):
        """
        Log détaillé des timings pour analyse des performances
        """
        metrics = {
            'token': token,
            'decision': decision,
            'prediction_age': time.time() - prediction_data.get('timestamp', time.time()),
            'api_latency': prediction_data.get('api_latency', 0),
            'freshness_score': self.calculate_freshness_score(prediction_data)
        }
        
        print(f"🕐 TIMING LOG [{token}]: "
              f"Age={metrics['prediction_age']:.2f}s, "
              f"Latency={metrics['api_latency']:.2f}s, "
              f"Freshness={metrics['freshness_score']:.3f}, "
              f"Decision={decision}")
        
        return metrics 