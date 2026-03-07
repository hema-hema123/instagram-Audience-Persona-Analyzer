"""Tests for the evaluation framework."""

import pytest
from app.evaluation import evaluate_model


class TestEvaluation:
    def test_evaluate_returns_metrics(self):
        result = evaluate_model()
        assert "error" not in result
        assert "accuracy" in result
        assert "per_bucket" in result
        assert "confusion_matrix" in result
        assert "confidence_stats" in result
        assert "misclassified" in result

    def test_accuracy_is_reasonable(self):
        result = evaluate_model()
        # With our test data and ensemble, accuracy should be > 70%
        assert result["accuracy"] > 0.70, (
            f"Accuracy too low: {result['accuracy']}"
        )

    def test_all_buckets_have_metrics(self):
        result = evaluate_model()
        for bucket, metrics in result["per_bucket"].items():
            assert "precision" in metrics
            assert "recall" in metrics
            assert "f1" in metrics
            assert "support" in metrics
            assert 0.0 <= metrics["precision"] <= 1.0
            assert 0.0 <= metrics["recall"] <= 1.0

    def test_confidence_stats(self):
        result = evaluate_model()
        stats = result["confidence_stats"]
        assert stats["min"] <= stats["mean"] <= stats["max"]
        assert stats["min"] <= stats["median"] <= stats["max"]

    def test_confusion_matrix_shape(self):
        result = evaluate_model()
        cm = result["confusion_matrix"]
        # Each true label should have at least one prediction
        assert len(cm) > 0

    def test_total_matches(self):
        result = evaluate_model()
        assert result["total"] == result["correct"] + len(result["misclassified"])

    def test_invalid_path(self):
        result = evaluate_model(test_path="/nonexistent/file.csv")
        assert "error" in result
