# CareerPilot AI (Python + Flask + SQLite)

Personal Career Co-Pilot for college students — rebuilt in **Python** using **Flask** and **SQLite** with zero-key Mock AI (plus optional `GEMINI_API_KEY` support via `google-genai`).

## Features

1. **Co-Pilot Chat (`/chat` & Floating Widget)**:
   - Streaming chat responses (`MockLLMProvider` out of the box, or `GeminiProvider` when `GEMINI_API_KEY` is set)
   - Fast deterministic greetings & in-memory response caching
   - Quick-reply action chips & conversational profile inference
2. **Deterministic ATS Resume Audit (`/api/resume`, `/api/upload`)**:
   - 100-point rubric (Formatting 20, Keyword Match 30, Quantified Impact 20, Section Completeness 15, Length & Clarity 15)
   - Exactly 3 fixable mistakes with Before/After bullet rewrites & fabrication guard
   - Secure upload pipeline: magic-byte verification (`%PDF`, `PK\x03\x04`, UTF-8/ASCII), filename sanitization, EICAR/malware scan hook, and real text extraction from PDF (`pypdf`) and DOCX (`python-docx`)
3. **Personalized 90-Day Roadmap (`/api/roadmap`, `/api/roadmap/toggle-task`)**:
   - 10 student tracks, 12 weeks across 3 phases (`Foundation`, `Build`, `Job Ready`)
   - Grounded strictly to vetted free resource IDs (`CURATED_RESOURCES`)
   - Interactive task progress persisted in SQLite; Weeks 1–2 unlocked for guests, Weeks 3–12 unlock upon registration
4. **Skill-Based Job Matching (`/api/jobs`, `/api/jobs/save`, `/api/jobs/report`)**:
   - 25 seeded roles ranked strictly on skills (zero CGPA/college tier bias)
   - Scam Shield advisory flags and high-CGPA warning badges
5. **5-Minute Mock Interview (`/api/interview/questions`, `/api/interview`)**:
   - Timed 5:00 interview with role-specific questions, Web Speech STT + fallback simulation, 4-pillar scoring, and model answer feedback
6. **Student Dashboard (`/dashboard`) & India DPDP Controls**:
   - Resume audit history, roadmap tracker, saved jobs, mock interview reports
   - Consent preference toggles, complete JSON data export (`/api/dashboard/export`), and deletion request (`/api/dashboard/delete`)
7. **Admin & Telemetry (`/admin`, `/api/admin/flags`)**:
   - Conversion funnel metrics, persistent SQLite feature flags, curated knowledge base view, and PII-redacted audit stream

## Quick Start

```bash
pip install -r requirements.txt
python app.py
```

Open **http://127.0.0.1:5000** in your browser.

## Run Tests

```bash
pytest -v
```
