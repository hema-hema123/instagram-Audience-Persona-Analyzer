from pydantic import BaseModel, Field
from typing import List, Optional, Dict

class Item(BaseModel):
    id: str = Field(..., description="Unique id (username, user id, etc.)")
    text: str = Field(..., description="Bio or comment text to classify")

class ClassifyRequest(BaseModel):
    items: List[Item]

class Classified(BaseModel):
    id: str
    bucket: str
    confidence: float
    matched_keywords: List[str] = []

class ClassifyResponse(BaseModel):
    results: List[Classified]

class ReportBucket(BaseModel):
    bucket: str
    count: int
    examples: List[str] = []
    top_keywords: List[str] = []

class ReportResponse(BaseModel):
    total: int
    buckets: List[ReportBucket]
    keywords_global: Dict[str, int]


# ── Metrics / Evaluation schemas ──

class BucketMetrics(BaseModel):
    precision: float
    recall: float
    f1: float
    support: int

class ConfidenceStats(BaseModel):
    mean: float
    min: float
    max: float
    median: float

class Misclassified(BaseModel):
    id: str
    bio: str
    true_label: str
    predicted: str
    confidence: float

class MetricsResponse(BaseModel):
    total: int
    correct: int
    accuracy: float
    per_bucket: Dict[str, BucketMetrics]
    confusion_matrix: Dict[str, Dict[str, int]]
    confidence_stats: ConfidenceStats
    misclassified: List[Misclassified]

class ModelInfoResponse(BaseModel):
    methods: List[str]
    weights: Dict[str, float]
    buckets: List[str]
    tfidf_features: Dict[str, List[str]]
    test_samples: int
    accuracy: float
