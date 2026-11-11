"""SQLite persistence layer for CareerPilot AI."""

from __future__ import annotations

import json
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional

from flask import current_app


DEFAULT_FLAGS: Dict[str, bool] = {
    "lockAtsMistakes2and3": True,
    "enableVoiceInterviewMock": False,
    "requireStrictOTP": False,
    "enablePostHogTracking": False,
}

DEFAULT_CONSENTS: Dict[str, bool] = {
    "dataProcessing": True,
    "whatsappUpdates": False,
    "modelTraining": False,
}


def utc_now_iso() -> str:
    """Return an ISO-8601 UTC timestamp string."""
    return datetime.now(timezone.utc).isoformat()


def get_db_path() -> Path:
    """Resolve the active SQLite database path from Flask app config."""
    db_path = Path(current_app.config["DATABASE_PATH"])
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return db_path


@contextmanager
def get_conn() -> Generator[sqlite3.Connection, None, None]:
    """Open a SQLite connection with row factory and automatic commit/rollback."""
    conn = sqlite3.connect(str(get_db_path()), timeout=10.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db(db_path: Optional[Path] = None) -> None:
    """Create all SQLite tables and default feature flags if they do not exist."""
    target = Path(db_path) if db_path else get_db_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(target), timeout=10.0)
    try:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                phone TEXT,
                email TEXT,
                role TEXT NOT NULL DEFAULT 'student',
                auth_provider TEXT NOT NULL DEFAULT 'phone_otp',
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                user_id TEXT REFERENCES users(id) ON DELETE SET NULL,
                is_registered INTEGER NOT NULL DEFAULT 0,
                deletion_requested_at TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS profiles (
                session_id TEXT PRIMARY KEY REFERENCES sessions(session_id) ON DELETE CASCADE,
                branch TEXT NOT NULL,
                year TEXT NOT NULL,
                skills_json TEXT NOT NULL,
                career_goal TEXT NOT NULL,
                target_role TEXT NOT NULL,
                college_name TEXT,
                location TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS chat_messages (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
                sender TEXT NOT NULL,
                text TEXT NOT NULL,
                chips_json TEXT,
                card_payload_json TEXT,
                timestamp TEXT NOT NULL,
                seq INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS resume_audits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
                file_name TEXT,
                target_role TEXT NOT NULL,
                score INTEGER NOT NULL,
                result_json TEXT NOT NULL,
                analyzed_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS roadmaps (
                session_id TEXT PRIMARY KEY REFERENCES sessions(session_id) ON DELETE CASCADE,
                role TEXT NOT NULL,
                roadmap_json TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS saved_jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
                job_id TEXT NOT NULL,
                job_json TEXT NOT NULL,
                saved_at TEXT NOT NULL,
                UNIQUE(session_id, job_id)
            );

            CREATE TABLE IF NOT EXISTS reported_jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
                job_id TEXT NOT NULL,
                reported_at TEXT NOT NULL,
                UNIQUE(session_id, job_id)
            );

            CREATE TABLE IF NOT EXISTS interview_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
                report_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS analytics_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                event_name TEXT NOT NULL,
                payload_json TEXT,
                timestamp TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS feature_flags (
                key TEXT PRIMARY KEY,
                value INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS dpdp_consents (
                session_id TEXT PRIMARY KEY REFERENCES sessions(session_id) ON DELETE CASCADE,
                data_processing INTEGER NOT NULL DEFAULT 1,
                whatsapp_updates INTEGER NOT NULL DEFAULT 0,
                model_training INTEGER NOT NULL DEFAULT 0,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS auth_tokens (
                token_key TEXT PRIMARY KEY,
                code TEXT NOT NULL,
                provider TEXT NOT NULL,
                name TEXT,
                expires_at REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS uploaded_files (
                file_key TEXT PRIMARY KEY,
                original_filename TEXT NOT NULL,
                content_type TEXT NOT NULL,
                size_bytes INTEGER NOT NULL,
                disk_path TEXT NOT NULL,
                uploaded_at TEXT NOT NULL
            );
            """
        )
        for key, val in DEFAULT_FLAGS.items():
            conn.execute(
                "INSERT OR IGNORE INTO feature_flags (key, value) VALUES (?, ?)",
                (key, 1 if val else 0),
            )
        conn.commit()
    finally:
        conn.close()


def ensure_session(session_id: str) -> None:
    """Ensure a session row and default consent row exist."""
    now = utc_now_iso()
    with get_conn() as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO sessions (session_id, is_registered, created_at, updated_at)
            VALUES (?, 0, ?, ?)
            """,
            (session_id, now, now),
        )
        conn.execute(
            """
            INSERT OR IGNORE INTO dpdp_consents (session_id, data_processing, whatsapp_updates, model_training, updated_at)
            VALUES (?, 1, 0, 0, ?)
            """,
            (session_id, now),
        )


def get_feature_flags() -> Dict[str, bool]:
    """Load feature flags from SQLite."""
    flags = dict(DEFAULT_FLAGS)
    with get_conn() as conn:
        rows = conn.execute("SELECT key, value FROM feature_flags").fetchall()
        for row in rows:
            flags[row["key"]] = bool(row["value"])
    return flags


def update_feature_flag(key: str, value: bool) -> Dict[str, bool]:
    """Persist a single feature flag change and return all flags."""
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO feature_flags (key, value) VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """,
            (key, 1 if value else 0),
        )
    return get_feature_flags()


def save_profile(session_id: str, profile: Dict[str, Any]) -> Dict[str, Any]:
    """Upsert the student's profile for a session."""
    ensure_session(session_id)
    now = utc_now_iso()
    with get_conn() as conn:
        existing = conn.execute(
            "SELECT created_at FROM profiles WHERE session_id = ?", (session_id,)
        ).fetchone()
        created_at = existing["created_at"] if existing else now
        skills = profile.get("skills") or ["Python", "SQL"]
        conn.execute(
            """
            INSERT INTO profiles (session_id, branch, year, skills_json, career_goal, target_role, college_name, location, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(session_id) DO UPDATE SET
                branch = excluded.branch,
                year = excluded.year,
                skills_json = excluded.skills_json,
                career_goal = excluded.career_goal,
                target_role = excluded.target_role,
                college_name = excluded.college_name,
                location = excluded.location,
                updated_at = excluded.updated_at
            """,
            (
                session_id,
                profile.get("branch", "CSE"),
                str(profile.get("year", "3")),
                json.dumps(skills),
                profile.get("careerGoal", profile.get("targetRole", "Software Developer")),
                profile.get("targetRole", "Software Developer"),
                profile.get("collegeName"),
                profile.get("location"),
                created_at,
                now,
            ),
        )
        conn.execute(
            "UPDATE sessions SET updated_at = ? WHERE session_id = ?", (now, session_id)
        )
    return get_profile(session_id) or {}


def get_profile(session_id: str) -> Optional[Dict[str, Any]]:
    """Return the stored profile for `session_id`, if any."""
    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT p.*, s.user_id
            FROM profiles p
            JOIN sessions s ON s.session_id = p.session_id
            WHERE p.session_id = ?
            """,
            (session_id,),
        ).fetchone()
        if not row:
            return None
        return {
            "sessionId": row["session_id"],
            "userId": row["user_id"],
            "branch": row["branch"],
            "year": row["year"],
            "skills": json.loads(row["skills_json"]),
            "careerGoal": row["career_goal"],
            "targetRole": row["target_role"],
            "collegeName": row["college_name"],
            "location": row["location"],
            "createdAt": row["created_at"],
            "updatedAt": row["updated_at"],
        }


def append_chat_message(
    session_id: str,
    sender: str,
    text: str,
    chips: Optional[List[Dict[str, Any]]] = None,
    card_payload: Optional[Dict[str, Any]] = None,
    msg_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Append a chat message to SQLite and return its serialized payload."""
    ensure_session(session_id)
    msg_id = msg_id or f"{sender}_{uuid.uuid4().hex[:8]}"
    now = utc_now_iso()
    with get_conn() as conn:
        max_seq_row = conn.execute(
            "SELECT COALESCE(MAX(seq), 0) AS max_seq FROM chat_messages WHERE session_id = ?",
            (session_id,),
        ).fetchone()
        next_seq = (max_seq_row["max_seq"] if max_seq_row else 0) + 1
        conn.execute(
            """
            INSERT OR REPLACE INTO chat_messages (id, session_id, sender, text, chips_json, card_payload_json, timestamp, seq)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                msg_id,
                session_id,
                sender,
                text,
                json.dumps(chips) if chips is not None else None,
                json.dumps(card_payload) if card_payload is not None else None,
                now,
                next_seq,
            ),
        )
    return {
        "id": msg_id,
        "sender": sender,
        "text": text,
        "timestamp": now,
        "chips": chips,
        "cardPayload": card_payload,
    }


def save_resume_audit(session_id: str, result: Dict[str, Any]) -> None:
    """Persist an ATS resume audit result."""
    ensure_session(session_id)
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO resume_audits (session_id, file_name, target_role, score, result_json, analyzed_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                result.get("fileName"),
                result.get("targetRole", "Software Developer (Web)"),
                int(result.get("score", 0)),
                json.dumps(result),
                result.get("analyzedAt", utc_now_iso()),
            ),
        )


def save_roadmap(session_id: str, roadmap: Dict[str, Any]) -> None:
    """Persist or replace the session's 90-day roadmap."""
    ensure_session(session_id)
    now = utc_now_iso()
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO roadmaps (session_id, role, roadmap_json, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(session_id) DO UPDATE SET
                role = excluded.role,
                roadmap_json = excluded.roadmap_json,
                updated_at = excluded.updated_at
            """,
            (session_id, roadmap.get("role", "Software Developer (Web)"), json.dumps(roadmap), now),
        )


def toggle_roadmap_task(session_id: str, week_number: int, task_id: str) -> Optional[Dict[str, Any]]:
    """Toggle completion status of a roadmap task and recalculate progressPercent."""
    ensure_session(session_id)
    with get_conn() as conn:
        row = conn.execute(
            "SELECT roadmap_json FROM roadmaps WHERE session_id = ?", (session_id,)
        ).fetchone()
        if not row:
            return None
        roadmap = json.loads(row["roadmap_json"])
        total_tasks = 0
        completed_tasks = 0
        for week in roadmap.get("weeks", []):
            for task in week.get("tasks", []):
                if week.get("weekNumber") == week_number and task.get("id") == task_id:
                    task["completed"] = not bool(task.get("completed"))
                total_tasks += 1
                if task.get("completed"):
                    completed_tasks += 1
        roadmap["progressPercent"] = (
            round((completed_tasks / total_tasks) * 100) if total_tasks > 0 else 0
        )
        conn.execute(
            "UPDATE roadmaps SET roadmap_json = ?, updated_at = ? WHERE session_id = ?",
            (json.dumps(roadmap), utc_now_iso(), session_id),
        )
        return roadmap


def toggle_saved_job(session_id: str, job: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Save or unsave a job for the session, returning updated saved jobs."""
    ensure_session(session_id)
    job_id = job["id"]
    with get_conn() as conn:
        existing = conn.execute(
            "SELECT id FROM saved_jobs WHERE session_id = ? AND job_id = ?",
            (session_id, job_id),
        ).fetchone()
        if existing:
            conn.execute("DELETE FROM saved_jobs WHERE id = ?", (existing["id"],))
        else:
            conn.execute(
                "INSERT INTO saved_jobs (session_id, job_id, job_json, saved_at) VALUES (?, ?, ?, ?)",
                (session_id, job_id, json.dumps(job), utc_now_iso()),
            )
    return get_saved_jobs(session_id)


def get_saved_jobs(session_id: str) -> List[Dict[str, Any]]:
    """Fetch saved jobs for a session."""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT job_json FROM saved_jobs WHERE session_id = ? ORDER BY id DESC",
            (session_id,),
        ).fetchall()
        return [json.loads(r["job_json"]) for r in rows]


def report_suspicious_job(session_id: str, job_id: str) -> None:
    """Record a suspicious job report."""
    ensure_session(session_id)
    with get_conn() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO reported_jobs (session_id, job_id, reported_at) VALUES (?, ?, ?)",
            (session_id, job_id, utc_now_iso()),
        )


def save_interview_report(session_id: str, report: Dict[str, Any]) -> None:
    """Persist a completed mock interview report."""
    ensure_session(session_id)
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO interview_reports (session_id, report_json, created_at) VALUES (?, ?, ?)",
            (session_id, json.dumps(report), report.get("createdAt", utc_now_iso())),
        )


def log_analytics_event(
    session_id: str, event_name: str, payload: Optional[Dict[str, Any]] = None
) -> None:
    """Record a PII-redacted analytics event."""
    redacted_payload = {}
    if payload:
        for k, v in payload.items():
            if k.lower() in {"phone", "email", "otp", "token", "resumetext"}:
                redacted_payload[k] = "[REDACTED]"
            else:
                redacted_payload[k] = v
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO analytics_events (session_id, event_name, payload_json, timestamp) VALUES (?, ?, ?, ?)",
            (session_id, event_name, json.dumps(redacted_payload), utc_now_iso()),
        )


def update_consents(session_id: str, consents: Dict[str, bool]) -> Dict[str, bool]:
    """Update DPDP consent flags for a session."""
    ensure_session(session_id)
    with get_conn() as conn:
        conn.execute(
            """
            UPDATE dpdp_consents
            SET data_processing = ?, whatsapp_updates = ?, model_training = ?, updated_at = ?
            WHERE session_id = ?
            """,
            (
                1 if consents.get("dataProcessing", True) else 0,
                1 if consents.get("whatsappUpdates", False) else 0,
                1 if consents.get("modelTraining", False) else 0,
                utc_now_iso(),
                session_id,
            ),
        )
    return get_consents(session_id)


def get_consents(session_id: str) -> Dict[str, bool]:
    """Fetch DPDP consent preferences for a session."""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT data_processing, whatsapp_updates, model_training FROM dpdp_consents WHERE session_id = ?",
            (session_id,),
        ).fetchone()
        if not row:
            return dict(DEFAULT_CONSENTS)
        return {
            "dataProcessing": bool(row["data_processing"]),
            "whatsappUpdates": bool(row["whatsapp_updates"]),
            "modelTraining": bool(row["model_training"]),
        }


def migrate_guest_to_user(
    session_id: str, phone_or_email: str, name: Optional[str] = None, auth_provider: str = "phone_otp"
) -> Dict[str, Any]:
    """Atomically convert a guest session into a registered student and unlock gated content."""
    ensure_session(session_id)
    now = utc_now_iso()
    user_id = f"usr_{uuid.uuid4().hex[:7]}"
    is_email = "@" in phone_or_email
    user = {
        "id": user_id,
        "name": (name or "").strip() or "Student Pilot",
        "phone": None if is_email else phone_or_email,
        "email": phone_or_email if is_email else None,
        "role": "student",
        "createdAt": now,
    }

    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO users (id, name, phone, email, role, auth_provider, created_at)
            VALUES (?, ?, ?, ?, 'student', ?, ?)
            """,
            (user_id, user["name"], user["phone"], user["email"], auth_provider, now),
        )
        conn.execute(
            """
            UPDATE sessions
            SET user_id = ?, is_registered = 1, updated_at = ?
            WHERE session_id = ?
            """,
            (user_id, now, session_id),
        )

        # Unlock roadmap weeks 3-12
        rm_row = conn.execute(
            "SELECT roadmap_json FROM roadmaps WHERE session_id = ?", (session_id,)
        ).fetchone()
        if rm_row:
            roadmap = json.loads(rm_row["roadmap_json"])
            for wk in roadmap.get("weeks", []):
                wk["isLocked"] = False
            conn.execute(
                "UPDATE roadmaps SET roadmap_json = ?, updated_at = ? WHERE session_id = ?",
                (json.dumps(roadmap), now, session_id),
            )

        # Unlock resume mistakes #2 & #3 in all existing resume audits for this session
        audit_rows = conn.execute(
            "SELECT id, result_json FROM resume_audits WHERE session_id = ?", (session_id,)
        ).fetchall()
        for a_row in audit_rows:
            audit = json.loads(a_row["result_json"])
            for m in audit.get("mistakes", []):
                m["isLocked"] = False
            conn.execute(
                "UPDATE resume_audits SET result_json = ? WHERE id = ?",
                (json.dumps(audit), a_row["id"]),
            )

    log_analytics_event(
        session_id,
        "registration_completed",
        {"userId": user_id, "provider": auth_provider},
    )
    return {"success": True, "user": user}


def request_account_deletion(session_id: str) -> str:
    """Mark a session for DPDP deletion and clear personal session history."""
    ensure_session(session_id)
    now = utc_now_iso()
    with get_conn() as conn:
        conn.execute(
            "UPDATE sessions SET deletion_requested_at = ?, updated_at = ? WHERE session_id = ?",
            (now, now, session_id),
        )
    log_analytics_event(session_id, "account_deletion_requested")
    return now


def get_full_state(session_id: str) -> Dict[str, Any]:
    """Assemble the complete AppStoreState for `session_id` from SQLite."""
    ensure_session(session_id)
    with get_conn() as conn:
        sess = conn.execute(
            "SELECT user_id, is_registered, deletion_requested_at FROM sessions WHERE session_id = ?",
            (session_id,),
        ).fetchone()

        user = None
        if sess and sess["user_id"]:
            u_row = conn.execute("SELECT * FROM users WHERE id = ?", (sess["user_id"],)).fetchone()
            if u_row:
                user = {
                    "id": u_row["id"],
                    "name": u_row["name"],
                    "phone": u_row["phone"],
                    "email": u_row["email"],
                    "role": u_row["role"],
                    "createdAt": u_row["created_at"],
                }

        msg_rows = conn.execute(
            "SELECT * FROM chat_messages WHERE session_id = ? ORDER BY seq ASC",
            (session_id,),
        ).fetchall()
        messages = [
            {
                "id": r["id"],
                "sender": r["sender"],
                "text": r["text"],
                "timestamp": r["timestamp"],
                "chips": json.loads(r["chips_json"]) if r["chips_json"] else None,
                "cardPayload": json.loads(r["card_payload_json"])
                if r["card_payload_json"]
                else None,
            }
            for r in msg_rows
        ]

        audit_rows = conn.execute(
            "SELECT result_json FROM resume_audits WHERE session_id = ? ORDER BY id DESC",
            (session_id,),
        ).fetchall()
        resume_history = [json.loads(r["result_json"]) for r in audit_rows]

        rm_row = conn.execute(
            "SELECT roadmap_json FROM roadmaps WHERE session_id = ?", (session_id,)
        ).fetchone()
        roadmap = json.loads(rm_row["roadmap_json"]) if rm_row else None

        interview_rows = conn.execute(
            "SELECT report_json FROM interview_reports WHERE session_id = ? ORDER BY id DESC",
            (session_id,),
        ).fetchall()
        interview_history = [json.loads(r["report_json"]) for r in interview_rows]

        event_rows = conn.execute(
            "SELECT event_name, session_id, payload_json, timestamp FROM analytics_events ORDER BY id DESC LIMIT 100"
        ).fetchall()
        analytics_events = [
            {
                "eventName": r["event_name"],
                "sessionId": r["session_id"],
                "payload": json.loads(r["payload_json"]) if r["payload_json"] else {},
                "timestamp": r["timestamp"],
            }
            for r in event_rows
        ]

        reported_rows = conn.execute(
            "SELECT job_id FROM reported_jobs WHERE session_id = ?", (session_id,)
        ).fetchall()
        reported_job_ids = [r["job_id"] for r in reported_rows]

    return {
        "user": user,
        "sessionId": session_id,
        "isRegistered": bool(sess["is_registered"]) if sess else False,
        "deletionRequestedAt": sess["deletion_requested_at"] if sess else None,
        "profile": get_profile(session_id),
        "messages": messages,
        "currentResumeResult": resume_history[0] if resume_history else None,
        "resumeHistory": resume_history,
        "roadmap": roadmap,
        "savedJobs": get_saved_jobs(session_id),
        "reportedJobIds": reported_job_ids,
        "interviewHistory": interview_history,
        "featureFlags": get_feature_flags(),
        "analyticsEvents": analytics_events,
        "consents": get_consents(session_id),
    }
