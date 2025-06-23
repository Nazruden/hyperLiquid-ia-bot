import unittest
import os
import tempfile
import sqlite3
from unittest.mock import patch, MagicMock
from strategy.adaptive_thresholds import AdaptiveThresholdCalculator

class TestAdaptiveThresholds(unittest.TestCase):
    def setUp(self):
        """Configuration pour les tests"""
        # Créer une base de données temporaire pour les tests
        self.test_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.test_db.close()
        
        # Variables d'environnement de test
        self.test_env = {
            'VALIDATION_SCORE_THRESHOLD': '0.5',
            'VOLATILITY_THRESHOLD_LOW': '0.015',
            'VOLATILITY_THRESHOLD_HIGH': '0.04',
            'ADAPTIVE_MIN_THRESHOLD': '0.25',
            'ADAPTIVE_MAX_THRESHOLD': '0.85'
        }
        
        # Mock de la base de données
        self.mock_db = MagicMock()
        
        with patch.dict(os.environ, self.test_env):
            with patch('strategy.adaptive_thresholds.DatabaseManager') as mock_db_manager:
                mock_db_manager.return_value = self.mock_db
                self.calculator = AdaptiveThresholdCalculator()
    
    def tearDown(self):
        """Nettoyage après les tests"""
        try:
            os.unlink(self.test_db.name)
        except:
            pass
    
    def test_initialization(self):
        """Test l'initialisation du calculateur"""
        self.assertEqual(self.calculator.base_threshold, 0.5)
        self.assertEqual(self.calculator.min_threshold, 0.25)
        self.assertEqual(self.calculator.max_threshold, 0.85)
        self.assertEqual(self.calculator.volatility_low, 0.015)
        self.assertEqual(self.calculator.volatility_high, 0.04)
    
    def test_volatility_adjustments(self):
        """Test des ajustements selon la volatilité"""
        # Marché très calme - doit être plus strict
        low_vol_threshold = self.calculator._adjust_for_volatility(0.5, 0.01)
        self.assertGreater(low_vol_threshold, 0.5)  # Plus strict
        
        # Haute volatilité - doit être plus permissif
        high_vol_threshold = self.calculator._adjust_for_volatility(0.5, 0.05)
        self.assertLess(high_vol_threshold, 0.5)  # Plus permissif
        
        # Volatilité normale - interpolation
        normal_vol_threshold = self.calculator._adjust_for_volatility(0.5, 0.025)
        self.assertGreater(normal_vol_threshold, high_vol_threshold)
        self.assertLess(normal_vol_threshold, low_vol_threshold)
    
    def test_market_condition_adjustments(self):
        """Test des ajustements selon les conditions de marché"""
        base = 0.5
        
        # Haute volatilité - plus permissif
        high_vol = self.calculator._adjust_for_market_condition(base, 'HIGH_VOLATILITY')
        self.assertLess(high_vol, base)
        
        # Basse volatilité - plus strict
        low_vol = self.calculator._adjust_for_market_condition(base, 'LOW_VOLATILITY')
        self.assertGreater(low_vol, base)
        
        # Normal - pas de changement
        normal = self.calculator._adjust_for_market_condition(base, 'NORMAL')
        self.assertEqual(normal, base)
        
        # Trending - légèrement plus permissif
        trending = self.calculator._adjust_for_market_condition(base, 'TRENDING')
        self.assertLess(trending, base)
        
        # Sideways - légèrement plus strict
        sideways = self.calculator._adjust_for_market_condition(base, 'SIDEWAYS')
        self.assertGreater(sideways, base)
    
    def test_historical_performance_no_data(self):
        """Test ajustement performance historique sans données"""
        # Mock pas de données
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (None, 0)
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        self.mock_db.get_connection.return_value = mock_conn
        
        result = self.calculator._adjust_for_historical_performance(0.5, 'BTC')
        self.assertEqual(result, 0.5)  # Pas de changement
    
    def test_historical_performance_excellent(self):
        """Test ajustement pour performance excellente"""
        # Mock performance excellente (>2%)
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (3.5, 5)  # 3.5% avg, 5 trades
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        self.mock_db.get_connection.return_value = mock_conn
        
        result = self.calculator._adjust_for_historical_performance(0.5, 'BTC')
        self.assertLess(result, 0.5)  # Plus permissif
    
    def test_historical_performance_poor(self):
        """Test ajustement pour performance mauvaise"""
        # Mock performance mauvaise (<-2%)
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (-3.2, 4)  # -3.2% avg, 4 trades
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        self.mock_db.get_connection.return_value = mock_conn
        
        result = self.calculator._adjust_for_historical_performance(0.5, 'BTC')
        self.assertGreater(result, 0.5)  # Plus strict
    
    def test_historical_performance_neutral(self):
        """Test ajustement pour performance neutre"""
        # Mock performance neutre (entre -2% et 2%)
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (0.8, 3)  # 0.8% avg, 3 trades
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_conn
        self.mock_db.get_connection.return_value = mock_conn
        
        result = self.calculator._adjust_for_historical_performance(0.5, 'BTC')
        self.assertEqual(result, 0.5)  # Pas de changement
    
    def test_threshold_clamping(self):
        """Test que les seuils sont limités dans les bornes"""
        # Test seuil trop bas
        threshold_low = self.calculator.get_threshold(volatility=0.001)  # Très faible volatilité
        self.assertGreaterEqual(threshold_low, self.calculator.min_threshold)
        
        # Test seuil trop haut (simulation impossible normalement mais test de sécurité)
        # Force un calcul qui pourrait dépasser max_threshold
        with patch.object(self.calculator, '_adjust_for_volatility', return_value=1.0):
            threshold_high = self.calculator.get_threshold(volatility=0.1)
            self.assertLessEqual(threshold_high, self.calculator.max_threshold)
    
    def test_get_threshold_explanation(self):
        """Test l'explication détaillée des ajustements"""
        # Mock données historiques neutres
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (1.0, 3)  # Neutre
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        self.mock_db.get_connection.return_value = mock_conn
        
        explanation = self.calculator.get_threshold_explanation(
            volatility=0.03,
            token='BTC',
            market_condition='HIGH_VOLATILITY'
        )
        
        self.assertIn('threshold', explanation)
        self.assertIn('base_threshold', explanation)
        self.assertIn('adjustments', explanation)
        self.assertIn('volatility', explanation['adjustments'])
        self.assertIn('market_condition', explanation['adjustments'])
        self.assertEqual(explanation['volatility_input'], 0.03)
        self.assertEqual(explanation['market_condition'], 'HIGH_VOLATILITY')
    
    def test_analyze_recent_performance(self):
        """Test l'analyse de performance récente"""
        # Mock données de trading
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (5, 2.5, -1.0, 8.0, 3, 4.0, -2.0)
        # (trade_count, avg_pnl, min_pnl, max_pnl, wins, avg_win, avg_loss)
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        self.mock_db.get_connection.return_value = mock_conn
        
        analysis = self.calculator.analyze_recent_performance('BTC', 7)
        
        self.assertEqual(analysis['token'], 'BTC')
        self.assertEqual(analysis['period_days'], 7)
        self.assertEqual(analysis['trade_count'], 5)
        self.assertEqual(analysis['avg_pnl_percent'], 2.5)
        self.assertEqual(analysis['win_rate_percent'], 60.0)  # 3/5 * 100
    
    def test_analyze_recent_performance_no_data(self):
        """Test analyse performance sans données"""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (0, None, None, None, None, None, None)
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        self.mock_db.get_connection.return_value = mock_conn
        
        analysis = self.calculator.analyze_recent_performance('NEWTOKEN', 7)
        
        self.assertEqual(analysis['token'], 'NEWTOKEN')
        self.assertEqual(analysis['trade_count'], 0)
        self.assertIn('message', analysis)
    
    def test_combined_adjustments_comprehensive(self):
        """Test combinaison de tous les ajustements"""
        # Mock performance excellent
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (4.0, 5)  # Excellente performance
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        self.mock_db.get_connection.return_value = mock_conn
        
        # Haute volatilité + performance excellente + marché trending
        threshold = self.calculator.get_threshold(
            volatility=0.05,  # Haute volatilité -> plus permissif
            token='BTC',      # Performance excellente -> plus permissif  
            market_condition='TRENDING'  # Trending -> plus permissif
        )
        
        # Devrait être significativement plus permissif que la base
        self.assertLess(threshold, self.calculator.base_threshold)
        
        # Mais jamais en dessous du minimum
        self.assertGreaterEqual(threshold, self.calculator.min_threshold)

if __name__ == '__main__':
    unittest.main() 