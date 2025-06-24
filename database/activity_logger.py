"""
Activity Logger - Enhanced logging for AI decisions and trading activity
Handles real-time activity logging for dashboard journal functionality
"""

import sqlite3
from datetime import datetime
import json
from colorama import Fore, Style
import logging

logger = logging.getLogger(__name__)

class ActivityLogger:
    """Enhanced logging system for AI decisions, predictions, and trading activity"""
    
    def __init__(self, db_path='trading_logs.db'):
        self.db_path = db_path
        self._create_activity_tables()
    
    def _create_activity_tables(self):
        """Create activity logging tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Enhanced trade logs table (existing)
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
                reason TEXT,
                exit_price REAL,
                profit_loss_percent REAL,
                trade_result TEXT
            )
        """)
        
        # AI decisions table (new)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ai_decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                token TEXT NOT NULL,
                provider TEXT NOT NULL,
                decision_type TEXT NOT NULL,
                confidence REAL,
                risk_score REAL,
                approval BOOLEAN,
                reasoning TEXT,
                metadata TEXT,
                prediction_value REAL,
                api_latency REAL
            )
        """)
        
        # Activity stream table (new)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS activity_stream (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                activity_type TEXT NOT NULL,
                token TEXT,
                title TEXT NOT NULL,
                description TEXT,
                data TEXT,
                severity TEXT DEFAULT 'INFO',
                category TEXT DEFAULT 'GENERAL'
            )
        """)
        
        conn.commit()
        conn.close()
        logger.info("Activity logging tables initialized")
    
    def log_trade(self, trade_data):
        """Log trade with enhanced formatting and activity stream"""
        log_id = datetime.now().strftime("%Y%m%d%H%M%S")
        
        # Console logging with colors
        print(f"{Fore.GREEN}[LOG-{log_id}] Trade Activity:{Style.RESET_ALL}")
        print(f"  {Fore.CYAN}Token:{Style.RESET_ALL} {trade_data['token']}")
        print(f"  {Fore.CYAN}Direction:{Style.RESET_ALL} {trade_data['direction']}")
        print(f"  {Fore.CYAN}Price:{Style.RESET_ALL} ${trade_data['current_price']:.2f}")
        print(f"  {Fore.CYAN}Prediction:{Style.RESET_ALL} ${trade_data['allora_prediction']:.2f}")
        print(f"  {Fore.CYAN}Difference:{Style.RESET_ALL} {trade_data['prediction_diff']:.2f}%")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Insert into trade_logs
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
            
            # Also log to activity stream
            self._log_to_activity_stream(
                cursor,
                'TRADE_SIGNAL',
                trade_data['token'],
                f"{trade_data['direction']} Signal",
                f"Price: ${trade_data['current_price']:.2f}, Prediction: ${trade_data['allora_prediction']:.2f}",
                trade_data,
                'INFO' if trade_data['direction'] == 'HOLD' else 'SUCCESS'
            )

            conn.commit()
            print(f"{Fore.GREEN}[LOG-{log_id}] Trade logged successfully{Style.RESET_ALL}")

        except Exception as e:
            print(f"{Fore.RED}[LOG-{log_id}] Error logging trade: {str(e)}{Style.RESET_ALL}")
            logger.error(f"Trade logging error: {e}")
        finally:
            conn.close()
    
    def log_ai_decision(self, token, provider, decision_data):
        """Log AI provider decision (Hyperbolic, OpenRouter)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO ai_decisions (
                    timestamp, token, provider, decision_type, confidence,
                    risk_score, approval, reasoning, metadata, prediction_value, api_latency
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                datetime.now(),
                token,
                provider,
                decision_data.get('decision_type', 'VALIDATION'),
                decision_data.get('confidence', 0),
                decision_data.get('risk_score', 0),
                decision_data.get('approval', False),
                decision_data.get('reasoning', ''),
                json.dumps(decision_data.get('metadata', {})),
                decision_data.get('prediction_value'),
                decision_data.get('api_latency', 0)
            ))
            
            # Log to activity stream
            approval_status = "✅ APPROVED" if decision_data.get('approval') else "❌ REJECTED"
            self._log_to_activity_stream(
                cursor,
                'AI_DECISION',
                token,
                f"{provider} AI Decision",
                f"{approval_status} - Confidence: {decision_data.get('confidence', 0)}%",
                decision_data,
                'SUCCESS' if decision_data.get('approval') else 'WARNING'
            )
            
            conn.commit()
            logger.info(f"AI decision logged: {provider} for {token}")
            
        except Exception as e:
            logger.error(f"Error logging AI decision: {e}")
        finally:
            conn.close()
    
    def log_allora_prediction(self, token, prediction_data):
        """Log Allora prediction with metadata"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Log to activity stream
            self._log_to_activity_stream(
                cursor,
                'ALLORA_PREDICTION',
                token,
                f"Allora Prediction - {token}",
                f"Value: ${prediction_data.get('prediction', 0):.2f}, Latency: {prediction_data.get('api_latency', 0):.3f}s",
                prediction_data,
                'INFO'
            )
            
            conn.commit()
            logger.debug(f"Allora prediction logged for {token}")
            
        except Exception as e:
            logger.error(f"Error logging Allora prediction: {e}")
        finally:
            conn.close()
    
    def log_trade_signal(self, token, signal, price, reasoning):
        """Log trade signal generation"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            signal_data = {
                'signal': signal,
                'price': price,
                'reasoning': reasoning,
                'timestamp': datetime.now().isoformat()
            }
            
            severity = 'SUCCESS' if signal in ['BUY', 'SELL'] else 'INFO'
            
            self._log_to_activity_stream(
                cursor,
                'TRADE_SIGNAL',
                token,
                f"Signal Generated: {signal}",
                f"Price: ${price:.2f} - {reasoning}",
                signal_data,
                severity
            )
            
            conn.commit()
            logger.debug(f"Trade signal logged: {signal} for {token}")
            
        except Exception as e:
            logger.error(f"Error logging trade signal: {e}")
        finally:
            conn.close()
    
    def get_recent_activity(self, limit=50, filters=None):
        """Get recent activity for dashboard"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            where_clause = "WHERE 1=1"
            params = []
            
            if filters:
                if filters.get('token'):
                    where_clause += " AND token = ?"
                    params.append(filters['token'])
                if filters.get('activity_type'):
                    where_clause += " AND activity_type = ?"
                    params.append(filters['activity_type'])
                if filters.get('since'):
                    where_clause += " AND timestamp >= ?"
                    params.append(filters['since'])
            
            cursor.execute(f"""
                SELECT id, timestamp, activity_type, token, title, description, 
                       data, severity, category
                FROM activity_stream 
                {where_clause}
                ORDER BY timestamp DESC 
                LIMIT ?
            """, params + [limit])
            
            activities = []
            for row in cursor.fetchall():
                activities.append({
                    'id': row[0],
                    'timestamp': row[1],
                    'activity_type': row[2],
                    'token': row[3],
                    'title': row[4],
                    'description': row[5],
                    'data': json.loads(row[6]) if row[6] else {},
                    'severity': row[7],
                    'category': row[8]
                })
            
            return activities
            
        except Exception as e:
            logger.error(f"Error getting recent activity: {e}")
            return []
        finally:
            conn.close()
    
    def get_activity_stream(self, since_timestamp):
        """Get activity stream since timestamp for real-time updates"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT id, timestamp, activity_type, token, title, description, 
                       data, severity, category
                FROM activity_stream 
                WHERE timestamp > ?
                ORDER BY timestamp ASC
            """, (since_timestamp,))
            
            activities = []
            for row in cursor.fetchall():
                activities.append({
                    'id': row[0],
                    'timestamp': row[1],
                    'activity_type': row[2],
                    'token': row[3],
                    'title': row[4],
                    'description': row[5],
                    'data': json.loads(row[6]) if row[6] else {},
                    'severity': row[7],
                    'category': row[8]
                })
            
            return activities
            
        except Exception as e:
            logger.error(f"Error getting activity stream: {e}")
            return []
        finally:
            conn.close()
    
    def update_trade_result(self, trade_id, exit_price, profit_loss, result):
        """Update trade result"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE trade_logs 
                SET exit_price = ?, profit_loss_percent = ?, trade_result = ?
                WHERE id = ?
            """, (exit_price, profit_loss, result, trade_id))
            
            conn.commit()
            logger.info(f"Trade result updated for ID {trade_id}: {result}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating trade result: {e}")
            return False
        finally:
            conn.close()
    
    def _log_to_activity_stream(self, cursor, activity_type, token, title, description, data, severity='INFO'):
        """Internal method to log to activity stream"""
        cursor.execute("""
            INSERT INTO activity_stream (
                timestamp, activity_type, token, title, description, data, severity, category
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now(),
            activity_type,
            token,
            title,
            description,
            json.dumps(data) if data else None,
            severity,
            'TRADING'
        )) 