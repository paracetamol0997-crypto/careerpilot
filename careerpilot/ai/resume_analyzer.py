"""Deterministic 100-point ATS resume rubric analyzer with fabrication protection."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Dict, List

from careerpilot.data.role_templates import ROLE_TEMPLATES, resolve_role_key

FABRICATION_TRIGGERS = (
    "fake experience",
    "fake work experience",
    "invent experience",
    "fake company",
    "lie about",
    "fabricate",
    "forge",
    "fake references",
    "fake degree",
)


def analyze_resume_content(
    resume_text: str,
    target_role: str = "software-developer",
    is_registered: bool = False,
    feature_flag_lock_mistakes: bool = True,
    file_name: str | None = None,
) -> Dict[str, Any]:
    """Evaluate resume text against a deterministic 100-point fresher ATS rubric."""
    normalized = resume_text.lower()
    now_iso = datetime.now(timezone.utc).isoformat()

    # 1. Safety guard against experience fabrication
    if any(trigger in normalized for trigger in FABRICATION_TRIGGERS):
        return {
            "score": 30,
            "breakdown": {
                "formatting": 10,
                "keywordMatch": 5,
                "quantifiedImpact": 5,
                "sectionCompleteness": 5,
                "lengthAndClarity": 5,
                "totalScore": 30,
            },
            "verdict": (
                "⚠️ Advisor note: Fabricating work experience can lead to permanent blacklisting during "
                "background checks. Let's replace unverified claims with genuine projects and measurable outcomes."
            ),
            "mistakes": [
                {
                    "id": 1,
                    "title": "Unverified / Fabricated Experience Detected",
                    "whatIsWrong": "Resume contains unverified claims or attempts to invent job tenure.",
                    "whyItHurts": "Tech recruiters cross-verify via employment records and GitHub commit histories. Fake claims lead to rejection.",
                    "howToFix": "Replace fabricated claims with genuine high-impact open-source contributions, hackathon demos, or university mini-projects.",
                    "beforeExample": "3 Years Experience as Senior Architect at Tech Giant (when in college).",
                    "afterExample": "Built full-stack e-commerce app with 1,000+ simulated users and documented architecture on GitHub.",
                    "isLocked": False,
                },
                {
                    "id": 2,
                    "title": "Missing Production Proof / Live Links",
                    "whatIsWrong": "Projects lack verifiable live URLs, GitHub repositories, or demo videos.",
                    "whyItHurts": "Recruiters cannot verify your actual coding skills without working links.",
                    "howToFix": "Deploy apps on Render/Railway and put clickable GitHub repositories.",
                    "beforeExample": "Library Management System in Python.",
                    "afterExample": "Library Management System: Built in Flask & SQLite with automated tests (Live: app.link, GitHub: repo.link).",
                    "isLocked": False,
                },
                {
                    "id": 3,
                    "title": "No Concrete Skill Evidence",
                    "whatIsWrong": "Skills listed as raw words without showing where they were applied.",
                    "whyItHurts": "ATS flags keyword stuffing if skills are not supported in project bullets.",
                    "howToFix": "Weave each primary skill into bullet points showing real usage.",
                    "beforeExample": "Skills: Python, Flask, React, SQL, Docker.",
                    "afterExample": "Developed 12 Flask REST endpoints consumed by a frontend client with indexed SQLite/PostgreSQL queries.",
                    "isLocked": False,
                },
            ],
            "targetRole": target_role,
            "matchedKeywords": [],
            "missingKeywords": ["Authentic Projects", "GitHub Repositories"],
            "analyzedAt": now_iso,
            "fileName": file_name,
        }

    role_key = resolve_role_key(target_role)
    role_template = ROLE_TEMPLATES[role_key]

    # 2. Target Role & Keywords Match (Max 30)
    expected_keywords = [k.lower() for k in role_template["atsKeywords"]]
    matched_keywords: List[str] = []
    missing_keywords: List[str] = []

    for kw in expected_keywords:
        if kw in normalized:
            matched_keywords.append(kw)
        else:
            missing_keywords.append(kw)

    keyword_ratio = (
        len(matched_keywords) / len(expected_keywords) if expected_keywords else 0.5
    )
    keyword_match_score = min(30, round(keyword_ratio * 30))

    # 3. Formatting & Parseability (Max 20)
    formatting_score = 14
    if "education" in normalized and "skills" in normalized:
        formatting_score += 3
    if "table" not in normalized and "column" not in normalized:
        formatting_score += 3

    # 4. Quantified Impact (Max 20)
    metrics_found = len(
        re.findall(r"\b\d+(?:\.\d+)?(?:%|ms|s|k|x|\+)?\b", normalized)
    )
    quantified_score = 8
    if metrics_found >= 3:
        quantified_score = 14
    if metrics_found >= 6:
        quantified_score = 20

    # 5. Section Completeness (Max 15)
    required_sections = ("education", "skills", "projects", "experience")
    sections_found = sum(1 for sec in required_sections if sec in normalized)
    section_completeness_score = round((sections_found / len(required_sections)) * 15)

    # 6. Length & Clarity (Max 15)
    word_count = len(resume_text.strip().split())
    if 150 <= word_count <= 700:
        length_clarity_score = 15
    elif word_count > 700:
        length_clarity_score = 11
    else:
        length_clarity_score = 8

    total_score = min(
        100,
        formatting_score
        + keyword_match_score
        + quantified_score
        + section_completeness_score
        + length_clarity_score,
    )

    breakdown = {
        "formatting": formatting_score,
        "keywordMatch": keyword_match_score,
        "quantifiedImpact": quantified_score,
        "sectionCompleteness": section_completeness_score,
        "lengthAndClarity": length_clarity_score,
        "totalScore": total_score,
    }

    if total_score >= 80:
        verdict = (
            "Strong resume foundation! You are well-positioned to clear initial ATS filters—"
            "tightening quantified impact metrics will push your shortlist rate even higher."
        )
    elif total_score < 60:
        verdict = (
            "Your resume reads a bit generic right now, but don't worry—applying the 3 targeted "
            "fixes below can lift your ATS score above 80."
        )
    else:
        verdict = (
            "Solid start! A few focused keyword and metric improvements will noticeably improve "
            "your recruiter shortlist rate."
        )

    should_lock = (not is_registered) and feature_flag_lock_mistakes
    missing_preview = ", ".join(missing_keywords[:3]) or "RESTful APIs, State Management, Git"
    missing_two = ", ".join(missing_keywords[:2]) or "REST APIs, Git"

    mistakes = [
        {
            "id": 1,
            "title": "Projects Lack Quantified Metrics & Business Impact",
            "whatIsWrong": "Project bullets describe features built without measurable scale, latency, or user outcomes.",
            "whyItHurts": "ATS parsers and hiring managers scan for concrete numbers (e.g., 'reduced latency by 40%', 'served 200+ users').",
            "howToFix": "Start every project bullet with an action verb + stack used + measurable outcome (numbers or percentages).",
            "beforeExample": "Built an e-commerce website using React and Node.js with login and checkout features.",
            "afterExample": "Engineered responsive full-stack e-commerce app with React & Node.js, achieving sub-200ms API responses across 50+ concurrent checkouts.",
            "isLocked": False,
        },
        {
            "id": 2,
            "title": f"Missing High-Priority ATS Keywords for {role_template['title']}",
            "whatIsWrong": f"Essential role keywords are missing from your resume: {missing_preview}.",
            "whyItHurts": "Applicant tracking systems score keyword overlap in the first pass; missing core terms lowers ranking.",
            "howToFix": f"Naturally weave missing terms ({missing_two}) into your Skills and Project descriptions.",
            "beforeExample": "Worked on website coding and backend data storage.",
            "afterExample": "Architected RESTful APIs with Python & PostgreSQL, integrating automated Git CI/CD checks.",
            "isLocked": should_lock,
        },
        {
            "id": 3,
            "title": "Passive Bullet Points Instead of Strong Action Verbs",
            "whatIsWrong": "Bullets start with passive phrasing like 'Responsible for...', 'Helped in...', or 'Worked with...'.",
            "whyItHurts": "Passive verbs obscure ownership and make your contribution sound secondary.",
            "howToFix": "Lead every bullet with strong engineering verbs: 'Architected', 'Implemented', 'Optimized', 'Automated'.",
            "beforeExample": "Responsible for creating database tables and fixing frontend bugs.",
            "afterExample": "Optimized relational database schemas with indexed queries and resolved 15+ UI rendering bugs.",
            "isLocked": should_lock,
        },
    ]

    return {
        "score": total_score,
        "breakdown": breakdown,
        "verdict": verdict,
        "mistakes": mistakes,
        "targetRole": role_template["title"],
        "matchedKeywords": matched_keywords,
        "missingKeywords": missing_keywords,
        "analyzedAt": now_iso,
        "fileName": file_name,
    }
