"""Personalized 90-day (12-week) placement roadmap generator."""

from __future__ import annotations

from typing import Any, Dict, List

from careerpilot.data.curated_resources import CURATED_RESOURCES, get_resources_for_role
from careerpilot.data.role_templates import ROLE_TEMPLATES, resolve_role_key


def generate_personalized_roadmap(
    target_role_key: str = "software-developer",
    user_skills: List[str] | None = None,
    year: str = "3",
    is_registered: bool = False,
) -> Dict[str, Any]:
    """Build a 12-week, 3-phase roadmap grounded strictly to curated free resources."""
    _ = (user_skills, year)  # Available for future pacing customizations
    role_key = resolve_role_key(target_role_key)
    role = ROLE_TEMPLATES[role_key]
    vetted_resources = get_resources_for_role(role["id"], limit=10) or CURATED_RESOURCES
    fallback_resource = CURATED_RESOURCES[0]

    p1_topics = [
        {
            "title": "Core Fundamentals & Tooling",
            "desc": "Programming syntax, command line basics, Git setup and environment configuration.",
            "topics": [role["primarySkills"][0] if role["primarySkills"] else "Programming Syntax", "Git & GitHub Setup", "Terminal & Dev Tools"],
            "task": "Set up GitHub profile and push your first clean project repository with a README.",
        },
        {
            "title": "Key Language Deep-Dive & Data Structures",
            "desc": "Control flow, object modeling, array manipulations, and asynchronous concepts.",
            "topics": [role["primarySkills"][1] if len(role["primarySkills"]) > 1 else "Core Concepts", "Algorithms & Logic", "Error Handling"],
            "task": "Write 5 problem-solving scripts and test edge-case inputs.",
        },
        {
            "title": "Architecture & Data Management",
            "desc": "Databases, schema normalization, SQL queries, or state management.",
            "topics": [role["primarySkills"][2] if len(role["primarySkills"]) > 2 else "Databases & SQL", "CRUD Operations", "Data Modeling"],
            "task": "Design a relational schema with at least 3 linked tables and run join queries.",
        },
        {
            "title": "Foundation Milestone Project",
            "desc": "Putting the initial fundamentals together in a working prototype.",
            "topics": ["End-to-end integration", "Code Modularization", "Debugging"],
            "task": f"Build MVP 1: {role['recommendedProjects'][0] if role['recommendedProjects'] else 'Starter Utility Tool'}.",
        },
    ]

    p2_topics = [
        {
            "title": "Advanced Frameworks & APIs",
            "desc": "Modern frameworks, RESTful API design, and component architecture.",
            "topics": [role["secondarySkills"][0] if role["secondarySkills"] else "Modern Framework", "API Integration", "Routing"],
            "task": "Create 4 connected API endpoints with request validation.",
        },
        {
            "title": "State, Caching & Performance",
            "desc": "Global state, caching patterns, query optimization, and latency tuning.",
            "topics": ["Caching", "Async Queues / Workers", "Query Indexing"],
            "task": "Profile API response times and optimize slow database queries.",
        },
        {
            "title": "Security, Authentication & Testing",
            "desc": "User auth tokens, role permissions, test suites, and regression checks.",
            "topics": ["Sessions / Auth", "Unit Testing", "Input Sanitization"],
            "task": "Write automated unit tests covering happy paths and failure scenarios.",
        },
        {
            "title": "Flagship Production Project",
            "desc": "Deploy a full-stack, production-ready project with live demo and documentation.",
            "topics": ["Production Deployment", "Cloud Setup", "Environment Config"],
            "task": f"Build & Deploy: {role['recommendedProjects'][1] if len(role['recommendedProjects']) > 1 else 'Production Application'}.",
        },
    ]

    p3_topics = [
        {
            "title": "Resume & Portfolio Optimization",
            "desc": "Incorporate quantified metrics into project bullets and pass ATS benchmarks.",
            "topics": ["ATS Keyword Alignment", "Portfolio Site", "GitHub Clean-up"],
            "task": "Run CareerPilot ATS checker and get score above 85+ points.",
        },
        {
            "title": "System Design & Technical Interview Prep",
            "desc": "Practice frequently asked technical and conceptual interview questions.",
            "topics": role["interviewTopics"][:3],
            "task": "Solve and record explanations for 5 core technical interview questions.",
        },
        {
            "title": "5-Minute Mock Interviews & HR Behavioral",
            "desc": "Practice answering using the STAR method (Situation, Task, Action, Result).",
            "topics": ["STAR Method", "Weakness / Conflict Handling", "Salary Negotiation Basics"],
            "task": "Complete 2 CareerPilot Mock Interview sessions with score 8+/10.",
        },
        {
            "title": "Targeted Job Applications & Cold Outreach",
            "desc": "Strategic outreach on LinkedIn, applying to filtered jobs, and direct HR messaging.",
            "topics": ["Cold Outreach Email/DM", "Job Board Filtering", "Follow-up Cadence"],
            "task": "Apply to 10 verified fresher openings and send 5 personalized outreach messages.",
        },
    ]

    phase_groups = [
        ("Foundation", p1_topics),
        ("Build", p2_topics),
        ("Job Ready", p3_topics),
    ]

    weeks: List[Dict[str, Any]] = []
    week_counter = 1
    for phase_name, items in phase_groups:
        for item in items:
            resource = (
                vetted_resources[week_counter % len(vetted_resources)]
                if vetted_resources
                else fallback_resource
            )
            is_locked = (not is_registered) and (week_counter > 2)
            weeks.append(
                {
                    "weekNumber": week_counter,
                    "phase": phase_name,
                    "title": item["title"],
                    "description": item["desc"],
                    "topics": item["topics"],
                    "tasks": [
                        {
                            "id": f"task-w{week_counter}-1",
                            "title": item["task"],
                            "completed": False,
                            "estMinutes": 90,
                        },
                        {
                            "id": f"task-w{week_counter}-2",
                            "title": f"Review vetted guide: {resource['title']}",
                            "completed": False,
                            "estMinutes": 45,
                        },
                    ],
                    "resourceId": resource["id"],
                    "resourceTitle": resource["title"],
                    "resourceUrl": resource["url"],
                    "isLocked": is_locked,
                }
            )
            week_counter += 1

    return {
        "role": role["title"],
        "phaseNames": [
            "Phase 1: Foundation (Days 1-30)",
            "Phase 2: Build & Production (Days 31-60)",
            "Phase 3: Job Ready & Placements (Days 61-90)",
        ],
        "weeks": weeks,
        "totalWeeks": 12,
        "progressPercent": 0,
    }
