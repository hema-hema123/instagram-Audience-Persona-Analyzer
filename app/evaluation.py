"""
Model evaluation framework.

Runs the classifier against labeled test data and computes:
  - Overall accuracy
  - Per-bucket precision, recall, F1
  - Confusion matrix
  - Confidence distribution statistics

Usage:
    from app.evaluation import evaluate_model
    results = evaluate_model()          # uses data/test_bios.csv by default
    print(results["accuracy"])
    print(results["per_bucket"])
"""

import csv
import os
from collections import Counter, defaultdict
from typing import Dict, List, Optional, Tuple

from .classifier import classify_text

DEFAULT_TEST_PATH = os.path.join(
    os.path.dirname(__file__), "..", "data", "test_bios.csv"
)


def _load_test_data(path: str) -> List[Dict[str, str]]:
    """Load labeled test CSV. Expects columns: id, bio, label."""
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            bio = (row.get("bio") or row.get("text") or "").strip()
            label = (row.get("label") or "").strip().lower()
            uid = row.get("id", "")
            if bio and label:
                rows.append({"id": uid, "bio": bio, "label": label})
    return rows


def evaluate_model(
    test_path: Optional[str] = None,
) -> Dict:
    """
    Run the ensemble classifier on labeled test data and compute metrics.

    Returns dict with:
        - total: number of test samples
        - correct: number correctly classified
        - accuracy: overall accuracy (0–1)
        - per_bucket: {bucket: {precision, recall, f1, support}}
        - confusion_matrix: {true_label: {predicted_label: count}}
        - confidence_stats: {mean, min, max, median}
        - misclassified: list of {id, bio, true_label, predicted, confidence}
    """
    path = test_path or DEFAULT_TEST_PATH
    if not os.path.exists(path):
        return {"error": f"Test file not found: {path}"}

    data = _load_test_data(path)
    if not data:
        return {"error": "No valid test data found"}

    # Run predictions
    predictions = []
    confidences = []
    for row in data:
        pred_label, conf, _ = classify_text(row["bio"])
        predictions.append({
            "id": row["id"],
            "bio": row["bio"],
            "true_label": row["label"],
            "predicted": pred_label,
            "confidence": conf,
        })
        confidences.append(conf)

    # Accuracy
    correct = sum(1 for p in predictions if p["true_label"] == p["predicted"])
    total = len(predictions)
    accuracy = round(correct / total, 4) if total else 0.0

    # Confusion matrix
    confusion: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for p in predictions:
        confusion[p["true_label"]][p["predicted"]] += 1

    # Per-bucket precision, recall, F1
    all_labels = sorted(
        set(p["true_label"] for p in predictions)
        | set(p["predicted"] for p in predictions)
    )
    per_bucket: Dict[str, Dict] = {}

    for label in all_labels:
        tp = sum(
            1 for p in predictions
            if p["true_label"] == label and p["predicted"] == label
        )
        fp = sum(
            1 for p in predictions
            if p["true_label"] != label and p["predicted"] == label
        )
        fn = sum(
            1 for p in predictions
            if p["true_label"] == label and p["predicted"] != label
        )
        support = tp + fn

        precision = round(tp / (tp + fp), 4) if (tp + fp) else 0.0
        recall = round(tp / (tp + fn), 4) if (tp + fn) else 0.0
        f1 = (
            round(2 * precision * recall / (precision + recall), 4)
            if (precision + recall)
            else 0.0
        )

        per_bucket[label] = {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "support": support,
        }

    # Confidence statistics
    sorted_conf = sorted(confidences)
    n = len(sorted_conf)
    conf_stats = {
        "mean": round(sum(sorted_conf) / n, 4),
        "min": round(sorted_conf[0], 4),
        "max": round(sorted_conf[-1], 4),
        "median": round(
            sorted_conf[n // 2]
            if n % 2
            else (sorted_conf[n // 2 - 1] + sorted_conf[n // 2]) / 2,
            4,
        ),
    }

    # Misclassified samples (for debugging)
    misclassified = [
        p for p in predictions if p["true_label"] != p["predicted"]
    ]

    return {
        "total": total,
        "correct": correct,
        "accuracy": accuracy,
        "per_bucket": per_bucket,
        "confusion_matrix": {k: dict(v) for k, v in confusion.items()},
        "confidence_stats": conf_stats,
        "misclassified": misclassified,
    }
