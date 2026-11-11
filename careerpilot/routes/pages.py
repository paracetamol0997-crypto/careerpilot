"""HTML page routes for CareerPilot AI."""

from __future__ import annotations

import uuid
from flask import Blueprint, render_template, session

from careerpilot.data.curated_resources import CURATED_RESOURCES
from careerpilot.db import ensure_session, get_full_state

pages_bp = Blueprint("pages", __name__)


def get_or_create_session_id() -> str:
    """Return the active Flask cookie session ID, creating a guest ID if needed."""
    sid = session.get("cp_session_id")
    if not sid:
        sid = f"guest_{uuid.uuid4().hex[:8]}"
        session["cp_session_id"] = sid
    ensure_session(sid)
    return sid


@pages_bp.get("/")
def home():
    sid = get_or_create_session_id()
    state = get_full_state(sid)
    return render_template("index.html", page="home", state=state)


@pages_bp.get("/chat")
def chat_page():
    sid = get_or_create_session_id()
    state = get_full_state(sid)
    return render_template("chat.html", page="chat", state=state)


@pages_bp.get("/dashboard")
def dashboard_page():
    sid = get_or_create_session_id()
    state = get_full_state(sid)
    return render_template("dashboard.html", page="dashboard", state=state)


@pages_bp.get("/admin")
def admin_page():
    sid = get_or_create_session_id()
    state = get_full_state(sid)
    return render_template(
        "admin.html",
        page="admin",
        state=state,
        curated_resources=CURATED_RESOURCES,
    )
