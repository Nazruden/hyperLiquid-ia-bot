"""
Core Database Manager - Handles crypto configuration and bot commands
Refactored to focus on core database operations (≤350 lines)
"""

import sqlite3
from datetime import datetime
import os
import json
from colorama import Fore, Style
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Core database operations for crypto configuration and bot command management"""
    
    def __init__(self):
        self.db_path = 'trading_logs.db'
        logger.info(f"Initializing database at {self.db_path}")
        self._create_tables()
    
    def _create_tables(self):
        """Create core database tables"""
        logger.info("Creating core database tables...")
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Crypto configuration table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS crypto_configs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT UNIQUE NOT NULL,
                topic_id INTEGER NOT NULL,
                is_active BOOLEAN DEFAULT FALSE,
                availability TEXT NOT NULL,
                hyperliquid_available BOOLEAN DEFAULT FALSE,
                allora_available BOOLEAN DEFAULT FALSE,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_price REAL,
                volume_24h REAL
            )
        """)
        
        # Bot commands table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bot_commands (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                command_type TEXT NOT NULL,
                command_data TEXT,
                status TEXT DEFAULT 'PENDING',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                executed_at TIMESTAMP,
                error_message TEXT
            )
        """)
        
        conn.commit()
        conn.close()
        logger.info("Core database tables initialized successfully")

    # ===== CRYPTO CONFIGURATION METHODS =====
    
    def get_crypto_configs(self):
        """Get all crypto configurations"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT symbol, topic_id, is_active, availability, 
                       hyperliquid_available, allora_available, 
                       last_price, volume_24h, updated_at
                FROM crypto_configs
                ORDER BY symbol
            """)
            
            configs = []
            for row in cursor.fetchall():
                configs.append({
                    'symbol': row[0],
                    'topic_id': row[1],
                    'is_active': bool(row[2]),
                    'availability': row[3],
                    'hyperliquid_available': bool(row[4]),
                    'allora_available': bool(row[5]),
                    'last_price': row[6],
                    'volume_24h': row[7],
                    'updated_at': row[8]
                })
            
            return configs
            
        except Exception as e:
            logger.error(f"Error getting crypto configs: {e}")
            return []
        finally:
            conn.close()
    
    def get_active_cryptos(self):
        """Get only active crypto configurations"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT symbol, topic_id 
                FROM crypto_configs 
                WHERE is_active = TRUE
                ORDER BY symbol
            """)
            
            active_cryptos = {}
            for row in cursor.fetchall():
                active_cryptos[row[0]] = row[1]  # {symbol: topic_id}
            
            return active_cryptos
            
        except Exception as e:
            logger.error(f"Error getting active cryptos: {e}")
            return {}
        finally:
            conn.close()
    
    def add_crypto_config(self, symbol, topic_id, availability, 
                        hyperliquid_available=None, allora_available=None):
        """Add a new crypto configuration"""
        # Auto-detect platform availability based on availability string
        if hyperliquid_available is None:
            hyperliquid_available = availability in ['both', 'hyperliquid']
        if allora_available is None:
            allora_available = availability in ['both', 'allora']
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO crypto_configs 
                (symbol, topic_id, is_active, availability, 
                 hyperliquid_available, allora_available, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                symbol, topic_id, False, availability,
                hyperliquid_available, allora_available, datetime.now()
            ))
            
            conn.commit()
            config_id = cursor.lastrowid
            logger.info(f"Added crypto config: {symbol} (ID: {config_id})")
            return config_id
            
        except Exception as e:
            logger.error(f"Error adding crypto config for {symbol}: {e}")
            return None
        finally:
            conn.close()

    def update_crypto_config(self, symbol, topic_id, is_active, availability, 
                           hyperliquid_available=False, allora_available=False,
                           last_price=None, volume_24h=None):
        """Insert or update crypto configuration"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO crypto_configs 
                (symbol, topic_id, is_active, availability, 
                 hyperliquid_available, allora_available, 
                 last_price, volume_24h, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                symbol, topic_id, is_active, availability,
                hyperliquid_available, allora_available,
                last_price, volume_24h, datetime.now()
            ))
            
            conn.commit()
            status_text = "ACTIVE" if is_active else "INACTIVE"
            print(f"{Fore.GREEN}Updated crypto config for {symbol}: {status_text}{Style.RESET_ALL}")
            logger.info(f"Updated crypto config: {symbol} -> {status_text}")
            return True
            
        except Exception as e:
            print(f"{Fore.RED}Error updating crypto config for {symbol}: {e}{Style.RESET_ALL}")
            logger.error(f"Error updating crypto config for {symbol}: {e}")
            return False
        finally:
            conn.close()
    
    def activate_crypto(self, symbol):
        """Activate a cryptocurrency for monitoring"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE crypto_configs 
                SET is_active = TRUE, updated_at = ?
                WHERE symbol = ?
            """, (datetime.now(), symbol))
            
            if cursor.rowcount > 0:
                conn.commit()
                print(f"{Fore.GREEN}✅ Activated crypto: {symbol}{Style.RESET_ALL}")
                logger.info(f"Activated crypto: {symbol}")
                return True
            else:
                print(f"{Fore.YELLOW}⚠️ Crypto {symbol} not found in configs{Style.RESET_ALL}")
                logger.warning(f"Crypto not found for activation: {symbol}")
                return False
                
        except Exception as e:
            print(f"{Fore.RED}❌ Error activating crypto {symbol}: {e}{Style.RESET_ALL}")
            logger.error(f"Error activating crypto {symbol}: {e}")
            return False
        finally:
            conn.close()
    
    def deactivate_crypto(self, symbol):
        """Deactivate a cryptocurrency from monitoring"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE crypto_configs 
                SET is_active = FALSE, updated_at = ?
                WHERE symbol = ?
            """, (datetime.now(), symbol))
            
            if cursor.rowcount > 0:
                conn.commit()
                print(f"{Fore.YELLOW}🔴 Deactivated crypto: {symbol}{Style.RESET_ALL}")
                logger.info(f"Deactivated crypto: {symbol}")
                return True
            else:
                print(f"{Fore.YELLOW}⚠️ Crypto {symbol} not found in configs{Style.RESET_ALL}")
                logger.warning(f"Crypto not found for deactivation: {symbol}")
                return False
                
        except Exception as e:
            print(f"{Fore.RED}❌ Error deactivating crypto {symbol}: {e}{Style.RESET_ALL}")
            logger.error(f"Error deactivating crypto {symbol}: {e}")
            return False
        finally:
            conn.close()

    # ===== BOT COMMAND METHODS =====
    
    def add_bot_command(self, command_type, command_data=None):
        """Add a new bot command to the queue"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO bot_commands (command_type, command_data, status, created_at)
                VALUES (?, ?, 'PENDING', ?)
            """, (
                command_type, 
                json.dumps(command_data) if command_data else None,
                datetime.now()
            ))
            
            command_id = cursor.lastrowid
            conn.commit()
            print(f"{Fore.CYAN}📨 Added bot command: {command_type} (ID: {command_id}){Style.RESET_ALL}")
            logger.info(f"Added bot command: {command_type} (ID: {command_id})")
            return command_id
            
        except Exception as e:
            print(f"{Fore.RED}❌ Error adding bot command: {e}{Style.RESET_ALL}")
            logger.error(f"Error adding bot command {command_type}: {e}")
            return None
        finally:
            conn.close()
    
    def get_pending_commands(self):
        """Get all pending bot commands"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT id, command_type, command_data, created_at
                FROM bot_commands 
                WHERE status = 'PENDING'
                ORDER BY created_at ASC
            """)
            
            commands = []
            for row in cursor.fetchall():
                commands.append({
                    'id': row[0],
                    'command_type': row[1],
                    'command_data': json.loads(row[2]) if row[2] else None,
                    'created_at': row[3]
                })
            
            return commands
            
        except Exception as e:
            logger.error(f"Error getting pending commands: {e}")
            return []
        finally:
            conn.close()
    
    def mark_command_executed(self, command_id, success=True, error_message=None):
        """Mark a bot command as executed"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        status = 'EXECUTED' if success else 'FAILED'
        
        try:
            cursor.execute("""
                UPDATE bot_commands 
                SET status = ?, executed_at = ?, error_message = ?
                WHERE id = ?
            """, (status, datetime.now(), error_message, command_id))
            
            conn.commit()
            status_icon = "✅" if success else "❌"
            print(f"{Fore.GREEN}{status_icon} Command {command_id} marked as {status}{Style.RESET_ALL}")
            logger.info(f"Command {command_id} marked as {status}")
            return True
            
        except Exception as e:
            print(f"{Fore.RED}❌ Error updating command status: {e}{Style.RESET_ALL}")
            logger.error(f"Error updating command {command_id} status: {e}")
            return False
        finally:
            conn.close()
    
    def cleanup_old_commands(self, days_old=7):
        """Clean up old executed commands"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                DELETE FROM bot_commands 
                WHERE status IN ('EXECUTED', 'FAILED') 
                AND executed_at < datetime('now', '-{} days')
            """.format(days_old))
            
            deleted_count = cursor.rowcount
            conn.commit()
            
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} old commands")
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error cleaning up old commands: {e}")
            return 0
        finally:
            conn.close()
    
    # ===== UTILITY METHODS =====
    
    def get_database_stats(self):
        """Get database statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            stats = {}
            
            # Crypto configs count
            cursor.execute("SELECT COUNT(*) FROM crypto_configs")
            stats['total_cryptos'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM crypto_configs WHERE is_active = TRUE")
            stats['active_cryptos'] = cursor.fetchone()[0]
            
            # Commands count
            cursor.execute("SELECT COUNT(*) FROM bot_commands WHERE status = 'PENDING'")
            stats['pending_commands'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM bot_commands WHERE status = 'EXECUTED'")
            stats['executed_commands'] = cursor.fetchone()[0]
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            return {}
        finally:
            conn.close()

    # ===== BACKWARD COMPATIBILITY METHODS =====
    
    def log_trade(self, trade_data):
        """Backward compatibility - delegate to ActivityLogger"""
        # Import here to avoid circular imports
        from database.activity_logger import ActivityLogger
        
        activity_logger = ActivityLogger(self.db_path)
        return activity_logger.log_trade(trade_data)
    
    def update_trade_result(self, trade_id, exit_price, profit_loss, result):
        """Backward compatibility - delegate to ActivityLogger"""
        from database.activity_logger import ActivityLogger
        
        activity_logger = ActivityLogger(self.db_path)
        return activity_logger.update_trade_result(trade_id, exit_price, profit_loss, result)