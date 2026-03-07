# Instagram Audience Persona Analyzer

An NLP-powered analytics tool that classifies Instagram audience bios into actionable persona segments using an **ensemble ML pipeline** (TF-IDF + rule-based keywords). Upload a CSV of bios, get back structured persona breakdowns with confidence scores, charts, and model evaluation metrics.

> **No scraping.** Works only with official Instagram Graph API data or consent-based CSV uploads.

![Python](https://img.shields.io/badge/Python-3.11+-3776ab?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)
![scikit-learn](https://img.shields.io/badge/scikit--learn-1.5-f7931e?logo=scikitlearn&logoColor=white)
![Tests](https://img.shields.io/badge/tests-39%20passed-4caf50)
![Accuracy](https://img.shields.io/badge/accuracy-89.7%25-2563eb)
![License](https://img.shields.io/badge/license-MIT-grey)

---

## Persona Buckets

| Bucket | Description | Example Bio |
|--------|-------------|-------------|
| **Student** | College students, learners | *"B.Tech CSE @ IIT • Learning DSA and ML"* |
| **Tech** | Software engineers, developers | *"Backend engineer • AWS • Docker • Open source"* |
| **Religious** | Faith-based, spiritual | *"Blessed • Har Har Mahadev • Gratitude"* |
| **Fitness** | Gym, sports, wellness | *"Personal Trainer • Calisthenics • NASM certified"* |
| **Job Seeker** | Actively looking for work | *"Open to work • Fresher • Actively interviewing"* |
| **Creator** | Content creators, influencers | *"YouTube 50K • DM for collabs • LinkInBio"* |
| **Business** | Entrepreneurs, founders | *"CEO @ startup • Ecommerce • Angel investor"* |
| **Other** | Doesn't fit above categories | *"Coffee lover • Travel addict • 🌍"* |

---

## Architecture

```text
┌──────────────────────────────────────────────────────┐
│                   FastAPI Server                     │
│                   (app/main.py)                      │
├──────────────┬───────────────────┬───────────────────┤
│  /classify   │  /report          │  /metrics         │
│  /report_csv │  /classify_detail │  /model_info      │
└──────┬───────┴─────────┬────────┴─────────┬─────────┘
       │                 │                  │
       ▼                 ▼                  ▼
┌─────────────────────────────┐   ┌─────────────────┐
│     Ensemble Classifier     │   │   Evaluation     │
│     (app/classifier.py)     │   │ (app/evaluation) │
├──────────┬──────────────────┤   │ precision/recall │
│ Rules    │ TF-IDF Cosine    │   │ F1 / confusion   │
│ (0.35)   │ (0.65)           │   │ matrix           │
├──────────┴──────────────────┤   └─────────────────┘
│ Optional: Zero-Shot (0.50)  │
│ (transformers, if enabled)  │
└─────────────────────────────┘
       │
       ▼
┌─────────────────────────────┐
│  TF-IDF Model (app/ml.py)  │
│  TfidfVectorizer (1,2-gram) │
│  cosine_similarity scoring  │
│  ~80 prototype bios trained │
└─────────────────────────────┘
```

### How the Ensemble Works

1. **Rule-based keywords** — pattern matching against curated keyword lists per bucket (weight: `0.35`)
2. **TF-IDF + cosine similarity** — vectorizes input against prototype bios, scores by similarity (weight: `0.65`)
3. **Optional zero-shot** — `facebook/bart-large-mnli` for out-of-vocabulary inputs (weight: `0.50`, requires `transformers`)

Weighted scores are normalized per bucket. The highest-scoring bucket wins if it exceeds the confidence threshold (0.08). Otherwise, the result is `"other"`.

---

## Evaluation Results

Evaluated on **87 labeled test bios** (`data/test_bios.csv`):

| Metric | Score |
|--------|-------|
| **Overall Accuracy** | **89.7%** |
| Best bucket (Fitness) | F1 = 96% |
| Best bucket (Creator) | F1 = 95% |
| Best bucket (Business) | F1 = 95% |
| Weakest bucket (Job Seeker) | F1 = 84% |

Run evaluation locally:

```bash
make evaluate
```

---

## Quick Start

### Prerequisites

- Python 3.11+
- pip

### Setup

```bash
git clone https://github.com/hema-hema123/instagram-Audience-Persona-Analyzer.git
cd instagram-Audience-Persona-Analyzer

python3 -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

### Run the Server

```bash
uvicorn app.main:app --reload --port 8000
```

Open in browser:

- **Dashboard:** <http://127.0.0.1:8000/ui>
- **API Docs:** <http://127.0.0.1:8000/docs>

### Run Tests

```bash
make test
# or
pytest tests/ -v
```

### Run Demo (no Instagram required)

```bash
python -m scripts.demo_classify
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/classify` | Classify a list of text items → bucket + confidence |
| `POST` | `/classify_detailed` | Same as classify, but returns per-method score breakdown |
| `POST` | `/report` | Classify + aggregate into report with charts data |
| `POST` | `/report_csv` | Upload a CSV file → full report |
| `GET` | `/demo_report` | Pre-built demo with 5 sample bios |
| `GET` | `/metrics` | Run evaluation → accuracy, precision, recall, F1, confusion matrix |
| `GET` | `/model_info` | Model architecture, weights, top TF-IDF features per bucket |
| `GET` | `/docs` | Swagger UI (auto-generated) |

### Example: Classify a Bio

```bash
curl -X POST http://127.0.0.1:8000/classify \
  -H "Content-Type: application/json" \
  -d '{"items": [{"id": "u1", "text": "B.Tech CSE | Learning ML and DSA"}]}'
```

Response:

```json
{
  "results": [
    {
      "id": "u1",
      "bucket": "student",
      "confidence": 0.82,
      "matched_keywords": ["b.tech", "learning", "cse"]
    }
  ]
}
```

### CSV Format

```csv
id,bio
user1,B.Tech CSE | Learning DSA and ML
user2,Gym Trainer | Calisthenics
user3,Startup founder | Ecommerce
```

---

## Project Structure

```text
├── app/
│   ├── main.py           # FastAPI routes, CORS, static files
│   ├── classifier.py     # Ensemble classifier (rules + TF-IDF + zero-shot)
│   ├── ml.py             # TF-IDF vectorizer + cosine similarity model
│   ├── evaluation.py     # Precision/recall/F1 evaluation framework
│   ├── report.py         # Aggregation logic for reports
│   ├── schemas.py        # Pydantic v2 request/response models
│   └── ig_api.py         # Instagram Graph API integration docs
├── data/
│   ├── sample_bios.csv   # 65+ sample bios for demo
│   └── test_bios.csv     # 90+ labeled bios for evaluation
├── tests/
│   ├── test_classifier.py  # 19 tests — rule-based, TF-IDF, ensemble
│   ├── test_api.py         # 10 tests — all API endpoints
│   └── test_evaluation.py  # 7 tests — metrics validation
├── web/
│   ├── index.html        # Dashboard UI
│   ├── style.css         # Clean analytics theme
│   └── script.js         # Charts, drag-drop, metrics rendering
├── scripts/
│   ├── demo_classify.py  # CLI demo script
│   ├── demo.sh           # Shell demo runner
│   ├── bootstrap.sh      # Environment setup
│   └── run_api.sh        # Server launcher
├── requirements.txt
├── Makefile              # test, evaluate, api, demo targets
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml
```

---

## Docker

```bash
docker build -t insta-audience .
docker run --rm -p 8000:8000 insta-audience
```

Or with Compose:

```bash
docker compose up
```

---

## Optional: Zero-Shot Classification

For higher accuracy on unusual bios, enable the transformer-based zero-shot classifier:

```bash
pip install transformers torch
export USE_ZEROSHOT=true
export ZS_MODEL=facebook/bart-large-mnli
uvicorn app.main:app --reload
```

This adds a third voter to the ensemble with weight `0.50`.

---

## Configuration

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `W_RULES` | `0.35` | Weight for rule-based classifier |
| `W_TFIDF` | `0.65` | Weight for TF-IDF classifier |
| `W_ZEROSHOT` | `0.50` | Weight for zero-shot classifier |
| `USE_ZEROSHOT` | `false` | Enable zero-shot transformer model |
| `ZS_MODEL` | `facebook/bart-large-mnli` | Hugging Face model ID |

---

## Instagram Graph API Integration

This tool is designed for **compliant** use:

1. Switch your Instagram account to Business or Creator
2. Create a Facebook App and obtain credentials
3. Get a long-lived Page Access Token
4. Fetch insights and comments (where permitted by platform policies)
5. Send consented text data to `/classify` or `/report`

> **Important:** Instagram does not provide follower bios via API. Do not scrape.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## License

MIT — see [LICENSE](LICENSE)

