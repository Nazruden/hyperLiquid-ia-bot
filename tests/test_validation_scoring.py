import unittest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from allora.allora_mind import AlloraMind
from unittest.mock import Mock, patch

class TestValidationScoring(unittest.TestCase):
    def setUp(self):
        """Setup pour chaque test"""
        # Mock des composants
        self.mock_manager = Mock()
        self.mock_manager.get_volatility.return_value = 0.025  # Volatilité moyenne
        
        # Variables d'environnement de test
        os.environ['VALIDATION_SCORE_THRESHOLD'] = '0.4'
        os.environ['ADAPTIVE_THRESHOLDS'] = 'True'
        os.environ['HYPERBOLIC_BASE_WEIGHT'] = '0.6'
        os.environ['OPENROUTER_BASE_WEIGHT'] = '0.4'
        
        self.allora_mind = AlloraMind(
            manager=self.mock_manager,
            allora_upshot_key="test_key",
            hyperbolic_api_key="test_key",
            openrouter_api_key="test_key",
            openrouter_model="test_model",
            threshold=0.03
        )
    
    def test_dynamic_weights_normal_volatility(self):
        """Test poids dynamiques avec volatilité normale"""
        weights = self.allora_mind.get_dynamic_weights(0.02)  # Volatilité normale
        
        self.assertEqual(weights['hyperbolic'], 0.6)
        self.assertEqual(weights['openrouter'], 0.4)
    
    def test_dynamic_weights_high_volatility(self):
        """Test poids dynamiques avec haute volatilité"""
        weights = self.allora_mind.get_dynamic_weights(0.05)  # Haute volatilité
        
        self.assertEqual(weights['hyperbolic'], 0.4)
        self.assertEqual(weights['openrouter'], 0.6)
    
    def test_validation_scoring_high_confidence_both_approve(self):
        """Test scoring avec haute confiance et approval des deux"""
        hyperbolic_review = {
            'approval': True,
            'confidence': 85,
            'risk_score': 3
        }
        
        openrouter_review = {
            'approval': True,
            'confidence': 75,
            'risk_score': 4
        }
        
        score = self.allora_mind.calculate_validation_score(
            hyperbolic_review, openrouter_review, volatility=0.025
        )
        
        # Score attendu: 
        # Hyperbolic: (0.85 * 1 * 0.7) * 0.6 = 0.357
        # OpenRouter: (0.75 * 1 * 0.6) * 0.4 = 0.18
        # Total: 0.537
        self.assertGreater(score, 0.5)
        self.assertLess(score, 0.6)
    
    def test_validation_scoring_mixed_approval(self):
        """Test scoring avec approval mixte"""
        hyperbolic_review = {
            'approval': True,
            'confidence': 80,
            'risk_score': 3
        }
        
        openrouter_review = {
            'approval': False,  # Rejet !
            'confidence': 60,
            'risk_score': 7
        }
        
        score = self.allora_mind.calculate_validation_score(
            hyperbolic_review, openrouter_review, volatility=0.025
        )
        
        # Seulement Hyperbolic contribue positivement
        # Score attendu: (0.8 * 1 * 0.7) * 0.6 + (0.6 * 0 * 0.3) * 0.4 = 0.336
        self.assertLess(score, 0.4)  # Devrait être rejeté avec seuil 0.4
    
    def test_validation_scoring_low_confidence(self):
        """Test scoring avec basse confiance"""
        hyperbolic_review = {
            'approval': True,
            'confidence': 45,
            'risk_score': 6
        }
        
        openrouter_review = {
            'approval': True,
            'confidence': 50,
            'risk_score': 5
        }
        
        score = self.allora_mind.calculate_validation_score(
            hyperbolic_review, openrouter_review, volatility=0.025
        )
        
        # Score attendu faible malgré approval
        self.assertLess(score, 0.3)
    
    def test_adaptive_threshold_low_volatility(self):
        """Test seuil adaptatif avec basse volatilité (marché calme)"""
        threshold = self.allora_mind.get_adaptive_threshold(0.01)  # Très calme
        
        # Marché calme = plus strict (seuil plus élevé)
        self.assertGreater(threshold, 0.5)  # Plus strict que base
        self.assertLessEqual(threshold, 0.75)  # Plafonné
    
    def test_adaptive_threshold_high_volatility(self):
        """Test seuil adaptatif avec haute volatilité"""
        threshold = self.allora_mind.get_adaptive_threshold(0.06)  # Très volatil
        
        # Marché volatil = plus permissif (seuil plus bas)
        self.assertLess(threshold, 0.4)  # Plus permissif que base
        self.assertGreaterEqual(threshold, 0.25)  # Plancher système (Sprint 1.2)
    
    def test_adaptive_threshold_medium_volatility(self):
        """Test seuil adaptatif avec volatilité moyenne"""
        threshold = self.allora_mind.get_adaptive_threshold(0.025)  # Moyenne
        
        # Interpolation linéaire autour de la base
        base_threshold = float(os.getenv('VALIDATION_SCORE_THRESHOLD', '0.5'))
        self.assertAlmostEqual(threshold, base_threshold, delta=0.1)
    
    def test_single_provider_scoring(self):
        """Test scoring avec un seul provider actif"""
        # Test avec seulement Hyperbolic
        hyperbolic_review = {
            'approval': True,
            'confidence': 80,
            'risk_score': 3
        }
        
        score = self.allora_mind.calculate_validation_score(
            hyperbolic_review, None, volatility=0.025
        )
        
        # Devrait avoir un score significatif avec un seul provider
        self.assertGreater(score, 0.4)
    
    def test_no_provider_response(self):
        """Test scoring sans réponse des providers"""
        score = self.allora_mind.calculate_validation_score(
            None, None, volatility=0.025
        )
        
        # Score devrait être 0
        self.assertEqual(score, 0.0)
    
    def test_risk_factor_calculation(self):
        """Test calcul du facteur de risque"""
        # Risque faible (score 2/10)
        low_risk_review = {
            'approval': True,
            'confidence': 80,
            'risk_score': 2
        }
        
        # Risque élevé (score 8/10)
        high_risk_review = {
            'approval': True,
            'confidence': 80,
            'risk_score': 8
        }
        
        low_risk_score = self.allora_mind.calculate_validation_score(
            low_risk_review, None, volatility=0.025
        )
        
        high_risk_score = self.allora_mind.calculate_validation_score(
            high_risk_review, None, volatility=0.025
        )
        
        # Score avec faible risque devrait être supérieur
        self.assertGreater(low_risk_score, high_risk_score)
    
    def test_validation_decision_integration(self):
        """Test intégration complète de la décision de validation"""
        # Setup test data
        hyperbolic_review = {
            'approval': True,
            'confidence': 75,
            'risk_score': 3
        }
        
        openrouter_review = {
            'approval': True,
            'confidence': 70,
            'risk_score': 4
        }
        
        volatility = 0.02
        
        # Calcul du score et seuil
        score = self.allora_mind.calculate_validation_score(
            hyperbolic_review, openrouter_review, volatility
        )
        
        threshold = self.allora_mind.get_adaptive_threshold(volatility)
        
        # Décision
        should_approve = score >= threshold
        
        # Log pour debugging
        print(f"Score: {score:.3f}, Threshold: {threshold:.3f}, Decision: {should_approve}")
        
        # Validation
        self.assertIsInstance(should_approve, bool)
        self.assertGreater(score, 0)
        self.assertGreater(threshold, 0)

class TestEnvironmentVariables(unittest.TestCase):
    """Test des variables d'environnement et configuration"""
    
    def test_environment_variables_loaded(self):
        """Test que les nouvelles variables d'environnement sont chargées"""
        from utils.env_loader import EnvLoader
        
        # Set all required environment variables for test
        os.environ['HL_SECRET_KEY'] = 'test_secret'
        os.environ['ALLORA_UPSHOT_KEY'] = 'test_allora'
        os.environ['HYPERBOLIC_API_KEY'] = 'test_hyperbolic'
        
        # Use testnet configuration values
        os.environ['VALIDATION_SCORE_THRESHOLD'] = '0.55'
        os.environ['ADAPTIVE_THRESHOLDS'] = 'True'
        os.environ['HYPERBOLIC_BASE_WEIGHT'] = '0.6'
        os.environ['OPENROUTER_BASE_WEIGHT'] = '0.4'
        
        env_loader = EnvLoader()
        config = env_loader.get_config()
        
        self.assertEqual(config['validation_score_threshold'], 0.55)
        self.assertTrue(config['adaptive_thresholds'])
        self.assertEqual(config['hyperbolic_base_weight'], 0.6)
        self.assertEqual(config['openrouter_base_weight'], 0.4)

if __name__ == '__main__':
    print("🧪 Testing Sprint 1.1: Validation Logic Flexible")
    print("=" * 50)
    
    # Run tests avec verbose output
    unittest.main(verbosity=2) 