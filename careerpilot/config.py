"""Configuration helpers for CareerPilot AI."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent


def resolve_instance_dir() -> Path:
    """Use /tmp on Vercel (read-only deployment bundle) and ./instance locally."""
    custom = os.getenv("CAREERPILOT_INSTANCE_DIR", "").strip()
    if custom:
        return Path(custom)
    if os.getenv("VERCEL") or os.getenv("VERCEL_ENV"):
        return Path(tempfile.gettempdir()) / "careerpilot_instance"
    return BASE_DIR / "instance"


class Config:
    """Application configuration loaded from environment variables."""

    SECRET_KEY: str = os.getenv("FLASK_SECRET_KEY", "careerpilot-dev-secret-key")
    INSTANCE_DIR: Path = resolve_instance_dir()
    DATABASE_PATH: Path = Path(
        os.getenv("CAREERPILOT_DB_PATH") or (INSTANCE_DIR / "careerpilot.db")
    )
    UPLOAD_DIR: Path = INSTANCE_DIR / "uploads"
    MAX_UPLOAD_BYTES: int = 5 * 1024 * 1024  # 5 MB per PRD
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "").strip()
