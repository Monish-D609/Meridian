"""
Meridian — Database seed data.

Seeds:
  - 7 CapabilityCategories
  - 5 Datasets (one per core category)
  - ~50 Tasks (10 per dataset, mix of closed and open)
  - 3 BaselineModels with BaselineScores per category
    (PLACEHOLDER: scores are illustrative/synthetic — clearly labelled.
     Real numbers will be sourced from published papers and dated.)
  - 4 default LLM Providers + free-tier Models
"""
from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import AsyncSessionLocal, Base, engine
from app.models.models import (
    BaselineModel,
    BaselineScore,
    CapabilityCategory,
    Dataset,
    Model,
    Provider,
    Task,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def uid() -> str:
    return str(uuid.uuid4())


# ---------------------------------------------------------------------------
# 1. Capability Categories
# ---------------------------------------------------------------------------
CATEGORIES = [
    {"name": "Coding",              "slug": "coding",          "description": "Code generation, debugging, explanation, and completion tasks."},
    {"name": "Mathematics",         "slug": "mathematics",     "description": "Arithmetic, algebra, calculus, and mathematical reasoning tasks."},
    {"name": "Reasoning",           "slug": "reasoning",       "description": "Logical inference, multi-step reasoning, and common-sense tasks."},
    {"name": "Creative Writing",    "slug": "creative_writing","description": "Story generation, poetry, style transfer, and creative composition."},
    {"name": "Summarization",       "slug": "summarization",   "description": "Document condensation and key-point extraction tasks."},
    {"name": "Factual QA",          "slug": "factual_qa",      "description": "Grounded question answering requiring factual accuracy and groundedness."},
    {"name": "Long-Context",        "slug": "long_context",    "description": "Tasks requiring retention and reasoning over extended context windows."},
]

# ---------------------------------------------------------------------------
# 2. Datasets (one per category for MVP; extensible)
# ---------------------------------------------------------------------------
DATASETS: list[dict] = [
    {
        "name": "Meridian Coding Benchmark v1",
        "description": "Code generation and debugging tasks across Python, JavaScript, and SQL.",
        "category_slug": "coding",
        "task_type": "open",
        "source_url": "https://github.com/your-org/meridian",
        "license_info": "MIT",
        "version_tag": "1.0.0-seed",
    },
    {
        "name": "Meridian Math Benchmark v1",
        "description": "GSM8K-style arithmetic word problems and symbolic math tasks.",
        "category_slug": "mathematics",
        "task_type": "closed",
        "source_url": "https://github.com/your-org/meridian",
        "license_info": "MIT",
        "version_tag": "1.0.0-seed",
    },
    {
        "name": "Meridian Reasoning Benchmark v1",
        "description": "Multi-step logical inference and common-sense reasoning problems.",
        "category_slug": "reasoning",
        "task_type": "open",
        "source_url": "https://github.com/your-org/meridian",
        "license_info": "MIT",
        "version_tag": "1.0.0-seed",
    },
    {
        "name": "Meridian Summarization Benchmark v1",
        "description": "Short-document summarization tasks with reference summaries.",
        "category_slug": "summarization",
        "task_type": "open",
        "source_url": "https://github.com/your-org/meridian",
        "license_info": "MIT",
        "version_tag": "1.0.0-seed",
    },
    {
        "name": "Meridian Factual QA Benchmark v1",
        "description": "Grounded factual question answering with reference passages.",
        "category_slug": "factual_qa",
        "task_type": "open",
        "source_url": "https://github.com/your-org/meridian",
        "license_info": "MIT",
        "version_tag": "1.0.0-seed",
    },
]

# ---------------------------------------------------------------------------
# 3. Tasks (10 per dataset)
# ---------------------------------------------------------------------------
TASKS_BY_DATASET: dict[str, list[dict]] = {
    "Meridian Coding Benchmark v1": [
        {
            "prompt": "Write a Python function `two_sum(nums: list[int], target: int) -> list[int]` that returns the indices of two numbers that add up to the target. Assume exactly one solution exists.",
            "reference_answer": "def two_sum(nums, target):\n    seen = {}\n    for i, n in enumerate(nums):\n        if target - n in seen:\n            return [seen[target - n], i]\n        seen[n] = i",
            "system_prompt": "You are an expert Python programmer. Respond with only the function code, no explanation.",
        },
        {
            "prompt": "Debug the following Python code and explain the bug:\n```python\ndef factorial(n):\n    if n == 0:\n        return 1\n    return n * factorial(n)\n```",
            "reference_answer": "The bug is infinite recursion: the recursive call should be `factorial(n - 1)` not `factorial(n)`. Corrected: `return n * factorial(n - 1)`.",
            "system_prompt": "You are an expert Python debugger.",
        },
        {
            "prompt": "Write a SQL query to find the top 3 customers by total order value from tables `orders(id, customer_id, amount)` and `customers(id, name)`.",
            "reference_answer": "SELECT c.name, SUM(o.amount) AS total FROM customers c JOIN orders o ON c.id = o.customer_id GROUP BY c.id, c.name ORDER BY total DESC LIMIT 3;",
            "system_prompt": "You are an expert SQL developer. Return only the SQL query.",
        },
        {
            "prompt": "Implement a binary search function in Python that returns the index of `target` in a sorted list `arr`, or -1 if not found.",
            "reference_answer": "def binary_search(arr, target):\n    lo, hi = 0, len(arr) - 1\n    while lo <= hi:\n        mid = (lo + hi) // 2\n        if arr[mid] == target: return mid\n        elif arr[mid] < target: lo = mid + 1\n        else: hi = mid - 1\n    return -1",
            "system_prompt": "Return only the function code.",
        },
        {
            "prompt": "Write a JavaScript async function that fetches JSON from a URL using the Fetch API and returns the parsed data. Handle errors gracefully.",
            "reference_answer": "async function fetchJSON(url) { try { const r = await fetch(url); if (!r.ok) throw new Error(r.statusText); return await r.json(); } catch (e) { console.error(e); return null; } }",
            "system_prompt": "Return only the JavaScript function.",
        },
        {
            "prompt": "Explain what a Python decorator is and write an example that measures a function's execution time.",
            "reference_answer": None,  # open-ended
            "system_prompt": "You are a clear technical educator.",
        },
        {
            "prompt": "Write a Python class `Stack` with methods `push(val)`, `pop()`, `peek()`, and `is_empty()` using a list internally.",
            "reference_answer": "class Stack:\n    def __init__(self): self._data = []\n    def push(self, v): self._data.append(v)\n    def pop(self): return self._data.pop()\n    def peek(self): return self._data[-1]\n    def is_empty(self): return len(self._data) == 0",
            "system_prompt": "Return only the class code.",
        },
        {
            "prompt": "What is the time complexity of Python's `list.sort()` and why? Explain the underlying algorithm.",
            "reference_answer": None,
            "system_prompt": "You are a computer science expert.",
        },
        {
            "prompt": "Write a regex pattern in Python that validates an email address (basic RFC 5321 compliance) and show how to use it with `re.match`.",
            "reference_answer": None,
            "system_prompt": "Provide working Python code with the pattern and usage example.",
        },
        {
            "prompt": "Refactor the following Python code to use list comprehension:\n```python\nresult = []\nfor x in range(10):\n    if x % 2 == 0:\n        result.append(x ** 2)\n```",
            "reference_answer": "result = [x ** 2 for x in range(10) if x % 2 == 0]",
            "system_prompt": "Return only the refactored line.",
        },
    ],

    "Meridian Math Benchmark v1": [
        {"prompt": "A train travels 300 km in 4 hours. What is its average speed in km/h?", "reference_answer": "75"},
        {"prompt": "If 5x + 3 = 23, what is x?", "reference_answer": "4"},
        {"prompt": "What is 15% of 240?", "reference_answer": "36"},
        {"prompt": "A rectangle has length 12 cm and width 7 cm. What is its area?", "reference_answer": "84"},
        {"prompt": "What is the sum of the first 10 natural numbers?", "reference_answer": "55"},
        {"prompt": "If a shirt costs $45 after a 25% discount, what was the original price?", "reference_answer": "60"},
        {"prompt": "Solve: 2^10 = ?", "reference_answer": "1024"},
        {"prompt": "The ratio of boys to girls in a class is 3:2. If there are 30 students, how many are girls?", "reference_answer": "12"},
        {"prompt": "What is the next prime number after 17?", "reference_answer": "19"},
        {"prompt": "If f(x) = 3x² - 2x + 1, what is f(2)?", "reference_answer": "9"},
    ],

    "Meridian Reasoning Benchmark v1": [
        {
            "prompt": "All mammals are warm-blooded. Whales are mammals. Are whales warm-blooded? Explain your reasoning.",
            "reference_answer": None,
        },
        {
            "prompt": "A is taller than B. C is shorter than A but taller than B. Who is the shortest?",
            "reference_answer": "B",
        },
        {
            "prompt": "If today is Wednesday, what day will it be in 100 days?",
            "reference_answer": "Friday",
        },
        {
            "prompt": "A farmer has 17 sheep. All but 9 die. How many sheep does the farmer have?",
            "reference_answer": "9",
        },
        {
            "prompt": "If you overtake the person in second place in a race, what position are you in?",
            "reference_answer": "Second place",
        },
        {
            "prompt": "Three boxes are labeled 'Apples', 'Oranges', and 'Apples & Oranges', but all labels are wrong. You can pick one fruit from one box. How do you determine all contents?",
            "reference_answer": None,
        },
        {
            "prompt": "A clock shows 3:15. What is the angle between the hour and minute hands?",
            "reference_answer": "7.5 degrees",
        },
        {
            "prompt": "If it takes 5 machines 5 minutes to make 5 widgets, how long does it take 100 machines to make 100 widgets?",
            "reference_answer": "5 minutes",
        },
        {
            "prompt": "You have two ropes that each take exactly 1 hour to burn, but they burn unevenly. How do you measure 45 minutes?",
            "reference_answer": None,
        },
        {
            "prompt": "A snail is at the bottom of a 10m well. Each day it climbs 3m and each night it slips back 2m. How many days to escape?",
            "reference_answer": "8 days",
        },
    ],

    "Meridian Summarization Benchmark v1": [
        {
            "prompt": "Summarize the following passage in 2-3 sentences:\n\nThe Amazon rainforest, often referred to as the 'lungs of the Earth', produces about 20% of the world's oxygen. It spans over 5.5 million square kilometers across nine countries in South America and is home to approximately 10% of all species on the planet. However, deforestation has destroyed about 17% of the forest in the last 50 years, primarily due to agricultural expansion and illegal logging.",
            "reference_answer": "The Amazon rainforest is a critical global ecosystem spanning 5.5 million km² that produces 20% of the world's oxygen and hosts 10% of all species. Despite its importance, 17% has been destroyed in 50 years due to agriculture and logging.",
            "context": "The Amazon rainforest, often referred to as the 'lungs of the Earth'...",
        },
        {
            "prompt": "Provide a one-sentence summary of this abstract:\n\nThis paper introduces Transformer-based neural networks as a new architecture for natural language processing. Unlike recurrent models, Transformers rely entirely on attention mechanisms, enabling parallelization during training and achieving state-of-the-art results on machine translation benchmarks.",
            "reference_answer": "Transformers are a new attention-based neural architecture that improves NLP performance through parallelization, achieving state-of-the-art machine translation results.",
            "context": "This paper introduces Transformer-based neural networks...",
        },
        {
            "prompt": "Summarize the key points from this meeting notes excerpt:\n\nAgenda: Q3 Marketing review. Budget shortfall of $50K identified. Decision to pause TV ads and redirect to social media campaigns. New influencer partnerships approved: 3 creators signed for October. Next meeting: October 15 to review campaign performance.",
            "reference_answer": None,
        },
        {
            "prompt": "Condense the following instruction into a single clear sentence:\n\nTo reset your password, first navigate to the login page, then click on 'Forgot Password', enter your registered email address in the field provided, and wait for a reset link which will be emailed to you within 5 minutes. Click the link in the email before it expires in 24 hours.",
            "reference_answer": "To reset your password, click 'Forgot Password' on the login page, enter your email, and use the link emailed to you within 24 hours.",
        },
        {
            "prompt": "What are the three most important points from this passage?\n\nClimate change is causing global temperatures to rise at an unprecedented rate, primarily due to greenhouse gas emissions from burning fossil fuels. This warming is melting polar ice caps, raising sea levels, and increasing the frequency of extreme weather events. Biodiversity is under severe threat, with many species facing extinction. Transitioning to renewable energy sources, implementing carbon capture technologies, and reducing deforestation are among the key solutions proposed by scientists.",
            "reference_answer": None,
        },
        {
            "prompt": "Summarize this product review in one sentence:\n\nI've been using this wireless mouse for 3 months now and it's been fantastic. The battery lasts about 6 months on a single charge, the tracking is super accurate even on glass surfaces, and it connects to three devices via Bluetooth which is great for switching between my laptop and desktop. My only minor complaint is that it's slightly heavier than I'd like.",
            "reference_answer": None,
        },
        {
            "prompt": "Create a TL;DR (too long; didn't read) summary for this news article intro:\n\nThe city council voted 7-2 last night to approve a $2.4 billion infrastructure package that includes resurfacing 340 miles of roads, replacing 12 aging bridges, expanding the public transit network with 50 new electric buses, and installing 1,200 new streetlights in underserved neighborhoods. The project, funded through a combination of municipal bonds and federal grants, is expected to create approximately 8,000 construction jobs over the next four years.",
            "reference_answer": None,
        },
        {
            "prompt": "Summarize the following legal text in plain English (2 sentences max):\n\nThe licensee hereby grants to the licensor a non-exclusive, royalty-free, worldwide, sublicensable, irrevocable license to use, reproduce, modify, publish, translate, create derivative works from, distribute, perform, and display the Licensed Content for any purpose.",
            "reference_answer": "You give the company a permanent, free, worldwide right to use and modify your content in any way they want. This license cannot be taken back.",
        },
        {
            "prompt": "What is the main conclusion of this research summary?\n\nAfter studying 2,400 employees across 35 companies over two years, researchers found that flexible work arrangements led to a 23% increase in productivity and a 34% reduction in voluntary turnover. Employee satisfaction scores improved by 41%. Companies with hybrid policies saw the greatest gains, while fully remote or fully in-office arrangements showed smaller improvements. The findings suggest that moderate flexibility, not maximum flexibility, yields optimal results.",
            "reference_answer": None,
        },
        {
            "prompt": "Summarize this sports match report in 2 sentences:\n\nIn a thrilling Champions League semifinal last night, FC Barcelona defeated Bayern Munich 3-2 at the Camp Nou, with Pedri scoring a stunning last-minute winner. The hosts trailed 2-0 after 60 minutes before mounting a remarkable comeback through goals by Gavi, Lewandowski, and Pedri. Barcelona advances to their first final in six years, where they will face Real Madrid in what promises to be a historic El Clasico final.",
            "reference_answer": None,
        },
    ],

    "Meridian Factual QA Benchmark v1": [
        {
            "prompt": "Based on the following passage, answer: What year was the Eiffel Tower completed?\n\nPassage: The Eiffel Tower is a wrought-iron lattice tower on the Champ de Mars in Paris, France. It was constructed between 1887 and 1889 as the centerpiece of the 1889 World's Fair and was completed on March 15, 1889.",
            "reference_answer": "1889",
            "context": "The Eiffel Tower is a wrought-iron lattice tower... completed on March 15, 1889.",
        },
        {
            "prompt": "According to the passage, who invented the telephone?\n\nPassage: The invention of the telephone is attributed to Alexander Graham Bell, who was awarded the first patent for the telephone by the United States Patent Office on March 7, 1876. Bell made the first successful telephone call to his assistant Thomas Watson on March 10, 1876.",
            "reference_answer": "Alexander Graham Bell",
            "context": "The invention of the telephone is attributed to Alexander Graham Bell...",
        },
        {
            "prompt": "Based on this passage, what is the capital of Australia?\n\nPassage: Australia is a country and continent in the Southern Hemisphere. Its capital city is Canberra, which was purpose-built as a compromise between Sydney and Melbourne. Many people mistakenly believe Sydney is the capital due to its size and international prominence, but Canberra has served as the capital since 1913.",
            "reference_answer": "Canberra",
            "context": "Australia is a country... Its capital city is Canberra...",
        },
        {
            "prompt": "According to the passage, how many bones are in the adult human body?\n\nPassage: The human skeleton is a complex framework of bones, cartilage, and connective tissue. An adult human body contains 206 bones, while newborn babies have around 270-300 bones that fuse together as they grow. The femur, or thigh bone, is the longest and strongest bone in the human body.",
            "reference_answer": "206",
            "context": "An adult human body contains 206 bones...",
        },
        {
            "prompt": "From the passage, what does DNA stand for?\n\nPassage: DNA, which stands for Deoxyribonucleic Acid, is the molecule that carries the genetic information for all living organisms and many viruses. The structure of DNA is a double helix, first described by James Watson and Francis Crick in 1953, using X-ray data from Rosalind Franklin.",
            "reference_answer": "Deoxyribonucleic Acid",
            "context": "DNA, which stands for Deoxyribonucleic Acid...",
        },
        {
            "prompt": "Based on the passage, how fast does light travel?\n\nPassage: Light travels at approximately 299,792,458 meters per second (roughly 186,000 miles per second) in a vacuum. This speed, denoted by the symbol 'c', is considered the universal speed limit under Einstein's theory of special relativity. Nothing with mass can travel at or beyond the speed of light.",
            "reference_answer": "299,792,458 meters per second (approximately 186,000 miles per second)",
            "context": "Light travels at approximately 299,792,458 meters per second...",
        },
        {
            "prompt": "According to this passage, who wrote Romeo and Juliet?\n\nPassage: Romeo and Juliet is a tragedy written by William Shakespeare, believed to have been written between 1594 and 1596. The play follows the story of two young lovers from feuding families in Verona, Italy, and is one of Shakespeare's most performed plays worldwide.",
            "reference_answer": "William Shakespeare",
            "context": "Romeo and Juliet is a tragedy written by William Shakespeare...",
        },
        {
            "prompt": "From the passage, what is the boiling point of water at sea level?\n\nPassage: Water is a unique substance with remarkable properties. At standard atmospheric pressure (sea level), water boils at 100 degrees Celsius or 212 degrees Fahrenheit. At higher altitudes, where atmospheric pressure is lower, water boils at temperatures below 100°C, which is why cooking times must be adjusted when cooking at high elevation.",
            "reference_answer": "100 degrees Celsius (212 degrees Fahrenheit)",
            "context": "At standard atmospheric pressure (sea level), water boils at 100 degrees Celsius...",
        },
        {
            "prompt": "Answer based only on the passage: What is the approximate population of Earth?\n\nPassage: As of 2024, Earth's human population stands at approximately 8.1 billion people. The global population crossed the 8 billion mark in November 2022. Population growth rate has been declining, but the world population is still expected to reach around 10 billion by 2050 according to UN projections.",
            "reference_answer": "Approximately 8.1 billion",
            "context": "As of 2024, Earth's human population stands at approximately 8.1 billion people.",
        },
        {
            "prompt": "According to the passage, what planet is closest to the Sun?\n\nPassage: The solar system consists of the Sun and all the objects that orbit it, including eight major planets. Mercury is the planet closest to the Sun, completing one orbit in approximately 88 Earth days. Despite being the closest to the Sun, Mercury is not the hottest planet — that distinction belongs to Venus due to its thick greenhouse-effect atmosphere.",
            "reference_answer": "Mercury",
            "context": "Mercury is the planet closest to the Sun...",
        },
    ],
}

# ---------------------------------------------------------------------------
# 4. Providers & Models (free-tier)
# ---------------------------------------------------------------------------
PROVIDERS_AND_MODELS = [
    {
        "name": "Groq",
        "base_url": "https://api.groq.com",
        "auth_env_var": "GROQ_API_KEY",
        "models": [
            {
                "model_id_external": "llama-3.1-8b-instant",
                "display_name": "Llama 3.1 8B Instant (Groq)",
                "description": "Meta Llama 3.1 8B via Groq's ultra-fast inference. Free tier.",
                "rate_limit_rpm": 30,
                "rate_limit_tpm": 6000,
            },
            {
                "model_id_external": "gemma2-9b-it",
                "display_name": "Gemma 2 9B Instruct (Groq)",
                "description": "Google Gemma 2 9B via Groq. Free tier.",
                "rate_limit_rpm": 30,
                "rate_limit_tpm": 15000,
            },
        ],
    },
    {
        "name": "Google AI Studio",
        "base_url": "https://generativelanguage.googleapis.com",
        "auth_env_var": "GEMINI_API_KEY",
        "models": [
            {
                "model_id_external": "gemini-1.5-flash-latest",
                "display_name": "Gemini 1.5 Flash (Google AI Studio)",
                "description": "Google Gemini 1.5 Flash via AI Studio. Primary LLM-judge. Free tier.",
                "rate_limit_rpm": 15,
                "rate_limit_tpm": None,
            },
            {
                "model_id_external": "gemini-1.5-pro-latest",
                "display_name": "Gemini 1.5 Pro (Google AI Studio)",
                "description": "Google Gemini 1.5 Pro via AI Studio. Free tier (lower limits).",
                "rate_limit_rpm": 2,
                "rate_limit_tpm": None,
            },
        ],
    },
    {
        "name": "OpenRouter",
        "base_url": "https://openrouter.ai/api",
        "auth_env_var": "OPENROUTER_API_KEY",
        "models": [
            {
                "model_id_external": "meta-llama/llama-3.1-8b-instruct:free",
                "display_name": "Llama 3.1 8B Instruct (OpenRouter Free)",
                "description": "Meta Llama 3.1 8B via OpenRouter free tier.",
                "rate_limit_rpm": 20,
                "rate_limit_tpm": None,
            },
            {
                "model_id_external": "google/gemma-2-9b-it:free",
                "display_name": "Gemma 2 9B (OpenRouter Free)",
                "description": "Google Gemma 2 9B via OpenRouter free tier.",
                "rate_limit_rpm": 20,
                "rate_limit_tpm": None,
            },
        ],
    },
    {
        "name": "Cloudflare Workers AI",
        "base_url": "https://api.cloudflare.com/client/v4/accounts",
        "auth_env_var": "CLOUDFLARE_API_TOKEN",
        "models": [
            {
                "model_id_external": "@cf/meta/llama-3.1-8b-instruct",
                "display_name": "Llama 3.1 8B Instruct (Cloudflare)",
                "description": "Meta Llama 3.1 8B via Cloudflare Workers AI. Free allocation.",
                "rate_limit_rpm": None,
                "rate_limit_tpm": None,
            },
        ],
    },
]

# ---------------------------------------------------------------------------
# 5. Baseline Models & Scores
#
# PLACEHOLDER — These scores are ILLUSTRATIVE ONLY and do NOT represent
# measured performance of the named models. They are sourced from publicly
# available academic benchmark summaries (MMLU, HumanEval, GSM8K, etc.)
# and normalized to [0, 1]. They are clearly marked is_placeholder=True.
# The captured_date reflects when the reference numbers were sourced.
# These will be replaced with measured baselines in Phase 8 (validation run).
# ---------------------------------------------------------------------------
BASELINE_MODELS = [
    {
        "display_name": "GPT-4-class Reference (Illustrative)",
        "version_tag": "gpt4-class-2024q3",
        "captured_date": "2024-09-01",
        "notes": "PLACEHOLDER: Illustrative scores representative of GPT-4-class frontier models "
                 "as reported in public benchmarks (MMLU, HumanEval, GSM8K, ROUGE-L, etc.) "
                 "circa Q3 2024. NOT measured by Meridian. Will be replaced with real measurements.",
        "source_url": "https://openai.com/research/gpt-4",
        "is_placeholder": True,
        "scores": {
            "coding": 0.87,
            "mathematics": 0.92,
            "reasoning": 0.88,
            "creative_writing": 0.82,
            "summarization": 0.85,
            "factual_qa": 0.84,
            "long_context": 0.81,
        },
    },
    {
        "display_name": "Claude-3-class Reference (Illustrative)",
        "version_tag": "claude3-class-2024q3",
        "captured_date": "2024-09-01",
        "notes": "PLACEHOLDER: Illustrative scores representative of Claude 3 Opus/Sonnet-class "
                 "models based on public leaderboard data circa Q3 2024. NOT measured by Meridian.",
        "source_url": "https://www.anthropic.com/claude",
        "is_placeholder": True,
        "scores": {
            "coding": 0.84,
            "mathematics": 0.85,
            "reasoning": 0.90,
            "creative_writing": 0.88,
            "summarization": 0.87,
            "factual_qa": 0.86,
            "long_context": 0.85,
        },
    },
    {
        "display_name": "Open-Source Mid-Tier Reference (Illustrative)",
        "version_tag": "oss-mid-2024q3",
        "captured_date": "2024-09-01",
        "notes": "PLACEHOLDER: Illustrative scores representative of strong open-source models "
                 "(Llama 3 70B class) circa Q3 2024. NOT measured by Meridian.",
        "source_url": "https://huggingface.co/spaces/open-llm-leaderboard/open_llm_leaderboard",
        "is_placeholder": True,
        "scores": {
            "coding": 0.72,
            "mathematics": 0.75,
            "reasoning": 0.74,
            "creative_writing": 0.70,
            "summarization": 0.73,
            "factual_qa": 0.71,
            "long_context": 0.65,
        },
    },
]


# ---------------------------------------------------------------------------
# Seed execution
# ---------------------------------------------------------------------------
async def seed(session: AsyncSession) -> None:
    from sqlalchemy import select

    print("🌱 Seeding Meridian database...")

    # --- Capability Categories ---
    cat_map: dict[str, CapabilityCategory] = {}
    for cat_data in CATEGORIES:
        existing = await session.scalar(
            select(CapabilityCategory).where(CapabilityCategory.slug == cat_data["slug"])
        )
        if existing:
            cat_map[cat_data["slug"]] = existing
            continue
        cat = CapabilityCategory(id=uid(), **cat_data)
        session.add(cat)
        cat_map[cat_data["slug"]] = cat
    await session.flush()
    print(f"  ✓ {len(cat_map)} capability categories")

    # --- Datasets ---
    dataset_map: dict[str, Dataset] = {}
    for ds_data in DATASETS:
        cat_slug = ds_data.pop("category_slug")
        existing = await session.scalar(
            select(Dataset).where(Dataset.name == ds_data["name"])
        )
        if existing:
            dataset_map[ds_data["name"]] = existing
            ds_data["category_slug"] = cat_slug
            continue
        ds = Dataset(
            id=uid(),
            category_id=cat_map[cat_slug].id,
            **ds_data,
        )
        session.add(ds)
        dataset_map[ds.name] = ds
        ds_data["category_slug"] = cat_slug
    await session.flush()
    print(f"  ✓ {len(dataset_map)} datasets")

    # --- Tasks ---
    task_count = 0
    for ds_name, tasks in TASKS_BY_DATASET.items():
        dataset = dataset_map.get(ds_name)
        if dataset is None:
            print(f"  ⚠ Dataset '{ds_name}' not found; skipping tasks")
            continue
        existing_count = await session.scalar(
            select(func_count()).select_from(Task).where(Task.dataset_id == dataset.id)
        )
        if existing_count and existing_count > 0:
            print(f"  ↩ Tasks for '{ds_name}' already seeded ({existing_count} tasks)")
            task_count += existing_count
            continue
        for t_data in tasks:
            t = Task(id=uid(), dataset_id=dataset.id, **t_data)
            session.add(t)
            task_count += 1
    await session.flush()
    print(f"  ✓ {task_count} tasks")

    # --- Providers & Models ---
    provider_count = 0
    model_count = 0
    for pd in PROVIDERS_AND_MODELS:
        models_data = pd.pop("models")
        existing_provider = await session.scalar(
            select(Provider).where(Provider.name == pd["name"])
        )
        if existing_provider:
            provider = existing_provider
        else:
            provider = Provider(id=uid(), **pd)
            session.add(provider)
            provider_count += 1
        pd["models"] = models_data
        await session.flush()

        for md in models_data:
            existing_model = await session.scalar(
                select(Model).where(
                    Model.provider_id == provider.id,
                    Model.model_id_external == md["model_id_external"],
                )
            )
            if existing_model:
                continue
            m = Model(id=uid(), provider_id=provider.id, **md)
            session.add(m)
            model_count += 1
    await session.flush()
    print(f"  ✓ {provider_count} providers, {model_count} models")

    # --- Baseline Models & Scores ---
    baseline_count = 0
    for bm_data in BASELINE_MODELS:
        scores = bm_data.pop("scores")
        existing_bm = await session.scalar(
            select(BaselineModel).where(BaselineModel.version_tag == bm_data["version_tag"])
        )
        if existing_bm:
            baseline = existing_bm
        else:
            baseline = BaselineModel(id=uid(), **bm_data)
            session.add(baseline)
            baseline_count += 1
        bm_data["scores"] = scores
        await session.flush()

        for cat_slug, raw_score in scores.items():
            cat = cat_map.get(cat_slug)
            if cat is None:
                continue
            existing_bs = await session.scalar(
                select(BaselineScore).where(
                    BaselineScore.baseline_model_id == baseline.id,
                    BaselineScore.category_id == cat.id,
                )
            )
            if existing_bs:
                continue
            bs = BaselineScore(
                id=uid(),
                baseline_model_id=baseline.id,
                category_id=cat.id,
                raw_score=raw_score,
            )
            session.add(bs)

    await session.flush()

    # Compute distribution stats across all baseline models per category
    from sqlalchemy import select as sa_select, func as sa_func
    for cat in cat_map.values():
        result = await session.execute(
            sa_select(BaselineScore).where(BaselineScore.category_id == cat.id)
        )
        cat_scores = result.scalars().all()
        if len(cat_scores) < 2:
            continue
        vals = [s.raw_score for s in cat_scores]
        mean = sum(vals) / len(vals)
        std = (sum((v - mean) ** 2 for v in vals) / len(vals)) ** 0.5
        for bs in cat_scores:
            bs.distribution_mean = mean
            bs.distribution_std = std if std > 0 else 1.0

    await session.flush()
    print(f"  ✓ {baseline_count} baseline models seeded (PLACEHOLDER — see notes)")
    print("🌱 Seeding complete!")


# Alias for Task count query
from sqlalchemy import func as func_count


async def main() -> None:
    """Run seed from CLI: python -m app.db.seed"""
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("  ✓ Tables created / verified")

    async with AsyncSessionLocal() as session:
        await seed(session)
        await session.commit()


if __name__ == "__main__":
    asyncio.run(main())
