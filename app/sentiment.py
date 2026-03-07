"""
Sentiment analysis module.

Uses TextBlob for polarity/subjectivity scoring on bios.
Provides per-bio sentiment and aggregate distribution stats.

Polarity:       -1.0 (very negative) → +1.0 (very positive)
Subjectivity:    0.0 (very objective) → 1.0 (very subjective)
"""

from dataclasses import dataclass
from typing import Dict, List
from textblob import TextBlob


@dataclass
class SentimentResult:
    """Sentiment scores for a single text."""
    polarity: float       # -1 to 1
    subjectivity: float   # 0 to 1
    label: str            # positive / neutral / negative


def analyze_sentiment(text: str) -> SentimentResult:
    """
    Analyze sentiment of a single bio/text.

    Returns:
        SentimentResult with polarity, subjectivity, and categorical label.
    """
    blob = TextBlob(text)
    polarity = round(blob.sentiment.polarity, 4)
    subjectivity = round(blob.sentiment.subjectivity, 4)

    if polarity > 0.1:
        label = "positive"
    elif polarity < -0.1:
        label = "negative"
    else:
        label = "neutral"

    return SentimentResult(
        polarity=polarity,
        subjectivity=subjectivity,
        label=label,
    )


def analyze_batch(texts: List[str]) -> List[SentimentResult]:
    """Analyze sentiment for a list of texts."""
    return [analyze_sentiment(t) for t in texts]


def aggregate_sentiment(results: List[SentimentResult]) -> Dict:
    """
    Compute aggregate sentiment statistics from a list of results.

    Returns dict with:
        - distribution: {positive: N, neutral: N, negative: N}
        - avg_polarity: float
        - avg_subjectivity: float
        - most_positive: index of most positive text
        - most_negative: index of most negative text
    """
    if not results:
        return {
            "distribution": {"positive": 0, "neutral": 0, "negative": 0},
            "avg_polarity": 0.0,
            "avg_subjectivity": 0.0,
        }

    distribution = {"positive": 0, "neutral": 0, "negative": 0}
    for r in results:
        distribution[r.label] += 1

    polarities = [r.polarity for r in results]
    subjectivities = [r.subjectivity for r in results]

    return {
        "distribution": distribution,
        "avg_polarity": round(sum(polarities) / len(polarities), 4),
        "avg_subjectivity": round(sum(subjectivities) / len(subjectivities), 4),
        "most_positive_idx": int(max(range(len(polarities)), key=lambda i: polarities[i])),
        "most_negative_idx": int(min(range(len(polarities)), key=lambda i: polarities[i])),
    }
