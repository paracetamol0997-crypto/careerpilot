"""4-pillar mock interview evaluator."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List

from careerpilot.data.interview_questions import get_interview_questions_for_role
from careerpilot.data.role_templates import resolve_role_key


def evaluate_interview_session(
    session_id: str,
    role_id: str = "software-developer",
    answers: List[Dict[str, Any]] | None = None,
) -> Dict[str, Any]:
    """Score answers across Accuracy, Clarity, Confidence, and Communication."""
    resolved_role = resolve_role_key(role_id)
    questions = get_interview_questions_for_role(resolved_role)
    answers = answers or []

    total_content = 0.0
    total_clarity = 0.0
    total_confidence = 0.0
    total_comm = 0.0

    weakest_index = 0
    lowest_score = 999.0

    for idx, ans in enumerate(answers):
        q = questions[idx] if idx < len(questions) else None
        text = str(ans.get("userAnswer") or "").strip().lower()
        words = [w for w in text.split() if w]

        content_score = 5.0
        clarity_score = 6.0
        confidence_score = 6.0
        comm_score = 6.0

        if len(words) < 5 or text == "skipped":
            content_score = 2.0
            clarity_score = 3.0
            confidence_score = 3.0
            comm_score = 3.0
        else:
            if 25 <= len(words) <= 150:
                content_score += 2
                clarity_score += 2

            if q:
                matches = [
                    kw for kw in q["expectedKeywords"] if kw.lower() in text
                ]
                if len(matches) >= 2:
                    content_score += 2
                if len(matches) >= 4:
                    content_score += 1

            if any(
                phrase in text
                for phrase in ("i built", "i implemented", "because", "specifically")
            ):
                confidence_score += 2

            if any(
                phrase in text
                for phrase in ("firstly", "furthermore", "in summary", "for example")
            ):
                comm_score += 2

        content_score = min(10.0, content_score)
        clarity_score = min(10.0, clarity_score)
        confidence_score = min(10.0, confidence_score)
        comm_score = min(10.0, comm_score)

        q_avg = (content_score + clarity_score + confidence_score + comm_score) / 4.0
        if q_avg < lowest_score:
            lowest_score = q_avg
            weakest_index = idx

        total_content += content_score
        total_clarity += clarity_score
        total_confidence += confidence_score
        total_comm += comm_score

    count = max(1, len(answers))
    avg_content = round(total_content / count, 1)
    avg_clarity = round(total_clarity / count, 1)
    avg_confidence = round(total_confidence / count, 1)
    avg_comm = round(total_comm / count, 1)
    overall = round((avg_content + avg_clarity + avg_confidence + avg_comm) / 4.0, 1)

    weakest_q = (
        questions[weakest_index]
        if weakest_index < len(questions)
        else (questions[0] if questions else None)
    )

    return {
        "sessionId": session_id,
        "overallScore": overall,
        "contentAccuracyScore": avg_content,
        "clarityScore": avg_clarity,
        "confidenceScore": avg_confidence,
        "communicationScore": avg_comm,
        "strengths": [
            "Natural conversational delivery with authentic answers and genuine project examples.",
            "Strong grasp of core technical fundamentals and concept clarity.",
            "Successfully attempted questions within the target 5-minute time window.",
        ],
        "improvements": [
            "Include deeper technical terminology and describe internal mechanisms in your answers.",
            "Apply the STAR framework (Situation → Task → Action → Result) to structure project explanations.",
            "Cite measurable outcomes and quantifiable metrics (e.g., latency, active users, test coverage).",
        ],
        "weakestQuestionIndex": weakest_index,
        "idealAnswerForWeakest": (
            weakest_q["sampleIdealAnswer"]
            if weakest_q
            else "Focus on clear cause-and-effect reasoning with the STAR framework."
        ),
        "nextRoadmapAction": "Check Week 10: System Design & Technical Interview Prep in your 90-day roadmap.",
        "createdAt": datetime.now(timezone.utc).isoformat(),
    }
