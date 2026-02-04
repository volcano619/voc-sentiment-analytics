"""
Sentiment Analysis Module

Implements:
1. TextBlob-based sentiment analysis (fallback)
2. Transformer-based sentiment (when available)
3. Business-aware sentiment scoring
"""

import logging
from typing import Dict, Tuple, List
import re

from config import (
    SENTIMENT_LABELS, SENTIMENT_TO_ACTION, NPS_MAPPING,
    CONFIDENCE_THRESHOLD
)

logger = logging.getLogger(__name__)

# Check for TextBlob
try:
    from textblob import TextBlob
    TEXTBLOB_AVAILABLE = True
except ImportError:
    TEXTBLOB_AVAILABLE = False
    logger.warning("TextBlob not available. Using rule-based fallback.")

# Check for transformers
try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False


class RuleBasedSentiment:
    """
    Simple rule-based sentiment analysis.
    Fallback when no ML libraries available.
    """
    
    POSITIVE_WORDS = {
        "great", "excellent", "amazing", "love", "best", "fantastic",
        "perfect", "wonderful", "awesome", "outstanding", "happy",
        "satisfied", "helpful", "recommend", "impressed", "quality"
    }
    
    NEGATIVE_WORDS = {
        "terrible", "horrible", "worst", "hate", "awful", "bad",
        "poor", "disappointed", "frustrated", "broken", "useless",
        "rude", "slow", "expensive", "refund", "complaint", "never"
    }
    
    INTENSIFIERS = {"very", "extremely", "absolutely", "completely", "totally"}
    
    def analyze(self, text: str) -> Tuple[str, float]:
        """
        Analyze sentiment using word matching.
        
        Returns:
            (sentiment_label, confidence)
        """
        text_lower = text.lower()
        words = set(re.findall(r'\b\w+\b', text_lower))
        
        positive_count = len(words & self.POSITIVE_WORDS)
        negative_count = len(words & self.NEGATIVE_WORDS)
        has_intensifier = bool(words & self.INTENSIFIERS)
        
        # Calculate score
        score = (positive_count - negative_count) / max(len(words) * 0.1, 1)
        
        # Map to label
        if score > 0.3:
            label = "Very Positive" if has_intensifier else "Positive"
            confidence = min(0.5 + score * 0.3, 0.9)
        elif score > 0.1:
            label = "Positive"
            confidence = 0.5 + score * 0.2
        elif score < -0.3:
            label = "Very Negative" if has_intensifier else "Negative"
            confidence = min(0.5 + abs(score) * 0.3, 0.9)
        elif score < -0.1:
            label = "Negative"
            confidence = 0.5 + abs(score) * 0.2
        else:
            label = "Neutral"
            confidence = 0.6
        
        return label, confidence


class TextBlobSentiment:
    """
    TextBlob-based sentiment analysis.
    Provides polarity (-1 to 1) and subjectivity (0 to 1).
    """
    
    def analyze(self, text: str) -> Tuple[str, float]:
        """
        Analyze sentiment using TextBlob.
        
        Returns:
            (sentiment_label, confidence)
        """
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity  # -1 to 1
        subjectivity = blob.sentiment.subjectivity  # 0 to 1
        
        # Map polarity to 5-class sentiment
        if polarity >= 0.5:
            label = "Very Positive"
            confidence = 0.7 + polarity * 0.2
        elif polarity >= 0.1:
            label = "Positive"
            confidence = 0.6 + polarity * 0.2
        elif polarity <= -0.5:
            label = "Very Negative"
            confidence = 0.7 + abs(polarity) * 0.2
        elif polarity <= -0.1:
            label = "Negative"
            confidence = 0.6 + abs(polarity) * 0.2
        else:
            label = "Neutral"
            confidence = 0.5 + (1 - abs(polarity)) * 0.3
        
        return label, min(confidence, 0.95)


class SentimentAnalyzer:
    """
    Main sentiment analysis class with business metrics integration.
    """
    
    def __init__(self, model_type: str = "auto"):
        """
        Initialize analyzer.
        
        Args:
            model_type: 'textblob', 'transformers', or 'auto'
        """
        if model_type == "auto":
            if TEXTBLOB_AVAILABLE:
                self.analyzer = TextBlobSentiment()
                self.model_type = "textblob"
            else:
                self.analyzer = RuleBasedSentiment()
                self.model_type = "rule_based"
        elif model_type == "textblob" and TEXTBLOB_AVAILABLE:
            self.analyzer = TextBlobSentiment()
            self.model_type = "textblob"
        else:
            self.analyzer = RuleBasedSentiment()
            self.model_type = "rule_based"
        
        logger.info(f"Using {self.model_type} sentiment analyzer")
    
    def analyze(self, text: str) -> Dict:
        """
        Analyze sentiment with business metrics.
        
        Returns:
            Dict with sentiment, confidence, churn_risk, action, predicted_nps
        """
        label, confidence = self.analyzer.analyze(text)
        
        # Get business mapping
        business_info = SENTIMENT_TO_ACTION.get(label, SENTIMENT_TO_ACTION["Neutral"])
        
        # Predict NPS from sentiment
        predicted_nps = NPS_MAPPING.get(label, 7)
        
        return {
            "text": text,
            "sentiment": label,
            "confidence": confidence,
            "churn_risk": business_info["churn_risk"],
            "recommended_action": business_info["action"],
            "priority": business_info["priority"],
            "predicted_nps": predicted_nps
        }
    
    def analyze_batch(self, texts: List[str]) -> List[Dict]:
        """Analyze multiple texts."""
        return [self.analyze(text) for text in texts]
    
    def get_business_summary(self, results: List[Dict]) -> Dict:
        """
        Generate business summary from analysis results.
        
        Returns:
            Summary with NPS, churn risk distribution, action priorities
        """
        if not results:
            return {}
        
        # Sentiment distribution
        sentiment_counts = {}
        for r in results:
            s = r["sentiment"]
            sentiment_counts[s] = sentiment_counts.get(s, 0) + 1
        
        # Calculate NPS
        promoters = sum(1 for r in results if r["predicted_nps"] >= 9)
        detractors = sum(1 for r in results if r["predicted_nps"] <= 6)
        total = len(results)
        nps = ((promoters - detractors) / total) * 100 if total > 0 else 0
        
        # Average churn risk
        avg_churn_risk = sum(r["churn_risk"] for r in results) / total
        
        # High risk count
        high_risk_count = sum(1 for r in results if r["churn_risk"] >= 0.7)
        
        # Priority distribution
        priority_counts = {}
        for r in results:
            p = r["priority"]
            priority_counts[p] = priority_counts.get(p, 0) + 1
        
        return {
            "total_analyzed": total,
            "sentiment_distribution": sentiment_counts,
            "calculated_nps": round(nps, 1),
            "average_churn_risk": round(avg_churn_risk, 2),
            "high_risk_customers": high_risk_count,
            "priority_breakdown": priority_counts,
            "promoters": promoters,
            "passives": total - promoters - detractors,
            "detractors": detractors
        }
