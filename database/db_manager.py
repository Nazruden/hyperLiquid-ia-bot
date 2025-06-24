"""
Core Database Manager - Handles crypto configuration and bot commands
Refactored to focus on core database operations (≤350 lines)
"""

import sqlite3
from datetime import datetime
import os
import json
import uuid
from colorama import Fore, Style
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Core database operations for crypto configuration and bot command management"""
    
    def __init__(self):
        # Use environment variable if available, otherwise default to trading_logs.db
        self.db_path = os.getenv('DB_PATH', 'trading_logs.db')
        self.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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
        
        # Bot commands table (now handled by file-based queue)
        # cursor.execute("""
        #     CREATE TABLE IF NOT EXISTS bot_commands (
        #         id INTEGER PRIMARY KEY AUTOINCREMENT,
        #         command_type TEXT NOT NULL,
        #         command_data TEXT,
        #         status TEXT DEFAULT 'PENDING',
        #         created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        #         executed_at TIMESTAMP,
        #         error_message TEXT
        #     )
        # """)
        
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

    # ===== BOT COMMAND METHODS (File-based Queue) =====
    
    def add_bot_command(self, command_type, command_data=None):
        """Creates a command file for the bot to execute."""
        try:
            command_dir = os.path.join(self.project_root, "tmp", "commands", "pending")
            os.makedirs(command_dir, exist_ok=True)

            command_id = str(uuid.uuid4())
            file_path = os.path.join(command_dir, f"{command_id}.json")

            command_content = {
                "id": command_id,
                "command_type": command_type,
                "data": command_data,
                "timestamp": datetime.now().isoformat()
            }

            with open(file_path, "w") as f:
                json.dump(command_content, f)

            print(f"📨 Fichier de commande créé : {file_path}")
            logger.info(f"Command file created: {file_path}")
            return command_id

        except Exception as e:
            print(f"❌ Error creating command file for {command_type}: {e}")
            logger.error(f"Error creating command file for {command_type}: {e}")
            return None

    def get_pending_commands(self):
        """
        DEPRECATED: This method is no longer used with the file-based queue.
        The bot now reads directly from the tmp/commands/pending directory.
        """
        logger.warning("get_pending_commands is deprecated and should not be used.")
        return []

    def mark_command_executed(self, command_id, success=True, error_message=None):
        """
        DEPRECATED: This method is no longer used.
        Command files are moved to the 'processed' directory by the bot.
        """
        logger.warning("mark_command_executed is deprecated and should not be used.")
        pass

    def cleanup_old_commands(self, days_old=7):
        """
        DEPRECATED: This method is no longer used.
        Old command files in 'processed' directory can be cleaned up with a separate script if needed.
        """
        logger.warning("cleanup_old_commands is deprecated and should not be used.")
        pass

    # ===== DATABASE STATISTICS =====
    
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