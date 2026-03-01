from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from typing import List
from .schemas import ClassifyRequest, ClassifyResponse, ReportResponse, Classified, Item
from .classifier import classify_text
from .report import build_report
from . import ig_api

app = FastAPI(title="Instagram Audience Persona Analyzer", version="0.1.0")

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
