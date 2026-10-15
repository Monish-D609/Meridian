# Meridian — Complete CLI Execution & Component Activation Guide

This document lists all command-line prompts and procedures required to set up, initialize, activate, and run every component of the **Meridian LLM Evaluation & Benchmarking Platform** (Backend API, Frontend Web UI, SQLite/PostgreSQL Database, Evaluation Engine, and Automated Test Suites).

---

## ⚡ Option 1: Quick Start (One-Click Launchers)

If you already have your environment configured, use the provided root launcher scripts to start both the Backend and Frontend concurrently in separate terminal windows and open your browser automatically.

### Windows PowerShell
```powershell
# From the project root
.\run.ps1
```

### Windows Command Prompt (CMD) / Double-Click
```cmd
:: From the project root or double-click in Windows Explorer
run.bat
```

### Stopping All Services
```powershell
# Stop services running on ports 8000 (Backend) and 5173 (Frontend)
.\stop.bat
```

---

## 🛠️ Option 2: Step-by-Step Manual Component Activation

Follow these steps to activate each component individually in dedicated terminal windows.

---

### Step 1: Environment & Dependency Setup

#### 1.1 Backend Python Environment
Open a terminal in the project root:

```powershell
# 1. Navigate to backend directory
cd backend

# 2. (Optional but recommended) Create and activate a virtual environment
python -m venv venv
.\venv\Scripts\activate

# 3. Install backend dependencies
pip install -r requirements.txt
# Or if using editable pyproject.toml:
pip install -e .
```

#### 1.2 Frontend Node Environment
Open a new terminal in the project root:

```powershell
# 1. Navigate to frontend directory
cd frontend

# 2. Install frontend dependencies (using npm or pnpm)
npm install
# or: pnpm install
```

---

### Step 2: Database Initialization & Seeding

Meridian uses an asynchronous SQLite database by default (`backend/meridian.db`), with PostgreSQL support via Neon for production deployments.

#### 2.1 Verify or Create Environment File (`backend/.env`)
Ensure `backend/.env` exists with your database URL and active LLM API credentials:

```env
# Database
DATABASE_URL=sqlite+aiosqlite:///./meridian.db
DATABASE_URL_SYNC=sqlite:///./meridian.db

# LLM Providers (Cloudflare, Groq, Google Gemini, OpenRouter)
CLOUDFLARE_ACCOUNT_ID=your_cloudflare_account_id
CLOUDFLARE_API_TOKEN=your_cloudflare_api_token
GROQ_API_KEY=your_groq_api_key
GEMINI_API_KEY=your_gemini_api_key
OPENROUTER_API_KEY=your_openrouter_api_key

# LLM-as-a-Judge Configuration
JUDGE_PROVIDER=cloudflare
JUDGE_MODEL=@cf/meta/llama-3.1-8b-instruct
JUDGE_MODEL_VERSION=llama-3.1-8b-instruct-cf
```

#### 2.2 Seed Categories, Datasets, Tasks, and Providers
Run the database seed script to populate canonical capability benchmarks and active model definitions:

```powershell
# From the backend directory:
cd backend
python -m app.db.seed
```

This creates and populates:
- **7 Capability Categories**: Coding, Mathematics, Reasoning, Creative Writing, Summarization, Factual QA, Long-Context.
- **8 Benchmark Datasets**: 70+ evaluation tasks with reference answers, system prompts, and ground truth contexts.
- **4 Verified Providers & Models**: Cloudflare Workers AI, Groq, Google AI Studio, and OpenRouter Free.
- **Historical Baselines**: GPT-4o, Claude 3.5 Sonnet, and Gemini 1.5 Pro benchmark snapshots.

---

### Step 3: Activate the Backend API Server

Start the FastAPI application via `uvicorn`:

```powershell
# From the backend directory:
cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

#### Verification & Health Checks
Open another terminal to verify the backend is running:

```powershell
# Check health endpoint
curl http://127.0.0.1:8000/api/v1/health

# List active providers
curl http://127.0.0.1:8000/api/v1/providers

# List active models
curl http://127.0.0.1:8000/api/v1/models
```

- **Interactive API Documentation (Swagger UI)**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc Documentation**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

### Step 4: Activate the Frontend Web Dashboard

Start the React + Vite development server:

```powershell
# From the frontend directory:
cd frontend
npm run dev
```

- **Frontend Application URL**: [http://localhost:5173/](http://localhost:5173/)

#### Production Build Verification
To compile and test the production frontend build:

```powershell
cd frontend
npm run build
npm run preview
```

---

### Step 5: Running Evaluation & Benchmark Tests

#### Method A: Via Web UI (Interactive)
1. Open [http://localhost:5173/](http://localhost:5173/) in your browser.
2. Under **Model Selection**, select target models (e.g., *Llama 3.1 8B Instruct (Cloudflare)*, *Qwen 3.8 27B (Groq)*, or *Gemini 1.5 Flash*).
3. Under **Benchmark Suites**, check the desired capability categories (Coding, Math, Reasoning, etc.).
4. Click **Run Benchmark**.
5. Watch the real-time execution matrix as tasks execute and stream scores (Quality, Groundedness, Latency, Cost).
6. View multi-model comparison charts, radar diagrams, and claim-level audit verifications on the **Results** and **Responses** pages.

#### Method B: Via CLI (cURL / REST API)
You can initiate and monitor evaluation runs directly from the command line:

```powershell
# 1. Create and trigger a new benchmark run
$response = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/runs" -Method Post -ContentType "application/json" -Body (@{
    name = "CLI Benchmark Evaluation"
    model_ids = @("d1361f0d4b774902b9bec7557da89fef", "9649ad2fed004ced9b50f7eae4f5a140")
    dataset_ids = @("c2392baa-19e5-4e33-9bc2-9ceff04f2caf", "cbf0d15e-2d7b-4a04-a94c-595e08454f01")
    max_tokens = 512
    temperature = 0.0
} | ConvertTo-Json)

$runId = $response.id
Write-Host "Benchmark Run Started with ID: $runId"

# 2. Poll progress
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/runs/$runId/progress"

# 3. Retrieve final comparison analytics and tier classification
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/runs/$runId/comparison"
```

---

### Step 6: Running Automated Test Suites

Meridian includes a comprehensive `pytest` test suite covering LLM adapters, comparison normalizers, scoring heuristics, and token F1 calculations.

```powershell
# From the backend directory:
cd backend

# Run the entire test suite
pytest -v

# Run adapter tests only
pytest tests/adapters/ -v

# Run comparison engine and tier classification tests
pytest tests/comparison/ -v

# Run evaluation quality and hallucination scorer tests
pytest tests/evaluation/ -v
```

---

### Step 7: Port Management & Troubleshooting

If you encounter `EADDRINUSE` or `Address already in use` errors when restarting services:

```powershell
# Identify processes on port 8000 (Backend)
Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | Select-Object OwningProcess

# Identify processes on port 5173 (Frontend)
Get-NetTCPConnection -LocalPort 5173 -ErrorAction SilentlyContinue | Select-Object OwningProcess

# Terminate process by PID (replace <PID>)
Stop-Process -Id <PID> -Force

# Or run stop.bat from the root directory
.\stop.bat
```

---

## 📌 Summary of Core Endpoints & URLs

| Component | URL | Notes |
|---|---|---|
| **Web UI** | [http://localhost:5173/](http://localhost:5173/) | Interactive React dashboard |
| **Backend API** | [http://127.0.0.1:8000/](http://127.0.0.1:8000/) | FastAPI root endpoint |
| **API Documentation** | [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) | Interactive Swagger UI |
| **Health Check** | [http://127.0.0.1:8000/api/v1/health](http://127.0.0.1:8000/api/v1/health) | Service health check |
| **Active Providers** | [http://127.0.0.1:8000/api/v1/providers](http://127.0.0.1:8000/api/v1/providers) | List supported providers |
| **Active Models** | [http://127.0.0.1:8000/api/v1/models](http://127.0.0.1:8000/api/v1/models) | List supported models |
| **Benchmark Datasets** | [http://127.0.0.1:8000/api/v1/datasets](http://127.0.0.1:8000/api/v1/datasets) | List benchmark suites |
