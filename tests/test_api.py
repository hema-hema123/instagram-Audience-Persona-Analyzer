"""Tests for API endpoints."""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestHealth:
    def test_health_ok(self):
        res = client.get("/health")
        assert res.status_code == 200
        assert res.json()["status"] == "ok"


class TestClassify:
    def test_classify_single(self):
        res = client.post("/classify", json={
            "items": [{"id": "u1", "text": "Software engineer Python backend"}]
        })
        assert res.status_code == 200
        data = res.json()
        assert len(data["results"]) == 1
        assert data["results"][0]["bucket"] in [
            "student", "tech", "religious", "fitness",
            "job-seeker", "creator", "business", "other"
        ]

    def test_classify_multiple(self):
        res = client.post("/classify", json={
            "items": [
                {"id": "u1", "text": "BTech student IIT"},
                {"id": "u2", "text": "Gym trainer fitness"},
            ]
        })
        assert res.status_code == 200
        assert len(res.json()["results"]) == 2

    def test_classify_empty_items(self):
        res = client.post("/classify", json={"items": []})
        assert res.status_code == 200
        assert res.json()["results"] == []


class TestReport:
    def test_report_endpoint(self):
        res = client.post("/report", json={
            "items": [
                {"id": "u1", "text": "BTech student college"},
                {"id": "u2", "text": "Gym trainer fitness coach"},
                {"id": "u3", "text": "Startup founder CEO"},
            ]
        })
        assert res.status_code == 200
        data = res.json()
        assert data["total"] == 3
        assert len(data["buckets"]) > 0

    def test_demo_report(self):
        res = client.get("/demo_report")
        assert res.status_code == 200
        data = res.json()
        assert data["total"] == 5
        assert len(data["buckets"]) > 0


class TestMetrics:
    def test_metrics_endpoint(self):
        res = client.get("/metrics")
        assert res.status_code == 200
        data = res.json()
        assert "accuracy" in data
        assert "per_bucket" in data
        assert "confusion_matrix" in data
        assert "confidence_stats" in data
        assert 0.0 <= data["accuracy"] <= 1.0

    def test_model_info(self):
        res = client.get("/model_info")
        assert res.status_code == 200
        data = res.json()
        assert "methods" in data
        assert "tfidf_cosine_similarity" in data["methods"]
        assert "tfidf_features" in data
        assert data["test_samples"] > 0


class TestCSVUpload:
    def test_csv_upload(self):
        csv_content = "id,bio\nu1,Software engineer Python\nu2,Gym trainer fitness"
        res = client.post(
            "/report_csv",
            files={"file": ("test.csv", csv_content, "text/csv")},
        )
        assert res.status_code == 200
        assert res.json()["total"] == 2

    def test_invalid_file_type(self):
        res = client.post(
            "/report_csv",
            files={"file": ("test.txt", "hello", "text/plain")},
        )
        assert res.status_code == 400
