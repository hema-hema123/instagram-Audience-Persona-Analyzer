from typing import List, Dict
from .classifier import classify_text, aggregate
from .schemas import Item, ReportResponse, ReportBucket

def build_report(items: List[Item]) -> ReportResponse:
    triples = []
    for it in items:
        b, conf, kws = classify_text(it.text)
        triples.append((it.id, b, conf, kws))
    bucket_counts, keywords, examples = aggregate(triples)
    total = sum(bucket_counts.values())

    buckets = []
    for b, count in bucket_counts.most_common():
        top_kws = []
        # per-bucket keyword prominence could be added; using global for simplicity
        top_kws = [k for k, _ in keywords.most_common(10)]
        buckets.append(ReportBucket(
            bucket=b,
            count=count,
            examples=examples.get(b, []),
            top_keywords=top_kws
        ))
    return ReportResponse(
        total=total,
        buckets=buckets,
        keywords_global=dict(keywords.most_common(50))
    )
