"""
Ensemble persona classifier.

Combines three classification strategies with weighted voting:
  1. Rule-based keyword matching (fast, high precision on known terms)
  2. TF-IDF + cosine similarity  (handles unseen vocab, real NLP)
  3. Zero-shot transformer        (optional, most powerful, GPU-heavy)

The ensemble merges scores to produce a final label + confidence.
"""

import os
import re
from collections import Counter
from typing import Dict, List, Tuple

from .ml import tfidf_model

USE_ZS = os.getenv("USE_ZEROSHOT", "false").lower() == "true"
ZS_MODEL = os.getenv("ZS_MODEL", "facebook/bart-large-mnli")

# ── Weights for ensemble voting ──
# Adjust these to control how much each method influences the result.
W_RULES = float(os.getenv("W_RULES", "0.35"))
W_TFIDF = float(os.getenv("W_TFIDF", "0.65"))
W_ZEROSHT = float(os.getenv("W_ZEROSHOT", "0.50"))

# Editable keyword buckets (seeded for Indian tech/student niche)
BUCKETS: Dict[str, List[str]] = {
    "student": [
        "student", "btech", "b.e", "b.e.", "b.sc", "bcom", "ba ",
        "mba", "mtech", "iit", "nit", "gate", "upsc", "jee", "college",
        "school", "undergrad", "fresher",
    ],
    "tech": [
        "software", "developer", "programmer", "coder", "coding", "engineer",
        "devops", "sre", "data", "ml", "ai", "nlp", "dl", "cloud", "aws",
        "gcp", "azure", "dsa", "system design", "backend", "frontend",
        "full stack",
    ],
    "religious": [
        "bhakt", "bhakti", "allah", "ram", "shri ram", "krishna", "mahadev",
        "shiv", "waheguru", "sai", "church", "jesus", "islam", "hindu",
        "sikh", "prayer", "om", "har har",
    ],
    "fitness": [
        "fitness", "gym", "trainer", "coach", "bodybuilder", "yoga", "runner",
        "marathon", "calisthenics", "powerlifting", "crossfit",
    ],
    "job-seeker": [
        "open to work", "seeking", "actively looking", "hiring me", "resume",
        "placements", "job seeker", "jobseeker", "freshers", "interview ready",
    ],
    "creator": [
        "creator", "influencer", "reels", "youtuber", "vlogger", "content",
        "shorts", "podcaster", "editor",
    ],
    "business": [
        "entrepreneur", "startup", "founder", "ceo", "cto", "coo", "marketer",
        "agency", "ecommerce", "shop", "brand",
    ],
}

LABELS = list(BUCKETS.keys()) + ["other"]


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower().strip())


# ────────────────────────────────────────
# Method 1: Rule-based keyword matching
# ────────────────────────────────────────
def rule_based_bucket(text: str) -> Tuple[str, float, List[str]]:
    """
    Score each bucket by counting keyword hits.
    Returns (best_bucket, confidence, matched_keywords).
    """
    t = _normalize(text)
    hits: Dict[str, int] = {}
    matched: List[str] = []
    for bucket, kws in BUCKETS.items():
        score = 0
        local_matches = []
        for kw in kws:
            if kw in t:
                score += 1
                local_matches.append(kw)
        hits[bucket] = score
        if score:
            matched.extend(local_matches)

    if not any(hits.values()):
        return "other", 0.0, []

    best = max(hits, key=hits.get)
    total_hits = hits[best]
    # Normalize: sigmoid-like confidence from hit count
    conf = min(0.5 + 0.12 * total_hits, 0.95)
    return best, conf, matched


# ────────────────────────────────────────
# Method 2: TF-IDF + cosine similarity
# ────────────────────────────────────────
def tfidf_bucket(text: str) -> Tuple[str, float, Dict[str, float]]:
    """
    Classify using the pre-trained TF-IDF model.
    Returns (best_bucket, confidence, all_bucket_scores).
    """
    return tfidf_model.predict(text)


# ────────────────────────────────────────
# Method 3: Zero-shot transformer (optional)
# ────────────────────────────────────────
_zs_pipeline = None

def _ensure_zs():
    global _zs_pipeline
    if _zs_pipeline is None:
        from transformers import pipeline
        _zs_pipeline = pipeline("zero-shot-classification", model=ZS_MODEL)
    return _zs_pipeline


def zeroshot_bucket(text: str) -> Tuple[str, float]:
    """Zero-shot classification. Returns (label, score)."""
    pipe = _ensure_zs()
    out = pipe(text, candidate_labels=LABELS, multi_label=False)
    return out["labels"][0], float(out["scores"][0])


# ────────────────────────────────────────
# Ensemble: merge all methods
# ────────────────────────────────────────
def classify_text(text: str) -> Tuple[str, float, List[str]]:
    """
    Ensemble classifier combining rule-based + TF-IDF (+ optional zero-shot).

    For each bucket, computes a weighted score:
        score[bucket] = W_RULES * rule_score + W_TFIDF * tfidf_score
                      + (W_ZEROSHT * zs_score if enabled)

    Returns (best_bucket, confidence, matched_keywords).
    """
    # Rule-based scores (normalized to 0–1 per bucket)
    rb_label, rb_conf, rb_keywords = rule_based_bucket(text)

    # TF-IDF scores (already 0–1 cosine similarity per bucket)
    tf_label, tf_conf, tf_all_scores = tfidf_bucket(text)

    # Build per-bucket rule scores for ensemble
    t = _normalize(text)
    rule_scores: Dict[str, float] = {}
    for bucket, kws in BUCKETS.items():
        hits = sum(1 for kw in kws if kw in t)
        rule_scores[bucket] = min(0.5 + 0.12 * hits, 0.95) if hits else 0.0
    rule_scores["other"] = 0.0

    # Weighted ensemble
    total_weight = W_RULES + W_TFIDF
    ensemble: Dict[str, float] = {}

    for label in LABELS:
        r_score = rule_scores.get(label, 0.0)
        t_score = tf_all_scores.get(label, 0.0)
        ensemble[label] = (W_RULES * r_score + W_TFIDF * t_score)

    # Optional: add zero-shot
    if USE_ZS:
        try:
            zs_label, zs_conf = zeroshot_bucket(text)
            total_weight += W_ZEROSHT
            for label in LABELS:
                zs_score = zs_conf if label == zs_label else 0.0
                ensemble[label] += W_ZEROSHT * zs_score
        except Exception:
            pass  # fallback: ignore ZS on error

    # Normalize by total weight
    for label in ensemble:
        ensemble[label] /= total_weight

    # Pick best
    best_label = max(ensemble, key=ensemble.get)
    best_score = ensemble[best_label]

    # If the best score is too low, classify as "other"
    if best_score < 0.08:
        best_label = "other"
        best_score = max(best_score, 0.05)

    # Clamp confidence to [0, 0.99]
    confidence = min(round(best_score, 4), 0.99)

    return best_label, confidence, rb_keywords


def classify_text_detailed(text: str) -> Dict:
    """
    Extended classification returning full details for metrics/debugging.
    """
    rb_label, rb_conf, rb_keywords = rule_based_bucket(text)
    tf_label, tf_conf, tf_all_scores = tfidf_bucket(text)
    final_label, final_conf, _ = classify_text(text)

    return {
        "text": text,
        "final_label": final_label,
        "final_confidence": final_conf,
        "rule_based": {"label": rb_label, "confidence": rb_conf, "keywords": rb_keywords},
        "tfidf": {"label": tf_label, "confidence": tf_conf, "scores": tf_all_scores},
        "method": "ensemble(rules+tfidf" + ("+zeroshot)" if USE_ZS else ")"),
    }


def aggregate(results: List[Tuple[str, str, float, List[str]]]):
    """Aggregate classification results into bucket counts, keywords, examples."""
    bucket_counts = Counter([b for _, b, _, _ in results])
    keywords = Counter([kw for *_, kws in results for kw in kws])
    examples: Dict[str, List[str]] = {}
    for uid, b, _, _ in results:
        examples.setdefault(b, [])
        if len(examples[b]) < 5:
            examples[b].append(uid)
    return bucket_counts, keywords, examples
