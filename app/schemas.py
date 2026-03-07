from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

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

# ── Sentiment schemas ──

class SentimentItem(BaseModel):
    id: str
    polarity: float
    subjectivity: float
    label: str  # positive / neutral / negative

class SentimentDistribution(BaseModel):
    positive: int = 0
    neutral: int = 0
    negative: int = 0

class SentimentAggregate(BaseModel):
    distribution: SentimentDistribution
    avg_polarity: float
    avg_subjectivity: float

# ── Engagement schemas ──

class EngagementItem(BaseModel):
    id: str
    total_score: int
    grade: str
    breakdown: Dict[str, int]

class EngagementAggregate(BaseModel):
    avg_score: float
    grade_distribution: Dict[str, int]
    avg_breakdown: Dict[str, float]

# ── Enhanced report (with sentiment + engagement) ──

class EnhancedClassified(BaseModel):
    id: str
    bucket: str
    confidence: float
    matched_keywords: List[str] = []
    sentiment: str = ""          # positive / neutral / negative
    polarity: float = 0.0
    subjectivity: float = 0.0
    engagement_score: int = 0
    engagement_grade: str = ""

class ReportResponse(BaseModel):
    total: int
    buckets: List[ReportBucket]
    keywords_global: Dict[str, int]
    sentiment: Optional[SentimentAggregate] = None
    engagement: Optional[EngagementAggregate] = None
    classified: Optional[List[EnhancedClassified]] = None
    session_id: Optional[str] = None


# ── History schemas ──

class HistorySession(BaseModel):
    session_id: str
    filename: Optional[str] = None
    total_items: int
    created_at: str
    distribution: Dict[str, int]
    avg_confidence: float
    avg_polarity: Optional[float] = None
    avg_engagement: Optional[float] = None

class HistoryResponse(BaseModel):
    sessions: List[HistorySession]

class TimelineDay(BaseModel):
    date: str
    total: int
    avg_confidence: float
    avg_polarity: Optional[float] = None
    avg_engagement: Optional[float] = None
    distribution: Dict[str, int]

class TimelineResponse(BaseModel):
    days: List[TimelineDay]


# ── Comparison schemas ──

class BucketShift(BaseModel):
    bucket: str
    count_a: int
    count_b: int
    pct_a: float
    pct_b: float
    change: float   # percentage point shift

class ComparisonResponse(BaseModel):
    total_a: int
    total_b: int
    shifts: List[BucketShift]
    sentiment_a: Optional[SentimentAggregate] = None
    sentiment_b: Optional[SentimentAggregate] = None
    engagement_a: Optional[EngagementAggregate] = None
    engagement_b: Optional[EngagementAggregate] = None


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

