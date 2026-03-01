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
