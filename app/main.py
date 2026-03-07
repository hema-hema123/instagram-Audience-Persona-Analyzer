from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import RedirectResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from typing import List, Optional
import csv, io, json, uuid, asyncio
from collections import Counter

from .schemas import (
    ClassifyRequest, ClassifyResponse, ReportResponse,
    Classified, Item, MetricsResponse, ModelInfoResponse,
    HistoryResponse, HistorySession, TimelineResponse, TimelineDay,
    ComparisonResponse, BucketShift,
    SentimentAggregate, SentimentDistribution,
    EngagementAggregate, EnhancedClassified,
)
from .classifier import classify_text, classify_text_detailed, LABELS, BUCKETS, W_RULES, W_TFIDF
from .ml import tfidf_model
from .report import build_report
from .evaluation import evaluate_model
from .sentiment import analyze_sentiment, aggregate_sentiment
from .engagement import score_engagement, aggregate_engagement
from .history import get_history, get_session_detail, get_timeline, clear_history
from . import ig_api

app = FastAPI(title="Instagram Audience Persona Analyzer", version="0.3.0")

# Serve the minimal web UI
app.mount("/ui", StaticFiles(directory="web", html=True), name="web")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── In-memory batch job store ──
_batch_jobs = {}


@app.get("/health")
def health():
    return {"status": "ok", "version": "0.3.0"}

@app.get("/docs/ig")
def docs_ig():
    return ig_api.docs()


# ──────────────────────────────────────
# Classification Endpoints
# ──────────────────────────────────────

@app.post("/classify", response_model=ClassifyResponse)
def classify(req: ClassifyRequest):
    out: List[Classified] = []
    for it in req.items:
        bucket, conf, hits = classify_text(it.text)
        out.append(Classified(id=it.id, bucket=bucket, confidence=conf, matched_keywords=hits))
    return ClassifyResponse(results=out)

@app.post("/classify_detailed")
def classify_detailed(req: ClassifyRequest):
    """Return full classification details including per-method scores."""
    return [classify_text_detailed(it.text) for it in req.items]


# ──────────────────────────────────────
# Report Endpoints
# ──────────────────────────────────────

@app.post("/report", response_model=ReportResponse)
def report(req: ClassifyRequest):
    return build_report(req.items)


@app.post("/report_csv", response_model=ReportResponse)
async def report_csv(file: UploadFile = File(...)):
    if not file.filename.lower().endswith((".csv",)):
        raise HTTPException(status_code=400, detail="Please upload a CSV file")
    items = await _parse_csv_upload(file)
    return build_report(items, filename=file.filename)


@app.get("/demo_report", response_model=ReportResponse)
def demo_report():
    demo = [
        Item(id="u1", text="B.Tech CSE @ IIT. Learning DSA and ML. Open to work"),
        Item(id="u2", text="Gym • Personal Trainer • Calisthenics"),
        Item(id="u3", text="Entrepreneur | Startup founder | Ecommerce"),
        Item(id="u4", text="Shri Ram | Har Har Mahadev | Fitness and yoga"),
        Item(id="u5", text="Software engineer | Backend | DevOps | AWS | Docker | Open source"),
        Item(id="u6", text="☕ Coffee lover | Travel addict | 🌍"),
        Item(id="u7", text="YouTube 120K | DM for collabs | Creator 🎥"),
        Item(id="u8", text="Open to work | Fresher | B.Tech 2024 | Actively interviewing"),
    ]
    return build_report(demo)


# ──────────────────────────────────────
# Batch Async Processing
# ──────────────────────────────────────

@app.post("/batch")
async def start_batch(file: UploadFile = File(...)):
    """
    Start an async batch classification job.
    Returns a job_id immediately. Poll GET /batch/{job_id} for results.
    """
    if not file.filename.lower().endswith((".csv",)):
        raise HTTPException(status_code=400, detail="Please upload a CSV file")

    items = await _parse_csv_upload(file)
    job_id = str(uuid.uuid4())[:8]
    _batch_jobs[job_id] = {"status": "processing", "total": len(items), "result": None}

    # Launch background task
    asyncio.get_event_loop().create_task(_run_batch(job_id, items, file.filename))

    return {"job_id": job_id, "status": "processing", "total": len(items)}


@app.get("/batch/{job_id}")
def get_batch_status(job_id: str):
    """Poll batch job status. Returns results when complete."""
    job = _batch_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job["status"] == "processing":
        return {"job_id": job_id, "status": "processing", "total": job["total"]}
    return {"job_id": job_id, "status": "complete", "result": job["result"]}


async def _run_batch(job_id: str, items: List[Item], filename: str):
    """Background task for batch classification."""
    try:
        # Run in executor to avoid blocking
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, build_report, items, filename)
        _batch_jobs[job_id] = {"status": "complete", "total": len(items), "result": result.model_dump()}
    except Exception as e:
        _batch_jobs[job_id] = {"status": "error", "total": len(items), "result": {"error": str(e)}}


# ──────────────────────────────────────
# Export Endpoints
# ──────────────────────────────────────

@app.post("/export/csv")
async def export_csv(req: ClassifyRequest):
    """Classify items and return results as a downloadable CSV file."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "bio", "bucket", "confidence", "sentiment", "polarity", "engagement_score", "engagement_grade", "keywords"])

    for it in req.items:
        bucket, conf, kws = classify_text(it.text)
        sent = analyze_sentiment(it.text)
        eng = score_engagement(it.text)
        writer.writerow([
            it.id, it.text, bucket, round(conf, 4),
            sent.label, round(sent.polarity, 4),
            eng.total_score, eng.grade,
            "; ".join(kws),
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=classified_results.csv"},
    )


@app.post("/export/json")
async def export_json(req: ClassifyRequest):
    """Classify items and return results as a downloadable JSON file."""
    results = []
    for it in req.items:
        bucket, conf, kws = classify_text(it.text)
        sent = analyze_sentiment(it.text)
        eng = score_engagement(it.text)
        results.append({
            "id": it.id,
            "bio": it.text,
            "bucket": bucket,
            "confidence": round(conf, 4),
            "sentiment": sent.label,
            "polarity": round(sent.polarity, 4),
            "subjectivity": round(sent.subjectivity, 4),
            "engagement_score": eng.total_score,
            "engagement_grade": eng.grade,
            "keywords": kws,
        })

    content = json.dumps(results, indent=2)
    return StreamingResponse(
        iter([content]),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=classified_results.json"},
    )


# ──────────────────────────────────────
# Comparison Endpoint
# ──────────────────────────────────────

@app.post("/compare", response_model=ComparisonResponse)
async def compare_audiences(
    file_a: UploadFile = File(...),
    file_b: UploadFile = File(...),
):
    """
    Upload two CSV files and get a side-by-side persona shift analysis.
    Shows how audience composition changed between dataset A and B.
    """
    items_a = await _parse_csv_upload(file_a)
    items_b = await _parse_csv_upload(file_b)

    # Classify both
    results_a = [(it.id, *classify_text(it.text)) for it in items_a]
    results_b = [(it.id, *classify_text(it.text)) for it in items_b]

    # Bucket counts
    counts_a = Counter(r[1] for r in results_a)
    counts_b = Counter(r[1] for r in results_b)
    total_a = len(results_a)
    total_b = len(results_b)

    # Build shifts for all buckets
    all_buckets = sorted(set(list(counts_a.keys()) + list(counts_b.keys())))
    shifts = []
    for bucket in all_buckets:
        ca = counts_a.get(bucket, 0)
        cb = counts_b.get(bucket, 0)
        pct_a = round(ca / total_a * 100, 1) if total_a else 0
        pct_b = round(cb / total_b * 100, 1) if total_b else 0
        shifts.append(BucketShift(
            bucket=bucket,
            count_a=ca, count_b=cb,
            pct_a=pct_a, pct_b=pct_b,
            change=round(pct_b - pct_a, 1),
        ))

    # Sentiment for both
    sent_a = [analyze_sentiment(it.text) for it in items_a]
    sent_b = [analyze_sentiment(it.text) for it in items_b]
    sent_agg_a = aggregate_sentiment(sent_a)
    sent_agg_b = aggregate_sentiment(sent_b)

    # Engagement for both
    eng_a = [score_engagement(it.text) for it in items_a]
    eng_b = [score_engagement(it.text) for it in items_b]
    eng_agg_a = aggregate_engagement(eng_a)
    eng_agg_b = aggregate_engagement(eng_b)

    return ComparisonResponse(
        total_a=total_a,
        total_b=total_b,
        shifts=shifts,
        sentiment_a=SentimentAggregate(
            distribution=SentimentDistribution(**sent_agg_a["distribution"]),
            avg_polarity=sent_agg_a["avg_polarity"],
            avg_subjectivity=sent_agg_a["avg_subjectivity"],
        ),
        sentiment_b=SentimentAggregate(
            distribution=SentimentDistribution(**sent_agg_b["distribution"]),
            avg_polarity=sent_agg_b["avg_polarity"],
            avg_subjectivity=sent_agg_b["avg_subjectivity"],
        ),
        engagement_a=EngagementAggregate(
            avg_score=eng_agg_a["avg_score"],
            grade_distribution=eng_agg_a["grade_distribution"],
            avg_breakdown=eng_agg_a["avg_breakdown"],
        ),
        engagement_b=EngagementAggregate(
            avg_score=eng_agg_b["avg_score"],
            grade_distribution=eng_agg_b["grade_distribution"],
            avg_breakdown=eng_agg_b["avg_breakdown"],
        ),
    )


# ──────────────────────────────────────
# History Endpoints
# ──────────────────────────────────────

@app.get("/history", response_model=HistoryResponse)
def history(limit: int = 50):
    """Get recent classification sessions."""
    sessions = get_history(limit)
    return HistoryResponse(sessions=[HistorySession(**s) for s in sessions])

@app.get("/history/{session_id}")
def history_detail(session_id: str):
    """Get full detail for a past session."""
    detail = get_session_detail(session_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Session not found")
    return detail

@app.get("/timeline", response_model=TimelineResponse)
def timeline(days: int = 30):
    """Get daily aggregate stats for audience trend analysis."""
    data = get_timeline(days)
    return TimelineResponse(days=[TimelineDay(**d) for d in data])

@app.delete("/history")
def delete_history():
    """Clear all classification history."""
    clear_history()
    return {"status": "cleared"}


# ──────────────────────────────────────
# Model Metrics Endpoints
# ──────────────────────────────────────

@app.get("/metrics", response_model=MetricsResponse)
def get_metrics():
    """
    Run the classifier against labeled test data and return evaluation metrics.
    """
    result = evaluate_model()
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return result

@app.get("/model_info", response_model=ModelInfoResponse)
def get_model_info():
    """Return model architecture info."""
    eval_result = evaluate_model()
    accuracy = eval_result.get("accuracy", 0.0)
    total = eval_result.get("total", 0)

    return ModelInfoResponse(
        methods=["rule_based_keywords", "tfidf_cosine_similarity"],
        weights={"rules": W_RULES, "tfidf": W_TFIDF},
        buckets=LABELS,
        tfidf_features=tfidf_model.get_top_features(8),
        test_samples=total,
        accuracy=accuracy,
    )


# ──────────────────────────────────────
# Helpers
# ──────────────────────────────────────

async def _parse_csv_upload(file: UploadFile) -> List[Item]:
    """Parse an uploaded CSV file into a list of Items."""
    content = await file.read()
    try:
        text = content.decode("utf-8", errors="ignore")
        reader = csv.DictReader(io.StringIO(text))
        items = []
        for i, row in enumerate(reader):
            uid = row.get("id") or f"u{i+1}"
            txt = (row.get("bio") or row.get("text") or "").strip()
            if txt:
                items.append(Item(id=uid, text=txt))
        if not items:
            raise HTTPException(
                status_code=400,
                detail="No rows with text found. Ensure CSV has columns 'id' and 'bio' or 'text'.",
            )
        return items
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not parse CSV: {e}")


@app.get("/")
def root():
    return RedirectResponse(url="/ui")

