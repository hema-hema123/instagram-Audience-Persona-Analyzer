from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from typing import List
from .schemas import (
    ClassifyRequest, ClassifyResponse, ReportResponse,
    Classified, Item, MetricsResponse, ModelInfoResponse,
)
from .classifier import classify_text, classify_text_detailed, LABELS, BUCKETS, W_RULES, W_TFIDF
from .ml import tfidf_model
from .report import build_report
from .evaluation import evaluate_model
from . import ig_api

app = FastAPI(title="Instagram Audience Persona Analyzer", version="0.2.0")

# Serve the minimal web UI
app.mount("/ui", StaticFiles(directory="web", html=True), name="web")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/docs/ig")
def docs_ig():
    return ig_api.docs()

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

@app.post("/report", response_model=ReportResponse)
def report(req: ClassifyRequest):
    return build_report(req.items)

from typing import Optional
import csv, io

@app.post("/report_csv", response_model=ReportResponse)
async def report_csv(file: UploadFile = File(...)):
    if not file.filename.lower().endswith((".csv")):
        raise HTTPException(status_code=400, detail="Please upload a CSV file")
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
            raise HTTPException(status_code=400, detail="No rows with text found. Ensure CSV has columns 'id' and 'bio' or 'text'.")
        return build_report(items)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not parse CSV: {e}")

@app.get("/demo_report", response_model=ReportResponse)
def demo_report():
    demo = [
        Item(id="u1", text="B.Tech CSE @ IIT. Learning DSA and ML. Open to work"),
        Item(id="u2", text="Gym • Personal Trainer • Calisthenics"),
        Item(id="u3", text="Entrepreneur | Startup founder | Ecommerce"),
        Item(id="u4", text="Shri Ram | Har Har Mahadev | Fitness and yoga"),
        Item(id="u5", text="Software engineer | Backend | DevOps | AWS | Docker | Open source"),
    ]
    return build_report(demo)


# ── Model Metrics Endpoints ──

@app.get("/metrics", response_model=MetricsResponse)
def get_metrics():
    """
    Run the classifier against labeled test data and return evaluation metrics:
    accuracy, per-bucket precision/recall/F1, confusion matrix, confidence stats.
    """
    result = evaluate_model()
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return result

@app.get("/model_info", response_model=ModelInfoResponse)
def get_model_info():
    """
    Return model architecture info: methods used, weights, bucket list,
    top TF-IDF features per bucket, and quick accuracy number.
    """
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


@app.get("/")
def root():
    return RedirectResponse(url="/ui")
