"""Tests for engagement scoring module."""

import pytest
from app.engagement import score_engagement, score_batch, aggregate_engagement, EngagementScore


class TestScoreEngagement:
    def test_plain_bio(self):
        result = score_engagement("hello")
        assert isinstance(result, EngagementScore)
        assert 0 <= result.total_score <= 100
        assert result.grade in ("A", "B", "C", "D", "F")

    def test_rich_bio(self):
        result = score_engagement(
            "🚀 Founder & CEO | DM for collabs 📩 | https://mysite.com "
            "#startup #tech | Python dev building the future!"
        )
        assert result.total_score > 40  # rich bio should score well

    def test_result_attributes(self):
        result = score_engagement("test bio")
        assert hasattr(result, "total_score")
        assert hasattr(result, "breakdown")
        assert hasattr(result, "signals")
        assert hasattr(result, "grade")

    def test_breakdown_has_all_signals(self):
        result = score_engagement("test bio text")
        expected_keys = {"emoji", "cta", "url", "completeness", "hashtags", "contact", "formatting"}
        assert set(result.breakdown.keys()) == expected_keys

    def test_grade_thresholds(self):
        # Minimal bio should get a low grade
        result = score_engagement("hi")
        assert result.grade in ("D", "F")

    def test_empty_bio(self):
        result = score_engagement("")
        assert result.grade == "F"

    def test_emoji_detected(self):
        result = score_engagement("🎉 Party time!")
        assert result.signals["emoji"]["emoji_count"] > 0

    def test_url_detected(self):
        result = score_engagement("Visit https://example.com today")
        assert result.signals["url"]["has_url"] is True

    def test_hashtag_detected(self):
        result = score_engagement("Love #python and #coding")
        assert result.signals["hashtags"]["hashtag_count"] >= 2


class TestScoreBatch:
    def test_batch(self):
        bios = ["Engineer", "🔥 CEO | DM me", "Student"]
        results = score_batch(bios)
        assert len(results) == 3
        assert all(isinstance(r, EngagementScore) for r in results)

    def test_batch_empty(self):
        assert score_batch([]) == []


class TestAggregateEngagement:
    def test_aggregate_structure(self):
        results = score_batch(["Hello", "🔥 CEO | https://x.com"])
        agg = aggregate_engagement(results)
        assert "avg_score" in agg
        assert "grade_distribution" in agg
        assert isinstance(agg["avg_score"], float)

    def test_aggregate_empty(self):
        agg = aggregate_engagement([])
        assert agg["avg_score"] == 0
