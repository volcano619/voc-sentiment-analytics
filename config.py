"""
Configuration Module for Voice of Customer Sentiment Analysis

Centralizes all configuration parameters with focus on business metrics.
"""

from pathlib import Path

# ============================================================================
# PATHS
# ============================================================================
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
MODELS_DIR = PROJECT_ROOT / "saved_models"

for d in [DATA_DIR, MODELS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ============================================================================
# SENTIMENT CLASSES
# ============================================================================
SENTIMENT_LABELS = {
    0: "Very Negative",
    1: "Negative", 
    2: "Neutral",
    3: "Positive",
    4: "Very Positive"
}

# Business mapping
SENTIMENT_TO_ACTION = {
    "Very Negative": {"churn_risk": 0.9, "action": "Immediate Escalation", "priority": "P0"},
    "Negative": {"churn_risk": 0.6, "action": "Proactive Outreach", "priority": "P1"},
    "Neutral": {"churn_risk": 0.3, "action": "Monitor", "priority": "P2"},
    "Positive": {"churn_risk": 0.1, "action": "Engagement Campaign", "priority": "P3"},
    "Very Positive": {"churn_risk": 0.05, "action": "Referral Program", "priority": "P4"}
}

# ============================================================================
# ASPECT CATEGORIES
# ============================================================================
ASPECTS = [
    "product_quality",
    "customer_support", 
    "pricing",
    "delivery",
    "user_experience",
    "general"
]

ASPECT_KEYWORDS = {
    "product_quality": ["quality", "broken", "defect", "works", "excellent", "poor quality", "great product"],
    "customer_support": ["support", "service", "help", "agent", "response", "wait", "resolved", "rude", "helpful"],
    "pricing": ["price", "expensive", "cheap", "value", "cost", "money", "worth", "overpriced", "affordable"],
    "delivery": ["shipping", "delivery", "arrived", "late", "fast", "slow", "package", "tracking"],
    "user_experience": ["easy", "difficult", "confusing", "intuitive", "app", "website", "design", "navigation"]
}

# ============================================================================
# NPS CONFIGURATION
# ============================================================================
NPS_MAPPING = {
    "Very Negative": 2,   # Detractor (0-6)
    "Negative": 5,        # Detractor
    "Neutral": 7,         # Passive (7-8)
    "Positive": 8,        # Passive/Promoter
    "Very Positive": 10   # Promoter (9-10)
}

# ============================================================================
# MODEL CONFIGURATION
# ============================================================================
MODEL_TYPE = "textblob"  # Options: textblob, distilbert
CONFIDENCE_THRESHOLD = 0.6

# ============================================================================
# SYNTHETIC DATA CONFIGURATION
# ============================================================================
SYNTHETIC_SAMPLES = 1000
FEEDBACK_SOURCES = ["review", "survey", "support_ticket", "social_media"]

# ============================================================================
# APPLICATION CONFIGURATION
# ============================================================================
APP_TITLE = "🎯 Voice of Customer Analytics"
APP_LAYOUT = "wide"
DEBUG_MODE = True

# ============================================================================
# BUSINESS METRICS TARGETS
# ============================================================================
TARGET_NPS = 50  # Good NPS benchmark
TARGET_CSAT = 4.0  # Out of 5
TARGET_RESPONSE_TIME_NEGATIVE = 24  # Hours for negative feedback
CHURN_RISK_THRESHOLD = 0.7  # High risk threshold
