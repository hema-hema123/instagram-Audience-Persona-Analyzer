"""
Engagement scoring module.

Computes a composite engagement-potential score (0-100) for each bio
based on signals that correlate with audience interaction:

  - Emoji usage (visual engagement)
  - Call-to-action presence (DM me, link in bio, etc.)
  - Link/URL presence (driving traffic)
  - Bio completeness (length, substance)
  - Hashtag usage (discoverability)
  - Contact information (professionalism)

Each signal contributes a weighted sub-score to the final composite.
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

# ── Regex patterns ──

EMOJI_RE = re.compile(
    "["
    "\U0001F600-\U0001F64F"  # emoticons
    "\U0001F300-\U0001F5FF"  # symbols & pictographs
    "\U0001F680-\U0001F6FF"  # transport & map
    "\U0001F1E0-\U0001F1FF"  # flags
    "\U00002700-\U000027BF"  # dingbats
    "\U0000FE00-\U0000FE0F"  # variation selectors
    "\U0001F900-\U0001F9FF"  # supplemental
    "\U0001FA00-\U0001FA6F"  # chess symbols
    "\U0001FA70-\U0001FAFF"  # symbols extended
    "\U00002702-\U000027B0"  # more dingbats
    "]+",
    flags=re.UNICODE,
)

URL_RE = re.compile(
    r"https?://[^\s]+|(?:www\.)[^\s]+|(?:linktr\.ee|bit\.ly|links\.)[^\s]+",
    re.IGNORECASE,
)

HASHTAG_RE = re.compile(r"#[A-Za-z0-9_]+")

EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")

CTA_PATTERNS = [
    "dm me", "dm for", "dm us", "message me", "message us",
    "link in bio", "linkinbio", "link below", "tap the link",
    "click the link", "check out", "follow for", "subscribe",
    "book now", "shop now", "order now", "buy now",
    "swipe up", "join us", "sign up", "download",
    "hire me", "contact me", "reach out", "let's connect",
    "collab", "collaborate", "partnership", "inquiries",
    "available for", "open for",
]

# ── Weights for composite score ──
WEIGHTS = {
    "emoji":       0.10,
    "cta":         0.25,
    "url":         0.15,
    "completeness": 0.20,
    "hashtags":    0.10,
    "contact":     0.10,
    "formatting":  0.10,
}


@dataclass
class EngagementScore:
    """Engagement analysis result for a single bio."""
    total_score: int             # 0-100 composite
    breakdown: Dict[str, int]    # per-signal scores (0-100 each)
    signals: Dict[str, any]      # raw signal details
    grade: str                   # A/B/C/D/F letter grade


def _score_emojis(text: str) -> Tuple[int, Dict]:
    """Score emoji usage. 1-3 emojis is ideal; too many is spammy."""
    count = len(EMOJI_RE.findall(text))
    if count == 0:
        score = 20
    elif 1 <= count <= 3:
        score = 100
    elif 4 <= count <= 6:
        score = 75
    elif 7 <= count <= 10:
        score = 50
    else:
        score = 30  # emoji overload
    return score, {"emoji_count": count}


def _score_cta(text: str) -> Tuple[int, Dict]:
    """Score call-to-action presence."""
    t = text.lower()
    found = [cta for cta in CTA_PATTERNS if cta in t]
    if len(found) == 0:
        score = 10
    elif len(found) == 1:
        score = 80
    elif len(found) == 2:
        score = 100
    else:
        score = 90  # multiple CTAs, slightly less focused
    return score, {"ctas_found": found}


def _score_url(text: str) -> Tuple[int, Dict]:
    """Score link/URL presence."""
    urls = URL_RE.findall(text)
    has_url = len(urls) > 0
    return (100 if has_url else 15), {"urls": urls, "has_url": has_url}


def _score_completeness(text: str) -> Tuple[int, Dict]:
    """Score bio completeness based on length and substance."""
    word_count = len(text.split())
    char_count = len(text.strip())

    if char_count < 10:
        score = 10
    elif char_count < 30:
        score = 30
    elif char_count < 60:
        score = 60
    elif char_count < 150:
        score = 90
    elif char_count <= 300:
        score = 100
    else:
        score = 85  # very long might be unfocused

    return score, {"word_count": word_count, "char_count": char_count}


def _score_hashtags(text: str) -> Tuple[int, Dict]:
    """Score hashtag usage for discoverability."""
    tags = HASHTAG_RE.findall(text)
    count = len(tags)
    if count == 0:
        score = 30
    elif 1 <= count <= 3:
        score = 100
    elif 4 <= count <= 6:
        score = 70
    else:
        score = 40  # hashtag stuffing
    return score, {"hashtags": tags, "hashtag_count": count}


def _score_contact(text: str) -> Tuple[int, Dict]:
    """Score professional contact info presence."""
    has_email = bool(EMAIL_RE.search(text))
    t = text.lower()
    has_phone_hint = any(w in t for w in ["call", "phone", "whatsapp", "telegram"])
    has_location = any(w in t for w in ["📍", "based in", "from ", "located"])

    signals_count = sum([has_email, has_phone_hint, has_location])
    score = min(30 + signals_count * 30, 100)
    return score, {
        "has_email": has_email,
        "has_phone_hint": has_phone_hint,
        "has_location": has_location,
    }


def _score_formatting(text: str) -> Tuple[int, Dict]:
    """Score formatting quality (separators, line breaks, structure)."""
    has_separator = any(sep in text for sep in ["|", "•", "·", "—", "–", "//", "→"])
    has_newlines = "\n" in text
    has_caps_word = bool(re.search(r"\b[A-Z]{2,}\b", text))  # emphasis words

    signals_count = sum([has_separator, has_newlines, has_caps_word])
    score = 25 + signals_count * 25
    return score, {
        "has_separator": has_separator,
        "has_newlines": has_newlines,
        "has_emphasis": has_caps_word,
    }


def _letter_grade(score: int) -> str:
    """Convert numeric score to letter grade."""
    if score >= 85:
        return "A"
    elif score >= 70:
        return "B"
    elif score >= 55:
        return "C"
    elif score >= 40:
        return "D"
    else:
        return "F"


def score_engagement(text: str) -> EngagementScore:
    """
    Compute composite engagement score for a single bio.

    Returns EngagementScore with total (0-100), per-signal breakdown,
    raw signal details, and letter grade.
    """
    scorers = {
        "emoji": _score_emojis,
        "cta": _score_cta,
        "url": _score_url,
        "completeness": _score_completeness,
        "hashtags": _score_hashtags,
        "contact": _score_contact,
        "formatting": _score_formatting,
    }

    breakdown = {}
    all_signals = {}
    weighted_total = 0.0

    for key, scorer in scorers.items():
        sub_score, signals = scorer(text)
        breakdown[key] = sub_score
        all_signals[key] = signals
        weighted_total += WEIGHTS[key] * sub_score

    total = min(round(weighted_total), 100)

    return EngagementScore(
        total_score=total,
        breakdown=breakdown,
        signals=all_signals,
        grade=_letter_grade(total),
    )


def score_batch(texts: List[str]) -> List[EngagementScore]:
    """Score engagement for a list of bios."""
    return [score_engagement(t) for t in texts]


def aggregate_engagement(scores: List[EngagementScore]) -> Dict:
    """
    Aggregate engagement scores for a batch.

    Returns:
        - avg_score: float
        - grade_distribution: {A: N, B: N, ...}
        - avg_breakdown: {signal: avg_score}
        - top_performers: indices of top 5 highest-scoring bios
    """
    if not scores:
        return {
            "avg_score": 0,
            "grade_distribution": {},
            "avg_breakdown": {},
        }

    grade_dist: Dict[str, int] = {}
    for s in scores:
        grade_dist[s.grade] = grade_dist.get(s.grade, 0) + 1

    # Average per-signal breakdown
    signal_keys = list(scores[0].breakdown.keys())
    avg_breakdown = {}
    for key in signal_keys:
        avg_breakdown[key] = round(
            sum(s.breakdown[key] for s in scores) / len(scores), 1
        )

    totals = [s.total_score for s in scores]
    sorted_indices = sorted(range(len(totals)), key=lambda i: totals[i], reverse=True)

    return {
        "avg_score": round(sum(totals) / len(totals), 1),
        "grade_distribution": grade_dist,
        "avg_breakdown": avg_breakdown,
        "top_performers": sorted_indices[:5],
    }
