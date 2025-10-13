ChainReport AI API is the **backend engine** that powers ChainReport AI App. It fetches, analyzes, and synthesizes data from multiple sources, generating comprehensive token research reports via AI. The API is designed to be **scalable, modular, and API-first**.

**Key Features:**

* Generate token research reports via AI agents.
* Aggregate data from on-chain metrics, social sentiment, audit reports, code quality, and whitepapers.
* Expose endpoints for report generation, token summaries, and analytics.
* Support multiple output formats: PDF, CSV, JSON.
* Secure, scalable, and ready for integration with frontend apps.

**Technology Stack:**

* **Backend Framework:** FastAPI (Python)
* **AI / NLP:** GPT-based agents for analysis and summarization
* **Database:** PostgreSQL / MongoDB
* **Task Queue:** Celery / Redis (for asynchronous report generation)
* **Deployment:** Docker / Kubernetes

**Repository Structure:**

```
/chainreport-ai-api
├── /app
│   ├── /routers        # API endpoints
│   ├── /services       # Data fetching and processing
│   ├── /models         # AI models and database schemas
│   └── main.py         # FastAPI app entrypoint
├── /scripts             # Data aggregation utilities
├── requirements.txt
├── Dockerfile
└── README.md
```

**Installation (Development):**

```bash
git clone https://github.com/Lumintel/chainreport-ai-api.git
cd chainreport-ai-api
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**API Endpoints (Examples):**

* **Generate Report:**

```
POST /generate-report
{
    "token_symbol": "ETH",
    "report_format": "pdf"
}
```

* **Get Token Summary:**

```
GET /token-summary?symbol=ETH
```

* **List Supported Tokens:**

```
GET /tokens
```

**Environment Variables (`.env`):**

```
DATABASE_URL=postgresql://user:password@localhost:5432/chainreport
REDIS_URL=redis://localhost:6379
AI_MODEL_PATH=./models/gpt-agent
SECRET_KEY=your_secret_key
```

**Contribution Guidelines:**

* Use feature branches for new endpoints or features.
* Follow PEP8 for Python code formatting.
* Write unit tests (PyTest) for new services and endpoints.
* Document new API endpoints in `/docs`.
