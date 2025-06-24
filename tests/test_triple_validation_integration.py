import unittest
import os
from unittest.mock import Mock, patch, MagicMock
from allora.allora_mind import AlloraMind
from strategy.perplexity_reviewer import PerplexityReviewer


class TestTripleValidationIntegration(unittest.TestCase):
    def setUp(self):
        """Setup test environment with mock OrderManager"""
        self.mock_manager = Mock()
        self.mock_manager.get_volatility.return_value = 0.025
        
        # Mock API keys
        self.hyperbolic_key = "test_hyperbolic_key"
        self.openrouter_key = "test_openrouter_key"
        self.perplexity_key = "test_perplexity_key"
        
        # Initialize AlloraMind with all three services
        self.allora_mind = AlloraMind(
            manager=self.mock_manager,
            allora_upshot_key="test_allora_key",
            hyperbolic_api_key=self.hyperbolic_key,
            openrouter_api_key=self.openrouter_key,
            openrouter_model="test-model",
            perplexity_api_key=self.perplexity_key,
            perplexity_model="sonar-pro"
        )
        
        # Test trade data
        self.test_trade_data = {
            'token': 'BTC',
            'current_price': 45000.00,
            'allora_prediction': 46500.00,
            'prediction_diff': 3.33,
            'direction': 'BUY',
            'market_condition': 'ANALYSIS'
        }
        
    def test_all_services_initialized(self):
        """Test that all three AI services are properly initialized"""
        self.assertIsNotNone(self.allora_mind.hyperbolic_reviewer)
        self.assertIsNotNone(self.allora_mind.openrouter_reviewer)
        self.assertIsNotNone(self.allora_mind.perplexity_reviewer)
        
        # Verify service types
        self.assertEqual(self.allora_mind.hyperbolic_reviewer.__class__.__name__, "HyperbolicReviewer")
        self.assertEqual(self.allora_mind.openrouter_reviewer.__class__.__name__, "OpenRouterReviewer")
        self.assertEqual(self.allora_mind.perplexity_reviewer.__class__.__name__, "PerplexityReviewer")
        
    def test_triple_validation_weights_default(self):
        """Test default weight distribution for triple validation"""
        weights = self.allora_mind.get_dynamic_weights(volatility=0.02)
        
        # Should have all three services
        self.assertIn('hyperbolic', weights)
        self.assertIn('openrouter', weights)
        self.assertIn('perplexity', weights)
        
        # Check default weights sum to 1.0
        total_weight = sum(weights.values())
        self.assertAlmostEqual(total_weight, 1.0, places=2)
        
        # Check expected default distribution
        self.assertAlmostEqual(weights['hyperbolic'], 0.40, places=2)
        self.assertAlmostEqual(weights['openrouter'], 0.35, places=2)
        self.assertAlmostEqual(weights['perplexity'], 0.25, places=2)
        
    def test_triple_validation_weights_high_volatility(self):
        """Test weight adjustment for high volatility scenarios"""
        weights = self.allora_mind.get_dynamic_weights(volatility=0.05)  # High volatility
        
        # High volatility should favor OpenRouter + Perplexity
        self.assertLess(weights['hyperbolic'], 0.30)  # Should be reduced
        self.assertGreater(weights['openrouter'], 0.40)  # Should be increased
        self.assertGreater(weights['perplexity'], 0.25)  # Should be increased
        
    def test_triple_validation_weights_market_events(self):
        """Test weight adjustment for market events"""
        market_events = {
            'recent_news_impact': 0.4,  # High news impact
            'regulatory_risk': 'medium',
            'technical_outlook': 'bullish'
        }
        
        weights = self.allora_mind.get_dynamic_weights(volatility=0.02, market_events=market_events)
        
        # High news impact should favor Perplexity
        self.assertEqual(weights['perplexity'], 0.40)  # Should get highest weight
        self.assertEqual(weights['hyperbolic'], 0.30)
        self.assertEqual(weights['openrouter'], 0.30)
        
    def test_triple_validation_score_calculation(self):
        """Test triple validation score calculation with all services"""
        # Mock reviews from all three services
        hyperbolic_review = {
            'approval': True,
            'confidence': 80,
            'risk_score': 3,
            'reasoning': 'Strong technical indicators'
        }
        
        openrouter_review = {
            'approval': True,
            'confidence': 75,
            'risk_score': 4,
            'reasoning': 'Positive market sentiment'
        }
        
        perplexity_review = {
            'approval': True,
            'confidence': 85,
            'risk_score': 2,
            'reasoning': 'Recent news supports bullish outlook',
            'source_quality': 'high',
            'citations_count': 3,
            'market_events': {
                'recent_news_impact': 0.2,
                'regulatory_risk': 'low'
            }
        }
        
        score = self.allora_mind.calculate_validation_score(
            hyperbolic_review, openrouter_review, volatility=0.02, perplexity_review=perplexity_review
        )
        
        # Score should be moderately high given all positive reviews (but realistic)
        self.assertGreater(score, 0.5)  # Realistic expectation
        self.assertLessEqual(score, 1.0)
        
    def test_triple_validation_with_citation_bonus(self):
        """Test that Perplexity gets citation bonus in scoring"""
        base_review = {
            'approval': True,
            'confidence': 70,
            'risk_score': 5,
            'reasoning': 'Analysis complete'
        }
        
        # Review with high quality sources
        perplexity_high_quality = {
            **base_review,
            'source_quality': 'high',
            'citations_count': 4
        }
        
        # Review with low quality sources
        perplexity_low_quality = {
            **base_review,
            'source_quality': 'low',
            'citations_count': 1
        }
        
        score_high = self.allora_mind.calculate_validation_score(
            base_review, base_review, volatility=0.02, perplexity_review=perplexity_high_quality
        )
        
        score_low = self.allora_mind.calculate_validation_score(
            base_review, base_review, volatility=0.02, perplexity_review=perplexity_low_quality
        )
        
        # High quality sources should result in higher score
        self.assertGreater(score_high, score_low)
        
    def test_fallback_to_dual_validation(self):
        """Test fallback when Perplexity is not available"""
        # Create AlloraMind without Perplexity
        allora_mind_dual = AlloraMind(
            manager=self.mock_manager,
            allora_upshot_key="test_allora_key",
            hyperbolic_api_key=self.hyperbolic_key,
            openrouter_api_key=self.openrouter_key,
            openrouter_model="test-model",
            perplexity_api_key=None  # No Perplexity
        )
        
        self.assertIsNone(allora_mind_dual.perplexity_reviewer)
        
        weights = allora_mind_dual.get_dynamic_weights(volatility=0.02)
        
        # Should only have hyperbolic and openrouter
        self.assertIn('hyperbolic', weights)
        self.assertIn('openrouter', weights)
        self.assertNotIn('perplexity', weights)
        
        # Weights should sum to 1.0
        total_weight = sum(weights.values())
        self.assertAlmostEqual(total_weight, 1.0, places=2)
        
    def test_single_service_fallback(self):
        """Test fallback when only one service is available"""
        # Create AlloraMind with only Perplexity
        allora_mind_single = AlloraMind(
            manager=self.mock_manager,
            allora_upshot_key="test_allora_key",
            hyperbolic_api_key=None,
            openrouter_api_key=None,
            openrouter_model="test-model",
            perplexity_api_key=self.perplexity_key
        )
        
        self.assertIsNone(allora_mind_single.hyperbolic_reviewer)
        self.assertIsNone(allora_mind_single.openrouter_reviewer)
        self.assertIsNotNone(allora_mind_single.perplexity_reviewer)
        
        weights = allora_mind_single.get_dynamic_weights(volatility=0.02)
        
        # Should only have perplexity with full weight
        self.assertEqual(weights, {'perplexity': 1.0})
        
    def test_no_services_raises_error(self):
        """Test that error is raised when no AI services are configured"""
        with self.assertRaises(ValueError) as context:
            AlloraMind(
                manager=self.mock_manager,
                allora_upshot_key="test_allora_key",
                hyperbolic_api_key=None,
                openrouter_api_key=None,
                openrouter_model="test-model",
                perplexity_api_key=None
            )
        
        self.assertIn("At least one AI validation service must be configured", str(context.exception))
        
    def test_validation_score_with_mixed_approvals(self):
        """Test validation score when services give mixed approvals"""
        # Mixed reviews: 2 approve, 1 rejects
        hyperbolic_review = {
            'approval': True,
            'confidence': 90,
            'risk_score': 2,
            'reasoning': 'Strong bullish signals'
        }
        
        openrouter_review = {
            'approval': False,
            'confidence': 60,
            'risk_score': 7,
            'reasoning': 'High market risk detected'
        }
        
        perplexity_review = {
            'approval': True,
            'confidence': 80,
            'risk_score': 3,
            'reasoning': 'Recent positive developments',
            'source_quality': 'medium',
            'citations_count': 2
        }
        
        score = self.allora_mind.calculate_validation_score(
            hyperbolic_review, openrouter_review, volatility=0.02, perplexity_review=perplexity_review
        )
        
        # Score should be moderate given mixed signals
        self.assertGreater(score, 0.3)
        self.assertLess(score, 0.8)
        
    @patch.dict(os.environ, {
        'TRIPLE_HYPERBOLIC_WEIGHT': '0.50',
        'TRIPLE_OPENROUTER_WEIGHT': '0.30',
        'PERPLEXITY_BASE_WEIGHT': '0.20'
    })
    def test_custom_weight_configuration(self):
        """Test that custom weights from environment are respected"""
        allora_mind_custom = AlloraMind(
            manager=self.mock_manager,
            allora_upshot_key="test_allora_key",
            hyperbolic_api_key=self.hyperbolic_key,
            openrouter_api_key=self.openrouter_key,
            openrouter_model="test-model",
            perplexity_api_key=self.perplexity_key
        )
        
        weights = allora_mind_custom.get_dynamic_weights(volatility=0.02)
        
        # Should use custom weights
        self.assertAlmostEqual(weights['hyperbolic'], 0.50, places=2)
        self.assertAlmostEqual(weights['openrouter'], 0.30, places=2)
        self.assertAlmostEqual(weights['perplexity'], 0.20, places=2)


if __name__ == '__main__':
    # Set up test environment
    os.environ['HL_SECRET_KEY'] = 'test_secret_key'
    os.environ['ALLORA_UPSHOT_KEY'] = 'test_allora_key'
    
    # Run tests
    unittest.main(verbosity=2) 