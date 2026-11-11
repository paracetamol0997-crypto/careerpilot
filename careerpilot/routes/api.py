"""JSON & streaming REST API endpoints for CareerPilot AI."""

from __future__ import annotations

import json
import re
import time
from typing import Any, Dict, Tuple

from flask import Blueprint, Response, jsonify, request, session, stream_with_context

from careerpilot.ai.chatbot_engine import (
    CHAT_STRINGS,
    FAST_GREETINGS,
    INITIAL_CHIPS,
    MAIN_FEATURE_CHIPS,
    OPENING_MESSAGE,
    generate_chatbot_llm_stream,
)
from careerpilot.ai.hybrid_retrieval import perform_hybrid_retrieval
from careerpilot.ai.mock_interview_engine import evaluate_interview_session
from careerpilot.ai.resume_analyzer import analyze_resume_content
from careerpilot.ai.roadmap_generator import generate_personalized_roadmap
from careerpilot.data.curated_resources import CURATED_RESOURCES
from careerpilot.data.demo_jobs import filter_and_rank_jobs
from careerpilot.data.interview_questions import get_interview_questions_for_role
from careerpilot.data.role_templates import resolve_role_key
from careerpilot.db import (
    append_chat_message,
    get_conn,
    get_feature_flags,
    get_full_state,
    get_profile,
    log_analytics_event,
    report_suspicious_job,
    request_account_deletion,
    save_interview_report,
    save_profile,
    save_resume_audit,
    save_roadmap,
    toggle_roadmap_task,
    toggle_saved_job,
    update_consents,
    update_feature_flag,
)
from careerpilot.routes.pages import get_or_create_session_id
from careerpilot.services.auth_service import (
    initiate_magic_link,
    initiate_phone_otp,
    verify_google_oauth,
    verify_magic_link,
    verify_phone_otp,
)
from careerpilot.services.storage_service import get_stored_file, process_secure_upload

api_bp = Blueprint("api", __name__, url_prefix="/api")

# In-memory response cache for repeated chat queries (1-hour TTL, max 150 entries)
_CHAT_CACHE: Dict[str, Tuple[str, float]] = {}
_CACHE_TTL_SEC = 3600.0


def _infer_profile_from_message(
    session_id: str, user_text: str, incoming_profile: Dict[str, Any] | None
) -> Dict[str, Any]:
    """Extract branch, year, and target role signals from conversational text."""
    existing = get_profile(session_id) or incoming_profile or {
        "branch": "CSE",
        "year": "3",
        "skills": ["Python", "JavaScript", "SQL"],
        "careerGoal": "Software Developer",
        "targetRole": "Software Developer",
    }
    updated = dict(existing)
    lower = user_text.lower()

    if "cse" in lower or "computer science" in lower:
        updated["branch"] = "CSE"
    elif "information tech" in lower or re.search(r"\bit\b", lower):
        updated["branch"] = "IT"
    elif "mech" in lower:
        updated["branch"] = "Mechanical"
    elif "civil" in lower:
        updated["branch"] = "Civil"
    elif "ece" in lower or "electronics" in lower:
        updated["branch"] = "ECE"
    elif "eee" in lower or "electrical" in lower:
        updated["branch"] = "EEE"

    if any(k in lower for k in ("1st year", "first year", "1st yr")):
        updated["year"] = "1"
    elif any(k in lower for k in ("2nd year", "second year", "2nd yr")):
        updated["year"] = "2"
    elif any(k in lower for k in ("3rd year", "third year", "3rd yr")):
        updated["year"] = "3"
    elif any(k in lower for k in ("4th year", "final year", "4th yr")):
        updated["year"] = "4"

    if "data analyst" in lower or "data analytics" in lower:
        updated["targetRole"] = "Data Analyst"
    elif any(k in lower for k in ("full stack", "web dev", "frontend", "software dev", "sde")):
        updated["targetRole"] = "Software Developer"
    elif "python" in lower:
        updated["targetRole"] = "Python Developer"
    elif "qa" in lower or "test" in lower:
        updated["targetRole"] = "QA / Test Engineer"

    return save_profile(session_id, updated)


@api_bp.get("/health")
def health():
    return jsonify({"status": "ok", "framework": "flask", "service": "careerpilot-ai"})


@api_bp.get("/state")
def api_state():
    sid = get_or_create_session_id()
    state = get_full_state(sid)
    if not state["messages"]:
        opening = append_chat_message(
            sid, "bot", OPENING_MESSAGE, chips=INITIAL_CHIPS, msg_id="msg_init"
        )
        state["messages"] = [opening]
    return jsonify(state)


@api_bp.post("/chat/reset")
def api_chat_reset():
    sid = get_or_create_session_id()
    with get_conn() as conn:
        conn.execute("DELETE FROM chat_messages WHERE session_id = ?", (sid,))
    opening = append_chat_message(
        sid, "bot", OPENING_MESSAGE, chips=INITIAL_CHIPS, msg_id="msg_init"
    )
    return jsonify({"success": True, "messages": [opening]})


@api_bp.post("/chat")
def api_chat():
    sid = get_or_create_session_id()
    body = request.get_json(silent=True) or {}
    message = body.get("message")
    if not message or not isinstance(message, str) or not message.strip():
        return jsonify({"error": "Message is required"}), 400

    trimmed = message.strip()
    append_chat_message(sid, "user", trimmed)
    updated_profile = _infer_profile_from_message(sid, trimmed, body.get("profile"))

    cleaned = re.sub(r"[^a-z0-9 ]", "", trimmed.lower()).strip()

    # 1. Fast greeting check
    if cleaned in FAST_GREETINGS:
        fast_reply = FAST_GREETINGS[cleaned]
        append_chat_message(sid, "bot", fast_reply, chips=MAIN_FEATURE_CHIPS)

        def generate_fast():
            words = fast_reply.split(" ")
            for idx, word in enumerate(words):
                yield ("" if idx == 0 else " ") + word

        return Response(
            stream_with_context(generate_fast()),
            mimetype="text/plain; charset=utf-8",
            headers={"Cache-Control": "no-cache, no-transform", "X-Content-Type-Options": "nosniff"},
        )

    # 2. LRU cache check
    cache_key = f"{cleaned}__{updated_profile.get('branch', '')}__{updated_profile.get('year', '')}"
    cached = _CHAT_CACHE.get(cache_key)
    if cached and (time.time() - cached[1]) < _CACHE_TTL_SEC:
        cached_text = cached[0]
        append_chat_message(sid, "bot", cached_text, chips=MAIN_FEATURE_CHIPS)

        def generate_cached():
            words = cached_text.split(" ")
            for idx, word in enumerate(words):
                yield ("" if idx == 0 else " ") + word

        return Response(
            stream_with_context(generate_cached()),
            mimetype="text/plain; charset=utf-8",
            headers={"Cache-Control": "no-cache, no-transform", "X-Content-Type-Options": "nosniff"},
        )

    # 3. Stream from Gemini or Mock provider
    def generate_live():
        chunks = []
        for chunk in generate_chatbot_llm_stream(trimmed, updated_profile):
            chunks.append(chunk)
            yield chunk
        full_reply = "".join(chunks).strip()
        if full_reply:
            append_chat_message(sid, "bot", full_reply, chips=MAIN_FEATURE_CHIPS)
            _CHAT_CACHE[cache_key] = (full_reply, time.time())
            if len(_CHAT_CACHE) > 150:
                oldest_key = next(iter(_CHAT_CACHE))
                _CHAT_CACHE.pop(oldest_key, None)

    return Response(
        stream_with_context(generate_live()),
        mimetype="text/plain; charset=utf-8",
        headers={"Cache-Control": "no-cache, no-transform", "X-Content-Type-Options": "nosniff"},
    )


@api_bp.post("/resume")
def api_resume():
    sid = get_or_create_session_id()
    body = request.get_json(silent=True) or {}
    resume_text = body.get("resumeText", "")
    if not isinstance(resume_text, str) or len(resume_text.strip()) < 10:
        return jsonify({"error": "Resume content too short to evaluate"}), 400

    state = get_full_state(sid)
    flags = state["featureFlags"]
    is_registered = bool(body.get("isRegistered", state["isRegistered"]))
    target_role = body.get("targetRole") or (
        state["profile"]["targetRole"] if state["profile"] else "software-developer"
    )
    file_name = body.get("fileName")

    result = analyze_resume_content(
        resume_text=resume_text,
        target_role=target_role,
        is_registered=is_registered,
        feature_flag_lock_mistakes=flags.get("lockAtsMistakes2and3", True),
        file_name=file_name,
    )
    save_resume_audit(sid, result)
    log_analytics_event(sid, "resume_score_viewed", {"score": result["score"]})

    if body.get("appendChat", True):
        append_chat_message(
            sid,
            "bot",
            f"Resume audit complete! Your ATS score is {result['score']}/100. Check full Mistake #1 fix below.",
            chips=[
                {"id": "c-unlock-fixes", "label": CHAT_STRINGS["unlockFixesChip"], "value": "open_reg"},
                {"id": "c-rm", "label": CHAT_STRINGS["seeRoadmapChip"], "value": "feature_roadmap"},
                {"id": "c-interview", "label": CHAT_STRINGS["practiceInterviewChip"], "value": "feature_interview"},
            ],
            card_payload={"type": "resume_preview", "data": result},
        )

    return jsonify(result)


@api_bp.post("/upload")
def api_upload_post():
    get_or_create_session_id()
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "No file provided in form data"}), 400

    data = file.read()
    result = process_secure_upload(data, file.filename or "resume.txt")
    sec = result["securityCheck"]
    if not sec["isValid"]:
        return jsonify({"error": sec.get("error"), "securityCheck": sec}), 422

    return jsonify(
        {
            "success": True,
            "fileKey": result["storedFile"]["fileKey"],
            "signedUrl": result["storedFile"]["signedUrl"],
            "securityCheck": sec,
            "extractedText": result.get("extractedText", ""),
        }
    )


@api_bp.get("/upload")
def api_upload_get():
    key = request.args.get("key")
    if not key:
        return jsonify({"error": "File key required"}), 400
    stored = get_stored_file(key)
    if not stored:
        return jsonify({"error": "File not found or expired"}), 404
    raw_bytes, _mime, filename = stored
    return Response(
        raw_bytes,
        mimetype="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@api_bp.post("/roadmap")
def api_roadmap():
    sid = get_or_create_session_id()
    body = request.get_json(silent=True) or {}
    state = get_full_state(sid)
    profile = state["profile"] or {}
    target_role_key = body.get("targetRoleKey") or profile.get("targetRole") or "software-developer"
    user_skills = body.get("userSkills") or profile.get("skills") or []
    year = str(body.get("year") or profile.get("year") or "3")
    is_registered = bool(body.get("isRegistered", state["isRegistered"]))

    roadmap = generate_personalized_roadmap(
        target_role_key=target_role_key,
        user_skills=user_skills,
        year=year,
        is_registered=is_registered,
    )
    save_roadmap(sid, roadmap)
    log_analytics_event(sid, "roadmap_preview_viewed", {"role": roadmap["role"]})

    if body.get("appendChat", True):
        append_chat_message(
            sid,
            "bot",
            CHAT_STRINGS["roadmapReady"],
            chips=[
                {"id": "c-unlock-rm", "label": CHAT_STRINGS["unlockFullRoadmapChip"], "value": "open_reg"},
                {"id": "c-jobs", "label": CHAT_STRINGS["checkJobsChip"], "value": "feature_jobs"},
            ],
            card_payload={"type": "roadmap_preview", "data": roadmap},
        )

    return jsonify(roadmap)


@api_bp.post("/roadmap/toggle-task")
def api_roadmap_toggle():
    sid = get_or_create_session_id()
    body = request.get_json(silent=True) or {}
    week_number = body.get("weekNumber")
    task_id = body.get("taskId")
    if week_number is None or not task_id:
        return jsonify({"error": "weekNumber and taskId are required"}), 400

    updated = toggle_roadmap_task(sid, int(week_number), str(task_id))
    if not updated:
        return jsonify({"error": "Roadmap not found"}), 404
    return jsonify(updated)


@api_bp.post("/jobs")
def api_jobs():
    sid = get_or_create_session_id()
    body = request.get_json(silent=True) or {}
    state = get_full_state(sid)
    profile = state["profile"] or {}

    target_role = body.get("targetRole") or profile.get("targetRole") or "software-developer"
    user_skills = body.get("userSkills") or profile.get("skills") or ["JavaScript", "Python", "SQL"]
    job_type = body.get("jobType", "all")
    remote_only = bool(body.get("remoteOnly", False))

    jobs = filter_and_rank_jobs(
        target_role=target_role,
        user_skills=user_skills,
        job_type=job_type,
        remote_only=remote_only,
    )
    log_analytics_event(sid, "job_preview_viewed", {"count": len(jobs), "role": target_role})

    if body.get("appendChat", False):
        append_chat_message(
            sid,
            "bot",
            CHAT_STRINGS["jobsReady"],
            chips=[
                {"id": "c-apply", "label": "Improve Resume ATS For These Jobs", "value": "feature_resume"},
                {"id": "c-rm", "label": CHAT_STRINGS["seeRoadmapChip"], "value": "feature_roadmap"},
            ],
            card_payload={"type": "jobs_preview", "data": jobs[:5]},
        )

    return jsonify({"jobs": jobs})


@api_bp.post("/jobs/save")
def api_jobs_save():
    sid = get_or_create_session_id()
    body = request.get_json(silent=True) or {}
    job = body.get("job")
    if not isinstance(job, dict) or not job.get("id"):
        return jsonify({"error": "Valid job payload required"}), 400
    saved = toggle_saved_job(sid, job)
    return jsonify({"savedJobs": saved})


@api_bp.post("/jobs/report")
def api_jobs_report():
    sid = get_or_create_session_id()
    body = request.get_json(silent=True) or {}
    job_id = body.get("jobId")
    if not job_id:
        return jsonify({"error": "jobId is required"}), 400
    report_suspicious_job(sid, str(job_id))
    log_analytics_event(sid, "scam_job_reported", {"jobId": str(job_id)})
    return jsonify({"success": True, "jobId": str(job_id)})


@api_bp.get("/interview/questions")
def api_interview_questions():
    role_id = resolve_role_key(request.args.get("roleId", "software-developer"))
    return jsonify({"roleId": role_id, "questions": get_interview_questions_for_role(role_id)})


@api_bp.post("/interview")
def api_interview():
    sid = get_or_create_session_id()
    body = request.get_json(silent=True) or {}
    answers = body.get("answers")
    if not isinstance(answers, list):
        return jsonify({"error": "answers array is required"}), 400

    role_id = body.get("roleId", "software-developer")
    report = evaluate_interview_session(
        session_id=body.get("sessionId") or sid,
        role_id=role_id,
        answers=answers,
    )
    save_interview_report(sid, report)
    log_analytics_event(sid, "mock_interview_completed", {"score": report["overallScore"]})

    if body.get("appendChat", True):
        append_chat_message(
            sid,
            "bot",
            (
                f"Mock interview complete. Overall rating: {report['overallScore']}/10.\n"
                f"Top strength: \"{report['strengths'][0]}\". Full feedback report saved to My Space."
            ),
            chips=[
                {"id": "c-dash", "label": "Open My Space Dashboard", "value": "go_dashboard"},
                {"id": "c-rm", "label": CHAT_STRINGS["seeRoadmapChip"], "value": "feature_roadmap"},
                {"id": "c-jobs", "label": CHAT_STRINGS["checkJobsChip"], "value": "feature_jobs"},
            ],
            card_payload={"type": "interview_invite", "data": report},
        )

    return jsonify(report)


@api_bp.post("/auth/phone/initiate")
def api_auth_phone_init():
    get_or_create_session_id()
    body = request.get_json(silent=True) or {}
    phone = str(body.get("phone") or "").strip()
    if not phone:
        return jsonify({"error": "Phone number is required"}), 400
    return jsonify(initiate_phone_otp(phone))


@api_bp.post("/auth/phone/verify")
def api_auth_phone_verify():
    sid = get_or_create_session_id()
    body = request.get_json(silent=True) or {}
    phone = str(body.get("phone") or "").strip()
    otp = str(body.get("otp") or "7890").strip()
    name = body.get("name")
    if not phone:
        return jsonify({"error": "Phone number is required"}), 400
    res = verify_phone_otp(sid, phone, otp, name)
    if not res["success"]:
        return jsonify(res), 400
    append_chat_message(sid, "bot", CHAT_STRINGS["registrationSuccess"], chips=MAIN_FEATURE_CHIPS)
    return jsonify(res)


@api_bp.post("/auth/google")
def api_auth_google():
    sid = get_or_create_session_id()
    body = request.get_json(silent=True) or {}
    res = verify_google_oauth(
        sid,
        email=body.get("email", "google.student@gmail.com"),
        name=body.get("name", "Google Student Pilot"),
    )
    append_chat_message(sid, "bot", CHAT_STRINGS["registrationSuccess"], chips=MAIN_FEATURE_CHIPS)
    return jsonify(res)


@api_bp.post("/auth/magic-link/initiate")
def api_auth_magic_init():
    get_or_create_session_id()
    body = request.get_json(silent=True) or {}
    email = str(body.get("email") or "").strip()
    if not email or "@" not in email:
        return jsonify({"error": "Valid email is required"}), 400
    return jsonify(initiate_magic_link(email, body.get("name")))


@api_bp.post("/auth/magic-link/verify")
def api_auth_magic_verify():
    sid = get_or_create_session_id()
    body = request.get_json(silent=True) or {}
    token = str(body.get("token") or "").strip()
    email = str(body.get("email") or "").strip()
    if not email:
        return jsonify({"error": "Email is required"}), 400
    res = verify_magic_link(sid, token, email)
    if not res["success"]:
        return jsonify(res), 400
    append_chat_message(sid, "bot", CHAT_STRINGS["registrationSuccess"], chips=MAIN_FEATURE_CHIPS)
    return jsonify(res)


@api_bp.post("/auth/logout")
def api_auth_logout():
    session.pop("cp_session_id", None)
    return jsonify({"success": True})


@api_bp.get("/dashboard/export")
def api_dashboard_export():
    sid = get_or_create_session_id()
    state = get_full_state(sid)
    payload = json.dumps(state, indent=2)
    return Response(
        payload,
        mimetype="application/json",
        headers={"Content-Disposition": 'attachment; filename="CareerPilot_Data_Export.json"'},
    )


@api_bp.post("/dashboard/consent")
def api_dashboard_consent():
    sid = get_or_create_session_id()
    body = request.get_json(silent=True) or {}
    consents = update_consents(sid, body)
    return jsonify({"consents": consents})


@api_bp.post("/dashboard/delete")
def api_dashboard_delete():
    sid = get_or_create_session_id()
    requested_at = request_account_deletion(sid)
    return jsonify(
        {
            "success": True,
            "deletionRequestedAt": requested_at,
            "message": "Deletion request queued. Your session records will be purged within 30 days per retention policy.",
        }
    )


@api_bp.post("/admin/flags")
def api_admin_flags():
    get_or_create_session_id()
    body = request.get_json(silent=True) or {}
    key = body.get("key")
    value = body.get("value")
    if key not in get_feature_flags() or not isinstance(value, bool):
        return jsonify({"error": "Valid flag key and boolean value required"}), 400
    flags = update_feature_flag(key, value)
    return jsonify({"featureFlags": flags})


@api_bp.post("/analytics")
def api_analytics():
    sid = get_or_create_session_id()
    body = request.get_json(silent=True) or {}
    event_name = body.get("eventName")
    if not event_name:
        return jsonify({"error": "eventName is required"}), 400
    log_analytics_event(sid, str(event_name), body.get("payload"))
    return jsonify({"success": True})


@api_bp.post("/retrieval")
def api_retrieval():
    body = request.get_json(silent=True) or {}
    query = str(body.get("query") or "")
    target_role = body.get("targetRole")
    language = body.get("language")
    top_k = int(body.get("topK", 5))
    result = perform_hybrid_retrieval(query, target_role=target_role, language=language, top_k=top_k)
    return jsonify(result)


@api_bp.get("/resources")
def api_resources():
    return jsonify({"resources": CURATED_RESOURCES})
