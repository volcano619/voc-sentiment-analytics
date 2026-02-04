"""
Aspect-Based Sentiment Analysis

Identifies WHAT customers are talking about:
- Product Quality
- Customer Support
- Pricing
- Delivery
- User Experience
"""

import re
from typing import Dict, List, Tuple
import logging

from config import ASPECTS, ASPECT_KEYWORDS

logger = logging.getLogger(__name__)


class AspectExtractor:
    """
    Extract aspects from customer feedback.
    
    Identifies which business area the feedback relates to.
    """
    
    def __init__(self):
        self.aspect_keywords = ASPECT_KEYWORDS
    
    def extract_aspects(self, text: str) -> List[Tuple[str, float]]:
        """
        Extract aspects mentioned in text.
        
        Returns:
            List of (aspect, confidence) tuples
        """
        text_lower = text.lower()
        words = set(re.findall(r'\b\w+\b', text_lower))
        
        aspects_found = []
        
        for aspect, keywords in self.aspect_keywords.items():
            matches = 0
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    matches += 1
            
            if matches > 0:
                confidence = min(matches / 3, 1.0)
                aspects_found.append((aspect, confidence))
        
        # If no specific aspect found, classify as general
        if not aspects_found:
            aspects_found.append(("general", 0.5))
        
        # Sort by confidence
        aspects_found.sort(key=lambda x: x[1], reverse=True)
        
        return aspects_found
    
    def get_primary_aspect(self, text: str) -> str:
        """Get the most likely aspect."""
        aspects = self.extract_aspects(text)
        return aspects[0][0] if aspects else "general"


class AspectSentimentAnalyzer:
    """
    Combined aspect and sentiment analysis.
    
    Provides fine-grained insights: "Customer is unhappy about DELIVERY"
    """
    
    def __init__(self, sentiment_analyzer):
        self.aspect_extractor = AspectExtractor()
        self.sentiment_analyzer = sentiment_analyzer
    
    def analyze(self, text: str) -> Dict:
        """
        Full aspect-based sentiment analysis.
        
        Returns:
            Dict with sentiment info + aspect breakdown
        """
        # Get overall sentiment
        sentiment_result = self.sentiment_analyzer.analyze(text)
        
        # Extract aspects
        aspects = self.aspect_extractor.extract_aspects(text)
        primary_aspect = aspects[0][0] if aspects else "general"
        
        # Enrich result
        sentiment_result["primary_aspect"] = primary_aspect
        sentiment_result["aspects"] = aspects
        sentiment_result["aspect_summary"] = self._get_aspect_summary(primary_aspect, sentiment_result["sentiment"])
        
        return sentiment_result
    
    def _get_aspect_summary(self, aspect: str, sentiment: str) -> str:
        """Generate human-readable aspect summary."""
        aspect_names = {
            "product_quality": "Product Quality",
            "customer_support": "Customer Support",
            "pricing": "Pricing",
            "delivery": "Delivery",
            "user_experience": "User Experience",
            "general": "General Experience"
        }
        
        aspect_name = aspect_names.get(aspect, "General")
        
        if sentiment in ["Very Negative", "Negative"]:
            return f"⚠️ Customer dissatisfied with {aspect_name}"
        elif sentiment in ["Very Positive", "Positive"]:
            return f"✅ Customer happy with {aspect_name}"
        else:
            return f"ℹ️ Neutral feedback about {aspect_name}"
    
    def get_aspect_breakdown(self, results: List[Dict]) -> Dict:
        """
        Get breakdown of sentiments by aspect.
        
        Helps identify which areas need improvement.
        """
        aspect_sentiments = {aspect: {"positive": 0, "negative": 0, "neutral": 0} for aspect in ASPECTS}
        aspect_sentiments["general"] = {"positive": 0, "negative": 0, "neutral": 0}
        
        for r in results:
            aspect = r.get("primary_aspect", "general")
            sentiment = r["sentiment"]
            
            if aspect not in aspect_sentiments:
                aspect = "general"
            
            if sentiment in ["Very Positive", "Positive"]:
                aspect_sentiments[aspect]["positive"] += 1
            elif sentiment in ["Very Negative", "Negative"]:
                aspect_sentiments[aspect]["negative"] += 1
            else:
                aspect_sentiments[aspect]["neutral"] += 1
        
        # Calculate health scores
        breakdown = {}
        for aspect, counts in aspect_sentiments.items():
            total = sum(counts.values())
            if total > 0:
                health_score = (counts["positive"] - counts["negative"]) / total
                breakdown[aspect] = {
                    "counts": counts,
                    "total": total,
                    "health_score": round(health_score, 2),
                    "status": "🟢 Healthy" if health_score > 0.3 else "🟡 Needs Attention" if health_score > -0.3 else "🔴 Critical"
                }
        
        return breakdown
