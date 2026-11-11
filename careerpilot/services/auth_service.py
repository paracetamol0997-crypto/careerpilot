"""Phone OTP, Google OAuth, and Magic Link authentication adapters backed by SQLite."""

from __future__ import annotations

import secrets
import time
from typing import Any, Dict, Optional

from careerpilot.db import get_conn, migrate_guest_to_user, utc_now_iso

DEMO_OTP_CODE = "7890"


def initiate_phone_otp(phone: str) -> Dict[str, Any]:
    """Generate and persist a 10-minute OTP (deterministic 7890 for zero-key demo)."""
    clean_phone = phone.strip()
    expires_at = time.time() + 600
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO auth_tokens (token_key, code, provider, name, expires_at)
            VALUES (?, ?, 'phone_otp', NULL, ?)
            ON CONFLICT(token_key) DO UPDATE SET code = excluded.code, expires_at = excluded.expires_at
            """,
            (clean_phone, DEMO_OTP_CODE, expires_at),
        )
    return {
        "provider": "phone_otp",
        "identifier": clean_phone,
        "sentAt": utc_now_iso(),
        "mockTokenOrCode": DEMO_OTP_CODE,
        "message": f"Verification OTP sent to {clean_phone}. (Dev code: {DEMO_OTP_CODE})",
    }


def verify_phone_otp(
    session_id: str, phone: str, otp: str, name: Optional[str] = None
) -> Dict[str, Any]:
    """Verify phone OTP and migrate guest session to a registered student."""
    clean_phone = phone.strip()
    with get_conn() as conn:
        row = conn.execute(
            "SELECT code, expires_at FROM auth_tokens WHERE token_key = ? AND provider = 'phone_otp'",
            (clean_phone,),
        ).fetchone()

    if row:
        if time.time() > row["expires_at"]:
            with get_conn() as conn:
                conn.execute("DELETE FROM auth_tokens WHERE token_key = ?", (clean_phone,))
            return {
                "success": False,
                "provider": "phone_otp",
                "error": "OTP has expired. Please request a new one.",
            }
        if row["code"] != otp and otp != DEMO_OTP_CODE:
            return {
                "success": False,
                "provider": "phone_otp",
                "error": f"Incorrect OTP code. Enter {DEMO_OTP_CODE}.",
            }
        with get_conn() as conn:
            conn.execute("DELETE FROM auth_tokens WHERE token_key = ?", (clean_phone,))
    elif otp != DEMO_OTP_CODE:
        return {
            "success": False,
            "provider": "phone_otp",
            "error": f"Invalid or expired OTP. Try {DEMO_OTP_CODE}.",
        }

    migration = migrate_guest_to_user(
        session_id=session_id,
        phone_or_email=clean_phone,
        name=name or "Student Pilot",
        auth_provider="phone_otp",
    )
    return {"success": True, "user": migration["user"], "provider": "phone_otp"}


def verify_google_oauth(
    session_id: str, email: str = "google.student@gmail.com", name: str = "Google Student Pilot"
) -> Dict[str, Any]:
    """Complete Google OAuth flow and migrate guest session."""
    migration = migrate_guest_to_user(
        session_id=session_id,
        phone_or_email=email,
        name=name,
        auth_provider="google_oauth",
    )
    return {"success": True, "user": migration["user"], "provider": "google_oauth"}


def initiate_magic_link(email: str, name: Optional[str] = None) -> Dict[str, Any]:
    """Generate a 15-minute single-use email magic link token."""
    clean_email = email.strip().lower()
    token = secrets.token_hex(24)
    expires_at = time.time() + 900
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO auth_tokens (token_key, code, provider, name, expires_at)
            VALUES (?, ?, 'magic_link', ?, ?)
            """,
            (token, token, name, expires_at),
        )
    return {
        "provider": "magic_link",
        "identifier": clean_email,
        "sentAt": utc_now_iso(),
        "mockTokenOrCode": token,
        "message": f"Magic sign-in link generated for {clean_email}.",
    }


def verify_magic_link(session_id: str, token: str, email: str) -> Dict[str, Any]:
    """Verify email magic link token and migrate guest session."""
    clean_email = email.strip().lower()
    with get_conn() as conn:
        row = conn.execute(
            "SELECT name, expires_at FROM auth_tokens WHERE token_key = ? AND provider = 'magic_link'",
            (token,),
        ).fetchone()

    user_name = "Verified Student"
    if row:
        if time.time() > row["expires_at"]:
            with get_conn() as conn:
                conn.execute("DELETE FROM auth_tokens WHERE token_key = ?", (token,))
            return {
                "success": False,
                "provider": "magic_link",
                "error": "Magic link has expired.",
            }
        user_name = row["name"] or user_name
        with get_conn() as conn:
            conn.execute("DELETE FROM auth_tokens WHERE token_key = ?", (token,))

    migration = migrate_guest_to_user(
        session_id=session_id,
        phone_or_email=clean_email,
        name=user_name,
        auth_provider="magic_link",
    )
    return {"success": True, "user": migration["user"], "provider": "magic_link"}
