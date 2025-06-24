import unittest
import os
import json
from unittest.mock import patch, MagicMock, Mock
import requests

# Import the classes to test
from strategy.perplexity_reviewer import PerplexityReviewer


class TestPerplexityIntegration(unittest.TestCase):
    def setUp(self):
        """Setup test environment"""
        self.test_api_key = "test_perplexity_key"
        self.reviewer = PerplexityReviewer(self.test_api_key, model="sonar-pro")
        
        # Test trade data
        self.test_trade_data = {
            'token': 'BTC',
            'current_price': 45000.50,
            'allora_prediction': 46500.00,
            'prediction_diff': 3.33,
            'direction': 'BUY',
            'market_condition': 'ANALYSIS'
        }
        
        # Mock successful API response
        self.mock_api_response = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps({
                            "approval": True,
                            "confidence": 75,
                            "risk_score": 3,
                            "reasoning": "Recent market analysis shows positive sentiment for BTC with strong institutional support",
                            "market_events": {
                                "recent_news_impact": 0.2,
                                "regulatory_risk": "low",
                                "technical_outlook": "bullish"
                            },
                            "sources_analyzed": ["coindesk.com", "bloomberg.com"]
                        })
                    }
                }
            ],
            "citations": [
                {"url": "https://coindesk.com/bitcoin-news", "title": "Bitcoin Shows Strength"},
                {"url": "https://bloomberg.com/crypto", "title": "Institutional Interest Rising"}
            ]
        }
        
    def test_initialization(self):
        """Test PerplexityReviewer initialization"""
        self.assertEqual(self.reviewer.api_key, self.test_api_key)
        self.assertEqual(self.reviewer.model, "sonar-pro")
        self.assertEqual(self.reviewer.api_url, "https://api.perplexity.ai/chat/completions")
        self.assertIn("Authorization", self.reviewer.headers)
        self.assertEqual(self.reviewer.headers["Authorization"], f"Bearer {self.test_api_key}")
        
    def test_model_info(self):
        """Test get_model_info method"""
        info = self.reviewer.get_model_info()
        self.assertEqual(info["provider"], "Perplexity")
        self.assertEqual(info["model"], "sonar-pro")
        self.assertIn("real_time_search", info["features"])
        self.assertIn("citations", info["features"])
        
    @patch('requests.post')
    def test_successful_review_trade(self, mock_post):
        """Test successful trade review with proper response"""
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.mock_api_response
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        # Perform review
        result = self.reviewer.review_trade(self.test_trade_data)
        
        # Verify result
        self.assertIsNotNone(result)
        self.assertTrue(result['approval'])
        self.assertEqual(result['confidence'], 75)
        self.assertEqual(result['risk_score'], 3)
        self.assertIn('citations', result)
        self.assertEqual(result['citations_count'], 2)
        self.assertIn('source_quality', result)  # Phase 3 adds source_quality instead of has_citations
        
        # Verify API call
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        self.assertIn('return_citations', call_args[1]['json'])
        self.assertTrue(call_args[1]['json']['return_citations'])
        
    @patch('requests.post')
    def test_api_unauthorized_error(self, mock_post):
        """Test handling of unauthorized API error"""
        # Mock 401 response
        mock_response = Mock()
        mock_response.status_code = 401
        mock_post.return_value = mock_response
        mock_post.return_value.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_response)
        
        result = self.reviewer.review_trade(self.test_trade_data)
        
        self.assertIsNone(result)
        
    @patch('requests.post')
    @patch('time.sleep')  # Mock sleep to speed up tests
    def test_rate_limit_retry_logic(self, mock_sleep, mock_post):
        """Test rate limit handling with retry logic"""
        # Mock rate limit response on first call, success on second
        mock_response_429 = Mock()
        mock_response_429.status_code = 429
        mock_response_429.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_response_429)
        
        mock_response_200 = Mock()
        mock_response_200.status_code = 200
        mock_response_200.json.return_value = self.mock_api_response
        mock_response_200.raise_for_status.return_value = None
        
        # First call rate limited, second call succeeds
        mock_post.side_effect = [mock_response_429, mock_response_200]
        
        result = self.reviewer.review_trade(self.test_trade_data)
        
        # Should have retried and succeeded
        self.assertIsNotNone(result)
        self.assertEqual(mock_post.call_count, 2)
        mock_sleep.assert_called_once()
        
    def test_prompt_creation(self):
        """Test market research prompt creation"""
        prompt = self.reviewer._select_optimal_prompt(self.test_trade_data)
        
        # Verify prompt contains all trade data
        self.assertIn('BTC', prompt)
        self.assertIn('45,000.5000', prompt)  # Phase 3 uses different formatting
        self.assertIn('46,500.0000', prompt)
        self.assertIn('3.33', prompt)
        self.assertIn('+3.33%', prompt)  # Phase 3 includes percentage format
        
        # Verify prompt structure (Phase 3 uses crypto-specific prompt for BTC)
        self.assertIn('CRYPTO-SPECIFIC RESEARCH', prompt)
        self.assertIn('Protocol updates', prompt)
        self.assertIn('DeFi ecosystem', prompt)
        self.assertIn('JSON format', prompt)
        
    def test_response_parsing_valid_json(self):
        """Test parsing of valid JSON response"""
        test_analysis = """
        Based on my research, here's the analysis:
        {
            "approval": true,
            "confidence": 80,
            "risk_score": 2,
            "reasoning": "Strong market conditions with positive news",
            "market_events": {
                "recent_news_impact": 0.4,
                "regulatory_risk": "low"
            }
        }
        Additional context follows...
        """
        
        citations = [{"url": "https://example.com", "title": "Test"}]
        result = self.reviewer._parse_enhanced_analysis(test_analysis, citations, self.test_trade_data)
        
        self.assertIsNotNone(result)
        self.assertTrue(result['approval'])
        self.assertEqual(result['confidence'], 80)
        self.assertEqual(result['citations_count'], 1)
        self.assertIn('market_events', result)
        
    def test_response_parsing_invalid_json(self):
        """Test parsing of invalid JSON response"""
        test_analysis = "This is not valid JSON response"
        citations = []
        
        result = self.reviewer._parse_enhanced_analysis(test_analysis, citations, self.test_trade_data)
        # Phase 3 has fallback parsing, so it returns a fallback result instead of None
        self.assertIsNotNone(result)
        self.assertIn('fallback_analysis', result)
        self.assertTrue(result['fallback_analysis'])
        self.assertFalse(result['approval'])  # Fallback should be conservative
        
    def test_source_quality_assessment(self):
        """Test source quality assessment logic"""
        # High quality sources (Tier 1)
        high_quality_citations = [
            {"url": "https://bloomberg.com/news", "title": "News"},
            {"url": "https://reuters.com/article", "title": "Article"}
        ]
        quality = self.reviewer._assess_source_quality_enhanced(high_quality_citations)
        self.assertEqual(quality, "very_high")
        
        # Medium-high quality sources (Tier 2) - coindesk is now tier 2 in Phase 3
        medium_quality_citations = [
            {"url": "https://coindesk.com/article", "title": "Article"}
        ]
        quality = self.reviewer._assess_source_quality_enhanced(medium_quality_citations)
        self.assertEqual(quality, "high")  # Phase 3 rates coindesk as tier 2 (high)
        
        # Low quality sources 
        low_quality_citations = [
            {"url": "https://random-blog.com/article", "title": "Article"}
        ]
        quality = self.reviewer._assess_source_quality_enhanced(low_quality_citations)
        self.assertEqual(quality, "very_low")  # Unknown sources get very_low
        
        # No sources
        quality = self.reviewer._assess_source_quality_enhanced([])
        self.assertEqual(quality, "no_sources")  # Updated to match Phase 3
        
    @patch.dict(os.environ, {
        'CONFIDENCE_THRESHOLD': '70',
        'MAXIMUM_RISK_THRESHOLD': '4',
        'PERPLEXITY_SOURCE_CITATIONS_MIN': '2'
    })
    @patch('requests.post')
    def test_approval_logic_with_thresholds(self, mock_post):
        """Test approval logic based on configured thresholds"""
        # Test case 1: Should approve (meets all thresholds with good score)
        good_response = {
            "choices": [{"message": {"content": json.dumps({
                "approval": False,  # Will be overridden by approval score calculation
                "confidence": 85,   # High confidence
                "risk_score": 2,    # Low risk
                "reasoning": "Strong market conditions with excellent sources",
                "market_events": {
                    "recent_news_impact": 0.3,
                    "regulatory_risk": "low"
                }
            })}}],
            "citations": [
                {"url": "https://bloomberg.com/news", "title": "Bloomberg News"}, 
                {"url": "https://reuters.com/article", "title": "Reuters Article"}
            ]  # 2 high-quality citations
        }

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = good_response
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = self.reviewer.review_trade(self.test_trade_data)
        self.assertTrue(result['approval'])  # Should be approved due to high approval score

        # Test case 2: Should reject (low confidence and high risk)
        bad_response = {
            "choices": [{"message": {"content": json.dumps({
                "approval": True,  # Will be overridden by approval score calculation
                "confidence": 50,  # Low confidence
                "risk_score": 8,   # High risk
                "reasoning": "Uncertain conditions with poor sources"
            })}}],
            "citations": [{"url": "https://random-blog.com/post", "title": "Random Blog"}]  # 1 low-quality citation
        }

        mock_response.json.return_value = bad_response
        result = self.reviewer.review_trade(self.test_trade_data)
        self.assertFalse(result['approval'])  # Should be rejected due to low approval score
        
    @patch('requests.post')
    def test_timeout_configuration(self, mock_post):
        """Test that timeout is properly configured"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.mock_api_response
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        # Test with default timeout
        self.reviewer.review_trade(self.test_trade_data)
        
        # Check that timeout was used in the request
        call_args = mock_post.call_args
        self.assertEqual(call_args[1]['timeout'], self.reviewer.timeout)


class TestPerplexityEnvironmentConfig(unittest.TestCase):
    """Test environment configuration for Perplexity"""
    
    @patch.dict(os.environ, {
        'HL_SECRET_KEY': 'test_secret',
        'ALLORA_UPSHOT_KEY': 'test_allora',
        'PERPLEXITY_API_KEY': 'test_perplexity',
        'PERPLEXITY_MODEL': 'sonar-pro',
        'PERPLEXITY_BASE_WEIGHT': '0.3',
        'PERPLEXITY_TIMEOUT': '15'
    })
    def test_perplexity_environment_variables(self):
        """Test that Perplexity environment variables are loaded correctly"""
        from utils.env_loader import EnvLoader
        
        env_loader = EnvLoader()
        config = env_loader.get_config()
        
        # Test Perplexity configuration
        self.assertEqual(config['perplexity_api_key'], 'test_perplexity')
        self.assertEqual(config['perplexity_model'], 'sonar-pro')
        self.assertEqual(config['perplexity_base_weight'], 0.3)
        self.assertEqual(config['perplexity_timeout'], 15)
        
    @patch.dict(os.environ, {
        'HL_SECRET_KEY': 'test_secret',
        'ALLORA_UPSHOT_KEY': 'test_allora',
        'PERPLEXITY_API_KEY': 'test_perplexity'  # Only Perplexity configured
    })
    def test_perplexity_only_configuration(self):
        """Test configuration with only Perplexity API key"""
        from utils.env_loader import EnvLoader
        
        env_loader = EnvLoader()
        config = env_loader.get_config()
        
        # Should not raise error with only Perplexity configured
        self.assertEqual(config['perplexity_api_key'], 'test_perplexity')
        
    @patch('os.getenv')
    def test_no_ai_services_configured(self, mock_getenv):
        """Test that error is raised when no AI services are configured"""
        def mock_getenv_func(key, default=None):
            if key == 'HL_SECRET_KEY':
                return 'test_secret'
            elif key == 'ALLORA_UPSHOT_KEY':
                return 'test_allora'
            elif key in ['HYPERBOLIC_API_KEY', 'OPENROUTER_API_KEY', 'PERPLEXITY_API_KEY']:
                return None  # No AI services configured
            else:
                return default
        
        mock_getenv.side_effect = mock_getenv_func
        
        from utils.env_loader import EnvLoader
        env_loader = EnvLoader()
        
        with self.assertRaises(ValueError) as context:
            env_loader.get_config()
        
        self.assertIn("PERPLEXITY_API_KEY", str(context.exception))


if __name__ == '__main__':
    # Set up test environment
    os.environ['HL_SECRET_KEY'] = 'test_secret_key'
    os.environ['ALLORA_UPSHOT_KEY'] = 'test_allora_key'
    os.environ['PERPLEXITY_API_KEY'] = 'test_perplexity_key'
    
    # Run tests
    unittest.main(verbosity=2) 