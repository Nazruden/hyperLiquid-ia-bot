import unittest
import os
import time
from unittest.mock import patch, MagicMock
from strategy.lag_detector import LagDetector

class TestLagDetection(unittest.TestCase):
    def setUp(self):
        """Configuration pour les tests"""
        # Variables d'environnement de test
        self.test_env = {
            'MAX_PREDICTION_AGE_SECONDS': '30',
            'MAX_API_LATENCY_SECONDS': '5',
            'LAG_WARNING_THRESHOLD_SECONDS': '15'
        }
        
        with patch.dict(os.environ, self.test_env):
            self.lag_detector = LagDetector()
    
    def tearDown(self):
        """Nettoyage après les tests"""
        pass
    
    def test_initialization(self):
        """Test l'initialisation du détecteur de lag"""
        self.assertEqual(self.lag_detector.max_prediction_age, 30.0)
        self.assertEqual(self.lag_detector.max_api_latency, 5.0)
        self.assertEqual(self.lag_detector.lag_warning_threshold, 15.0)
        self.assertEqual(self.lag_detector.total_predictions, 0)
        self.assertEqual(self.lag_detector.rejected_by_age, 0)
        self.assertEqual(self.lag_detector.rejected_by_latency, 0)
        self.assertEqual(self.lag_detector.warnings_issued, 0)
    
    def test_fresh_prediction_accepted(self):
        """Test qu'une prédiction fraîche est acceptée"""
        current_time = time.time()
        prediction_data = {
            'prediction': 50000.0,
            'timestamp': current_time,  # Fraîche
            'api_latency': 1.0,  # Latence acceptable
            'request_time': current_time - 1.0
        }
        
        is_valid, reason, metrics = self.lag_detector.check_prediction_freshness(prediction_data)
        
        self.assertTrue(is_valid)
        self.assertEqual(reason, "Fresh prediction")
        self.assertFalse(metrics['is_stale'])
        self.assertFalse(metrics['is_slow_api'])
        self.assertEqual(self.lag_detector.total_predictions, 1)
        self.assertEqual(self.lag_detector.rejected_by_age, 0)
        self.assertEqual(self.lag_detector.rejected_by_latency, 0)
    
    def test_old_prediction_rejected(self):
        """Test qu'une prédiction trop ancienne est rejetée"""
        current_time = time.time()
        old_timestamp = current_time - 35  # 35 secondes = trop vieux
        
        prediction_data = {
            'prediction': 50000.0,
            'timestamp': old_timestamp,
            'api_latency': 1.0,
            'request_time': old_timestamp
        }
        
        is_valid, reason, metrics = self.lag_detector.check_prediction_freshness(prediction_data)
        
        self.assertFalse(is_valid)
        self.assertIn("Prediction too old", reason)
        self.assertTrue(metrics['is_stale'])
        self.assertFalse(metrics['is_slow_api'])
        self.assertEqual(self.lag_detector.total_predictions, 1)
        self.assertEqual(self.lag_detector.rejected_by_age, 1)
        self.assertEqual(self.lag_detector.rejected_by_latency, 0)
    
    def test_high_latency_rejected(self):
        """Test qu'une prédiction avec latence élevée est rejetée"""
        current_time = time.time()
        prediction_data = {
            'prediction': 50000.0,
            'timestamp': current_time,
            'api_latency': 6.0,  # 6 secondes > 5 secondes max
            'request_time': current_time - 6.0
        }
        
        is_valid, reason, metrics = self.lag_detector.check_prediction_freshness(prediction_data)
        
        self.assertFalse(is_valid)
        self.assertIn("API latency too high", reason)
        self.assertFalse(metrics['is_stale'])
        self.assertTrue(metrics['is_slow_api'])
        self.assertEqual(self.lag_detector.total_predictions, 1)
        self.assertEqual(self.lag_detector.rejected_by_age, 0)
        self.assertEqual(self.lag_detector.rejected_by_latency, 1)
    
    def test_warning_threshold_triggered(self):
        """Test qu'un avertissement est émis pour des prédictions proches du seuil"""
        current_time = time.time()
        prediction_data = {
            'prediction': 50000.0,
            'timestamp': current_time - 18,  # 18 secondes > 15 secondes warning
            'api_latency': 2.0,
            'request_time': current_time - 18 - 2.0
        }
        
        is_valid, reason, metrics = self.lag_detector.check_prediction_freshness(prediction_data)
        
        self.assertTrue(is_valid)  # Accepté mais avec warning
        self.assertEqual(reason, "Fresh prediction")
        self.assertTrue(metrics['warning'])
        self.assertEqual(self.lag_detector.warnings_issued, 1)
    
    def test_warning_high_api_latency(self):
        """Test avertissement pour latence API élevée mais acceptable"""
        current_time = time.time()
        prediction_data = {
            'prediction': 50000.0,
            'timestamp': current_time,
            'api_latency': 4.0,  # 4s > 70% de 5s = 3.5s
            'request_time': current_time - 4.0
        }
        
        is_valid, reason, metrics = self.lag_detector.check_prediction_freshness(prediction_data)
        
        self.assertTrue(is_valid)
        self.assertTrue(metrics['warning'])
        self.assertEqual(self.lag_detector.warnings_issued, 1)
    
    def test_lag_statistics(self):
        """Test le calcul des statistiques de lag"""
        # Simuler plusieurs prédictions
        current_time = time.time()
        
        # Prédiction acceptée
        pred1 = {'timestamp': current_time, 'api_latency': 1.0}
        self.lag_detector.check_prediction_freshness(pred1)
        
        # Prédiction rejetée par âge
        pred2 = {'timestamp': current_time - 35, 'api_latency': 1.0}
        self.lag_detector.check_prediction_freshness(pred2)
        
        # Prédiction rejetée par latence
        pred3 = {'timestamp': current_time, 'api_latency': 6.0}
        self.lag_detector.check_prediction_freshness(pred3)
        
        stats = self.lag_detector.get_lag_statistics()
        
        self.assertEqual(stats['total_predictions_checked'], 3)
        self.assertEqual(stats['rejected_by_age'], 1)
        self.assertEqual(stats['rejected_by_latency'], 1)
        self.assertEqual(stats['total_rejections'], 2)
        self.assertEqual(stats['rejection_rate_percent'], 66.67)  # 2/3 * 100
    
    def test_freshness_score_calculation(self):
        """Test le calcul du score de fraîcheur"""
        current_time = time.time()
        
        # Prédiction très fraîche
        fresh_data = {'timestamp': current_time, 'api_latency': 0.5}
        fresh_score = self.lag_detector.calculate_freshness_score(fresh_data)
        self.assertGreater(fresh_score, 0.9)
        
        # Prédiction ancienne
        old_data = {'timestamp': current_time - 25, 'api_latency': 4.0}
        old_score = self.lag_detector.calculate_freshness_score(old_data)
        self.assertLess(old_score, 0.3)
        
        # Score doit être entre 0 et 1
        self.assertGreaterEqual(fresh_score, 0.0)
        self.assertLessEqual(fresh_score, 1.0)
        self.assertGreaterEqual(old_score, 0.0)
        self.assertLessEqual(old_score, 1.0)
    
    def test_is_prediction_too_old_utility(self):
        """Test la méthode utilitaire is_prediction_too_old"""
        current_time = time.time()
        
        # Prédiction fraîche
        fresh_timestamp = current_time - 10
        self.assertFalse(self.lag_detector.is_prediction_too_old(fresh_timestamp))
        
        # Prédiction ancienne
        old_timestamp = current_time - 35
        self.assertTrue(self.lag_detector.is_prediction_too_old(old_timestamp))
    
    def test_reset_statistics(self):
        """Test la remise à zéro des statistiques"""
        # Générer quelques statistiques
        current_time = time.time()
        pred = {'timestamp': current_time - 35, 'api_latency': 1.0}
        self.lag_detector.check_prediction_freshness(pred)
        
        # Vérifier que des statistiques existent
        self.assertGreater(self.lag_detector.total_predictions, 0)
        
        # Reset
        self.lag_detector.reset_statistics()
        
        # Vérifier que tout est remis à zéro
        self.assertEqual(self.lag_detector.total_predictions, 0)
        self.assertEqual(self.lag_detector.rejected_by_age, 0)
        self.assertEqual(self.lag_detector.rejected_by_latency, 0)
        self.assertEqual(self.lag_detector.warnings_issued, 0)
    
    def test_log_prediction_timing(self):
        """Test le logging des timings de prédiction"""
        current_time = time.time()
        prediction_data = {
            'timestamp': current_time - 5,
            'api_latency': 2.0
        }
        
        metrics = self.lag_detector.log_prediction_timing('BTC', prediction_data, 'ACCEPTED')
        
        self.assertEqual(metrics['token'], 'BTC')
        self.assertEqual(metrics['decision'], 'ACCEPTED')
        self.assertAlmostEqual(metrics['prediction_age'], 5.0, delta=0.1)
        self.assertEqual(metrics['api_latency'], 2.0)
        self.assertIn('freshness_score', metrics)
    
    def test_edge_case_missing_metadata(self):
        """Test le comportement avec métadonnées manquantes"""
        current_time = time.time()
        
        # Données incomplètes
        incomplete_data = {
            'prediction': 50000.0
            # timestamp et api_latency manquants
        }
        
        is_valid, reason, metrics = self.lag_detector.check_prediction_freshness(incomplete_data)
        
        # Devrait être accepté car utilise current_time par défaut
        self.assertTrue(is_valid)
        self.assertIn('prediction_age_seconds', metrics)
        self.assertIn('api_latency_seconds', metrics)

if __name__ == '__main__':
    unittest.main() 