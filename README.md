# Meridian — LLM Evaluation & Benchmarking Platform

An enterprise-grade, reproducible LLM benchmarking platform with multi-dimensional evaluation, 7-axis capability profiling, industry baseline percentile ranking, and publication-ready PDF exports.

---

## ⚡ Quick Start (Run on your own)

### Option 1: Double-Click (Windows File Explorer)
Just double-click **`run.bat`** in the project root folder.
It will:
1. Start the FastAPI backend server on `http://127.0.0.1:8000`
2. Start the Vite React frontend on `http://localhost:5173`
3. Automatically launch your default web browser to `http://localhost:5173/`

### Option 2: PowerShell
```powershell
.\run.ps1
```

### Option 3: Command Prompt (cmd.exe)
```cmd
run.bat
```

---

## 🛑 How to Stop the App

- Simply close the two terminal windows that opened (one for Backend, one for Frontend).
- **OR** double-click **`stop.bat`** (or run `.\stop.ps1`), which immediately terminates processes on ports 8000 and 5173.

---

## 🔗 Platform Endpoints

| Service | URL | Description |
| :--- | :--- | :--- |
| **Frontend Web App** | [http://localhost:5173/](http://localhost:5173/) | Interactive benchmarking lab & results dashboard |
| **Backend API** | [http://127.0.0.1:8000/](http://127.0.0.1:8000/) | FastAPI async backend |
| **Swagger API Docs** | [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) | Interactive API exploration and testing |

---

## 🔑 Adding API Keys

You can add or update your provider credentials at any time in **Settings** inside the web app, or by adding them to `backend/.env`:

```env
# Priority #1: Cloudflare Workers AI (Zero-Cost inference)
CLOUDFLARE_ACCOUNT_ID=your_cloudflare_account_id
CLOUDFLARE_API_TOKEN=your_cloudflare_api_token

# Priority #2: Google AI Studio (Gemini 1.5 Flash Judge)
GEMINI_API_KEY=your_gemini_api_key

# Priority #3: xAI (Grok 2 / Grok 2 Mini)
GROK_API_KEY=your_xai_api_key

# Priority #4: Groq
GROQ_API_KEY=your_groq_api_key

# Priority #10: OpenRouter (Free tier models)
OPENROUTER_API_KEY=your_openrouter_api_key
```

---

## 📊 Prebuilt Benchmark Suites

Meridian ships with canonical benchmarks covering all 7 core capability categories:
1. **Coding**: `Meridian Coding Benchmark v1`
2. **Mathematics**: `Meridian Math Benchmark v1`
3. **Reasoning**: `Meridian Reasoning Benchmark v1`
4. **Creative Writing**: `Meridian Creative Writing Benchmark v1`
5. **Summarization**: `Meridian Summarization Benchmark v1`
6. **Factual QA**: `Meridian Factual QA Benchmark v1`
7. **Long-Context**: `Meridian Long-Context Benchmark v1`

You can also click **`+ Upload Custom Dataset`** on the **New Run** page to upload your own CSV or JSON benchmark datasets with live schema validation.
