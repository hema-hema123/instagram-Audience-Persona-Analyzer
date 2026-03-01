

# 📊 Instagram Audience Persona Analyzer (Compliant)

Analyze Instagram audience bios and comments to identify user personas and generate actionable insights.

This tool classifies audience text into personas such as:

- 🎓 Student  
- 💻 Tech  
- 🛐 Religious  
- 💪 Fitness  
- 💼 Job Seeker  
- 🎥 Creator  
- 🏢 Business  
- 🔎 Other  

⚠️ **No scraping.** Works only with official Instagram Graph API data or consent-based CSV uploads.

---

## 🚀 Features

✔ Persona classification from bios/comments  
✔ Aggregated audience insights & charts  
✔ CSV upload with consented data  
✔ FastAPI backend + interactive dashboard  
✔ Docker-ready deployment  
✔ Privacy & compliance focused  

---

## 🛠 Tech Stack

- **Backend:** Python, FastAPI  
- **Visualization:** Chart.js  
- **Data Processing:** NLP-based classification  
- **Deployment:** Docker  
- **API Docs:** Swagger UI  

---

## 📷 Demo Preview

Run locally and open:

👉 http://127.0.0.1:8000/ui

---

## ⚙️ Installation

### 1️⃣ Clone Repository

```bash
git clone https://github.com/hema-hema123/nstagram-Audience-Persona-Analyzer.git
cd nstagram-Audience-Persona-Analyzer


⸻

2️⃣ Create Virtual Environment

macOS / Linux

python3 -m venv .venv
source .venv/bin/activate

Windows (PowerShell)

python -m venv .venv
.venv\Scripts\activate


⸻

3️⃣ Install Dependencies

pip install -r requirements.txt


⸻

▶️ Run Demo (No Instagram Required)

python -m scripts.demo_classify

Creates:

data/report.json


⸻

▶️ Start API Server

uvicorn app.main:app --reload --port 8000


⸻

🌐 Open in Browser

API Documentation

👉 http://127.0.0.1:8000/docs

Web Dashboard

👉 http://127.0.0.1:8000/ui

⸻

📊 Using the Dashboard

Inside the UI:

✔ Click Load Demo Data to view sample charts
✔ OR upload a CSV file

⸻

📄 CSV Format

Upload CSV with columns:

id,bio
user1,B.Tech CSE | Learning DSA and ML
user2,Gym Trainer | Calisthenics
user3,Startup founder | Ecommerce


⸻

🧠 API Endpoints

Method	Endpoint	Description
GET	/health	Health check
POST	/classify	Classify text items
POST	/report	Classifies & aggregates

Swagger UI:

👉 http://127.0.0.1:8000/docs

⸻

🔧 Customize Personas

Edit keyword buckets:

app/classifier.py

Update categories inside:

BUCKETS = { ... }

Restart server to apply changes.

⸻

🤖 Optional: Zero-Shot AI Classification (Smarter)

pip install transformers torch
export USE_ZEROSHOT=true
export ZS_MODEL=facebook/bart-large-mnli
uvicorn app.main:app --reload


⸻

📷 Instagram Graph API Integration (Compliant)
	1.	Switch Instagram to Business/Creator
	2.	Create Facebook App → get credentials
	3.	Obtain long-lived Page token
	4.	Fetch insights & comments (where permitted)
	5.	Send consented text to /classify or /report

⚠️ Instagram does not provide follower bios via API.
Do not scrape.

⸻

🐳 Docker Deployment

docker build -t insta-audience .
docker run --rm -p 8000:8000 insta-audience

Open:

👉 http://127.0.0.1:8000/ui

⸻

🎯 Future Improvements
	•	Sentiment analysis
	•	Engagement scoring
	•	Real-time Instagram insights
	•	ML clustering for audience segments
	•	Cloud deployment dashboard

⸻

📜 License

MIT License

⸻

⭐ Support

If you find this project useful:

⭐ Star the repository
💡 Share feedback
🚀 Contribute improvements

⸻


---

## ✅ Next Steps

1️⃣ Open your repo  
2️⃣ Replace README.md content  
3️⃣ Commit & push  

```bash
git add README.md
git commit -m "updated professional readme"
git push


