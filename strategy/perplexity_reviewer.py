import requests
from typing import Dict, Optional
import json
import os
from dotenv import load_dotenv
import time
from datetime import datetime

load_dotenv()


class PerplexityReviewer:
    # Production-optimized prompt templates for different trading scenarios
    MARKET_RESEARCH_PROMPT_TEMPLATE = """
As an expert cryptocurrency trading analyst with access to real-time market data, conduct comprehensive research and analysis for {token} trading decision.

🔍 CURRENT TRADE CONTEXT:
- Token: {token}
- Current Price: ${current_price:,.4f}
- AI Prediction: ${allora_prediction:,.4f}
- Price Difference: {prediction_diff:+.2f}% ({direction})
- Market Condition: {market_condition}
- Volatility Level: {volatility_level}

📊 REQUIRED ANALYSIS FRAMEWORK:

1. BREAKING NEWS IMPACT (Last 24-48 hours):
   ▪ Search for {token} regulatory announcements or policy changes
   ▪ Corporate/protocol updates, partnerships, or technical developments
   ▪ Large institutional movements, whale transactions, or custody changes
   ▪ Market maker activity or exchange-related developments
   ▪ Social sentiment shifts from key influencers or communities

2. MACRO-MARKET CORRELATION:
   ▪ Bitcoin correlation and overall crypto market trend
   ▪ Traditional market influences (equity markets, DXY, bonds)
   ▪ Federal Reserve policy impact and macroeconomic indicators
   ▪ Geopolitical events affecting crypto adoption or regulation
   ▪ Institutional adoption trends or ETF-related developments

3. TECHNICAL & ON-CHAIN SIGNALS:
   ▪ Key support/resistance levels and technical patterns
   ▪ Trading volume trends and liquidity depth analysis
   ▪ On-chain metrics: wallet activity, exchange flows, supply dynamics
   ▪ Derivatives market signals: funding rates, open interest, options flow
   ▪ Market structure changes or unusual trading patterns

4. RISK-REWARD ASSESSMENT:
   ▪ Immediate catalysts that could trigger price movement
   ▪ Regulatory risks or compliance concerns
   ▪ Technical risks: smart contract, security, or operational issues
   ▪ Market liquidity risks and slippage considerations
   ▪ Time-sensitive factors affecting the trade opportunity

🎯 RESPONSE FORMAT (JSON):
{{
    "approval": false,
    "confidence": 75,
    "risk_score": 6,
    "reasoning": "Comprehensive analysis with specific citations and data points",
    "market_events": {{
        "recent_news_impact": 0.0,
        "regulatory_risk": "low",
        "technical_outlook": "neutral",
        "macro_correlation": 0.7,
        "liquidity_concern": false
    }},
    "source_analysis": {{
        "primary_sources": ["source1", "source2"],
        "data_recency": "within_24h",
        "source_reliability": "high"
    }},
    "trade_signals": {{
        "bullish_factors": ["factor1", "factor2"],
        "bearish_factors": ["factor1", "factor2"],
        "neutral_factors": ["factor1"]
    }}
}}

⚠️ DECISION CRITERIA:
- Approval Threshold: Confidence ≥70% AND Risk ≤6/10 AND ≥2 reliable sources
- Factor in real-time developments and their likely 24-48h impact
- Weight recent high-impact news more heavily than general market trends
- Consider both immediate and medium-term (1-7 days) outlook
- Prioritize factual, verifiable information over speculation

🔍 Research {token} NOW and provide data-driven analysis with specific citations.
"""

    CRYPTO_SPECIFIC_PROMPT = """
Analyze {token} for immediate trading decision with focus on crypto-native factors:

CRYPTO-SPECIFIC RESEARCH:
- Protocol updates, governance proposals, or technical upgrades
- DeFi ecosystem impact: TVL changes, yield farming developments
- NFT marketplace activity if applicable
- Cross-chain bridge activity and interoperability updates
- Staking rewards changes or validator activity
- Token unlock schedules or vesting events
- Exchange listing/delisting rumors or confirmations

Current context: {token} at ${current_price:,.4f}, prediction ${allora_prediction:,.4f} ({prediction_diff:+.2f}%)

Response in standard JSON format with crypto-specific insights.
"""

    VOLATILITY_FOCUSED_PROMPT = """
VOLATILITY ANALYSIS for {token} - High volatility detected ({volatility_level})

Focus on:
- Sudden price movements in last 4-8 hours
- Volume spikes and unusual trading patterns
- Flash crash or pump triggers
- Market manipulation indicators
- Liquidation cascades or leverage unwinding
- Social media catalyst identification

Current: ${current_price:,.4f} vs prediction ${allora_prediction:,.4f}
Provide risk assessment with emphasis on volatility sources.
"""

    def __init__(self, api_key: str, model: str = "sonar-pro"):
        self.api_key = api_key
        self.model = model
        self.api_url = "https://api.perplexity.ai/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # Production-optimized configuration
        self.timeout = int(os.getenv('PERPLEXITY_TIMEOUT', '12'))  # Slightly increased
        self.max_tokens = int(os.getenv('PERPLEXITY_MAX_TOKENS', '2000'))  # Increased for detailed analysis
        self.max_retries = int(os.getenv('PERPLEXITY_RETRY_ATTEMPTS', '3'))
        self.backoff_factor = float(os.getenv('PERPLEXITY_BACKOFF_FACTOR', '1.5'))
        
        # Enhanced quality thresholds
        self.min_citations = int(os.getenv('PERPLEXITY_SOURCE_CITATIONS_MIN', '2'))
        self.confidence_threshold = int(os.getenv("CONFIDENCE_THRESHOLD", 70))
        self.max_risk_threshold = int(os.getenv("MAXIMUM_RISK_THRESHOLD", 6))
        
        # Metrics tracking
        self.request_count = 0
        self.total_latency = 0
        self.citation_stats = {"high": 0, "medium": 0, "low": 0}

    def review_trade(self, trade_data: Dict) -> Optional[Dict]:
        """
        Review a trade using optimized Perplexity prompts and enhanced error handling
        """
        start_time = time.time()
        self.request_count += 1
        
        # Select appropriate prompt based on market conditions
        prompt = self._select_optimal_prompt(trade_data)
        
        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    self.api_url,
                    headers=self.headers,
                    json={
                        "model": self.model,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.1,  # Even lower for more factual responses
                        "max_tokens": self.max_tokens,
                        "return_citations": True,
                        "return_images": False,
                        "search_domain_filter": ["coindesk.com", "bloomberg.com", "reuters.com", 
                                               "cointelegraph.com", "theblock.co", "decrypt.co"]  # Focus on quality sources
                    },
                    timeout=self.timeout
                )
                response.raise_for_status()
                
                # Track latency
                latency = time.time() - start_time
                self.total_latency += latency
                
                response_data = response.json()

                # Robustness check: Ensure the response is a dictionary
                if not isinstance(response_data, dict):
                    # Raise an exception that can be caught by the generic handler
                    raise ValueError(f"API returned a non-JSON object: {response_data}")

                analysis = response_data.get("choices", [{}])[0].get("message", {}).get("content")
                if not analysis:
                    raise ValueError("API response is missing 'content' in choices.")

                citations = response_data.get("citations", [])
                
                parsed_analysis = self._parse_enhanced_analysis(analysis, citations, trade_data)
                
                if parsed_analysis:
                    # Enhanced validation with production criteria
                    source_quality = self._assess_source_quality_enhanced(citations)
                    parsed_analysis["source_quality"] = source_quality
                    parsed_analysis["citations"] = citations
                    parsed_analysis["latency_ms"] = int(latency * 1000)
                    parsed_analysis["model_used"] = self.model
                    
                    # Production approval logic with enhanced criteria
                    approval_score = self._calculate_approval_score(parsed_analysis, citations)
                    parsed_analysis["approval"] = approval_score >= 0.7  # 70% threshold
                    parsed_analysis["approval_score"] = approval_score
                    
                    # Track citation quality stats
                    if source_quality in self.citation_stats:
                        self.citation_stats[source_quality] += 1
                    
                    return parsed_analysis
                
            except requests.exceptions.RequestException as e:
                error_summary = str(e)
                # For HTTPError, provide a cleaner summary
                if isinstance(e, requests.exceptions.HTTPError) and e.response is not None:
                    error_summary = f"HTTP {e.response.status_code} - {e.response.reason}"
                    if e.response.status_code == 401:
                        print(f"🚫 Perplexity API unauthorized - check API key. Aborting retries.")
                        return None # No point in retrying on auth error
                    elif e.response.status_code == 429:
                        error_summary += " (Rate Limit)"

                if attempt < self.max_retries - 1:
                    wait_time = (self.backoff_factor ** attempt) * 2
                    print(f"⚠️ Perplexity request error (attempt {attempt + 1}/{self.max_retries}): {error_summary}. Retrying in {wait_time:.1f}s...")
                    time.sleep(wait_time)
                else:
                    print(f"❌ Perplexity request failed after {self.max_retries} attempts: {error_summary}")
            
            except json.JSONDecodeError as e:
                print(f"❌ Perplexity error: Failed to decode API response as JSON. Content: {response.text[:100]}...")
                # No retry on malformed JSON, as it's a persistent issue
                return None

            except Exception as e:
                if attempt < self.max_retries - 1:
                    wait_time = (self.backoff_factor ** attempt)
                    # Log a clean summary instead of the raw error object
                    error_summary = f"{type(e).__name__}: {str(e)}"
                    print(f"⚠️ An unexpected Perplexity error occurred (attempt {attempt + 1}/{self.max_retries}): {error_summary}. Retrying in {wait_time:.1f}s...")
                    time.sleep(wait_time)
                else:
                    print(f"❌ An unexpected Perplexity error occurred after {self.max_retries} attempts: {e}")
                    return None

        return None

    def _select_optimal_prompt(self, trade_data: Dict) -> str:
        """
        Select the most appropriate prompt template based on trading context
        """
        # Determine volatility level
        volatility = trade_data.get('volatility', 0.02)
        if volatility > 0.05:
            volatility_level = "HIGH"
        elif volatility > 0.03:
            volatility_level = "MEDIUM"
        else:
            volatility_level = "LOW"
        
        trade_data['volatility_level'] = volatility_level
        
        # Select prompt based on conditions
        if volatility_level == "HIGH":
            return self.VOLATILITY_FOCUSED_PROMPT.format(**trade_data)
        elif trade_data['token'] in ['BTC', 'ETH', 'SOL', 'AVAX', 'MATIC']:  # Major tokens
            return self.CRYPTO_SPECIFIC_PROMPT.format(**trade_data)
        else:
            return self.MARKET_RESEARCH_PROMPT_TEMPLATE.format(**trade_data)

    def _parse_enhanced_analysis(self, analysis: str, citations: list, trade_data: Dict) -> Optional[Dict]:
        """
        Enhanced parsing with better error handling and data extraction
        """
        try:
            # Find JSON in response with multiple patterns
            json_patterns = [
                (analysis.find('{'), analysis.rfind('}')),
                (analysis.find('```json\n{'), analysis.find('}\n```')),
                (analysis.find('```\n{'), analysis.find('}\n```'))
            ]
            
            parsed_data = None
            for start_idx, end_idx in json_patterns:
                if start_idx != -1 and end_idx != -1:
                    if start_idx == analysis.find('```json\n{'):
                        start_idx += 8  # Skip ```json\n
                    elif start_idx == analysis.find('```\n{'):
                        start_idx += 4  # Skip ```\n
                    
                    json_str = analysis[start_idx:end_idx + 1]
                    try:
                        parsed_data = json.loads(json_str)
                        break
                    except json.JSONDecodeError:
                        continue
            
            if not parsed_data:
                # Fallback: extract key metrics from text
                return self._extract_fallback_metrics(analysis, citations, trade_data)
            
            # --- FIX: Ensure critical keys always exist for reliability ---
            if "approval" not in parsed_data:
                parsed_data["approval"] = False  # Default to not approved for safety
            
            if "risk_score" not in parsed_data:
                parsed_data["risk_score"] = 10  # Default to max risk
            
            if "confidence" not in parsed_data:
                # Estimate confidence from risk if not present, ensuring it's never a deal-breaker
                risk = parsed_data.get("risk_score", 10)
                parsed_data["confidence"] = max(0, 100 - (risk * 10))

            if "reasoning" not in parsed_data:
                parsed_data["reasoning"] = "No reasoning provided by API." # Add default reasoning
            # --- END FIX ---
            
            # Enhance with metadata
            parsed_data["citations_count"] = len(citations)
            parsed_data["has_quality_citations"] = len(citations) >= self.min_citations
            parsed_data["analysis_timestamp"] = datetime.now().isoformat()
            parsed_data["token_analyzed"] = trade_data['token']
            
            # Extract enhanced market events
            if "market_events" not in parsed_data:
                parsed_data["market_events"] = self._extract_market_events(analysis)
            
            return parsed_data
            
        except Exception as e:
            print(f"⚠️ Enhanced parsing error: {e}")
            return self._extract_fallback_metrics(analysis, citations, trade_data)

    def _extract_fallback_metrics(self, analysis: str, citations: list, trade_data: Dict) -> Dict:
        """
        Fallback analysis extraction when JSON parsing fails
        """
        # Basic sentiment analysis from text
        bullish_words = ['bullish', 'positive', 'upward', 'buy', 'long', 'support', 'growth']
        bearish_words = ['bearish', 'negative', 'downward', 'sell', 'short', 'resistance', 'decline']
        
        analysis_lower = analysis.lower()
        bullish_count = sum(1 for word in bullish_words if word in analysis_lower)
        bearish_count = sum(1 for word in bearish_words if word in analysis_lower)
        
        # Simple confidence calculation
        confidence = min(90, max(30, 50 + (bullish_count - bearish_count) * 10))
        risk_score = max(3, min(8, 6 - (bullish_count - bearish_count)))
        
        return {
            "approval": False,  # Conservative fallback
            "confidence": confidence,
            "risk_score": risk_score,
            "reasoning": f"Fallback analysis - {bullish_count} bullish vs {bearish_count} bearish indicators found",
            "citations_count": len(citations),
            "has_quality_citations": len(citations) >= self.min_citations,
            "market_events": {"recent_news_impact": 0.0, "regulatory_risk": "unknown"},
            "fallback_analysis": True
        }

    def _extract_market_events(self, analysis: str) -> Dict:
        """
        Extract market event indicators from analysis text
        """
        events = {
            "recent_news_impact": 0.0,
            "regulatory_risk": "unknown",
            "technical_outlook": "neutral"
        }
        
        analysis_lower = analysis.lower()
        
        # News impact indicators
        high_impact_terms = ['breaking', 'major', 'significant', 'announced', 'regulatory']
        impact_count = sum(1 for term in high_impact_terms if term in analysis_lower)
        events["recent_news_impact"] = min(1.0, impact_count * 0.2)
        
        # Regulatory risk assessment
        if any(word in analysis_lower for word in ['sec', 'regulation', 'banned', 'lawsuit']):
            events["regulatory_risk"] = "high"
        elif any(word in analysis_lower for word in ['compliance', 'approval', 'legal']):
            events["regulatory_risk"] = "medium"
        else:
            events["regulatory_risk"] = "low"
        
        return events

    def _assess_source_quality_enhanced(self, citations: list) -> str:
        if not citations:
            return "none"

        high_quality_domains = ["reuters.com", "bloomberg.com", "wsj.com", "apnews.com", "coindesk.com", "cointelegraph.com", "theblock.co", "decrypt.co", "arxiv.org"]
        medium_quality_domains = ["forbes.com", "businessinsider.com", "techcrunch.com", "wired.com"]
        
        scores = []
        for url in citations: # Directly iterate over URLs (which are strings)
            try:
                # The 'citation' is now just a URL string, so no .get() is needed.
                domain = url.split('/')[2].replace("www.", "")
                if domain in high_quality_domains:
                    scores.append(3)
                elif domain in medium_quality_domains:
                    scores.append(2)
                else:
                    scores.append(1)
            except IndexError:
                # Handle cases where the URL might be malformed
                scores.append(0)

        if not scores:
            return "low"

        avg_quality = sum(scores) / len(scores)
        
        if avg_quality >= 2.5:
            return "very_high"
        elif avg_quality >= 2.0:
            return "high"
        elif avg_quality >= 1.5:
            return "medium"
        elif avg_quality >= 1.0:
            return "low"
        else:
            return "very_low"

    def _calculate_approval_score(self, analysis: Dict, citations: list) -> float:
        """
        Calculate comprehensive approval score based on multiple factors
        """
        base_score = 0.0
        
        # Confidence component (40% weight)
        confidence = analysis.get("confidence", 50)
        confidence_score = min(1.0, confidence / 100.0)
        base_score += confidence_score * 0.4
        
        # Risk component (30% weight) - inverted
        risk_score = analysis.get("risk_score", 5)
        risk_component = max(0.0, (10 - risk_score) / 10.0)
        base_score += risk_component * 0.3
        
        # Citation quality component (20% weight)
        source_quality = analysis.get("source_quality", "low")
        quality_scores = {
            "very_high": 1.0, "high": 0.8, "medium": 0.6, 
            "low": 0.4, "very_low": 0.2, "no_sources": 0.0
        }
        citation_score = quality_scores.get(source_quality, 0.0)
        base_score += citation_score * 0.2
        
        # Market events component (10% weight)
        market_events = analysis.get("market_events", {})
        news_impact = market_events.get("recent_news_impact", 0.0)
        base_score += min(0.1, news_impact * 0.1)
        
        return min(1.0, base_score)

    def get_model_info(self) -> Dict:
        """
        Return information about the current Perplexity model being used
        """
        return {
            "provider": "Perplexity",
            "model": self.model,
            "features": ["real_time_search", "citations", "market_research"],
            "timeout": self.timeout,
            "max_tokens": self.max_tokens
        }

    def get_performance_metrics(self) -> Dict:
        """
        Get performance metrics for monitoring and optimization (Phase 3)
        """
        avg_latency = (self.total_latency / max(self.request_count, 1)) * 1000  # ms
        
        return {
            "request_count": self.request_count,
            "average_latency_ms": round(avg_latency, 2),
            "total_latency_seconds": round(self.total_latency, 2),
            "citation_quality_distribution": self.citation_stats.copy(),
            "configuration": {
                "timeout": self.timeout,
                "max_tokens": self.max_tokens,
                "model": self.model,
                "min_citations": self.min_citations
            }
        }

    def reset_metrics(self):
        """
        Reset performance tracking metrics
        """
        self.request_count = 0
        self.total_latency = 0
        self.citation_stats = {"high": 0, "medium": 0, "low": 0}

    def health_check(self) -> Dict:
        """
        Perform a health check of the Perplexity service (Phase 3)
        """
        try:
            # Simple test query
            test_response = requests.post(
                self.api_url,
                headers=self.headers,
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": "What is the current time?"}],
                    "max_tokens": 50,
                    "temperature": 0.1
                },
                timeout=5
            )
            
            status = "healthy" if test_response.status_code == 200 else "degraded"
            
            return {
                "status": status,
                "response_code": test_response.status_code,
                "latency_ms": test_response.elapsed.total_seconds() * 1000,
                "timestamp": datetime.now().isoformat(),
                "api_key_configured": bool(self.api_key),
                "model": self.model
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "api_key_configured": bool(self.api_key),
                "model": self.model
            }

    def optimize_for_token(self, token: str) -> Dict:
        """
        Get token-specific optimization recommendations (Phase 3)
        """
        optimizations = {
            "recommended_model": self.model,
            "suggested_timeout": self.timeout,
            "prompt_template": "standard"
        }
        
        # Major crypto tokens get enhanced analysis
        if token in ['BTC', 'ETH', 'SOL', 'AVAX', 'MATIC', 'ADA', 'DOT']:
            optimizations.update({
                "prompt_template": "crypto_specific",
                "suggested_timeout": self.timeout + 2,  # More time for detailed analysis
                "focus_areas": ["institutional_activity", "technical_developments", "regulatory_updates"]
            })
        
        # Smaller tokens get volatility focus
        elif token not in ['BTC', 'ETH', 'BNB', 'XRP', 'ADA', 'SOL', 'DOT', 'MATIC', 'AVAX']:
            optimizations.update({
                "prompt_template": "volatility_focused",
                "focus_areas": ["liquidity_risk", "pump_dump_detection", "social_sentiment"]
            })
        
        return optimizations 