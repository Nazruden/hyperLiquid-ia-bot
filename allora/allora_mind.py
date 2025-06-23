import requests
import time
import os
from utils.helpers import round_price
from strategy.custom_strategy import custom_strategy
from utils.constants import ALLORA_API_BASE_URL
from database.db_manager import DatabaseManager
from strategy.hyperbolic_reviewer import HyperbolicReviewer
from strategy.openrouter_reviewer import OpenRouterReviewer
from strategy.adaptive_thresholds import AdaptiveThresholdCalculator
from strategy.lag_detector import LagDetector


class AlloraMind:
    def __init__(self, manager, allora_upshot_key, hyperbolic_api_key, openrouter_api_key, openrouter_model, threshold=0.03):
        """
        Initializes the AlloraMind with a given OrderManager and strategy parameters.

        :param manager: Instance of OrderManager to interact with orders.
        :param threshold: The percentage threshold for generating signals.
        """
        self.manager = manager
        self.threshold = threshold
        self.allora_upshot_key = allora_upshot_key
        self.topic_ids = {}
        self.timeout = 5
        self.base_url = ALLORA_API_BASE_URL
        self.db = DatabaseManager()
        
        # Initialize AI reviewers only if API keys are provided
        self.hyperbolic_reviewer = HyperbolicReviewer(hyperbolic_api_key) if hyperbolic_api_key else None
        self.openrouter_reviewer = OpenRouterReviewer(openrouter_api_key, openrouter_model) if openrouter_api_key else None
        
        # Initialize adaptive threshold calculator
        self.adaptive_threshold_calculator = AdaptiveThresholdCalculator()
        
        # Initialize lag detector (Sprint 1.3)
        self.lag_detector = LagDetector()
        
        # Validate at least one AI service is available
        if not self.hyperbolic_reviewer and not self.openrouter_reviewer:
            raise ValueError("At least one AI validation service must be configured (Hyperbolic or OpenRouter)")
        
        # Log which AI services are active
        active_services = []
        if self.hyperbolic_reviewer:
            active_services.append("Hyperbolic AI")
        if self.openrouter_reviewer:
            active_services.append("OpenRouter AI")
        print(f"AI Validation Services: {', '.join(active_services)}")
        print(f"Adaptive Thresholds: {'Enabled' if os.getenv('ADAPTIVE_THRESHOLDS', 'True').lower() == 'true' else 'Disabled'}")
        print(f"Lag Detection: {'Enabled' if os.getenv('LAG_DETECTION_ENABLED', 'True').lower() == 'true' else 'Disabled'}")

    def set_topic_ids(self, topic_ids):
        """
        Set topic IDs for the tokens.
        :param topic_ids: Dictionary mapping tokens to topic IDs.
        """
        self.topic_ids = topic_ids

    def get_dynamic_weights(self, volatility):
        """
        Calcule les poids dynamiques selon volatilité et performance historique
        """
        # Valeurs par défaut basées sur l'analyse
        base_weights = {
            'hyperbolic': float(os.getenv('HYPERBOLIC_BASE_WEIGHT', '0.6')),
            'openrouter': float(os.getenv('OPENROUTER_BASE_WEIGHT', '0.4'))
        }
        
        # Ajustement selon volatilité (haute volatilité favorise OpenRouter d'après tests)
        if volatility and volatility > 0.03:  # Haute volatilité
            return {
                'hyperbolic': 0.4,
                'openrouter': 0.6
            }
        
        return base_weights

    def calculate_validation_score(self, hyperbolic_review, openrouter_review, volatility=None):
        """
        Calcule un score de validation pondéré dynamique (0.0-1.0)
        """
        weights = self.get_dynamic_weights(volatility)
        total_score = 0
        total_weight = 0
        
        # Score Hyperbolic
        if hyperbolic_review and self.hyperbolic_reviewer:
            confidence_factor = hyperbolic_review.get('confidence', 0) / 100
            approval_factor = 1 if hyperbolic_review.get('approval', False) else 0
            risk_factor = max(0, (10 - hyperbolic_review.get('risk_score', 5)) / 10)  # Inverse risk
            
            score = (confidence_factor * approval_factor * risk_factor)
            total_score += score * weights['hyperbolic']
            total_weight += weights['hyperbolic']
        
        # Score OpenRouter
        if openrouter_review and self.openrouter_reviewer:
            confidence_factor = openrouter_review.get('confidence', 0) / 100
            approval_factor = 1 if openrouter_review.get('approval', False) else 0
            risk_factor = max(0, (10 - openrouter_review.get('risk_score', 5)) / 10)
            
            score = (confidence_factor * approval_factor * risk_factor)
            total_score += score * weights['openrouter']
            total_weight += weights['openrouter']
        
        final_score = total_score / total_weight if total_weight > 0 else 0
        
        # Log pour debug
        print(f"Validation Score: {final_score:.3f} (Hyperbolic: {weights.get('hyperbolic', 0):.1f}, OpenRouter: {weights.get('openrouter', 0):.1f})")
        
        return final_score

    def get_adaptive_threshold(self, volatility=None, token=None, market_condition='NORMAL'):
        """
        Calcule le seuil adaptatif selon volatilité, performance historique et conditions marché
        """
        # Utiliser l'ancien système si ADAPTIVE_THRESHOLDS est désactivé
        if os.getenv('ADAPTIVE_THRESHOLDS', 'True').lower() == 'false':
            base_threshold = float(os.getenv('VALIDATION_SCORE_THRESHOLD', '0.5'))
            if not volatility:
                return base_threshold
            
            # Ancien système simple
            if volatility < 0.015:
                return min(0.75, base_threshold + 0.2)
            elif volatility > 0.04:
                return max(0.3, base_threshold - 0.2)
            else:
                factor = (volatility - 0.015) / (0.04 - 0.015)
                adjustment = 0.2 - (factor * 0.4)
                return base_threshold + adjustment
        
        # Nouveau système adaptatif avancé
        return self.adaptive_threshold_calculator.get_threshold(
            volatility=volatility,
            token=token,
            market_condition=market_condition
        )

    def get_inference_ai_model(self, topic_id):
        url = f'{self.base_url}ethereum-11155111?allora_topic_id={topic_id}'
        headers = {
            'accept': 'application/json',
            'x-api-key': self.allora_upshot_key
        }

        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Timestamp AVANT l'appel API
                request_time = time.time()
                
                response = requests.get(url, headers=headers)
                response.raise_for_status()
                
                # Timestamp APRÈS réception
                response_time = time.time()
                api_latency = response_time - request_time
                
                data = response.json()
                network_inference_normalized = float(data['data']['inference_data']['network_inference_normalized'])
                
                # Check if lag detection is enabled
                if os.getenv('LAG_DETECTION_ENABLED', 'True').lower() == 'true':
                    # Return with temporal metadata for lag detection
                    return {
                        'prediction': network_inference_normalized,
                        'timestamp': response_time,
                        'request_time': request_time,
                        'api_latency': api_latency,
                        'topic_id': topic_id,
                        'raw_data': data
                    }
                else:
                    # Legacy mode - just return the prediction value
                    return network_inference_normalized
                    
            except requests.exceptions.RequestException as e:
                print(f"Attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2)
                else:
                    print("Max retries reached, could not fetch data.")
                    return None

    def generate_signal(self, token):
        """
        Generates a signal based on Allora predictions with lag detection.
        :param token: The token symbol (e.g., 'BTC', 'ETH') to fetch the price for.
        :return: A signal string ("BUY", "SELL", or "HOLD"), the percentage difference, current price, and prediction.
        """
        topic_id = self.topic_ids.get(token)
        if topic_id is None:
            self.log_analysis(token, "SKIP", None, None, reason="No topic ID configured")
            return "HOLD", None, None, None

        prediction_data = self.get_inference_ai_model(topic_id)
        if prediction_data is None:
            self.log_analysis(token, "SKIP", None, None, reason="No prediction available")
            return "HOLD", None, None, None

        # Handle both legacy and new formats
        if isinstance(prediction_data, dict):
            # New format with lag detection
            prediction_value = prediction_data['prediction']
            
            # Check lag detection if enabled
            if os.getenv('LAG_DETECTION_ENABLED', 'True').lower() == 'true':
                is_fresh, rejection_reason, lag_metrics = self.lag_detector.check_prediction_freshness(prediction_data)
                
                if not is_fresh:
                    self.log_analysis(token, "SKIP", None, None, reason=f"Lag rejection: {rejection_reason}")
                    return "HOLD", None, None, None
                
                # Log timing metrics
                self.lag_detector.log_prediction_timing(token, prediction_data, "ACCEPTED")
        else:
            # Legacy format - just a number
            prediction_value = prediction_data

        current_price = self.manager.get_price(token)
        if current_price is None:
            self.log_analysis(token, "SKIP", None, None, reason="No price available")
            return "HOLD", None, None, None

        prediction_value = float(prediction_value)
        current_price = float(current_price)
        difference = (prediction_value - current_price) / current_price

        if abs(difference) >= self.threshold:
            signal = "BUY" if difference > 0 else "SELL"
            self.log_analysis(token, signal, current_price, prediction_value, difference)
            return signal, difference, current_price, prediction_value
            
        self.log_analysis(token, "HOLD", current_price, prediction_value, difference, "Below threshold")
        return "HOLD", difference, current_price, prediction_value

    def open_trade(self):
        """
        Opens a trade based on Allora and optional custom strategies.
        """
        tokens = list(self.topic_ids.keys())
        for token in tokens:
            # Get open positions using the new format
            open_positions = self.manager.list_open_positions()
            
            # Check if token is already in an open position
            if token in open_positions:
                print(f"Already an open position for {token}, skipping...")
                continue

            allora_signal, allora_diff, current_price, prediction = self.generate_signal(token)

            if allora_signal == "HOLD":
                print(f"Allora AI suggested HOLD for {token}. Skipping Hyperbolic review.")
                time.sleep(self.timeout)  # Wait for the specified interval before the next prediction
                continue

            # Pass more information to custom strategy
            custom_signal = custom_strategy(
                token, 
                current_price, 
                allora_signal, 
                prediction
            )

            # Proceed with Hyperbolic review only for BUY or SELL signals
            trade_data = {
                'token': token,
                'current_price': current_price,
                'allora_prediction': prediction,
                'prediction_diff': allora_diff * 100 if allora_diff else None,
                'direction': allora_signal,
                'market_condition': 'ANALYSIS'
            }
            # Get reviews from both AI validators
            hyperbolic_review = self.hyperbolic_reviewer.review_trade(trade_data) if self.hyperbolic_reviewer else None
            openrouter_review = self.openrouter_reviewer.review_trade(trade_data) if self.openrouter_reviewer else None
            
            # Check if at least one validator responded
            if hyperbolic_review is None and openrouter_review is None:
                print("Both AI reviews failed: No response received.")
                continue

            # Calculate volatility for adaptive scoring
            current_volatility = None
            if hasattr(self.manager, 'get_volatility'):
                current_volatility = self.manager.get_volatility(token)

            # NEW: Calculate weighted validation score with token context
            validation_score = self.calculate_validation_score(hyperbolic_review, openrouter_review, current_volatility)
            adaptive_threshold = self.get_adaptive_threshold(current_volatility, token=token, market_condition='NORMAL')

            # Log individual validator results with new system
            if hyperbolic_review:
                print(f"Hyperbolic AI - Approval: {hyperbolic_review['approval']}, Confidence: {hyperbolic_review['confidence']}%")
            else:
                print("Hyperbolic AI - No response")
                
            if openrouter_review:
                print(f"OpenRouter AI - Approval: {openrouter_review['approval']}, Confidence: {openrouter_review['confidence']}%")
            else:
                print("OpenRouter AI - No response")

            # NEW: Validation decision based on adaptive scoring
            validation_mode = f"Adaptive Scoring (threshold: {adaptive_threshold:.3f}, score: {validation_score:.3f})"
            both_approve = validation_score >= adaptive_threshold

            print(f"Validation Mode: {validation_mode}")
            print(f"Volatility: {current_volatility:.4f}" if current_volatility else "Volatility: N/A")
            
            if both_approve:
                # Continue with existing trade execution logic
                if custom_signal == "BUY" and allora_signal == "BUY":
                    signal = "BUY"
                elif custom_signal == "SELL" and allora_signal == "SELL":
                    signal = "SELL"
                elif not custom_signal and allora_signal in ["BUY", "SELL"]:
                    signal = allora_signal
                else:
                    print(f"No trading opportunity for {token}, signal: HOLD")
                    continue

                # If there's no signal, skip the token
                if signal == "HOLD":
                    continue

                # Calculate profit target and stop-loss automatically
                target_profit = abs(allora_diff) * 100  # Convert to percentage based on Allora's diff
                stop_loss = target_profit * 0.5  # Stop-loss is 50% of the profit target
                print(f"Profit Target: {target_profit}% and Stop Loss: {stop_loss}%")

                # Generate the order based on the signal
                if signal == "BUY":
                    print(f"Generating BUY order for {token} with {allora_diff:.2%} difference "
                          f"and Current Price: {current_price} Predicted Price: {prediction}")
                    res = self.manager.create_trade_order(token, is_buy=True,
                                                          profit_target=target_profit,
                                                          loss_target=stop_loss)
                    print(res)
                elif signal == "SELL":
                    print(f"Generating SELL order for {token} with {allora_diff:.2%} difference"
                          f" and Current Price: {current_price} Predicted Price: {prediction}")
                    print(f" token:{token}, profit targit: {target_profit} and Loss: {stop_loss}")
                    res = self.manager.create_trade_order(token, is_buy=False,
                                                          profit_target=target_profit,
                                                          loss_target=stop_loss)
                    print(res)
            else:
                print(f"Trade rejected by AI scoring system:")
                print(f"Validation score {validation_score:.3f} below threshold {adaptive_threshold:.3f}")
                if hyperbolic_review:
                    print(f"Hyperbolic AI - Confidence: {hyperbolic_review['confidence']}%, Risk Score: {hyperbolic_review['risk_score']}/10")
                    print(f"Reasoning: {hyperbolic_review['reasoning']}")
                if openrouter_review:
                    print(f"OpenRouter AI - Confidence: {openrouter_review['confidence']}%, Risk Score: {openrouter_review['risk_score']}/10")
                    print(f"Reasoning: {openrouter_review['reasoning']}")
                return

    def monitor_positions(self):
        """
        Monitors open positions and manages trades based on Allora predictions.
        Uses 1% buffer to avoid closing on small prediction movements.
        """
        open_positions = self.manager.get_open_positions()
        if not open_positions:
            print("No open positions to track.")
            return

        CLOSE_BUFFER = 0.01  # 1% buffer for closing positions

        for position in open_positions:
            token = position["coin"]
            entry_price = float(position["entryPrice"])
            side = "A" if float(position["szi"]) > 0 else "B"

            topic_id = self.topic_ids.get(token)
            if not topic_id:
                print(f"No topic ID configured for token: {token}")
                continue

            prediction = self.get_inference_ai_model(topic_id)
            current_price = self.manager.get_current_price(token)
            
            if prediction is None or current_price is None:
                print(f"Data unavailable for {token}. Skipping...")
                continue

            current_price = float(current_price)
            prediction = float(prediction)
            pnl_percent = ((current_price - entry_price) / entry_price) * 100 * (1 if side == "A" else -1)
            
            # Calculate prediction difference as percentage
            pred_diff_percent = (prediction - current_price) / current_price

            # For SHORT positions (side B), close when prediction > current_price by buffer
            # For LONG positions (side A), close when prediction < current_price by buffer
            should_close = (side == "B" and pred_diff_percent > CLOSE_BUFFER) or \
                          (side == "A" and pred_diff_percent < -CLOSE_BUFFER)

            if should_close:
                print(f"Closing {'LONG' if side == 'A' else 'SHORT'} position for {token}:")
                print(f"  Side: {side}")
                print(f"  Entry: ${entry_price:,.2f}")
                print(f"  Current: ${current_price:,.2f} ({pnl_percent:+.2f}%)")
                print(f"  Prediction: ${prediction:,.2f}")
                print(f"  Prediction Difference: {pred_diff_percent:+.2%}")
                print(f"  Reason: {'Prediction above current price by >1%' if side == 'B' else 'Prediction below current price by >1%'}")
                self.manager.market_close(token)
            else:
                print(f"Holding position for {token}:")
                print(f"  Side: {side}")
                print(f"  Entry: ${entry_price:,.2f}")
                print(f"  Current: ${current_price:,.2f} ({pnl_percent:+.2f}%)")
                print(f"  Prediction: ${prediction:,.2f}")
                print(f"  Prediction Difference: {pred_diff_percent:+.2%}")

    def start_allora_trade_bot(self, interval=180):
        """
        Starts the trading and monitoring process at regular intervals.
        :param interval: Time in seconds between checks (default: 180 seconds).
        :param profit_target: Profit target percentage for trades.
        :param loss_target: Loss target percentage for trades.
        """
        while True:
            print("Running trading and position monitoring...")
            self.open_trade()
            self.monitor_positions()
            print(f"Sleeping for {interval} seconds...")
            time.sleep(interval)

    def log_analysis(self, token, signal_type, current_price, prediction, difference=None, reason=None):
        """Silent logging to database without affecting console output"""
        try:
            trade_data = {
                'token': token,
                'current_price': current_price,
                'allora_prediction': prediction,
                'prediction_diff': difference * 100 if difference else None,
                'volatility': self.manager.get_volatility(token) if hasattr(self.manager, 'get_volatility') else None,
                'direction': signal_type,
                'entry_price': current_price,
                'market_condition': 'ANALYSIS',
                'reason': reason
            }
            self.db.log_trade(trade_data)
        except Exception as e:
            print(f"Database logging error: {str(e)}")  # Only error gets printed
