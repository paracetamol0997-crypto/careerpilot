"""Configuration helpers for CareerPilot AI."""

from __future__ import annotations

import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent


class Config:
    """Application configuration loaded from environment variables."""

    SECRET_KEY: str = os.getenv("FLASK_SECRET_KEY", "careerpilot-dev-secret-key")
    INSTANCE_DIR: Path = BASE_DIR / "instance"
    DATABASE_PATH: Path = Path(
        os.getenv("CAREERPILOT_DB_PATH") or (INSTANCE_DIR / "careerpilot.db")
    )
    UPLOAD_DIR: Path = INSTANCE_DIR / "uploads"
    MAX_UPLOAD_BYTES: int = 5 * 1024 * 1024  # 5 MB per PRD
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "").strip()
