"""
Text Preprocessing and Synthetic Data Generation

Handles:
1. Synthetic customer feedback generation
2. Text cleaning and preprocessing
3. Data loading utilities
"""

import random
import csv
from pathlib import Path
from typing import List, Dict, Tuple
import logging
import re
from datetime import datetime, timedelta

from config import (
    DATA_DIR, SYNTHETIC_SAMPLES, ASPECTS, ASPECT_KEYWORDS,
    FEEDBACK_SOURCES, SENTIMENT_LABELS
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# SYNTHETIC FEEDBACK TEMPLATES
# ============================================================================

FEEDBACK_TEMPLATES = {
    "Very Negative": [
        "Absolutely terrible {aspect_noun}! I'm done with this company. {detail}",
        "This is the worst {aspect_noun} I've ever experienced. {detail} Never again!",
        "Completely unacceptable! {detail} I want a full refund.",
        "Horrible experience. {detail} I'm switching to a competitor.",
        "Disgusted with the {aspect_noun}. {detail} Filing a complaint.",
    ],
    "Negative": [
        "Disappointed with the {aspect_noun}. {detail}",
        "Not happy with my experience. {detail}",
        "The {aspect_noun} needs improvement. {detail}",
        "Expected better {aspect_noun}. {detail}",
        "Frustrated with {detail}. Will think twice before ordering again.",
    ],
    "Neutral": [
        "The {aspect_noun} was okay. {detail}",
        "Average experience. {detail} Nothing special.",
        "It's fine, I guess. {detail}",
        "The {aspect_noun} met my basic expectations. {detail}",
        "Neither impressed nor disappointed. {detail}",
    ],
    "Positive": [
        "Pretty good {aspect_noun}! {detail}",
        "Happy with my purchase. {detail}",
        "The {aspect_noun} exceeded my expectations. {detail}",
        "Good experience overall. {detail} Would recommend.",
        "Satisfied with the {aspect_noun}. {detail}",
    ],
    "Very Positive": [
        "Absolutely love the {aspect_noun}! {detail} Best purchase ever!",
        "Outstanding! {detail} Will definitely buy again!",
        "The {aspect_noun} is amazing! {detail} Highly recommend!",
        "Exceeded all expectations! {detail} 5 stars!",
        "Incredible experience! {detail} You've earned a loyal customer!",
    ]
}

ASPECT_DETAILS = {
    "product_quality": {
        "noun": "product quality",
        "positive": ["works perfectly", "excellent build quality", "exactly as described", "premium materials"],
        "negative": ["broke after a week", "cheap materials", "not as advertised", "defective on arrival"]
    },
    "customer_support": {
        "noun": "customer support",
        "positive": ["agent was very helpful", "quick response time", "resolved my issue immediately", "friendly staff"],
        "negative": ["waited 2 hours on hold", "agent was rude", "no resolution after 3 calls", "ignored my emails"]
    },
    "pricing": {
        "noun": "pricing",
        "positive": ["great value for money", "competitive prices", "worth every penny", "affordable quality"],
        "negative": ["way overpriced", "hidden fees everywhere", "not worth the cost", "bait and switch pricing"]
    },
    "delivery": {
        "noun": "delivery",
        "positive": ["arrived early", "fast shipping", "excellent packaging", "tracking updates were helpful"],
        "negative": ["arrived 2 weeks late", "package was damaged", "wrong item delivered", "no tracking info"]
    },
    "user_experience": {
        "noun": "user experience",
        "positive": ["intuitive interface", "easy to use", "smooth checkout process", "great app design"],
        "negative": ["confusing navigation", "app keeps crashing", "checkout is broken", "impossible to find what I need"]
    }
}


def generate_feedback(sentiment: str, aspect: str = None) -> Dict:
    """Generate a single synthetic feedback entry."""
    if aspect is None:
        aspect = random.choice(list(ASPECT_DETAILS.keys()))
    
    template = random.choice(FEEDBACK_TEMPLATES[sentiment])
    aspect_info = ASPECT_DETAILS.get(aspect, ASPECT_DETAILS["product_quality"])
    
    # Choose positive or negative details based on sentiment
    if sentiment in ["Very Positive", "Positive"]:
        detail = random.choice(aspect_info["positive"])
    elif sentiment in ["Very Negative", "Negative"]:
        detail = random.choice(aspect_info["negative"])
    else:
        # Neutral - mix or generic
        detail = random.choice(aspect_info["positive"] + aspect_info["negative"] + ["nothing remarkable"])
    
    text = template.format(aspect_noun=aspect_info["noun"], detail=detail.capitalize())
    
    # Generate metadata
    source = random.choice(FEEDBACK_SOURCES)
    date = datetime.now() - timedelta(days=random.randint(0, 90))
    
    # Customer ID
    customer_id = f"CUST_{random.randint(10000, 99999)}"
    
    # Simulated NPS score (correlated with sentiment)
    nps_base = {"Very Negative": 2, "Negative": 5, "Neutral": 7, "Positive": 8, "Very Positive": 10}
    nps_score = max(0, min(10, nps_base[sentiment] + random.randint(-1, 1)))
    
    return {
        "text": text,
        "sentiment": sentiment,
        "aspect": aspect,
        "source": source,
        "date": date.strftime("%Y-%m-%d"),
        "customer_id": customer_id,
        "nps_score": nps_score
    }


def generate_synthetic_dataset(n_samples: int = SYNTHETIC_SAMPLES) -> List[Dict]:
    """Generate full synthetic dataset with realistic distribution."""
    
    # Realistic sentiment distribution (skewed positive, some negative)
    distribution = {
        "Very Negative": 0.05,
        "Negative": 0.15,
        "Neutral": 0.25,
        "Positive": 0.35,
        "Very Positive": 0.20
    }
    
    data = []
    
    for sentiment, ratio in distribution.items():
        count = int(n_samples * ratio)
        for _ in range(count):
            data.append(generate_feedback(sentiment))
    
    # Shuffle
    random.shuffle(data)
    
    # Save to CSV
    output_path = DATA_DIR / "customer_feedback.csv"
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["text", "sentiment", "aspect", "source", "date", "customer_id", "nps_score"])
        writer.writeheader()
        writer.writerows(data)
    
    logger.info(f"Generated {len(data)} feedback samples to {output_path}")
    
    return data


def clean_text(text: str) -> str:
    """Clean and preprocess text."""
    # Lowercase
    text = text.lower()
    
    # Remove URLs
    text = re.sub(r'http\S+|www\S+', '', text)
    
    # Remove special characters but keep basic punctuation
    text = re.sub(r'[^a-zA-Z0-9\s.,!?]', '', text)
    
    # Remove extra whitespace
    text = ' '.join(text.split())
    
    return text


def load_feedback_data() -> List[Dict]:
    """Load feedback data from CSV."""
    filepath = DATA_DIR / "customer_feedback.csv"
    
    if not filepath.exists():
        logger.info("No data found, generating synthetic dataset...")
        return generate_synthetic_dataset()
    
    data = []
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row["nps_score"] = int(row["nps_score"])
            data.append(row)
    
    return data


if __name__ == "__main__":
    generate_synthetic_dataset()
