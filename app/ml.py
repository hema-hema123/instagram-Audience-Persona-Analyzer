"""
TF-IDF + Cosine Similarity classifier for audience persona buckets.

Instead of raw keyword substring matching, we build a TF-IDF vocabulary
from representative text for each persona bucket, then score new bios
by cosine similarity against each bucket centroid.

This is a proper NLP pipeline:
  1. Build corpus of synthetic "prototype" documents per bucket
  2. Fit TF-IDF vectorizer on the full corpus
  3. Compute centroid vectors per bucket
  4. Classify new text by highest cosine similarity to a centroid

Why this is better than keyword matching:
  - Handles partial matches and related words
  - Weighs rare, informative words higher (IDF)
  - Produces real similarity scores (not just hit count)
  - Easily extensible with new training data
"""

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from typing import Dict, List, Tuple

# Representative corpus per bucket — each string is a synthetic "prototype bio"
# that captures the vocabulary of that persona type.
TRAINING_CORPUS: Dict[str, List[str]] = {
    "student": [
        "btech cse student at iit learning dsa and ml preparing for gate",
        "3rd year btech computer science college student jee qualified",
        "undergrad student bsc physics fresher nit college campus",
        "mba student pursuing management studies college campus life",
        "mtech research student iit gate qualified data science aspirant",
        "bcom student commerce university college undergraduate fresher",
        "ba english literature student university undergrad creative writing",
        "class 12 student jee aspirant preparing for engineering entrance",
        "phd research scholar iit computer science machine learning student",
        "school student preparing for upsc civil services competitive exams",
        "college student hackathon participant coding club tech enthusiast",
        "btech ece student electronics engineering embedded systems vlsi",
    ],
    "tech": [
        "software engineer backend developer python java microservices",
        "full stack developer react nodejs typescript frontend backend",
        "devops engineer cloud aws gcp azure kubernetes docker ci cd",
        "data scientist machine learning ai nlp deep learning python",
        "system design backend engineer distributed systems scalable",
        "sre site reliability engineer monitoring observability infrastructure",
        "programmer coder open source contributor github developer",
        "ml engineer tensorflow pytorch model training deployment mlops",
        "frontend developer react angular vue css javascript web development",
        "cloud architect aws solutions certified infrastructure as code",
        "data engineer etl pipeline spark airflow data warehouse analytics",
        "cybersecurity engineer penetration testing security analyst infosec",
    ],
    "religious": [
        "bhakt shri ram har har mahadev spiritual devotional hindu temple",
        "allah bismillah islam prayer quran faith muslim devotion mosque",
        "waheguru sikh khalsa gurbani kirtan gurudwara seva punjab",
        "krishna consciousness bhakti yoga devotion spiritual temple iskcon",
        "jesus christ church prayer christian faith bible gospel worship",
        "om namah shivaya mahadev shiv bhakt spiritual devotion temple",
        "sai baba devotee faith prayer spiritual guidance divine blessings",
        "ram bhakt jai shri ram hindu spiritual dharma sanatan devotion",
        "meditation spirituality yoga mindfulness inner peace consciousness",
        "devotional music bhajan kirtan spiritual songs worship prayer",
    ],
    "fitness": [
        "fitness gym personal trainer bodybuilder workout muscle strength",
        "yoga instructor meditation wellness health flexibility mindfulness",
        "runner marathon athlete track running cardio distance training",
        "calisthenics bodyweight workout street workout pull ups strength",
        "powerlifting deadlift squat bench press strength training gym",
        "crossfit functional fitness workout wod training athlete coach",
        "sports coach athletic training basketball football cricket team",
        "nutritionist diet health wellness meal prep macros fitness coach",
        "weight loss transformation fitness journey healthy lifestyle gym",
        "swimming cyclist triathlon endurance athlete sports training",
    ],
    "job-seeker": [
        "open to work actively seeking software developer opportunities",
        "fresher looking for job placement interview ready hiring me",
        "actively looking for roles in data science ml ai engineer",
        "job seeker resume portfolio seeking opportunities tech industry",
        "recent graduate open to work entry level software engineer",
        "experienced professional seeking new opportunities career growth",
        "interview preparation coding practice placement season fresher",
        "actively looking freelance remote work contract opportunities",
        "career transition seeking roles in product management tech",
        "open to internship fresher student looking for industry experience",
    ],
    "creator": [
        "content creator influencer reels youtube shorts social media",
        "youtuber vlogger daily vlogs travel content digital creator",
        "reels creator instagram content trending viral social media growth",
        "podcaster host interviews conversations weekly episodes audio",
        "video editor motion graphics after effects premiere pro creator",
        "photographer visual storyteller content creator instagram portfolio",
        "digital creator social media manager brand collaborations influencer",
        "streamer twitch gaming content live stream community creator",
        "blogger writer content creator articles stories digital media",
        "music producer beats creator soundcloud spotify artist producer",
    ],
    "business": [
        "entrepreneur startup founder ceo building saas product company",
        "ecommerce business online shop d2c brand founder dropshipping",
        "digital marketer growth hacking seo sem social media marketing",
        "agency owner marketing branding design services business founder",
        "cto coo startup co-founder tech product engineering leadership",
        "freelancer consultant business owner independent professional",
        "small business owner local shop retail entrepreneur handmade",
        "investor angel funding venture capital startup ecosystem fintech",
        "brand strategist marketing consultant business growth revenue",
        "real estate agent property business investment entrepreneur broker",
    ],
}

# Labels in order — 'other' is the fallback
LABELS = list(TRAINING_CORPUS.keys())


class TfidfClassifier:
    """
    TF-IDF based persona classifier.

    Trains on synthetic prototype documents per bucket.
    Classifies new text by cosine similarity to bucket centroids.
    """

    def __init__(self, min_confidence: float = 0.10):
        self.min_confidence = min_confidence
        self.vectorizer = TfidfVectorizer(
            lowercase=True,
            stop_words="english",
            max_features=5000,
            ngram_range=(1, 2),        # unigrams + bigrams
            sublinear_tf=True,         # apply log to TF (standard practice)
        )
        self.centroids: np.ndarray = None  # shape (n_buckets, n_features)
        self.labels: List[str] = []
        self._fitted = False

    def fit(self) -> "TfidfClassifier":
        """Train the vectorizer and compute bucket centroids."""
        all_docs = []
        doc_labels = []
        for label, docs in TRAINING_CORPUS.items():
            all_docs.extend(docs)
            doc_labels.extend([label] * len(docs))

        # Fit and transform the full corpus
        tfidf_matrix = self.vectorizer.fit_transform(all_docs)

        # Compute centroid for each bucket (mean of its document vectors)
        self.labels = LABELS
        centroids = []
        for label in self.labels:
            indices = [i for i, l in enumerate(doc_labels) if l == label]
            centroid = tfidf_matrix[indices].mean(axis=0)
            centroids.append(np.asarray(centroid).flatten())

        self.centroids = np.array(centroids)
        self._fitted = True
        return self

    def predict(self, text: str) -> Tuple[str, float, Dict[str, float]]:
        """
        Classify a single text.

        Returns:
            (best_label, confidence, all_scores)
            - best_label: predicted persona bucket
            - confidence: cosine similarity to best bucket (0–1)
            - all_scores: dict of {bucket: similarity} for all buckets
        """
        if not self._fitted:
            self.fit()

        vec = self.vectorizer.transform([text.lower()])
        similarities = cosine_similarity(vec, self.centroids).flatten()

        all_scores = {
            label: round(float(sim), 4)
            for label, sim in zip(self.labels, similarities)
        }

        best_idx = int(np.argmax(similarities))
        best_score = float(similarities[best_idx])

        if best_score < self.min_confidence:
            return "other", best_score, all_scores

        return self.labels[best_idx], best_score, all_scores

    def predict_batch(
        self, texts: List[str]
    ) -> List[Tuple[str, float, Dict[str, float]]]:
        """Classify multiple texts efficiently."""
        if not self._fitted:
            self.fit()

        vecs = self.vectorizer.transform([t.lower() for t in texts])
        sim_matrix = cosine_similarity(vecs, self.centroids)  # (n_texts, n_buckets)

        results = []
        for similarities in sim_matrix:
            all_scores = {
                label: round(float(sim), 4)
                for label, sim in zip(self.labels, similarities)
            }
            best_idx = int(np.argmax(similarities))
            best_score = float(similarities[best_idx])
            if best_score < self.min_confidence:
                results.append(("other", best_score, all_scores))
            else:
                results.append((self.labels[best_idx], best_score, all_scores))
        return results

    def get_top_features(self, n: int = 10) -> Dict[str, List[str]]:
        """Return top-n TF-IDF features per bucket centroid — useful for explainability."""
        if not self._fitted:
            self.fit()

        feature_names = self.vectorizer.get_feature_names_out()
        result = {}
        for i, label in enumerate(self.labels):
            top_indices = self.centroids[i].argsort()[-n:][::-1]
            result[label] = [feature_names[j] for j in top_indices]
        return result


# Module-level singleton — trained once on import
tfidf_model = TfidfClassifier().fit()
