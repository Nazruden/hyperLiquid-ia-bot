import requests
from typing import Dict, Optional
import json
import os
from dotenv import load_dotenv

load_dotenv()


class OpenRouterReviewer:
    def __init__(self, api_key: str, model: str = "anthropic/claude-3-sonnet"):
        self.api_key = api_key
        self.model = model
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    def review_trade(self, trade_data: Dict) -> Optional[Dict]:
        prompt = self._create_review_prompt(trade_data)

        try:
            # Add timeout to prevent hanging
            timeout = int(os.getenv('API_TIMEOUT', 10))
            
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.1,
                    "max_tokens": 4000,
                    "top_p": 1
                },
                timeout=timeout
            )
            response.raise_for_status()
            analysis = response.json()["choices"][0]["message"]["content"]
            parsed_analysis = self._parse_analysis(analysis)

            # Override AI response based on thresholds
            confidence_threshold = int(os.getenv("CONFIDENCE_THRESHOLD", 70))
            max_risk_threshold = int(os.getenv("MAXIMUM_RISK_THRESHOLD", 4))

            if parsed_analysis:
                if (parsed_analysis["confidence"] >= confidence_threshold and
                        parsed_analysis["risk_score"] <= max_risk_threshold):
                    parsed_analysis["approval"] = True

            return parsed_analysis
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                # Silently fail for unauthorized - API key not configured
                return None
            else:
                print(f"OpenRouter review failed: {str(e)}")
                return None
        except Exception as e:
            print(f"OpenRouter review failed: {str(e)}")
            return None

    def _create_review_prompt(self, trade_data: Dict) -> str:
        return f"""
        As an advanced AI leveraged trading expert with x5, review this potential trade:
        
        Token: {trade_data['token']}
        Current Price: ${trade_data['current_price']:,.2f}
        IA Prediction: ${trade_data['allora_prediction']:,.2f}
        Prediction Difference: {trade_data['prediction_diff']:.2f}%
        Direction: {trade_data['direction']}
        Market Condition: {trade_data['market_condition']}
        
        Please analyze this trade and respond in JSON format with:
        1. approval (true/false)
        2. confidence (0-100)
        3. reasoning (string)
        4. risk_score (1-10)
        """

    def _parse_analysis(self, analysis: str) -> Dict:
        try:
            start = analysis.find('{')
            end = analysis.rfind('}')

            if start == -1 or end == -1:
                raise ValueError("No valid JSON found in the response")

            json_str = analysis[start:end + 1]
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            print(f"JSON decoding error: {e}")
        except Exception as e:
            print(f"Error parsing analysis: {e}")

        return None 