"""
Business Metrics Module

Transforms sentiment analysis into actionable business KPIs:
- NPS (Net Promoter Score)
- CSAT (Customer Satisfaction)
- Churn Risk Score
- Priority-based Action Queue
"""

from typing import Dict, List
from datetime import datetime, timedelta
import logging

from config import (
    TARGET_NPS, TARGET_CSAT, CHURN_RISK_THRESHOLD,
    TARGET_RESPONSE_TIME_NEGATIVE, SENTIMENT_TO_ACTION
)

logger = logging.getLogger(__name__)


class BusinessMetricsCalculator:
    """
    Calculate business KPIs from sentiment analysis results.
    """
    
    def __init__(self, target_nps=TARGET_NPS, target_csat=TARGET_CSAT):
        self.history = []
        self.target_nps = target_nps
        self.target_csat = target_csat
    
    def calculate_nps(self, results: List[Dict]) -> Dict:
        """
        Calculate Net Promoter Score from predicted NPS values.
        
        NPS = % Promoters (9-10) - % Detractors (0-6)
        """
        if not results:
            return {"nps": 0, "promoters": 0, "passives": 0, "detractors": 0}
        
        promoters = sum(1 for r in results if r.get("predicted_nps", 7) >= 9)
        detractors = sum(1 for r in results if r.get("predicted_nps", 7) <= 6)
        passives = len(results) - promoters - detractors
        
        nps = ((promoters - detractors) / len(results)) * 100
        
        return {
            "nps": round(nps, 1),
            "promoters": promoters,
            "promoters_pct": round(promoters / len(results) * 100, 1),
            "passives": passives,
            "passives_pct": round(passives / len(results) * 100, 1),
            "detractors": detractors,
            "detractors_pct": round(detractors / len(results) * 100, 1),
            "total": len(results),
            "vs_target": round(nps - self.target_nps, 1),
            "status": "🟢 Above Target" if nps >= self.target_nps else "🔴 Below Target"
        }
    
    def calculate_csat(self, results: List[Dict]) -> Dict:
        """
        Calculate Customer Satisfaction Score.
        
        Maps sentiment to 1-5 scale.
        """
        if not results:
            return {"csat": 0, "total": 0}
        
        sentiment_to_csat = {
            "Very Negative": 1,
            "Negative": 2,
            "Neutral": 3,
            "Positive": 4,
            "Very Positive": 5
        }
        
        scores = [sentiment_to_csat.get(r["sentiment"], 3) for r in results]
        avg_csat = sum(scores) / len(scores)
        
        # Distribution
        distribution = {}
        for score in range(1, 6):
            distribution[score] = scores.count(score)
        
        return {
            "csat": round(avg_csat, 2),
            "distribution": distribution,
            "total": len(results),
            "vs_target": round(avg_csat - self.target_csat, 2),
            "status": "🟢 Above Target" if avg_csat >= self.target_csat else "🔴 Below Target",
            "satisfied_pct": round(sum(1 for s in scores if s >= 4) / len(scores) * 100, 1)
        }
    
    def calculate_churn_risk(self, results: List[Dict]) -> Dict:
        """
        Calculate overall churn risk metrics.
        """
        if not results:
            return {"avg_risk": 0, "high_risk": 0}
        
        risks = [r.get("churn_risk", 0.3) for r in results]
        avg_risk = sum(risks) / len(risks)
        
        high_risk = sum(1 for r in risks if r >= CHURN_RISK_THRESHOLD)
        medium_risk = sum(1 for r in risks if 0.4 <= r < CHURN_RISK_THRESHOLD)
        low_risk = len(risks) - high_risk - medium_risk
        
        return {
            "average_risk": round(avg_risk, 2),
            "high_risk_count": high_risk,
            "high_risk_pct": round(high_risk / len(results) * 100, 1),
            "medium_risk_count": medium_risk,
            "low_risk_count": low_risk,
            "total": len(results),
            "estimated_churn": round(high_risk * 0.7 + medium_risk * 0.3),
            "retention_opportunity": high_risk  # Customers that could be saved
        }
    
    def generate_action_queue(self, results: List[Dict]) -> List[Dict]:
        """
        Generate prioritized action queue for customer success team.
        """
        actions = []
        
        for r in results:
            if r.get("churn_risk", 0) >= 0.5:  # Medium+ risk
                actions.append({
                    "customer_id": r.get("customer_id", "Unknown"),
                    "sentiment": r["sentiment"],
                    "aspect": r.get("primary_aspect", "general"),
                    "churn_risk": r["churn_risk"],
                    "priority": r["priority"],
                    "recommended_action": r["recommended_action"],
                    "text_preview": r["text"][:100] + "..." if len(r["text"]) > 100 else r["text"],
                    "urgency": "🔴 Urgent" if r["priority"] == "P0" else "🟠 High" if r["priority"] == "P1" else "🟡 Medium"
                })
        
        # Sort by priority
        priority_order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3, "P4": 4}
        actions.sort(key=lambda x: priority_order.get(x["priority"], 5))
        
        return actions


class DashboardMetrics:
    """
    Aggregate metrics for executive dashboard.
    """
    
    def __init__(self, results: List[Dict], target_nps=TARGET_NPS, target_csat=TARGET_CSAT):
        self.results = results
        self.calculator = BusinessMetricsCalculator(target_nps=target_nps, target_csat=target_csat)
    
    def get_executive_summary(self) -> Dict:
        """
        Generate executive-level summary for AI PM reporting.
        """
        nps_metrics = self.calculator.calculate_nps(self.results)
        csat_metrics = self.calculator.calculate_csat(self.results)
        churn_metrics = self.calculator.calculate_churn_risk(self.results)
        action_queue = self.calculator.generate_action_queue(self.results)
        
        # Sentiment breakdown
        sentiment_counts = {}
        for r in self.results:
            s = r["sentiment"]
            sentiment_counts[s] = sentiment_counts.get(s, 0) + 1
        
        return {
            "summary": {
                "total_feedback": len(self.results),
                "analysis_date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "overall_health": self._calculate_overall_health(nps_metrics, csat_metrics, churn_metrics)
            },
            "nps": nps_metrics,
            "csat": csat_metrics,
            "churn": churn_metrics,
            "sentiment_distribution": sentiment_counts,
            "action_queue_size": len(action_queue),
            "urgent_actions": sum(1 for a in action_queue if a["priority"] in ["P0", "P1"]),
            "top_actions": action_queue[:5]
        }
    
    def _calculate_overall_health(self, nps: Dict, csat: Dict, churn: Dict) -> str:
        """Calculate overall customer health score."""
        score = 0
        
        # NPS contribution (0-40 points)
        if nps["nps"] >= 50:
            score += 40
        elif nps["nps"] >= 30:
            score += 30
        elif nps["nps"] >= 0:
            score += 20
        else:
            score += 10
        
        # CSAT contribution (0-30 points)
        if csat["csat"] >= 4.5:
            score += 30
        elif csat["csat"] >= 4.0:
            score += 25
        elif csat["csat"] >= 3.5:
            score += 15
        else:
            score += 5
        
        # Churn risk contribution (0-30 points)
        if churn["high_risk_pct"] <= 5:
            score += 30
        elif churn["high_risk_pct"] <= 10:
            score += 20
        elif churn["high_risk_pct"] <= 20:
            score += 10
        else:
            score += 5
        
        if score >= 80:
            return "🟢 Excellent"
        elif score >= 60:
            return "🟡 Good"
        elif score >= 40:
            return "🟠 Needs Improvement"
        else:
            return "🔴 Critical"
