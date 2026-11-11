"""Conversational CareerPilot guide engine, chips, and fast greetings."""

from __future__ import annotations

from typing import Any, Dict, Iterator, List, Optional

from careerpilot.ai.provider import get_active_llm_provider

OPENING_MESSAGE = (
    "Hey! I'm CareerPilot 👋 Your personal career guide. Tell me about yourself — "
    "what college branch or year are you in, and what career goals are you targeting? "
    "Or ask me anything to get started!"
)

INITIAL_CHIPS: List[Dict[str, str]] = [
    {"id": "f-resume", "label": "📄 ATS Resume Review", "value": "feature_resume"},
    {"id": "f-roadmap", "label": "🗺️ 90-Day Roadmap", "value": "feature_roadmap"},
    {"id": "f-jobs", "label": "💼 Matched Jobs", "value": "feature_jobs"},
    {"id": "f-interview", "label": "🎙️ 5-Min Mock Interview", "value": "feature_interview"},
]

MAIN_FEATURE_CHIPS = INITIAL_CHIPS

FAST_GREETINGS: Dict[str, str] = {
    "hi": "Hey there! I'm CareerPilot 👋 What college branch and year are you in, and what career goals are you targeting?",
    "hello": "Hello! Welcome to CareerPilot 👋 Tell me your college branch and target role, and let's build your path together!",
    "hey": "Hey! Great to connect. Are you targeting software roles, data analytics, or core engineering?",
    "good morning": "Good morning! ☀️ Ready to take your career prep to the next level? Tell me what branch and year you're in!",
    "good evening": "Good evening! 🌙 Let's accelerate your placement prep. What roles or skills are you focusing on?",
}

CHAT_STRINGS: Dict[str, Any] = {
    "welcome": OPENING_MESSAGE,
    "roadmapReady": "Here is your personalised 90-day roadmap! First 2 weeks preview is unlocked with vetted free resources.",
    "jobsReady": "Here are the top jobs matched to your skills. Potential scam postings have been auto-flagged by heuristics!",
    "registrationSuccess": "Congratulations! Registration complete 🎉 All 12 weeks, remaining 2 ATS fixes, and Mock Interview are unlocked!",
    "unlockFullRoadmapChip": "🔓 Unlock Full 12 Weeks",
    "checkJobsChip": "💼 Check Matched Jobs",
    "unlockFixesChip": "🔓 Unlock Remaining 2 Fixes",
    "seeRoadmapChip": "🗺️ See 90-Day Roadmap",
    "practiceInterviewChip": "🎙️ Practice Mock Interview",
}


def generate_chatbot_llm_stream(
    user_query: str, profile: Optional[Dict[str, Any]] = None
) -> Iterator[str]:
    """Stream response chunks from active LLM provider with student profile context."""
    provider = get_active_llm_provider(task="chat")
    if profile:
        skills = ", ".join(profile.get("skills") or []) or "None listed"
        profile_context = (
            f"Target Role: {profile.get('targetRole', 'Unknown')}, "
            f"Branch: {profile.get('branch', 'Unknown')}, "
            f"Year: {profile.get('year', 'Unknown')}, "
            f"Skills: {skills}."
        )
    else:
        profile_context = "No student profile available yet."

    system_context = f"Student Profile Context:\n{profile_context}"
    yield from provider.generate_stream(user_query, system_context)
