import os
import time
import sqlite3
from typing import Dict, Optional
from database.db_manager import DatabaseManager

class AdaptiveThresholdCalculator:
    """
    Calcule des seuils de validation adaptatifs selon:
    - Volatilité du marché
    - Performance historique  
    - Conditions de trading
    """
    
    def __init__(self):
        self.base_threshold = float(os.getenv('VALIDATION_SCORE_THRESHOLD', '0.5'))
        self.min_threshold = 0.25  # Jamais en dessous
        self.max_threshold = 0.85  # Jamais au dessus
        self.db = DatabaseManager()
        
        # Paramètres de volatilité
        self.volatility_low = float(os.getenv('VOLATILITY_THRESHOLD_LOW', '0.015'))
        self.volatility_high = float(os.getenv('VOLATILITY_THRESHOLD_HIGH', '0.04'))
        
        print(f"AdaptiveThresholdCalculator initialized:")
        print(f"  Base threshold: {self.base_threshold}")
        print(f"  Range: {self.min_threshold} - {self.max_threshold}")
        print(f"  Volatility thresholds: {self.volatility_low} - {self.volatility_high}")
    
    def get_threshold(self, volatility: Optional[float] = None, 
                     token: str = None, 
                     market_condition: str = 'NORMAL') -> float:
        """
        Calcule le seuil optimal selon les conditions
        """
        threshold = self.base_threshold
        
        # Ajustement volatilité
        if volatility:
            threshold = self._adjust_for_volatility(threshold, volatility)
        
        # Ajustement performance historique
        if token:
            threshold = self._adjust_for_historical_performance(threshold, token)
        
        # Ajustement condition marché
        threshold = self._adjust_for_market_condition(threshold, market_condition)
        
        # Clamp dans les limites
        return max(self.min_threshold, min(self.max_threshold, threshold))
    
    def _adjust_for_volatility(self, base_threshold: float, volatility: float) -> float:
        """
        Ajuste selon volatilité:
        - Haute volatilité → seuil plus bas (plus permissif)
        - Basse volatilité → seuil plus haut (plus strict)
        """
        if volatility <= self.volatility_low:
            # Marché très calme - être plus strict
            return base_threshold + 0.25
        elif volatility >= self.volatility_high:
            # Haute volatilité - être plus permissif
            return base_threshold - 0.15
        else:
            # Interpolation linéaire
            volatility_factor = (volatility - self.volatility_low) / (self.volatility_high - self.volatility_low)
            adjustment = 0.25 - (volatility_factor * 0.4)
            return base_threshold + adjustment
    
    def _adjust_for_historical_performance(self, base_threshold: float, token: str) -> float:
        """
        Ajuste selon performance récente du token
        """
        try:
            # Récupérer performance 7 derniers jours
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT AVG(profit_loss_percent), COUNT(*)
                FROM trade_logs 
                WHERE token = ? AND timestamp >= datetime('now', '-7 days')
                AND profit_loss_percent IS NOT NULL
            """, (token,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result and result[1] >= 3:  # Au moins 3 trades
                avg_performance = result[0]
                
                if avg_performance > 2:  # Performance excellente
                    adjustment = -0.05  # Plus permissif
                    print(f"Historical performance adjustment for {token}: {adjustment:.3f} (excellent: {avg_performance:.1f}%)")
                    return base_threshold + adjustment
                elif avg_performance < -2:  # Performance mauvaise
                    adjustment = 0.1   # Plus strict
                    print(f"Historical performance adjustment for {token}: {adjustment:.3f} (poor: {avg_performance:.1f}%)")
                    return base_threshold + adjustment
                else:
                    print(f"Historical performance for {token}: neutral ({avg_performance:.1f}%)")
            else:
                print(f"Insufficient historical data for {token} ({result[1] if result else 0} trades)")
        
        except Exception as e:
            print(f"Error adjusting for historical performance: {e}")
        
        return base_threshold
    
    def _adjust_for_market_condition(self, base_threshold: float, condition: str) -> float:
        """
        Ajuste selon condition marché globale
        """
        adjustments = {
            'HIGH_VOLATILITY': -0.1,  # Plus permissif
            'NORMAL': 0.0,
            'LOW_VOLATILITY': 0.05,   # Plus strict
            'TRENDING': -0.05,        # Légèrement plus permissif
            'SIDEWAYS': 0.03          # Légèrement plus strict
        }
        
        adjustment = adjustments.get(condition, 0.0)
        if adjustment != 0.0:
            print(f"Market condition adjustment ({condition}): {adjustment:.3f}")
        
        return base_threshold + adjustment
    
    def get_threshold_explanation(self, volatility: Optional[float] = None, 
                                 token: str = None, 
                                 market_condition: str = 'NORMAL') -> Dict:
        """
        Retourne le seuil avec explication pour debugging
        """
        base = self.base_threshold
        adjustments = {}
        
        current_threshold = base
        
        if volatility:
            vol_threshold = self._adjust_for_volatility(base, volatility)
            vol_adj = vol_threshold - base
            adjustments['volatility'] = vol_adj
            current_threshold = vol_threshold
        
        if token:
            hist_threshold = self._adjust_for_historical_performance(current_threshold, token) 
            hist_adj = hist_threshold - current_threshold
            adjustments['historical'] = hist_adj
            current_threshold = hist_threshold
        
        market_threshold = self._adjust_for_market_condition(current_threshold, market_condition)
        market_adj = market_threshold - current_threshold
        adjustments['market_condition'] = market_adj
        current_threshold = market_threshold
        
        # Apply limits
        clamped_threshold = max(self.min_threshold, min(self.max_threshold, current_threshold))
        
        return {
            'threshold': clamped_threshold,
            'base_threshold': base,
            'adjustments': adjustments,
            'clamped': current_threshold != clamped_threshold,
            'volatility_input': volatility,
            'market_condition': market_condition,
            'total_adjustment': sum(adjustments.values())
        }
    
    def analyze_recent_performance(self, token: str, days: int = 7) -> Dict:
        """
        Analyse la performance récente d'un token pour debugging
        """
        try:
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    COUNT(*) as trade_count,
                    AVG(profit_loss_percent) as avg_pnl,
                    MIN(profit_loss_percent) as min_pnl,
                    MAX(profit_loss_percent) as max_pnl,
                    SUM(CASE WHEN profit_loss_percent > 0 THEN 1 ELSE 0 END) as wins,
                    AVG(CASE WHEN profit_loss_percent > 0 THEN profit_loss_percent END) as avg_win,
                    AVG(CASE WHEN profit_loss_percent <= 0 THEN profit_loss_percent END) as avg_loss
                FROM trade_logs 
                WHERE token = ? AND timestamp >= datetime('now', '-{} days')
                AND profit_loss_percent IS NOT NULL
            """.format(days), (token,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result and result[0] > 0:
                trade_count, avg_pnl, min_pnl, max_pnl, wins, avg_win, avg_loss = result
                win_rate = (wins / trade_count) * 100 if trade_count > 0 else 0
                
                return {
                    'token': token,
                    'period_days': days,
                    'trade_count': trade_count,
                    'avg_pnl_percent': round(avg_pnl, 2) if avg_pnl else 0,
                    'min_pnl_percent': round(min_pnl, 2) if min_pnl else 0,
                    'max_pnl_percent': round(max_pnl, 2) if max_pnl else 0,
                    'win_rate_percent': round(win_rate, 1),
                    'avg_win_percent': round(avg_win, 2) if avg_win else 0,
                    'avg_loss_percent': round(avg_loss, 2) if avg_loss else 0
                }
            else:
                return {
                    'token': token,
                    'period_days': days,
                    'trade_count': 0,
                    'message': 'No historical data available'
                }
                
        except Exception as e:
            return {
                'token': token,
                'error': str(e)
            } 