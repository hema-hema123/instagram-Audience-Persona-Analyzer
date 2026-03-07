"""Tests for sentiment analysis module."""

import pytest
from app.sentiment import analyze_sentiment, analyze_batch, aggregate_sentiment, SentimentResult


class TestAnalyzeSentiment:
    def test_positive_text(self):
        result = analyze_sentiment("I love this amazing wonderful life!")
        assert isinstance(result, SentimentResult)
        assert result.polarity > 0.0
        assert result.label == "positive"

    def test_negative_text(self):
        result = analyze_sentiment("This is terrible awful horrible")
        assert result.polarity < 0.0
        assert result.label == "negative"

    def test_neutral_text(self):
        result = analyze_sentiment("User account id 12345")
        assert result.label == "neutral"

    def test_result_attributes(self):
        result = analyze_sentiment("Some text here")
        assert hasattr(result, "polarity")
        assert hasattr(result, "subjectivity")
        assert hasattr(result, "label")

    def test_empty_text(self):
        result = analyze_sentiment("")
        assert result.label == "neutral"

    def test_polarity_range(self):
        result = analyze_sentiment("This is great and wonderful")
        assert -1.0 <= result.polarity <= 1.0
        assert 0.0 <= result.subjectivity <= 1.0


class TestAnalyzeBatch:
    def test_batch(self):
        texts = ["I love coding", "This is bad", "Account 123"]
        results = analyze_batch(texts)
        assert len(results) == 3
        assert all(isinstance(r, SentimentResult) for r in results)

    def test_batch_empty(self):
        results = analyze_batch([])
        assert results == []


class TestAggregateSentiment:
    def test_aggregate_structure(self):
        texts = [
            "I love this so much!",
            "This is terrible",
            "User account number",
        ]
        results = analyze_batch(texts)
        agg = aggregate_sentiment(results)
        assert "distribution" in agg
        assert "avg_polarity" in agg
        assert "avg_subjectivity" in agg
        dist = agg["distribution"]
        assert "positive" in dist
        assert "negative" in dist
        assert "neutral" in dist
        assert dist["positive"] + dist["negative"] + dist["neutral"] == 3

    def test_aggregate_empty(self):
        agg = aggregate_sentiment([])
        assert agg["avg_polarity"] == 0.0
        assert agg["avg_subjectivity"] == 0.0
