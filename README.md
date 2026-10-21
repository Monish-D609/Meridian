# Meridian — LLM Evaluation & Benchmarking Platform

<div align="center">

![Meridian Banner](https://img.shields.io/badge/Meridian-LLM%20Benchmarking-6366f1?style=for-the-badge&logo=compass&logoColor=white)

**An enterprise-grade, reproducible LLM benchmarking and comparative positioning platform.**  
Multi-dimensional evaluation, 7-axis capability profiling, industry-relative percentile tiering, and publication-ready reporting — designed to run on a 100% free-tier stack.

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI%200.115-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/Frontend-React%2019%20+%20Vite-61DAFB?style=flat-square&logo=react&logoColor=black)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.x-3178C6?style=flat-square&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![SQLAlchemy](https://img.shields.io/badge/ORM-SQLAlchemy%202.0%20(Async)-D71F00?style=flat-square&logo=sqlalchemy&logoColor=white)](https://www.sqlalchemy.org/)
[![Database](https://img.shields.io/badge/Database-SQLite%20%7C%20Neon%20Postgres-00E599?style=flat-square&logo=postgresql&logoColor=white)](https://neon.tech/)
[![Inference Cost](https://img.shields.io/badge/Inference-Zero--Cost%20Free%20Tier-success?style=flat-square&logo=cachet&logoColor=white)](#-supported-providers--free-tier-stack)

</div>

---

## 📖 Table of Contents

- [Overview & Vision](#-overview--vision)
- [The Problem Meridian Solves](#-the-problem-meridian-solves)
- [Key Features & Novelty](#-key-features--novelty)
- [System Architecture](#-system-architecture)
- [Evaluation Dimensions & Methodology](#-evaluation-dimensions--methodology)
- [Core Capability Axes](#-core-capability-axes)
- [Project Structure](#-project-structure)
- [⚡ Quick Start (Run on your own)](#-quick-start-run-on-your-own)
- [🛠️ Manual Developer Setup](#️-manual-developer-setup)
- [🛑 How to Stop the App](#-how-to-stop-the-app)
- [🔗 Platform Endpoints](#-platform-endpoints)
- [🔑 Environment Configuration & API Keys](#-environment-configuration--api-keys)
- [📊 Prebuilt Benchmark Suites & Custom Datasets](#-prebuilt-benchmark-suites--custom-datasets)
- [🚢 Cloud Deployment](#-cloud-deployment)
- [🧪 Testing & Verification](#-testing--verification)
- [❓ Frequently Asked Questions (FAQ) & Project Review Guide](#-frequently-asked-questions-faq--project-review-guide)
- [👥 Authors & Academic Context](#-authors--academic-context)

---

## 🌟 Overview & Vision

**Meridian** is a self-hostable, developer-centric evaluation and benchmarking platform for Large Language Models (LLMs). While traditional leaderboards (such as open arena rankings or single-score academic benchmarks) collapse model performance into a single aggregate number, Meridian answers the real-world engineering question:

> *"Where does this model actually stand compared to industry-standard frontier models across the specific capabilities my workload requires — and does it hallucinate under scrutiny?"*

Meridian delivers a comprehensive **positioning profile** rather than a solitary leaderboard ranking. Every evaluated model is classified into actionable tiers (**Frontier**, **Strong**, **Mid**, or **Weak**) across **7 distinct capability dimensions**, with factual reliability and hallucination tracked as an independent primary axis.

---

## 🎯 The Problem Meridian Solves

| Common Leaderboard Flaws | The Meridian Solution |
| :--- | :--- |
| **Single-Score Flattening**: Averages coding, math, and creative writing into a single metric, hiding critical task-specific weaknesses. | **7-Axis Capability Profiling**: Deconstructs model performance across 7 distinct axes visualized via interactive radar charts. |
| **Hallucination Blindspot**: Factual accuracy and hallucinations are bundled into general score rubrics or ignored. | **First-Class Hallucination Tracking**: Claim-level extraction and groundedness scoring isolate hallucinations independently from stylistic fluency. |
| **Expensive Infrastructure**: Many evaluation harnesses demand high-end GPUs or costly enterprise API credits. | **Zero-Cost Inference Architecture**: Built natively around generous free-tier providers (Cloudflare Workers AI, Groq LPU, Google AI Studio, OpenRouter free models). |
| **Opaque Scoring**: Raw percentages fail to communicate whether 74% is stellar or mediocre on a particular test set. | **Industry Baseline Percentile Ranking**: Automatically normalizes scores against a versioned registry of frontier and standard reference baselines. |

---

## ✨ Key Features & Novelty

### 1. 🏅 Industry-Relative Positioning & Tiering Engine
- Normalizes raw evaluation scores against a maintained registry of industry baselines (GPT-4o, Claude 3.5 Sonnet, Gemini 1.5 Pro, Llama 3 70B, etc.).
- Categorizes performance into intuitive tiers based on statistical distribution ($z$-score and percentile rankings):
  - 👑 **Frontier Tier** ($\ge 85\text{th}$ percentile): Matches or challenges state-of-the-art frontier models.
  - 🚀 **Strong Tier** ($65\text{th} - 84\text{th}$ percentile): Highly capable for production deployment.
  - ⚖️ **Mid Tier** ($40\text{th} - 64\text{th}$ percentile): Solid on common tasks; requires guardrails for complex logic.
  - ⚠️ **Weak Tier** ($< 40\text{th}$ percentile): Significant deficiencies; not recommended for autonomous tasks.

### 2. 🛡️ Dual-Stage Hallucination & Groundedness Scorer
- **Atomic Claim Extraction**: Uses NLP / linguistic parsing (`spaCy`) to split outputs into discrete factual assertions.
- **Verification & Consistency Check**: Cross-verifies claims against ground-truth context and reference answers.
- **Reliability Metrics**: Generates a claim-level hallucination rate, response-level hallucination score, and groundedness ratio (0.0 to 1.0).

### 3. 📐 Multi-Dimensional Evaluation Engine
- **Quality**: Accuracy, semantic relevance (via sentence-transformer embeddings), completeness, and instruction-following (deterministic heuristics + LLM-as-a-Judge rubrics).
- **Efficiency**: Latency (ms), Time to First Token (TTFT), and throughput (tokens per second).
- **Economics**: Real-time token usage accounting and dollar cost estimation ($/run and $/1M tokens).

### 4. 📊 Interactive Visual Analytics & Radar Charts
- Web-based interactive dashboard built with React 19, TypeScript, and SVG/Recharts.
- Side-by-side multi-model comparison overlays.
- Capability radar charts, latency-vs-quality trade-off scatter views, and granular response drill-down tables.

### 5. 📄 Publication-Ready Reports
- One-click export to **high-fidelity PDF reports** (powered by ReportLab) containing executive summaries, capability radars, metric tables, and sample failure analysis.
- Raw run export to **CSV** for secondary academic or data science workflows.

### 6. 📁 Custom Benchmark Ingest
- Ships with 50+ pre-seeded benchmark tasks across 5 core datasets.
- Flexible **Custom Dataset Uploader** supporting CSV and JSON datasets with instant client-side and server-side schema validation.

---

## 🏗️ System Architecture

Meridian is built with a clean separation of concerns, ensuring modularity, security, and reproducibility:

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           MERIDIAN PLATFORM ARCHITECTURE                        │
└─────────────────────────────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────────────────────┐
  │                         Frontend (Vite + React 19)                          │
  │   - New Run Lab            - Live Progress Polling   - Capability Radar     │
  │   - Results & Comparisons  - Response Drill-Down     - PDF / CSV Export     │
  └──────────────────────────────────────┬──────────────────────────────────────┘
                                         │ REST API & WebSockets
                                         ▼
  ┌─────────────────────────────────────────────────────────────────────────────┐
  │                         Backend (FastAPI + Pydantic v2)                     │
  │                                                                             │
  │   ┌─────────────────────────────────────────────────────────────────────┐   │
  │   │                         Benchmark Manager                           │   │
  │   │  Orchestrates concurrent model queries, rate limiting, and runs.    │   │
  │   └───────────────┬─────────────────────────────────────┬───────────────┘   │
  │                   │                                     │                   │
  │                   ▼                                     ▼                   │
  │   ┌───────────────────────────────┐     ┌───────────────────────────────┐   │
  │   │      LLM Adapter Layer        │     │       Evaluation Engine       │   │
  │   │  • Cloudflare Workers AI      │     │  • Quality Scorer             │   │
  │   │  • Groq LPU                   │     │  • Hallucination / NLP Scorer │   │
  │   │  • Google Gemini Studio       │     │  • Efficiency Scorer          │   │
  │   │  • OpenRouter (Free Tier)     │     │  • Cost & Economics Scorer    │   │
  │   └───────────────┬───────────────┘     └───────────────┬───────────────┘   │
  │                   │                                     │                   │
  │                   └──────────────────┬──────────────────┘                   │
  │                                      ▼                                      │
  │   ┌─────────────────────────────────────────────────────────────────────┐   │
  │   │                   Industry Comparison Engine                        │   │
  │   │  • Normalizer (z-score & percentile mapping against Baselines)      │   │
  │   │  • Tier Classifier (Frontier / Strong / Mid / Weak)                 │   │
  │   │  • Capability Profile Aggregator (7 Core Axes)                      │   │
  │   │  • Narrative Summary Generator (Executive Insights)                 │   │
  │   └──────────────────────────────────┬──────────────────────────────────┘   │
  │                                      ▼                                      │
  │   ┌─────────────────────────────────────────────────────────────────────┐   │
  │   │                   Persistence & Export Engine                       │   │
  │   │  • SQLAlchemy 2.0 Async (SQLite / Neon PostgreSQL)                  │   │
  │   │  • ReportLab Publication-Quality PDF Exporter & CSV Streaming       │   │
  │   └─────────────────────────────────────────────────────────────────────┘   │
  └─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔬 Evaluation Dimensions & Methodology

Meridian measures models across five synchronized evaluation layers:

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│     Quality     │     │  Reliability &  │     │   Capability    │
│   Evaluation    │     │  Hallucination  │     │    Profiling    │
│                 │     │                 │     │                 │
│ • Accuracy      │     │ • Claim extract │     │ • 7 core axes   │
│ • Relevance     │     │ • Groundedness  │     │ • Normalization │
│ • Completeness  │     │ • Contradiction │     │ • Percentile    │
│ • Instructions  │     │ • Hallucination │     │ • Tier ranking  │
└────────┬────────┘     └────────┬────────┘     └────────┬────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                 ┌───────────────┴───────────────┐
                 │                               │
                 ▼                               ▼
      ┌─────────────────────┐         ┌─────────────────────┐
      │     Efficiency      │         │     Cost Tracking   │
      │                     │         │                     │
      │ • Total Latency     │         │ • Token accounting  │
      │ • Time to 1st Token │         │ • $/Run calculation │
      │ • Tokens / Second   │         │ • $/1M token rate   │
      └─────────────────────┘         └─────────────────────┘
```

1. **Quality**: Deterministic string/regex matching combined with sentence embedding cosine similarity (`sentence-transformers`) and structured LLM-as-a-Judge rubrics (evaluating on a 1–5 scale with rationale).
2. **Hallucination & Reliability**: Dissects candidate responses into atomic assertions using sentence dependency parsing (`spaCy`), verifying claims against provided reference documents and facts.
3. **Capability Profiling**: Groups task performance into canonical domains and normalizes them against maintained baseline distributions.
4. **Efficiency**: High-resolution wall-clock timers record latency, TTFT, and generation throughput.
5. **Cost**: Tracks exact prompt and completion token counts multiplied by provider rate cards.

---

## 🧭 Core Capability Axes

Meridian benchmarks across 7 fundamental dimensions:

| Capability Axis | Focus Areas | Evaluation Method |
| :--- | :--- | :--- |
| **1. Coding** | Code generation, debugging, algorithmic syntax, syntax correctness. | Unit test execution & AST/fuzzy matching |
| **2. Mathematics** | Arithmetic, algebra, multi-step problem solving, proof steps. | Exact numeric extraction & symbolic equivalence |
| **3. Reasoning** | Multi-hop deduction, logical puzzles, syllogisms, common sense. | Step-by-step validity & outcome checks |
| **4. Creative Writing** | Narrative generation, style transfer, tone fidelity, voice constraints. | LLM-as-a-Judge criteria rubric |
| **5. Summarization** | Information density, salient point retention, brevity. | ROUGE-1/2/L, BERTScore & completeness |
| **6. Factual QA** | Factual precision, refusal calibration, hallucination avoidance. | Atomic claim extraction & groundedness score |
| **7. Long-Context** | Needle-in-a-haystack, cross-document reasoning over long prompts. | Retrieval accuracy & retention metrics |

---

## 📂 Project Structure

```
Meridian/
├── backend/                       # FastAPI Backend
│   ├── app/
│   │   ├── adapters/              # Provider adapters (Cloudflare, Groq, Gemini, OpenRouter)
│   │   ├── api/                   # REST API routes (runs, results, datasets, baselines, etc.)
│   │   ├── comparison/            # Industry Comparison Engine (tiering, normalization, radar)
│   │   ├── core/                  # Configuration & settings (Pydantic Settings)
│   │   ├── db/                    # Database session, models, and seed data
│   │   ├── evaluation/            # Quality, hallucination, efficiency, and cost scorers
│   │   ├── manager/               # Benchmark execution manager
│   │   ├── models/                # SQLAlchemy ORM schemas
│   │   ├── reporting/             # ReportLab PDF & CSV report generators
│   │   └── main.py                # FastAPI application entry point
│   ├── tests/                     # Comprehensive pytest test suite
│   ├── requirements.txt           # Python backend dependencies
│   └── .env.example               # Template environment configuration
│
├── frontend/                      # React 19 + TypeScript Frontend
│   ├── src/
│   │   ├── api/                   # Axios API client functions
│   │   ├── components/            # Reusable UI widgets (RadarChart, Sidebar, etc.)
│   │   ├── pages/                 # NewRunPage, ResultsPage, ResponsesPage, HistoryPage, Settings
│   │   ├── types/                 # TypeScript interfaces and domain schemas
│   │   ├── App.tsx                # App routing and layout
│   │   └── main.tsx               # Frontend entry point
│   ├── package.json               # Frontend dependencies & scripts
│   └── vite.config.ts             # Vite configuration
│
├── DEPLOYMENT.md                  # Cloud deployment guide (Railway + Neon Postgres)
├── PRD.md                         # Product Requirements Document
├── SRS.md                         # Software Requirements Specification (IEEE 830)
├── run.bat                        # 1-Click Windows Batch launcher
├── run.ps1                        # 1-Click PowerShell launcher
├── stop.bat                       # 1-Click Windows process terminator
├── stop.ps1                       # 1-Click PowerShell process terminator
└── README.md                      # Project documentation
```

---

## ⚡ Quick Start (Run on your own)

### Option 1: Double-Click (Windows File Explorer)
Just double-click **`run.bat`** in the project root folder.  
It will automatically:
1. Start the FastAPI backend server on `http://127.0.0.1:8000`
2. Start the Vite React frontend on `http://localhost:5173`
3. Launch your default web browser directly to `http://localhost:5173/`

### Option 2: PowerShell
```powershell
.\run.ps1
```

### Option 3: Command Prompt (cmd.exe)
```cmd
run.bat
```

---

## 🛠️ Manual Developer Setup

If you prefer to run services manually or on Linux/macOS:

### 1. Prerequisites
- **Python**: Version 3.10, 3.11, or 3.12 installed
- **Node.js**: Version 18+ or 20+ (with `npm` or `pnpm`)
- **Git**

### 2. Backend Setup
```bash
# Navigate to backend directory
cd backend

# Create and activate virtual environment
python -m venv venv

# Windows:
.\venv\Scripts\activate
# Linux / macOS:
# source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Download spaCy English model for hallucination claim extraction
python -m spacy download en_core_web_sm

# Configure environment variables
copy .env.example .env     # On Windows (or cp on Linux/macOS)

# Seed database with canonical benchmarks, baselines, and categories
python -m app.db.seed

# Start backend server
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 3. Frontend Setup
```bash
# In a separate terminal, navigate to frontend directory
cd frontend

# Install dependencies
npm install
# or: pnpm install

# Start Vite development server
npm run dev
# or: pnpm dev
```

Visit **`http://localhost:5173/`** in your browser.

---

## 🛑 How to Stop the App

- **GUI / Terminal**: Close the two terminal windows that opened (one for Backend, one for Frontend).
- **Automated Script**: Double-click **`stop.bat`** (or run `.\stop.ps1` in PowerShell), which immediately terminates the processes listening on ports `8000` and `5173`.

---

## 🔗 Platform Endpoints

| Service | URL | Description |
| :--- | :--- | :--- |
| **Frontend Web App** | [http://localhost:5173/](http://localhost:5173/) | Interactive benchmarking lab, radar charts & results dashboard |
| **Backend API** | [http://127.0.0.1:8000/](http://127.0.0.1:8000/) | FastAPI asynchronous REST & WebSocket service |
| **Swagger API Docs** | [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) | Interactive OpenAPI / Swagger UI for endpoint testing |
| **ReDoc API Docs** | [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc) | Clean alternate API documentation |

---

## 🔑 Environment Configuration & API Keys

Meridian stores provider credentials securely. You can configure API keys via the **Settings** page in the web app or directly in `backend/.env`.

```env
# =============================================================================
# Database Configuration
# Defaults to SQLite (meridian.db) locally. Set Postgres URL for production/Neon.
# =============================================================================
DATABASE_URL=sqlite+aiosqlite:///../meridian.db

# =============================================================================
# Free-Tier LLM Providers (Add any or all)
# =============================================================================

# 1. Cloudflare Workers AI (Zero-Cost inference)
# Sign up: https://dash.cloudflare.com/ -> Workers AI
CLOUDFLARE_ACCOUNT_ID=your_cloudflare_account_id
CLOUDFLARE_API_TOKEN=your_cloudflare_api_token

# 2. Groq (Ultra-fast LPU inference)
# Free key: https://console.groq.com/keys
GROQ_API_KEY=your_groq_api_key

# 3. Google AI Studio (Gemini 1.5 Flash & Pro — Judge & Target Models)
# Free key: https://aistudio.google.com/app/apikey
GEMINI_API_KEY=your_gemini_api_key

# 4. OpenRouter (Free tier models: :free)
# Free key: https://openrouter.ai/keys
OPENROUTER_API_KEY=your_openrouter_api_key

# =============================================================================
# LLM-as-a-Judge Configuration
# =============================================================================
JUDGE_PROVIDER=cloudflare
JUDGE_MODEL=@cf/meta/llama-3.1-8b-instruct
```

> **Note**: API keys are encrypted at rest and never transmitted back to the browser client. All external LLM inference requests occur server-side.

---

## 📊 Prebuilt Benchmark Suites & Custom Datasets

Meridian ships with canonical test suites covering all 7 core capability categories out-of-the-box:

1. **Coding Benchmark v1**: Python function implementations, bug fixes, algorithmic problem solving.
2. **Math Benchmark v1**: Word problems, algebraic manipulations, step-by-step arithmetic verification.
3. **Reasoning Benchmark v1**: Multi-hop logical deduction, syllogisms, and puzzle solving.
4. **Creative Writing Benchmark v1**: Structured narrative composition, style imitation, constraint satisfaction.
5. **Summarization Benchmark v1**: Multi-paragraph document reduction, salient fact extraction.
6. **Factual QA Benchmark v1**: High-precision factual verification with claim-level ground truth.
7. **Long-Context Benchmark v1**: Needle-in-a-haystack information retrieval and reasoning across long prompts.

### 📤 Uploading Custom Datasets
Click **`+ Upload Custom Dataset`** on the **New Run** page in the UI to upload your own benchmark tasks. Meridian supports:
- **CSV format**: Columns `prompt`, `category` (optional), `ground_truth` (optional), `task_type` (open/closed).
- **JSON format**: Array of task objects with automated schema validation.

---

## 🚢 Cloud Deployment

Meridian is architected to deploy seamlessly to cloud infrastructure with zero ongoing hosting costs:

- **Backend**: Deploy to **Railway** or **Render** using Docker or Python runtime.
- **Database**: Connect to **Neon Serverless PostgreSQL** via standard `postgresql+asyncpg://` URI.
- **Frontend**: Deploy to **Vercel**, **Netlify**, or **Railway Static Sites**.

For detailed step-by-step cloud deployment instructions and environment variables, refer to [`DEPLOYMENT.md`](file:///c:/Users/Monish%20D/Documents/Meridian/DEPLOYMENT.md).

---

## 🧪 Testing & Verification

The backend includes a comprehensive automated test suite covering adapters, scoring engines, tier classification, and API routes.

```bash
cd backend

# Run all automated tests
pytest

# Run tests with verbose output and coverage
pytest -v --tb=short
```

---

## ❓ Frequently Asked Questions (FAQ) & Project Review Guide

### Core System & Evaluation Architecture

#### 1. How is hallucination exactly detected in Meridian?
In Meridian, hallucination detection is treated as a **first-class, independent reliability dimension** rather than an accuracy footnote ([`hallucination_scorer.py`](file:///c:/Users/Monish%20D/Documents/Meridian/backend/app/evaluation/hallucination_scorer.py)). The methodology adapts the core concepts of RAGAS faithfulness into a multi-stage NLP and verification pipeline:

1. **Atomic Claim Extraction (`extract_claims`)**: The candidate response is passed to the LLM evaluator at `temperature=0.0`. The model decomposes the output into discrete, independently verifiable factual assertions while stripping out conversational hedges, filler phrases, and formatting boilerplate:
   ```json
   ["Claim 1: The Eiffel Tower was completed in 1889.", "Claim 2: It is located in Lyon, France."]
   ```
2. **Claim-Level Fact Verification (`verify_claim`)**: Each atomic proposition is cross-verified against the reference source document/context. The judge outputs a strict categorical verdict:
   - `supported`: The claim is directly substantiated by the reference context.
   - `contradicted`: The claim asserts a fact directly conflicting with the reference (a verified hallucination).
   - `insufficient_info`: The reference does not provide enough evidence to confirm or deny.
3. **Quantitative Metrics**:
   - $\text{Groundedness Score} = \frac{\text{Supported Claims Count}}{\text{Total Claims Count}}$
   - $\text{Hallucination Rate} = \frac{\text{Contradicted Claims Count}}{\text{Total Claims Count}}$
   - $\text{Faithfulness Score} = 1.0 - \text{Hallucination Rate}$
4. **Holistic Groundedness Fallback (`score_groundedness_holistic`)**: If the reference context exceeds 8,000 characters or no claims can be parsed, Meridian evaluates overall groundedness on a structured 0–10 rubric mapped to $[0, 1]$.
5. **Self-Consistency Scoring**: When repeated sampling ($T > 0$) is enabled, semantic cosine similarity across consecutive stochastic generations is calculated to measure factual consistency.

---

#### 2. If LLM-as-a-Judge is used, how do you select and validate the judge model?
Selecting an LLM Judge requires balancing reasoning capability, strict schema adherence, and objectivity ([`quality_scorer.py`](file:///c:/Users/Monish%20D/Documents/Meridian/backend/app/evaluation/quality_scorer.py) and [`config.py`](file:///c:/Users/Monish%20D/Documents/Meridian/backend/app/core/config.py)):

- **Candidate Isolation (Zero Self-Enhancement Bias)**: A model is **never** permitted to evaluate its own outputs in the same benchmark run. The judge is an isolated external model (default: `Meta Llama 3.1 8B Instruct` via Cloudflare Workers AI or `Gemini 1.5 Flash` via Google AI Studio).
- **Deterministic Sampling ($T = 0.0$)**: All evaluations run at zero temperature with fixed seed configurations to eliminate variance and produce deterministic scoring.
- **Calibrated Multi-Criteria Rubric**: Instead of general "vibe checks," the judge scores candidate answers across 4 distinct dimensions on a 0–10 scale:
  1. **Accuracy / Correctness**: Factual correctness against gold reference.
  2. **Relevance**: Direct alignment with the user's prompt.
  3. **Completeness**: Coverage of all necessary components or sub-questions.
  4. **Instruction Following**: Adherence to length, format, syntax, and negative constraints.
- **Reproducibility Contract**: Every evaluation record in `run_results` permanently binds `judge_provider`, `judge_model_id`, and `judge_model_version`, ensuring complete auditability.

---

#### 3. Where is the dataset actually stored?
- **Relational Storage Schema**: Datasets and their constituent tasks are persisted in relational tables via SQLAlchemy 2.0 Async ORM:
  - `datasets`: Stores dataset metadata (`id`, `name`, `slug`, `category_id`, `version`, `is_canonical`, etc.).
  - `tasks`: Stores individual prompts (`id`, `dataset_id`, `prompt`, `reference_answer`, `context`, `task_type` [open/closed], `expected_format`, `criteria_json`).
- **Database Engines**:
  - **Local Development**: Stored in a local SQLite file (`meridian.db` in the repository root) with WAL (Write-Ahead Logging) and `busy_timeout=60000` for high concurrency.
  - **Production Deployment**: Connects to **PostgreSQL** (e.g., Neon Serverless Postgres) via `DATABASE_URL`.
- **Dataset Provenance**:
  - *Canonical benchmarks*: 50+ pre-seeded benchmark tasks across 5 core categories seeded via [`seed.py`](file:///c:/Users/Monish%20D/Documents/Meridian/backend/app/db/seed.py).
  - *Custom datasets*: When uploaded via the web UI (`+ Upload Custom Dataset`), CSV or JSON files are validated against Pydantic schemas and written directly to the database.

---

#### 4. How and on what basis is the industry baseline calculated for the metrics?
- **Baseline Registry**: Meridian maintains a versioned registry of reference models (`baseline_models` and `baseline_scores`) representing industry standards (e.g., GPT-4o, Claude 3.5 Sonnet, Gemini 1.5 Pro, Llama 3 70B) across all 7 capability categories.
- **Distribution Modeling**: For each capability category $c$, Meridian models the baseline distribution across all reference models:
  $$\mu_c = \frac{1}{N}\sum_{i=1}^N s_{i,c}, \quad \sigma_c = \sqrt{\frac{1}{N}\sum_{i=1}^N (s_{i,c} - \mu_c)^2}$$
- **Decoupled Architecture**: The Normalizer ([`normalizer.py`](file:///c:/Users/Monish%20D/Documents/Meridian/backend/app/comparison/normalizer.py)) is isolated from the evaluation engine. This allows updating or refreshing industry baseline numbers without re-running or recalculating raw model evaluations.

---

#### 5. How are models ranked and how is the percentile calculated?
Meridian rejects single-aggregate leaderboard rankings in favor of per-category statistical positioning:
1. **$z$-Score Calculation**: Measures standard deviations above or below the baseline mean:
   $$z = \frac{\text{raw\_score} - \mu_c}{\sigma_c}$$
2. **Empirical Percentile Ranking**: Determines the fraction of industry baseline models that the evaluated model outperforms:
   $$\text{Percentile} = \frac{\sum_{i=1}^N \mathbf{1}(s_{\text{baseline}, i} < \text{raw\_score})}{N}$$
3. **Tier Classification**: Percentiles map directly to qualitative, actionable tiers:
   - 👑 **Frontier Tier** ($\ge 80\text{th}$ percentile): Matches or surpasses state-of-the-art frontier models.
   - 🚀 **Strong Tier** ($60\text{th} - 79\text{th}$ percentile): Highly reliable for enterprise production.
   - ⚖️ **Mid Tier** ($40\text{th} - 59\text{th}$ percentile): Capable for common use; requires guardrails on complex tasks.
   - ⚠️ **Weak Tier** ($< 40\text{th}$ percentile): Significant deficiencies; not recommended for autonomous workloads.

---

#### 6. How are metrics like semantics and completeness evaluated?
- **Semantics (Semantic Similarity)**:
  - Computed in [`quality_scorer.py`](file:///c:/Users/Monish%20D/Documents/Meridian/backend/app/evaluation/quality_scorer.py) using the **`all-MiniLM-L6-v2`** model from **`sentence-transformers`**.
  - Maps both the model's prediction and the gold reference answer into a 384-dimensional dense semantic embedding space:
    $$\text{Cosine Similarity} = \frac{\mathbf{u} \cdot \mathbf{v}}{\|\mathbf{u}\| \|\mathbf{v}\| + 10^{-10}}$$
  - Captures conceptual correctness even if phrasing, vocabulary, or length differs from the reference answer.
- **Completeness**:
  - **Closed Tasks**: Calculated via token-level recall (SQuAD-style):
    $$\text{Recall} = \frac{|\text{Tokens}_{\text{pred}} \cap \text{Tokens}_{\text{ref}}|}{|\text{Tokens}_{\text{ref}}|}$$
  - **Open-Ended Tasks**: Assessed by the LLM-as-a-Judge on a calibrated 0–10 rubric scale specifically examining whether all constraints, sub-questions, and facets of the prompt were satisfied.

---

### 🎓 Project Review & Viva Preparation Questions

#### 7. Why use 7-axis capability profiling instead of LMSYS Chatbot Arena's Elo rating?
**Answer**: LMSYS Chatbot Arena collapses all tasks into a single scalar Elo rating based on crowd-sourced pairwise preferences. While valuable for general vibe checks, a developer choosing an LLM needs to know: *"Is this model strong at Python code generation, even if its creative poetry is weak?"* Meridian's 7-axis radar profile reveals category-specific trade-offs that aggregate leaderboards obscure.

#### 8. How does Meridian mitigate common LLM-as-a-Judge biases?
**Answer**:
- **Position Bias**: Independent single-answer rubric scoring rather than pairwise comparison eliminates first/second order presentation bias.
- **Verbosity Bias**: The rubric explicitly separates *Completeness* from *Conciseness*, and strict deterministic metrics (exact match, token F1, ROUGE) anchor the evaluation.
- **Self-Enhancement Bias**: A model is strictly barred from serving as the judge for its own outputs.

#### 9. How is the zero-budget constraint achieved?
**Answer**: Meridian achieves $0 operating cost by utilizing generous free-tier inference APIs:
- **Cloudflare Workers AI**: Free daily neural network inference quota (Meta Llama 3.1 8B).
- **Groq Cloud**: High-speed LPU free tier for fast inference.
- **Google AI Studio**: Free Gemini 1.5 Flash tier without requiring a credit card.
- **OpenRouter**: Free access to community open models (`:free` models).
- **Local SQLite / Neon Free Postgres**: Zero hosting costs for database storage.

#### 10. What is the difference between closed-ended and open-ended task evaluation?
**Answer**:
- **Closed Tasks**: Have unambiguous ground truth (math answers, code test cases, factual dates). Scored deterministically using normalized string exact match, token F1, and sentence embedding similarity without requiring an LLM judge call.
- **Open Tasks**: Creative writing, complex multi-paragraph explanations, or summarization where no single exact string exists. Evaluated via structured LLM-as-a-Judge rubrics and ROUGE scores.

#### 11. How does Meridian ensure evaluation reproducibility?
**Answer**: Every benchmark run creates an immutable `benchmark_runs` database record storing the exact timestamp, task IDs, dataset version, provider model IDs, temperature settings, and judge model version. Running the same benchmark against deterministic closed tasks yields identical results.

#### 12. How are user API keys secured?
**Answer**: Provider API keys entered in the Settings dashboard are encrypted at rest using Fernet symmetric encryption (`cryptography` library) before being written to the database. API keys are never exposed in API responses or sent back to the frontend browser client.

---

## 👥 Authors & Academic Context

Meridian was designed and developed as an academic software engineering capstone project:

- **Monish D** — `24BDS1033`
- **Soaham S** — `24BDS1021`

**Course**: Software Engineering — Digital Assignment  
**Specification Documents**:
- Product Requirements Document: [`PRD.md`](file:///c:/Users/Monish%20D/Documents/Meridian/PRD.md)
- Software Requirements Specification: [`SRS.md`](file:///c:/Users/Monish%20D/Documents/Meridian/SRS.md)

---

<div align="center">
<sub>Built with precision for transparent, reliable, and multi-dimensional LLM evaluation.</sub>
</div>
