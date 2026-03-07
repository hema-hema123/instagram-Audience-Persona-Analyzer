"""Tests for the ensemble classifier."""

import pytest
from app.classifier import classify_text, rule_based_bucket, tfidf_bucket, LABELS


class TestRuleBased:
    """Test the keyword-based classifier."""

    def test_student_bio(self):
        label, conf, kws = rule_based_bucket("BTech CSE student at IIT preparing for GATE")
        assert label == "student"
        assert conf > 0.5
        assert len(kws) > 0

    def test_tech_bio(self):
        label, conf, kws = rule_based_bucket("Software engineer backend developer Python AWS")
        assert label == "tech"
        assert conf > 0.5

    def test_fitness_bio(self):
        label, conf, kws = rule_based_bucket("Gym personal trainer bodybuilder coach")
        assert label == "fitness"

    def test_religious_bio(self):
        label, conf, kws = rule_based_bucket("Shri Ram Har Har Mahadev bhakt")
        assert label == "religious"

    def test_creator_bio(self):
        label, conf, kws = rule_based_bucket("Content creator reels YouTuber shorts")
        assert label == "creator"

    def test_business_bio(self):
        label, conf, kws = rule_based_bucket("Entrepreneur startup founder CEO ecommerce")
        assert label == "business"

    def test_job_seeker_bio(self):
        label, conf, kws = rule_based_bucket("Open to work actively looking for roles")
        assert label == "job-seeker"

    def test_other_bio(self):
        label, conf, kws = rule_based_bucket("Love travel and food exploring the world")
        assert label == "other"
        assert len(kws) == 0

    def test_empty_text(self):
        label, conf, kws = rule_based_bucket("")
        assert label == "other"


class TestTfidf:
    """Test the TF-IDF cosine similarity classifier."""

    def test_student_bio(self):
        label, conf, scores = tfidf_bucket("BTech college student preparing for GATE exam")
        assert label == "student"
        assert conf > 0.0
        assert isinstance(scores, dict)

    def test_tech_bio(self):
        label, conf, scores = tfidf_bucket("Machine learning engineer Python TensorFlow deployment")
        assert label == "tech"

    def test_returns_all_scores(self):
        label, conf, scores = tfidf_bucket("Gym fitness training")
        # Should have a score for every known bucket
        assert len(scores) >= 7

    def test_low_confidence_other(self):
        label, conf, scores = tfidf_bucket("zxcvbnm asdfgh qwerty")
        # Gibberish should get very low confidence
        assert conf < 0.3


class TestEnsemble:
    """Test the combined ensemble classifier."""

    def test_returns_valid_label(self):
        label, conf, kws = classify_text("Software developer Python backend")
        assert label in LABELS

    def test_confidence_range(self):
        label, conf, kws = classify_text("Yoga instructor fitness coach wellness")
        assert 0.0 <= conf <= 1.0

    def test_keywords_are_list(self):
        label, conf, kws = classify_text("Startup founder entrepreneur CEO")
        assert isinstance(kws, list)

    def test_student_classification(self):
        label, conf, kws = classify_text("BTech CSE student at IIT college")
        assert label == "student"

    def test_tech_classification(self):
        label, conf, kws = classify_text("DevOps engineer AWS Kubernetes Docker CI/CD")
        assert label == "tech"

    def test_fitness_classification(self):
        label, conf, kws = classify_text("Gym personal trainer calisthenics bodybuilder")
        assert label == "fitness"

    def test_creator_classification(self):
        label, conf, kws = classify_text("YouTube content creator reels daily vlogger")
        assert label == "creator"

    def test_business_classification(self):
        label, conf, kws = classify_text("Founder CEO building a SaaS startup ecommerce")
        assert label == "business"

    def test_other_classification(self):
        label, conf, kws = classify_text("Love sunshine and coffee morning walks")
        assert label == "other"
