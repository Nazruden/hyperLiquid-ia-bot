import sqlite3
from datetime import datetime
import os
import json
from colorama import Fore, Style

class DatabaseManager:
    def __init__(self):
        self.db_path = 'trading_logs.db'
        print(f"Initializing database at {self.db_path}")  # Debug print
        self._create_tables()
    
    def _create_tables(self):
        """
        Create tables if they don't exist
        """
        print("Creating tables...")  # Debug print
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Original trade logs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trade_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                token TEXT,
                current_price REAL,
                allora_prediction REAL,
                prediction_difference_percent REAL,
                volatility_24h REAL,
                trade_direction TEXT,
                entry_price REAL,
                market_condition TEXT,
                reason TEXT
            )
        """)
        
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
        print(f"Database initialized successfully with crypto management tables")  # Debug print

    def log_trade(self, trade_data):
        log_id = datetime.now().strftime("%Y%m%d%H%M%S")  # Unique log ID based on timestamp
        print(f"{Fore.GREEN}[LOG-{log_id}] Attempting to log trade:{Style.RESET_ALL}")
        print(f"  {Fore.CYAN}Token:{Style.RESET_ALL} {trade_data['token']}")
        print(f"  {Fore.CYAN}Current Price:{Style.RESET_ALL} ${trade_data['current_price']:.2f}")
        print(f"  {Fore.CYAN}Prediction:{Style.RESET_ALL} ${trade_data['allora_prediction']:.2f}")
        print(f"  {Fore.CYAN}Difference:{Style.RESET_ALL} {trade_data['prediction_diff']:.2f}%")
        print(f"  {Fore.CYAN}Volatility:{Style.RESET_ALL} {trade_data['volatility']}")
        print(f"  {Fore.CYAN}Direction:{Style.RESET_ALL} {trade_data['direction']}")
        print(f"  {Fore.CYAN}Entry Price:{Style.RESET_ALL} ${trade_data['entry_price']:.2f}")
        print(f"  {Fore.CYAN}Market Condition:{Style.RESET_ALL} {trade_data['market_condition']}")
        print(f"  {Fore.CYAN}Reason:{Style.RESET_ALL} {trade_data.get('reason', 'N/A')}")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO trade_logs (
                    timestamp, token, current_price, allora_prediction, 
                    prediction_difference_percent, volatility_24h,
                    trade_direction, entry_price, market_condition, reason
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                datetime.now(),
                trade_data['token'],
                trade_data['current_price'],
                trade_data['allora_prediction'],
                trade_data['prediction_diff'],
                trade_data['volatility'],
                trade_data['direction'],
                trade_data['entry_price'],
                trade_data['market_condition'],
                trade_data.get('reason', None)
            ))

            conn.commit()
            print(f"{Fore.GREEN}[LOG-{log_id}] Trade successfully logged.{Style.RESET_ALL}")

        except Exception as e:
            print(f"{Fore.RED}[LOG-{log_id}] Error logging trade: {str(e)}{Style.RESET_ALL}")
        finally:
            conn.close()
    
    def update_trade_result(self, trade_id, exit_price, profit_loss, result):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE trade_logs 
            SET exit_price = ?, profit_loss_percent = ?, trade_result = ?
            WHERE id = ?
        """, (exit_price, profit_loss, result, trade_id))
        
        conn.commit()
        conn.close()

    # ===== CRYPTO CONFIGURATION METHODS =====
    
    def get_crypto_configs(self):
        """Get all crypto configurations"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
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
        
        conn.close()
        return configs
    
    def get_active_cryptos(self):
        """Get only active crypto configurations"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT symbol, topic_id 
            FROM crypto_configs 
            WHERE is_active = TRUE
            ORDER BY symbol
        """)
        
        active_cryptos = {}
        for row in cursor.fetchall():
            active_cryptos[row[0]] = row[1]  # {symbol: topic_id}
        
        conn.close()
        return active_cryptos
    
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
            print(f"{Fore.GREEN}Updated crypto config for {symbol}: active={is_active}{Style.RESET_ALL}")
            return True
            
        except Exception as e:
            print(f"{Fore.RED}Error updating crypto config for {symbol}: {e}{Style.RESET_ALL}")
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
                print(f"{Fore.GREEN}Activated crypto: {symbol}{Style.RESET_ALL}")
                return True
            else:
                print(f"{Fore.YELLOW}Crypto {symbol} not found in configs{Style.RESET_ALL}")
                return False
                
        except Exception as e:
            print(f"{Fore.RED}Error activating crypto {symbol}: {e}{Style.RESET_ALL}")
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
                print(f"{Fore.YELLOW}Deactivated crypto: {symbol}{Style.RESET_ALL}")
                return True
            else:
                print(f"{Fore.YELLOW}Crypto {symbol} not found in configs{Style.RESET_ALL}")
                return False
                
        except Exception as e:
            print(f"{Fore.RED}Error deactivating crypto {symbol}: {e}{Style.RESET_ALL}")
            return False
        finally:
            conn.close()

    # ===== BOT COMMAND METHODS =====
    
    def add_bot_command(self, command_type, command_data=None):
        """Add a new bot command"""
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
            print(f"{Fore.CYAN}Added bot command: {command_type} (ID: {command_id}){Style.RESET_ALL}")
            return command_id
            
        except Exception as e:
            print(f"{Fore.RED}Error adding bot command: {e}{Style.RESET_ALL}")
            return None
        finally:
            conn.close()
    
    def get_pending_commands(self):
        """Get all pending bot commands"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
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
        
        conn.close()
        return commands
    
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
            print(f"{Fore.GREEN}Command {command_id} marked as {status}{Style.RESET_ALL}")
            return True
            
        except Exception as e:
            print(f"{Fore.RED}Error updating command status: {e}{Style.RESET_ALL}")
            return False
        finally:
            conn.close()