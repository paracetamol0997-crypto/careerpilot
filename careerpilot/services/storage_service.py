"""Secure resume upload pipeline: magic-byte verification, malware hook, disk storage, and text extraction."""

from __future__ import annotations

import io
import os
import re
import time
import uuid
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from flask import current_app

from careerpilot.db import get_conn, utc_now_iso

EICAR_SIGNATURE = b"X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"
DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def validate_magic_bytes(data: bytes) -> Tuple[bool, str]:
    """Validate file signature via leading magic bytes or UTF-8/ASCII text check."""
    if not data or len(data) < 4:
        return False, "unknown"

    if data[:4] == b"%PDF":
        return True, "application/pdf"

    if data[:4] == b"PK\x03\x04":
        return True, DOCX_MIME

    sample = data[:512]
    try:
        decoded = sample.decode("utf-8")
        if all(ch.isprintable() or ch in "\t\n\r" for ch in decoded):
            return True, "text/plain"
    except UnicodeDecodeError:
        pass

    return False, "application/octet-stream"


def sanitize_filename(filename: str) -> str:
    """Strip path traversal prefixes and unsafe characters."""
    if not filename:
        return f"resume_{int(time.time())}.pdf"
    base = re.sub(r"^.*[\\/]", "", filename)
    cleaned = re.sub(r"[^a-zA-Z0-9.\-_]", "_", base)
    return (cleaned or "resume.txt")[:100]


def scan_buffer_for_malware(data: bytes) -> Tuple[bool, Optional[str]]:
    """Inspect buffer for EICAR test string or suspicious executable hooks."""
    head = data[:2048]
    if EICAR_SIGNATURE in head:
        return False, "EICAR_Test_Signature_Detected"

    head_text = head.decode("utf-8", errors="ignore")
    if "<script>malicious_payload" in head_text or "cmd.exe /c" in head_text:
        return False, "Suspicious_Executable_Hook"

    return True, None


def extract_resume_text(data: bytes, mime_type: str) -> str:
    """Extract readable resume text from PDF, DOCX, or plain text uploads."""
    if mime_type == "text/plain":
        return data.decode("utf-8", errors="replace").strip()

    if mime_type == "application/pdf":
        try:
            from pypdf import PdfReader  # type: ignore

            reader = PdfReader(io.BytesIO(data))
            pages = [page.extract_text() or "" for page in reader.pages]
            return "\n".join(pages).strip()
        except Exception:
            return ""

    if mime_type == DOCX_MIME:
        try:
            from docx import Document  # type: ignore

            doc = Document(io.BytesIO(data))
            lines = [p.text for p in doc.paragraphs if p.text.strip()]
            return "\n".join(lines).strip()
        except Exception:
            return ""

    return ""


def process_secure_upload(
    file_bytes: bytes, raw_filename: str, max_size_bytes: int = 5 * 1024 * 1024
) -> Dict[str, Any]:
    """Run size check, magic-byte validation, sanitization, malware scan, and disk persistence."""
    clean_name = sanitize_filename(raw_filename)

    if len(file_bytes) > max_size_bytes:
        mb = len(file_bytes) / (1024 * 1024)
        return {
            "securityCheck": {
                "isValid": False,
                "detectedMimeType": "unknown",
                "sanitizedFilename": clean_name,
                "fileSizeBytes": len(file_bytes),
                "isMalwareClean": True,
                "error": f"File size exceeds 5 MB limit (actual: {mb:.2f} MB)",
            }
        }

    is_valid_sig, mime_type = validate_magic_bytes(file_bytes)
    if not is_valid_sig:
        return {
            "securityCheck": {
                "isValid": False,
                "detectedMimeType": mime_type,
                "sanitizedFilename": clean_name,
                "fileSizeBytes": len(file_bytes),
                "isMalwareClean": True,
                "error": "Invalid file signature. Only valid PDF, DOCX, and TXT resumes are supported.",
            }
        }

    is_clean, threat_name = scan_buffer_for_malware(file_bytes)
    if not is_clean:
        return {
            "securityCheck": {
                "isValid": False,
                "detectedMimeType": mime_type,
                "sanitizedFilename": clean_name,
                "fileSizeBytes": len(file_bytes),
                "isMalwareClean": False,
                "malwareScanNotes": f"Threat detected: {threat_name}",
                "error": f"Security alert: {threat_name}. Upload rejected.",
            }
        }

    upload_dir = Path(current_app.config["UPLOAD_DIR"])
    upload_dir.mkdir(parents=True, exist_ok=True)
    storage_key = f"resumes/{uuid.uuid4().hex}_{clean_name}"
    safe_disk_name = storage_key.replace("/", "__")
    disk_path = upload_dir / safe_disk_name
    disk_path.write_bytes(file_bytes)

    now = utc_now_iso()
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO uploaded_files (file_key, original_filename, content_type, size_bytes, disk_path, uploaded_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (storage_key, clean_name, mime_type, len(file_bytes), str(disk_path), now),
        )

    extracted_text = extract_resume_text(file_bytes, mime_type)

    return {
        "securityCheck": {
            "isValid": True,
            "detectedMimeType": mime_type,
            "sanitizedFilename": clean_name,
            "fileSizeBytes": len(file_bytes),
            "isMalwareClean": True,
        },
        "storedFile": {
            "fileKey": storage_key,
            "originalFilename": clean_name,
            "contentType": mime_type,
            "sizeBytes": len(file_bytes),
            "uploadedAt": now,
            "signedUrl": f"/api/upload?key={storage_key}",
        },
        "extractedText": extracted_text,
    }


def get_stored_file(file_key: str) -> Optional[Tuple[bytes, str, str]]:
    """Retrieve stored file bytes, content type, and filename by file_key."""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT original_filename, content_type, disk_path FROM uploaded_files WHERE file_key = ?",
            (file_key,),
        ).fetchone()
    if not row:
        return None
    path = Path(row["disk_path"])
    if not path.exists():
        return None
    return path.read_bytes(), row["content_type"], row["original_filename"]
