"""
Evaluation Metrics for Sentiment Analysis

Standard NLP classification metrics plus business-specific KPIs.
"""

import numpy as np
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


def accuracy(y_true: List[str], y_pred: List[str]) -> float:
    """Calculate accuracy."""
    if not y_true:
        return 0.0
    return sum(1 for t, p in zip(y_true, y_pred) if t == p) / len(y_true)


def precision_recall_f1(y_true: List[str], y_pred: List[str], label: str) -> Dict:
    """Calculate precision, recall, F1 for a specific label."""
    tp = sum(1 for t, p in zip(y_true, y_pred) if t == label and p == label)
    fp = sum(1 for t, p in zip(y_true, y_pred) if t != label and p == label)
    fn = sum(1 for t, p in zip(y_true, y_pred) if t == label and p != label)
    
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    
    return {"precision": precision, "recall": recall, "f1": f1}


def macro_f1(y_true: List[str], y_pred: List[str]) -> float:
    """Calculate macro-averaged F1 score."""
    labels = set(y_true)
    if not labels:
        return 0.0
    
    f1_scores = []
    for label in labels:
        metrics = precision_recall_f1(y_true, y_pred, label)
        f1_scores.append(metrics["f1"])
    
    return sum(f1_scores) / len(f1_scores)


def confusion_matrix(y_true: List[str], y_pred: List[str], labels: List[str]) -> Dict:
    """Build confusion matrix."""
    matrix = {label: {l: 0 for l in labels} for label in labels}
    
    for t, p in zip(y_true, y_pred):
        if t in matrix and p in matrix[t]:
            matrix[t][p] += 1
    
    return matrix


def nps_prediction_error(true_nps: List[int], pred_nps: List[int]) -> Dict:
    """Calculate NPS prediction errors."""
    if not true_nps:
        return {"mae": 0, "rmse": 0}
    
    errors = [abs(t - p) for t, p in zip(true_nps, pred_nps)]
    squared_errors = [(t - p) ** 2 for t, p in zip(true_nps, pred_nps)]
    
    mae = sum(errors) / len(errors)
    rmse = (sum(squared_errors) / len(squared_errors)) ** 0.5
    
    return {
        "mae": round(mae, 2),
        "rmse": round(rmse, 2),
        "max_error": max(errors) if errors else 0,
        "within_2_points": round(sum(1 for e in errors if e <= 2) / len(errors) * 100, 1)
    }


class SentimentEvaluator:
    """Evaluate sentiment analysis model."""
    
    def __init__(self):
        self.labels = ["Very Negative", "Negative", "Neutral", "Positive", "Very Positive"]
    
    def evaluate(self, y_true: List[str], y_pred: List[str]) -> Dict:
        """Full evaluation."""
        metrics = {
            "accuracy": round(accuracy(y_true, y_pred), 4),
            "macro_f1": round(macro_f1(y_true, y_pred), 4)
        }
        
        # Per-class metrics
        for label in self.labels:
            prf = precision_recall_f1(y_true, y_pred, label)
            metrics[f"{label}_precision"] = round(prf["precision"], 4)
            metrics[f"{label}_recall"] = round(prf["recall"], 4)
            metrics[f"{label}_f1"] = round(prf["f1"], 4)
        
        # Negative class performance (critical for business)
        neg_labels = ["Very Negative", "Negative"]
        tp = sum(1 for t, p in zip(y_true, y_pred) if t in neg_labels and p in neg_labels)
        fn = sum(1 for t, p in zip(y_true, y_pred) if t in neg_labels and p not in neg_labels)
        
        metrics["negative_recall"] = round(tp / (tp + fn), 4) if (tp + fn) > 0 else 0
        
        return metrics
    
    def summary(self, metrics: Dict) -> str:
        """Generate evaluation summary."""
        lines = [
            "Sentiment Analysis Evaluation",
            "=" * 40,
            f"Accuracy: {metrics['accuracy']:.1%}",
            f"Macro F1: {metrics['macro_f1']:.4f}",
            f"Negative Recall: {metrics['negative_recall']:.1%} (Critical for catching issues)",
            "",
            "Per-Class Performance:"
        ]
        
        for label in self.labels:
            p = metrics.get(f"{label}_precision", 0)
            r = metrics.get(f"{label}_recall", 0)
            f1 = metrics.get(f"{label}_f1", 0)
            lines.append(f"  {label}: P={p:.2f}, R={r:.2f}, F1={f1:.2f}")
        
        return "\n".join(lines)
