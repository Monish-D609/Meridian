# Meridian — Reference Research Notes

> **For team use only. This folder is not part of the shipped application and is never imported from.**
> Last updated: 2026-09-07

---

## 1. Existing LLM Evaluation Frameworks — Detailed Survey

### 1.1 EleutherAI `lm-evaluation-harness`
- **What it does:** CLI-based framework for evaluating LLMs on 200+ academic benchmarks (MMLU, GSM8K, HellaSwag, TruthfulQA, ARC, etc.). Backend for Hugging Face Open LLM Leaderboard.
- **Evaluation methodology:** Standardized prompts, fixed few-shot settings, multiple-choice logprob scoring for closed-form tasks; generative scoring for open-ended tasks.
- **Per-capability tiering vs industry baselines?** No. Produces raw scores per benchmark. No normalization against a "baseline model" distribution, no tier labels, no positioning summary.
- **Hallucination as first-class metric?** No. TruthfulQA is one benchmark in a list; not a claim-level groundedness axis applied across all tasks.
- **License:** MIT
- **Repo:** https://github.com/EleutherAI/lm-evaluation-harness
- **Ideas we borrow (concept, not code):** Task YAML structure — a task defines: prompt template, reference answer, scoring method, few-shot count. We adopt this pattern in our Task and Dataset entities.
- **Clone note:** Not cloned; docs and task YAML patterns reviewed online.

### 1.2 OpenAI Evals
- **What it does:** Open-source framework for building custom LLM test suites. JSONL-based test cases + model-graded evaluations. Originally had a hosted platform (deprecated late 2026).
- **Evaluation methodology:** Custom per-application. Supports exact-match, LLM-judge, fuzzy-match.
- **Per-capability tiering vs industry baselines?** No. Purely application-specific; no baseline registry.
- **Hallucination as first-class metric?** No. Accuracy is the primary lens.
- **License:** MIT
- **Ideas we borrow (concept, not code):** LLM-as-a-Judge pattern for open-ended scoring, with the judge identity stored as metadata per scored item. We adopt this in EvaluationScore.scorer_version and BenchmarkRun.judge_model_id.
- **Clone note:** Not cloned; patterns reviewed online.

### 1.3 Stanford HELM (Holistic Evaluation of Language Models)
- **What it does:** Multi-dimensional evaluation across 7 axes: accuracy, calibration, robustness, fairness, bias, toxicity, efficiency. Operates on scenarios x metrics grids.
- **Evaluation methodology:** Standardized, reproducible scenarios with a large set of metrics per scenario; heavy compute budget.
- **Per-capability tiering vs industry baselines?** Partial. HELM Capabilities leaderboard segments by competency area but produces raw rankings, not normalized per-capability tier labels.
- **Hallucination as first-class metric?** Folded into calibration/accuracy metrics.
- **License:** Apache 2.0
- **Ideas we borrow (concept, not code):** The "scenarios x metrics" grid concept informs our Task x Model x Metric run-result matrix. Also validates tracking efficiency (latency/cost) alongside quality.
- **Clone note:** Not cloned (compute-heavy; not suitable for free-tier inference).

### 1.4 LMSYS Chatbot Arena
- **What it does:** Crowdsourced human-preference pairwise battles. Bradley-Terry Elo for ranking.
- **Evaluation methodology:** Blind A/B voting by anonymous humans.
- **Per-capability tiering vs industry baselines?** Category filters exist (coding, math, creative writing) but based on human preference votes, not ground-truth accuracy or z-score normalization against a fixed baseline.
- **Hallucination as first-class metric?** Not tracked separately.
- **License:** CC-BY for data; proprietary platform.
- **Ideas we borrow:** Nothing directly. Confirms category-level filtering demand exists.

### 1.5 DeepEval
- **What it does:** pytest-native LLM quality unit tests. CI/CD quality gates. Dedicated hallucination, faithfulness, relevancy metrics.
- **Evaluation methodology:** LLM-judge-based metrics. Per-test pass/fail against thresholds.
- **Per-capability tiering vs industry baselines?** No baseline registry; no tier labels; no positioning summaries.
- **Hallucination as first-class metric?** Yes — response-level hallucination metric that checks generated text against context/source. Not claim-level extraction + verification.
- **License:** Apache 2.0
- **Ideas we borrow (concept, not code):** The pattern of a dedicated hallucination metric separate from accuracy, and threshold-based pass/fail. We extend to claim-level (extract claims from response -> verify each claim against reference).

### 1.6 promptfoo
- **What it does:** Prompt engineering A/B testing, multi-model comparison, red-teaming.
- **Evaluation methodology:** YAML-configured, language-agnostic. 40+ adversarial plugins for red-teaming.
- **Per-capability tiering vs industry baselines?** No.
- **Hallucination as first-class metric?** Red-team style (adversarial probing), not groundedness measurement.
- **License:** MIT
- **Ideas we borrow:** Nothing directly.

### 1.7 RAGAS
- **What it does:** RAG pipeline evaluation — faithfulness, context precision/recall, answer relevancy, groundedness.
- **Evaluation methodology:** LLM-based metrics for retrieval-augmented generation. Claim-level faithfulness: extracts statements from generated answer, verifies each against retrieved context.
- **Per-capability tiering vs industry baselines?** No. Scoped to RAG pipelines only.
- **Hallucination as first-class metric?** YES — closest to our approach. RAGAS faithfulness score decomposes the answer into atomic claims and checks groundedness per-claim.
- **License:** Apache 2.0
- **Ideas we borrow (concept, not code):** The atomic-claim decomposition approach for hallucination detection is the right pattern. We adapt this concept for general (non-RAG) responses: extract factual claims from any response, verify against the task's reference/context. Attribution: RAGAS (https://github.com/explodinggradients/ragas).

### 1.8 TruLens
- **What it does:** Observability/tracing platform for RAG and LLM chains. Feedback functions for groundedness/relevancy.
- **License:** MIT
- **Ideas we borrow:** Nothing directly.

### 1.9 Langfuse / Helicone
- **What they do:** Production observability — cost tracking, latency monitoring, prompt management.
- **License:** MIT (Langfuse self-hosted), proprietary SaaS.
- **Ideas we borrow:** Cost-per-token tracking pattern informs our cost_scorer.py pricing table design.

---

## 2. Commercial LLM Evaluation Startups

| Product | Free tier? | Per-category baseline tiering? | Claim-level hallucination? |
|---|---|---|---|
| Scale AI Evals | No | No | No |
| Patronus AI | Trial only | No | Some claim-level |
| Confident AI (DeepEval hosted) | Freemium with limits | No | Response-level |
| Vellum AI | Limited free | No | Response-level |
| LangSmith | Free tier (100k traces) | No | Trace-based |
| Arthur AI | No | No | Yes |

Key observation: Every commercial player that does claim-level hallucination or rigorous eval is enterprise-only (paid). No free tool combines all three of Meridian's novelty pillars.

---

## 3. What is Genuinely Novel About Meridian

The combination of three properties — all in a single, free, self-hostable platform:

1. Versioned, date-stamped industry-baseline registry with z-score normalization per capability category. No free tool does this.
2. Per-capability-category Tier labels (Frontier / Strong / Mid / Weak) with configurable thresholds and a radar chart visualization.
3. Claim-level hallucination/groundedness as a first-class, independently reported reliability axis — not folded into accuracy, not only for RAG contexts.

What we borrow (ideas, never code):
- Claim decomposition methodology -> RAGAS (Apache 2.0) — concept only, re-implemented
- Task YAML schema -> lm-eval-harness (MIT) — concept only
- LLM-judge identity stored per score -> OpenAI Evals (MIT) — concept only
- Efficiency/cost as a parallel metric axis -> HELM (Apache 2.0) — concept only

---

## 4. Cloned Repos (For Inspiration/Reading Only)

None cloned yet pending user approval of implementation plan. The following are planned shallow clones for reading:
- EleutherAI/lm-evaluation-harness — for task format patterns (MIT compatible)
- explodinggradients/ragas — for claim-level faithfulness methodology (Apache 2.0 compatible)

LICENSE COMPATIBILITY NOTES:
- MIT: Compatible with our project under any license.
- Apache 2.0: Compatible, but if we adapt code (not just concepts) we must include the NOTICE file and attribution.
- We will NOT copy code from any cloned repo into backend/ or frontend/. The /reference folder is isolated and not imported from.

---

## 5. Free Inference Provider Notes (As of Sept 2026)

| Provider | Status | Key constraint for Meridian |
|---|---|---|
| Groq | Active free tier | ~30 RPM; model-specific daily limits. Best for fast inference. |
| Google AI Studio (Gemini Flash) | Active free tier | ~10-15 RPM, ~1,500 RPD. Best quality/free tradeoff. Primary LLM-judge. |
| OpenRouter :free models | Active | 20 RPM, 50-1000 RPD. Model list changes frequently — treat as config. |
| Cloudflare Workers AI | Active | 10k Neurons/day. Lower capability models; good as fallback. |
| NVIDIA NIM | Requires account | Free credits for registered users. Adapter stubbed. |

All adapters treat rate limits as configuration. On exhaustion: mark cell as failed/quota_exceeded, continue run.

---

## 6. Database Choice Rationale

Chosen: Neon Postgres (free tier)
- Scale-to-zero (no manual wake needed vs Supabase 1-week inactivity pause)
- Standard Postgres connection strings (no vendor lock-in)
- 0.5 GB storage sufficient for academic benchmark data
- Better for Railway-deployed apps (Supabase IPv6-only free tier can cause Railway connectivity issues)

---

*This file is maintained by the Meridian development team (Monish D 24BDS1033, Soaham S 24BDS1021) as a living research log.*
