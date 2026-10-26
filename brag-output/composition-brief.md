# Hyperframes Composition Brief: Meridian

## Objective
Create a short, premium launch-style brag video for Meridian (LLM Evaluation & Benchmarking Platform).

## Output
- Composition directory: `brag-output/composition/`
- Rendered video: `brag-output/brag.mp4`
- Format: landscape — 1920x1080
- Duration: 18.0 seconds (540 frames @ 30fps)

## Source Material
- Project root: `c:/Users/Monish D/Documents/Meridian`
- Primary files read: `README.md`, `frontend/src/index.css`, `frontend/src/components/RadarChart.tsx`, `frontend/src/pages/ResultsPage.tsx`, `frontend/src/pages/ResponsesPage.tsx`
- Product name: Meridian
- Tagline / strongest claim: "An enterprise-grade, reproducible LLM benchmarking and comparative positioning platform on a 100% free-tier stack."
- Key UI or visual moment to recreate:
  - 7-Axis Geometric Radar Chart (`RadarChart.tsx`) comparing candidate model polygon vs baseline median
  - Live benchmark matrix showing zero-cost inference providers (Cloudflare Workers AI, Groq LPU, Google AI Studio)
  - Atomic claim hallucination extraction cards highlighting `[FABRICATED]` text with evidence breakdown
- Copy that must appear verbatim:
  - "Where does this model actually stand across the specific capabilities my workload requires?"
  - "Frontier · Strong · Mid · Weak"
  - "7-Axis Capability Profiling"
  - "Dual-Stage Hallucination & Groundedness Scorer"
  - "Zero-Cost Free Tier Inference"

## Creative Direction
- Tone preset: `polished`
- Creative direction: clean developer-grade telemetry & AI positioning audit
- Interpretation: Serious, elegant, high-contrast dark theme. Restrained typography and smooth data visualizations rather than noisy flashy animations.
- Angle: Exposing the flaw of single-number LLM leaderboards and demonstrating how Meridian provides actionable 7-axis positioning and sentence-level hallucination detection.
- Hook (0.0s – 3.7s): "Single-score leaderboards flatten LLMs. Meridian maps their coordinates."
- Outro / punchline (15.8s – 18.0s): "Stop guessing model performance. Know their exact coordinates. Meridian."
- Avoid:
  - Generic SaaS buzzwords ("streamline your workflow", "supercharge your AI")
  - Abstract filler shapes or floating glass spheres
  - Low-contrast unreadable text

## Visual Identity
- Background: `#10151B`
- Card Panels: `#18202A`
- Borders / Lines: `#2B3642`
- Primary Text: `#E8ECF0`
- Secondary Text: `#AAB4BF`
- Muted Labels: `#7C8997`
- Accent: `#6B93F5` (Electric Indigo) / Soft Accent `#1D2A47`
- Tiers:
  - Frontier: `#B3A9FF` (BG: `#2A2652`)
  - Strong: `#5ED0CE` (BG: `#12363A`)
  - Mid: `#E8B659` (BG: `#40331A`)
  - Weak: `#F08A82` (BG: `#432220`)
- Display Font: `Source Serif 4`, serif
- Body Font: `Hanken Grotesk`, sans-serif
- Code Font: `SF Mono`, Menlo, monospace

## Storyboard
1. **Scene 1 (0.0s – 3.7s)**: The Leaderboard Problem — Single-score flattening contrasted with multidimensional positioning.
2. **Scene 2 (3.7s – 7.8s)**: Free-Tier Benchmark Matrix — Cloudflare, Groq, Google AI Studio executing 7 capability suites on $0 stack.
3. **Scene 3 (7.8s – 12.6s)**: 7-Axis Capability Radar & Percentile Tiering — Geometric polygon expansion, 92nd percentile Math (Frontier), 86th percentile Coding (Strong) vs GPT-4o baselines.
4. **Scene 4 (12.6s – 15.8s)**: Atomic Claim Hallucination Scorer — Claim extraction highlighting fabricated facts with ground truth evidence audit.
5. **Scene 5 (15.8s – 18.0s)**: Outro & Call to Action — Meridian brand lockup, free-tier stack badges, and CLI run prompt.

## Audio
- Audio role: Sleek, high-tech electronic groove bed with crisp percussive accents and UI telemetry clicks.
- Audio arc: Clean electronic pulse building from hook through multi-model execution, reaching full fidelity during the radar chart reveal, dropping into analytical focus during claim verification, and resolving with a musical fade over the Meridian lock.
- Music: `happy-beats-business-moves-vol-11-by-ende-dot-app.mp3`
- Music treatment: Starts at 0.0s at volume 0.75, subtle volume ducking under key metric highlights, gentle fade-out over final logo from 16.5s to 18.0s.
- Music cue guidance: Preset tempo 114.84 BPM.
  - Strong Cues: 1.60s (hook lock), 3.70s (transition), 5.80s (matrix execution), 8.96s (radar bloom), 12.65s (claim alert), 17.91s (outro lock).
  - Beat-grid windows: 4.23s, 4.75s, 5.28s (Scene 2 chips); 8.96s, 9.50s, 10.54s (Scene 3 tier badges).
- Audio-reactive treatment: Subtle RMS/bass breathing on radar polygon border and tier badges.
- SFX:
  - Subtle switch clicks (`click1.ogg` / `switch1.ogg`) on chip activation.
  - Smooth tone on radar chart expansion.
  - Low ping on fabricated claim detection.

## Hyperframes Instructions
- Composition directory: `brag-output/composition/`
- Build a pure HTML/CSS/JS Hyperframes composition complying with 1920x1080 resolution, 30fps, and 18.0s total duration.
- Ensure all text passes WCAG contrast and readability requirements.
- Use native SVG for the 7-axis radar chart and claim audit cards.
- Run `npx hyperframes check` and ensure 0 errors before rendering.
