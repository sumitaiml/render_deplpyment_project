# 🚀 HRTech Platform - Backend

An AI-powered resume screening and candidate ranking system with explainable AI decisions.

## 🎯 Quick Start

### Prerequisites
- Python 3.9+
- PostgreSQL 12+
- Redis (optional, for caching)

### Installation

1. **Clone and navigate to backend directory**
```bash
cd hrtech-platform/backend
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Download NLP models**
```bash
python -m spacy download en_core_web_sm
```

5. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your database credentials
```

6. **Initialize database**
```bash
python -c "from app.core import DatabaseManager; DatabaseManager.create_all_tables()"
```

7. **Run the server**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API will be available at: **http://localhost:8000**
- Interactive Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## 📊 Backend Architecture

```
backend/
├── app/
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py              # Database & settings configuration
│   │
│   ├── models/
│   │   └── __init__.py            # SQLAlchemy ORM models
│   │
│   ├── schemas/
│   │   └── __init__.py            # Pydantic request/response schemas
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── resume_parser.py       # Resume parsing (PDF/DOCX/TXT)
│   │   ├── skill_engine.py        # Skill extraction & graph
│   │   ├── seniority_engine.py    # Seniority inference
│   │   ├── ranking_engine.py      # Candidate ranking model
│   │   └── explainability_engine.py # Explanation generation
│   │
│   ├── apis/
│   │   ├── __init__.py
│   │   ├── candidates.py          # Candidate endpoints
│   │   ├── jobs.py                # Job endpoints
│   │   └── ranking.py             # Ranking & explainability endpoints
│   │
│   ├── ml_models/                 # Trained ML models (optional)
│   │
│   └── main.py                    # FastAPI application
│
├── tests/
│   └── test_backend.py            # Comprehensive tests
│
├── data/
│   ├── skill_ontology/            # Skill graph data
│   └── embeddings/                # FAISS vector DB
│
├── requirements.txt               # Python dependencies
├── .env.example                   # Environment template
└── README.md                      # This file
```

---

## 🔌 API Endpoints

### Candidates

**POST /api/candidates/upload-resume**
- Upload and parse resume (PDF/DOCX/TXT)
- Returns: Parsed resume data with extracted skills and seniority

**GET /api/candidates/list**
- List all candidates (paginated)

**GET /api/candidates/{candidate_id}**
- Get detailed candidate information

### Jobs

**POST /api/jobs/create**
- Create new job posting with required/preferred skills

**GET /api/jobs/list**
- List all jobs (paginated)

**GET /api/jobs/{job_id}**
- Get detailed job information

### Ranking & Explainability

**POST /api/ranking/rank-candidates**
- Rank candidates against a job with ML model
- Returns: Ranked list with explainability data

**GET /api/ranking/rankings/{job_id}**
- Get all rankings for a job

**GET /api/ranking/ranking-details/{ranking_id}**
- Get detailed ranking with full explanation

---

## 🧠 Core Components

### 1. Resume Parser
**File:** `app/services/resume_parser.py`

**Capabilities:**
- Extract text from PDF, DOCX, TXT files
- Extract: Name, Email, Phone, Experience, Education, Projects
- Handle messy resume formats
- Calculate years of experience

**Key Methods:**
```python
parser = ResumeParser()
result = parser.parse_resume(file_content, file_format='pdf')
```

### 2. Skill Engine
**File:** `app/services/skill_engine.py`

**Capabilities:**
- Extract explicit skills (mentioned directly)
- Infer implicit skills (from descriptions)
- Normalize skill names using ontology
- Navigate skill graph for related skills
- Skill relationships: requires, implies, related_to

**Key Methods:**
```python
extractor = SkillExtractor()
skills = extractor.extract_all_skills(resume_data)

skill_graph = SkillGraph()
related = skill_graph.get_related_skills('Java', depth=2)
```

**Skill Graph Example:**
```
Spring Boot --> (requires) Java --> (implies) Backend Development
Java --> (implies) Microservices
Docker --> (related_to) Kubernetes
```

### 3. Seniority Inference Engine
**File:** `app/services/seniority_engine.py`

**Signals Used:**
- Years of experience (40% weight)
- Role progression (30% weight)
- Skill depth & diversity (30% weight)

**Seniority Levels:**
- Intern (< 1 year)
- Junior (1-2 years)
- Mid-Level (2-5 years)
- Senior (5-10 years)
- Lead (10+ years)

**Key Methods:**
```python
engine = SeniorityInference()
result = engine.infer_seniority(resume_data)
# Returns: predicted_seniority, confidence_score, reasoning
```

### 4. Ranking Model
**File:** `app/services/ranking_engine.py`

**Scoring Components:**
- **Skill Match (45%)**
  - Matches required & preferred skills
  - Penalizes missing critical skills
  - Range: 0-100

- **Experience Match (35%)**
  - Compares candidate years vs. required
  - Scores: 100 (exact match) → 40 (2+ years below)
  - Range: 0-100

- **Seniority Alignment (20%)**
  - Matches candidate seniority to job level
  - Accepts over-qualification
  - Penalizes under-qualification
  - Range: 0-100

**Final Score:** `0.45*skill + 0.35*exp + 0.20*seniority` (0-100)

**Key Methods:**
```python
ranker = RankingModel()
rankings = ranker.rank_candidates(candidates, job)
```

### 5. Explainability Engine
**File:** `app/services/explainability_engine.py`

**Generates:**
- Ranking reason (why candidate ranked #X)
- Matched skills breakdown
- Missing skills with impact
- Experience alignment analysis
- Seniority reasoning
- Overall summary with recommendation

**Example Output:**
```
"Alice ranked #2 due to strong backend skills, 5+ years experience, 
and partial match on cloud skills. She matches 8 of 10 required skills 
but lacks Kubernetes expertise (could be learned quickly)."
```

---

## 🧪 Testing

Run all tests:
```bash
pytest tests/test_backend.py -v
```

Test specific component:
```bash
pytest tests/test_backend.py::TestResumeParser -v
pytest tests/test_backend.py::TestRankingModel -v
pytest tests/test_backend.py::TestExplainabilityEngine -v
```

Run with coverage:
```bash
pytest tests/test_backend.py --cov=app --cov-report=html
```

**Test Coverage:**
- Resume parsing (9 tests)
- Skill extraction (4 tests)
- Seniority inference (6 tests)
- Ranking model (4 tests)
- Explainability (4 tests)
- End-to-end pipeline (1 test)

---

## 📋 Database Schema

### Key Models

**Candidates**
- `id`: UUID primary key
- `name`, `email`, `phone`
- `years_of_experience`: Calculated from experience entries
- `inferred_seniority`: ML-inferred level + confidence
- `parsed_experience`: JSON array of work history
- `parsed_education`: JSON array of education
- `parsed_projects`: JSON array of projects

**Skills**
- `id`, `name` (unique)
- `category`: Programming, Database, Cloud, etc.
- `parent_skills`, `child_skills`: Skill graph relationships
- `embedding`: SentenceTransformer embeddings

**CandidateSkills** (Join Table)
- `candidate_id`, `skill_id`
- `proficiency_level`: beginner, intermediate, advanced, expert
- `confidence_score`: 0-1 (how sure are we they have this skill)
- `is_explicit`: True if mentioned directly, False if inferred
- `mentioned_in`: skills_section, experience, projects, inferred

**Jobs**
- `id`, `title`, `description`
- `company`, `job_level`
- `years_of_experience_required`
- `parsed_description`, `required_skills_json`, `preferred_skills_json`

**JobSkills** (Join Table)
- `job_id`, `skill_id`
- `is_required`: True if must-have, False if nice-to-have
- `minimum_proficiency`: Required proficiency level
- `importance_score`: Weight in ranking (1.0 = 100%)

**CandidateRankings**
- `job_id`, `candidate_id`
- `overall_rank_score`, `skill_match_score`, `experience_match_score`, `seniority_alignment_score`
- `rank_position`, `percentile`
- `explanation`: JSON with full reasoning
- `bias_mitigated`: Whether bias mitigation was applied

---

## 🛡️ Bias Mitigation

**Masking Applied:**
- ✅ Candidate names
- ✅ Gender indicators
- ✅ Age proxies (graduation year)
- ✅ College prestige (optional)

**Ranking Based On:**
- ✅ Skills match
- ✅ Experience years
- ✅ Seniority alignment
- ✅ Role progression

**Fairness Metrics:**
- Demographic parity difference
- Equal opportunity difference
- Overall fairness score

---

## 🚀 Deployment

### Docker

```bash
docker build -t hrtech-backend .
docker run -p 8000:8000 -e DATABASE_URL=postgresql://... hrtech-backend
```

### Using Uvicorn (Production)

```bash
gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Environment Variables

See `.env.example` for all configuration options.

---

## 📊 Performance Notes

- **Resume Parsing:** ~2-5 seconds per PDF
- **Skill Extraction:** ~1-2 seconds (NLP processing)
- **Seniority Inference:** ~500ms (heuristic-based)
- **Ranking 100 candidates:** ~2-3 seconds
- **Explanation Generation:** ~500ms per candidate

---

## 🔍 Debugging

Enable verbose logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Check API documentation:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json

---

## 📚 Architecture Decisions

1. **NLP Library:** spaCy + Transformers for named entity recognition and semantic understanding
2. **Embeddings:** Sentence-BERT for semantic similarity
3. **Ranking:** Heuristic + ML-ready (XGBoost can be plugged in)
4. **Database:** PostgreSQL for structured data + FAISS for vector search
5. **API Framework:** FastAPI for speed, type safety, and auto-documentation

---

## 🔜 Next Steps

1. ✅ Backend complete with all core services
2. ⏭️ Frontend (React/Next.js) with recruiter dashboard
3. ⏭️ ML model training pipeline
4. ⏭️ Advanced bias metrics & fairness reports
5. ⏭️ Admin skill ontology management UI

---

## 📝 License

Proprietary - HRTech Platform

---

## 🤝 Support

For issues or questions, please refer to the main project README.
