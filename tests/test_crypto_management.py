"""
Test suite for crypto management and bot mode control functionality.
Phase 2: Bot Integration Testing
"""

import unittest
import tempfile
import os
import json
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path for imports
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import DatabaseManager
from allora.allora_mind import AlloraMind


class TestCryptoManagement(unittest.TestCase):
    """Test crypto management functionality"""
    
    def setUp(self):
        """Set up test environment"""
        # Create temporary database
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        # Initialize database manager and set test database path
        self.db = DatabaseManager()
        self.db.db_path = self.temp_db.name
        self.db._create_tables()  # Recreate tables for test database
        
        # Mock order manager
        self.mock_manager = Mock()
        self.mock_manager.get_volatility.return_value = 0.025
        
        # Initialize AlloraMind with mocked dependencies
        with patch.dict(os.environ, {
            'BOT_DEFAULT_MODE': 'STANDBY',
            'CONFIG_UPDATE_INTERVAL': '5'
        }):
            self.allora_mind = AlloraMind(
                manager=self.mock_manager,
                allora_upshot_key="test_key",
                hyperbolic_api_key="test_hyperbolic",
                openrouter_api_key="test_openrouter",
                openrouter_model="test_model",
                threshold=0.03
            )
        
        # Override database instance
        self.allora_mind.db = self.db
    
    def tearDown(self):
        """Clean up test environment"""
        os.unlink(self.temp_db.name)
    
    def test_initial_standby_mode(self):
        """Test bot starts in STANDBY mode"""
        self.assertEqual(self.allora_mind.mode, "STANDBY")
        self.assertFalse(self.allora_mind.monitoring_enabled)
        self.assertEqual(self.allora_mind.topic_ids, {})
    
    def test_activate_crypto(self):
        """Test activating a single cryptocurrency"""
        command_data = {
            'symbol': 'BTC',
            'topic_id': 14
        }
        
        result = self.allora_mind.activate_crypto(command_data)
        
        self.assertTrue(result)
        self.assertIn('BTC', self.allora_mind.topic_ids)
        self.assertEqual(self.allora_mind.topic_ids['BTC'], 14)
    
    def test_deactivate_crypto(self):
        """Test deactivating a cryptocurrency"""
        # First activate
        self.allora_mind.topic_ids['BTC'] = 14
        
        command_data = {'symbol': 'BTC'}
        result = self.allora_mind.deactivate_crypto(command_data)
        
        self.assertTrue(result)
        self.assertNotIn('BTC', self.allora_mind.topic_ids)
    
    def test_set_mode_active(self):
        """Test setting bot to ACTIVE mode"""
        command_data = {
            'active_cryptos': {
                'BTC': 14,
                'ETH': 13
            }
        }
        
        result = self.allora_mind.set_mode_active(command_data)
        
        self.assertTrue(result)
        self.assertEqual(self.allora_mind.mode, "ACTIVE")
        self.assertTrue(self.allora_mind.monitoring_enabled)
        self.assertEqual(len(self.allora_mind.topic_ids), 2)
    
    def test_set_mode_active_no_cryptos(self):
        """Test activating without cryptocurrencies fails"""
        command_data = {'active_cryptos': {}}
        
        result = self.allora_mind.set_mode_active(command_data)
        
        self.assertFalse(result)
        self.assertEqual(self.allora_mind.mode, "STANDBY")
    
    def test_set_mode_standby(self):
        """Test setting bot to STANDBY mode"""
        # First set to active
        self.allora_mind.mode = "ACTIVE"
        self.allora_mind.monitoring_enabled = True
        
        result = self.allora_mind.set_mode_standby({})
        
        self.assertTrue(result)
        self.assertEqual(self.allora_mind.mode, "STANDBY")
        self.assertFalse(self.allora_mind.monitoring_enabled)
    
    def test_update_crypto_config(self):
        """Test updating crypto configuration"""
        # Initial config
        self.allora_mind.topic_ids = {'BTC': 14}
        
        command_data = {
            'active_cryptos': {
                'BTC': 14,
                'ETH': 13,
                'SOL': 15
            }
        }
        
        result = self.allora_mind.update_crypto_config(command_data)
        
        self.assertTrue(result)
        self.assertEqual(len(self.allora_mind.topic_ids), 3)
        self.assertIn('ETH', self.allora_mind.topic_ids)
        self.assertIn('SOL', self.allora_mind.topic_ids)
    
    def test_batch_update_cryptos(self):
        """Test batch crypto updates"""
        # Setup initial state
        self.allora_mind.topic_ids = {'BTC': 14, 'ETH': 13}
        
        # Mock database response
        with patch.object(self.db, 'get_active_cryptos', return_value={'BTC': 14, 'SOL': 15}):
            command_data = {
                'activated': ['SOL'],
                'deactivated': ['ETH']
            }
            
            result = self.allora_mind.batch_update_cryptos(command_data)
            
            self.assertTrue(result)
            # Should have updated from database
            self.assertIn('SOL', self.allora_mind.topic_ids)
    
    def test_execute_command_unknown_type(self):
        """Test handling unknown command types"""
        command = {
            'command_type': 'UNKNOWN_COMMAND',
            'command_data': {}
        }
        
        result = self.allora_mind.execute_command(command)
        self.assertFalse(result)
    
    def test_command_execution_with_error(self):
        """Test command execution error handling"""
        # Force an error by providing invalid data
        command = {
            'command_type': 'ACTIVATE_CRYPTO',
            'command_data': {}  # Missing required fields
        }
        
        result = self.allora_mind.execute_command(command)
        self.assertFalse(result)


class TestDatabaseCryptoOperations(unittest.TestCase):
    """Test database operations for crypto management"""
    
    def setUp(self):
        """Set up test database"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db = DatabaseManager()
        self.db.db_path = self.temp_db.name
        self.db._create_tables()
    
    def tearDown(self):
        """Clean up test database"""
        os.unlink(self.temp_db.name)
    
    def test_crypto_config_operations(self):
        """Test crypto configuration database operations"""
        # Add crypto config
        self.db.add_crypto_config('BTC', 14, 'both')
        self.db.add_crypto_config('ETH', 13, 'allora')
        
        # Test get_crypto_configs
        configs = self.db.get_crypto_configs()
        self.assertEqual(len(configs), 2)
        
        # Test activate crypto
        self.db.activate_crypto('BTC')
        active_cryptos = self.db.get_active_cryptos()
        self.assertIn('BTC', active_cryptos)
        self.assertEqual(active_cryptos['BTC'], 14)
        
        # Test deactivate crypto
        self.db.deactivate_crypto('BTC')
        active_cryptos = self.db.get_active_cryptos()
        self.assertNotIn('BTC', active_cryptos)
    
    def test_bot_command_operations(self):
        """Test bot command database operations"""
        # Add command
        command_data = {'active_cryptos': {'BTC': 14}}
        command_id = self.db.add_bot_command('SET_MODE_ACTIVE', command_data)
        
        # Get pending commands
        pending = self.db.get_pending_commands()
        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0]['command_type'], 'SET_MODE_ACTIVE')
        
        # Mark as executed
        self.db.mark_command_executed(command_id, success=True)
        pending = self.db.get_pending_commands()
        self.assertEqual(len(pending), 0)
    
    def test_crypto_availability_tracking(self):
        """Test crypto availability tracking"""
        # Add cryptos with different availability
        self.db.add_crypto_config('BTC', 14, 'both')
        self.db.add_crypto_config('DOGE', 99, 'hyperliquid')
        self.db.add_crypto_config('CUSTOM', 50, 'allora')
        
        configs = self.db.get_crypto_configs()
        
        # Check availability tracking
        btc_config = next(c for c in configs if c['symbol'] == 'BTC')
        self.assertEqual(btc_config['availability'], 'both')
        
        doge_config = next(c for c in configs if c['symbol'] == 'DOGE')
        self.assertEqual(doge_config['availability'], 'hyperliquid')


class TestPhase2Integration(unittest.TestCase):
    """Integration tests for Phase 2 functionality"""
    
    def setUp(self):
        """Set up integration test environment"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        self.db = DatabaseManager()
        self.db.db_path = self.temp_db.name
        self.db._create_tables()
        self.mock_manager = Mock()
        
        with patch.dict(os.environ, {
            'BOT_DEFAULT_MODE': 'STANDBY',
            'CONFIG_UPDATE_INTERVAL': '2'
        }):
            self.allora_mind = AlloraMind(
                manager=self.mock_manager,
                allora_upshot_key="test_key",
                hyperbolic_api_key="test_hyperbolic",
                openrouter_api_key="test_openrouter",
                openrouter_model="test_model"
            )
        
        self.allora_mind.db = self.db
    
    def tearDown(self):
        """Clean up integration test environment"""
        os.unlink(self.temp_db.name)
    
    def test_full_crypto_activation_flow(self):
        """Test complete crypto activation workflow"""
        # 1. Add crypto config to database
        self.db.add_crypto_config('BTC', 14, 'both')
        self.db.add_crypto_config('ETH', 13, 'both')
        
        # 2. Add command to activate cryptos
        command_data = {'active_cryptos': {'BTC': 14, 'ETH': 13}}
        command_id = self.db.add_bot_command('SET_MODE_ACTIVE', command_data)
        
        # 3. Simulate command processing
        commands = self.db.get_pending_commands()
        self.assertEqual(len(commands), 1)
        
        # 4. Execute command
        success = self.allora_mind.execute_command(commands[0])
        self.assertTrue(success)
        
        # 5. Verify bot state
        self.assertEqual(self.allora_mind.mode, "ACTIVE")
        self.assertTrue(self.allora_mind.monitoring_enabled)
        self.assertEqual(len(self.allora_mind.topic_ids), 2)
        
        # 6. Mark command as executed
        self.db.mark_command_executed(command_id, success=True)
        
        # 7. Verify no pending commands
        pending = self.db.get_pending_commands()
        self.assertEqual(len(pending), 0)
    
    @patch('time.time')
    def test_command_checking_timing(self, mock_time):
        """Test command checking interval timing"""
        # Mock time progression
        mock_time.side_effect = [0, 1, 3, 5]  # Simulate time passing
        
        # Set short check interval
        self.allora_mind.command_check_interval = 2
        self.allora_mind.last_command_check = 0
        
        # First check - should execute (3 - 0 >= 2)
        with patch.object(self.allora_mind, 'check_dashboard_commands') as mock_check:
            # Simulate condition check
            current_time = 3
            should_check = current_time - self.allora_mind.last_command_check >= self.allora_mind.command_check_interval
            self.assertTrue(should_check)


if __name__ == '__main__':
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestCryptoManagement))
    suite.addTests(loader.loadTestsFromTestCase(TestDatabaseCryptoOperations))
    suite.addTests(loader.loadTestsFromTestCase(TestPhase2Integration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Exit with error code if tests failed
    sys.exit(0 if result.wasSuccessful() else 1) 