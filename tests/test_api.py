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
        assert res.json()["version"] == "0.3.0"


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
    def test_report_has_sentiment_and_engagement(self):
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
        # New fields
        assert "sentiment" in data
        assert "engagement" in data
        assert "classified" in data
        assert "session_id" in data
        # Sentiment structure
        assert "distribution" in data["sentiment"]
        assert "avg_polarity" in data["sentiment"]
        # Engagement structure
        assert "avg_score" in data["engagement"]
        assert "grade_distribution" in data["engagement"]

    def test_classified_items_have_all_fields(self):
        res = client.post("/report", json={
            "items": [{"id": "u1", "text": "Software engineer AWS Docker"}]
        })
        data = res.json()
        c = data["classified"][0]
        assert "bucket" in c
        assert "confidence" in c
        assert "sentiment" in c
        assert "polarity" in c
        assert "engagement_score" in c
        assert "engagement_grade" in c

    def test_demo_report(self):
        res = client.get("/demo_report")
        assert res.status_code == 200
        data = res.json()
        assert data["total"] == 8  # updated demo has 8 items
        assert len(data["buckets"]) > 0
        assert data["sentiment"] is not None
        assert data["engagement"] is not None


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
        data = res.json()
        assert data["total"] == 2
        assert data["sentiment"] is not None
        assert data["session_id"] is not None

    def test_invalid_file_type(self):
        res = client.post(
            "/report_csv",
            files={"file": ("test.txt", "hello", "text/plain")},
        )
        assert res.status_code == 400


class TestExport:
    def test_export_csv(self):
        res = client.post("/export/csv", json={
            "items": [{"id": "u1", "text": "Software engineer Python"}]
        })
        assert res.status_code == 200
        assert "text/csv" in res.headers["content-type"]
        assert "attachment" in res.headers.get("content-disposition", "")

    def test_export_json(self):
        res = client.post("/export/json", json={
            "items": [{"id": "u1", "text": "Gym trainer fitness"}]
        })
        assert res.status_code == 200
        data = res.json()
        assert len(data) == 1
        assert "bucket" in data[0]
        assert "sentiment" in data[0]
        assert "engagement_score" in data[0]


class TestHistory:
    def test_history_endpoint(self):
        res = client.get("/history")
        assert res.status_code == 200
        data = res.json()
        assert "sessions" in data

    def test_timeline_endpoint(self):
        res = client.get("/timeline?days=30")
        assert res.status_code == 200
        data = res.json()
        assert "days" in data


class TestBatch:
    def test_batch_start(self):
        csv_content = "id,bio\nu1,Software engineer\nu2,Gym trainer"
        res = client.post(
            "/batch",
            files={"file": ("test.csv", csv_content, "text/csv")},
        )
        assert res.status_code == 200
        data = res.json()
        assert "job_id" in data
        assert data["status"] == "processing"

    def test_batch_unknown_job(self):
        res = client.get("/batch/nonexistent")
        assert res.status_code == 404

