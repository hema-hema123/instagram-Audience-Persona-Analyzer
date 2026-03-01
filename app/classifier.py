import os
import re
from collections import Counter
from typing import Dict, List, Tuple

USE_ZS = os.getenv("USE_ZEROSHOT", "false").lower() == "true"
ZS_MODEL = os.getenv("ZS_MODEL", "facebook/bart-large-mnli")

# Editable keyword buckets (seeded for Indian tech/student niche)
BUCKETS: Dict[str, List[str]] = {
    "student": ["student","btech","b.e","b.e.","btech","b.sc","bcom","ba ","mba","mtech","iit","nit","gate","upsc","jee","college","school","undergrad","fresher"],
    "tech": ["software","developer","programmer","coder","coding","engineer","devops","sre","data","ml","ai","nlp","dl","cloud","aws","gcp","azure","dsa","system design","backend","frontend","full stack"],
    "religious": ["bhakt","bhakti","allah","ram","shri ram","krishna","mahadev","shiv","waheguru","sai","church","jesus","islam","hindu","sikh","prayer","om","har har"],
    "fitness": ["fitness","gym","trainer","coach","bodybuilder","yoga","runner","marathon","calisthenics","powerlifting","crossfit"],
    "job-seeker": ["open to work","seeking","actively looking","hiring me","resume","placements","job seeker","jobseeker","freshers","interview ready"],
    "creator": ["creator","influencer","reels","youtuber","vlogger","content","shorts","podcaster","editor"],
    "business": ["entrepreneur","startup","founder","ceo","cto","coo","marketer","agency","ecommerce","shop","brand"],
}

LABELS = list(BUCKETS.keys()) + ["other"]

def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower().strip())

def rule_based_bucket(text: str) -> Tuple[str, float, List[str]]:
    t = _normalize(text)
    hits = {}
    matched = []
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
    # pick best bucket
    if not any(hits.values()):
        return "other", 0.5, []
    best = max(hits, key=hits.get)
    # confidence = sigmoid-ish of score
    conf = min(0.5 + 0.1 * hits[best], 0.95)
    # small tie-handling
    return best, conf, matched

# Optional zero-shot classification
_zs_pipeline = None
def _ensure_zs():
    global _zs_pipeline
    if _zs_pipeline is None:
        from transformers import pipeline
        _zs_pipeline = pipeline("zero-shot-classification", model=ZS_MODEL)
    return _zs_pipeline

def classify_text(text: str) -> Tuple[str, float, List[str]]:
    if USE_ZS:
        try:
            pipe = _ensure_zs()
            out = pipe(text, candidate_labels=LABELS, multi_label=False)
            label = out["labels"][0]
            score = float(out["scores"][0])
            # merge with rules as prior if rules found strong signal
            rb_label, rb_conf, rb_hits = rule_based_bucket(text)
            if rb_conf >= 0.75 and rb_label != "other":
                # nudge toward rule label
                if rb_label != label and rb_conf > score:
                    label, score = rb_label, rb_conf
                else:
                    score = min(0.98, (score + rb_conf) / 2)
            return label, score, list(set(rb_hits))
        except Exception:
            # fallback to rules if any issue
            pass
    return rule_based_bucket(text)

def aggregate(results: List[Tuple[str, str, float, List[str]]]):
    # results: list of (id, bucket, conf, matched_keywords)
    bucket_counts = Counter([b for _, b, _, _ in results])
    keywords = Counter([kw for *_, kws in results for kw in kws])
    examples = {}
    for uid, b, _, _ in results:
        examples.setdefault(b, [])
        if len(examples[b]) < 5:
            examples[b].append(uid)
    return bucket_counts, keywords, examples
