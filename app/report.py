from typing import List, Dict, Optional
import uuid
from .classifier import classify_text, aggregate
from .schemas import (
    Item, ReportResponse, ReportBucket,
    EnhancedClassified, SentimentAggregate, SentimentDistribution,
    EngagementAggregate,
)
from .sentiment import analyze_sentiment, aggregate_sentiment
from .engagement import score_engagement, aggregate_engagement
from .history import save_session


def build_report(items: List[Item], filename: Optional[str] = None) -> ReportResponse:
    triples = []
    enhanced: List[EnhancedClassified] = []
    sentiment_results = []
    engagement_scores = []
    history_records = []

    for it in items:
        # Classification
        b, conf, kws = classify_text(it.text)
        triples.append((it.id, b, conf, kws))

        # Sentiment
        sent = analyze_sentiment(it.text)
        sentiment_results.append(sent)

        # Engagement
        eng = score_engagement(it.text)
        engagement_scores.append(eng)

        # Enhanced per-item record
        enhanced.append(EnhancedClassified(
            id=it.id,
            bucket=b,
            confidence=conf,
            matched_keywords=kws,
            sentiment=sent.label,
            polarity=sent.polarity,
            subjectivity=sent.subjectivity,
            engagement_score=eng.total_score,
            engagement_grade=eng.grade,
        ))

        # History record
        history_records.append({
            "user_id": it.id,
            "bio": it.text,
            "bucket": b,
            "confidence": conf,
            "sentiment": sent.label,
            "polarity": sent.polarity,
            "engagement": eng.total_score,
        })

    # Aggregations
    bucket_counts, keywords, examples = aggregate(triples)
    total = sum(bucket_counts.values())

    buckets = []
    for b, count in bucket_counts.most_common():
        top_kws = [k for k, _ in keywords.most_common(10)]
        buckets.append(ReportBucket(
            bucket=b,
            count=count,
            examples=examples.get(b, []),
            top_keywords=top_kws
        ))

    # Sentiment aggregate
    sent_agg = aggregate_sentiment(sentiment_results)
    sentiment = SentimentAggregate(
        distribution=SentimentDistribution(**sent_agg["distribution"]),
        avg_polarity=sent_agg["avg_polarity"],
        avg_subjectivity=sent_agg["avg_subjectivity"],
    )

    # Engagement aggregate
    eng_agg = aggregate_engagement(engagement_scores)
    engagement = EngagementAggregate(
        avg_score=eng_agg["avg_score"],
        grade_distribution=eng_agg["grade_distribution"],
        avg_breakdown=eng_agg["avg_breakdown"],
    )

    # Save to history
    session_id = str(uuid.uuid4())[:8]
    try:
        save_session(session_id, history_records, filename=filename)
    except Exception:
        pass  # Don't fail the report if DB write fails

    return ReportResponse(
        total=total,
        buckets=buckets,
        keywords_global=dict(keywords.most_common(50)),
        sentiment=sentiment,
        engagement=engagement,
        classified=enhanced,
        session_id=session_id,
    )

