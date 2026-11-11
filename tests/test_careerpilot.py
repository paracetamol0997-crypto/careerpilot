"""End-to-end tests for CareerPilot AI (Python + Flask + SQLite)."""

from __future__ import annotations

import io
import json
from pathlib import Path

import pytest

from app import create_app
from careerpilot.ai.hybrid_retrieval import perform_hybrid_retrieval
from careerpilot.services.storage_service import EICAR_SIGNATURE


@pytest.fixture()
def client(tmp_path: Path):
    db_path = tmp_path / "test_careerpilot.db"
    upload_dir = tmp_path / "uploads"
    app = create_app(
        {
            "TESTING": True,
            "INSTANCE_DIR": tmp_path,
            "DATABASE_PATH": db_path,
            "UPLOAD_DIR": upload_dir,
        }
    )
    with app.test_client() as test_client:
        yield test_client


def test_pages_render_200(client):
    for route in ("/", "/chat", "/dashboard", "/admin"):
        resp = client.get(route)
        assert resp.status_code == 200
        assert b"CareerPilot" in resp.data


def test_health_and_initial_state(client):
    health = client.get("/api/health")
    assert health.status_code == 200
    assert health.get_json()["framework"] == "flask"

    state_resp = client.get("/api/state")
    assert state_resp.status_code == 200
    state = state_resp.get_json()
    assert state["isRegistered"] is False
    assert len(state["messages"]) == 1
    assert state["featureFlags"]["lockAtsMistakes2and3"] is True


def test_chat_streaming_and_profile_inference(client):
    resp = client.post(
        "/api/chat",
        json={"message": "I am in CSE 3rd year targeting Python Developer"},
    )
    assert resp.status_code == 200
    assert len(resp.data.decode("utf-8").strip()) > 10

    state = client.get("/api/state").get_json()
    assert state["profile"]["branch"] == "CSE"
    assert state["profile"]["year"] == "3"
    assert state["profile"]["targetRole"] == "Python Developer"


def test_resume_ats_audit_and_fabrication_guard(client):
    bad = client.post(
        "/api/resume",
        json={"resumeText": "I want to add fake experience at Google for 3 years"},
    )
    assert bad.status_code == 200
    bad_json = bad.get_json()
    assert bad_json["score"] == 30
    assert "Fabricated" in bad_json["mistakes"][0]["title"]

    good = client.post(
        "/api/resume",
        json={
            "resumeText": (
                "RAHUL VERMA — PYTHON BACKEND ENGINEER\n"
                "Education: B.Tech in Computer Science and Engineering (2023 - 2027), CGPA 8.1/10.\n"
                "Skills: Python, Flask, FastAPI, Django ORM, SQLite, PostgreSQL, Microservices, "
                "Data Pipelines, Multithreading, API Integration, Automated Testing, Git, Docker.\n"
                "Projects:\n"
                "1. High-Throughput Campus API Gateway: Engineered 12 REST endpoints using Flask and FastAPI, "
                "serving 1500+ active students with 45ms median response time and 99% uptime across 3 semesters.\n"
                "2. Automated Resume ETL Pipeline: Built multithreaded Python data pipelines processing 200+ PDF files "
                "with 38% faster throughput and 95% pytest automated testing coverage.\n"
                "Experience: Backend Engineering Intern at ZetaScale — optimized 8 slow SQL queries, cutting database CPU load by 30%."
                "Coursework: Data Structures, Algorithms, Operating Systems, Database Management Systems, Software Engineering, "
                "Object Oriented Programming, Computer Networks, Distributed Systems, Web Security, Cloud Computing Fundamentals."
            ),
            "targetRole": "python-developer",
        },
    )
    assert good.status_code == 200
    good_json = good.get_json()
    assert good_json["score"] >= 80
    assert len(good_json["mistakes"]) == 3
    assert good_json["mistakes"][0]["isLocked"] is False
    assert good_json["mistakes"][1]["isLocked"] is True


def test_roadmap_generation_task_toggle_and_registration_unlock(client):
    rm_resp = client.post("/api/roadmap", json={"targetRoleKey": "python-developer"})
    assert rm_resp.status_code == 200
    rm = rm_resp.get_json()
    assert len(rm["weeks"]) == 12
    assert rm["weeks"][0]["isLocked"] is False
    assert rm["weeks"][2]["isLocked"] is True

    toggled = client.post(
        "/api/roadmap/toggle-task",
        json={"weekNumber": 1, "taskId": "task-w1-1"},
    ).get_json()
    assert toggled["weeks"][0]["tasks"][0]["completed"] is True
    assert toggled["progressPercent"] > 0

    # Register via Phone OTP 7890 -> migrates guest & unlocks weeks 3-12
    client.post("/api/auth/phone/initiate", json={"phone": "+91 98765 43210"})
    verify = client.post(
        "/api/auth/phone/verify",
        json={"phone": "+91 98765 43210", "otp": "7890", "name": "Prince"},
    )
    assert verify.status_code == 200
    assert verify.get_json()["success"] is True

    state = client.get("/api/state").get_json()
    assert state["isRegistered"] is True
    assert state["user"]["name"] == "Prince"
    assert all(wk["isLocked"] is False for wk in state["roadmap"]["weeks"])


def test_jobs_ranking_save_and_scam_report(client):
    jobs_resp = client.post(
        "/api/jobs",
        json={"userSkills": ["Python", "SQL", "Flask"]},
    )
    assert jobs_resp.status_code == 200
    jobs = jobs_resp.get_json()["jobs"]
    assert len(jobs) == 25
    assert jobs[0]["isScamSuspicious"] is False
    assert jobs[-1]["isScamSuspicious"] is True

    saved = client.post("/api/jobs/save", json={"job": jobs[0]}).get_json()
    assert len(saved["savedJobs"]) == 1

    rep = client.post("/api/jobs/report", json={"jobId": "job-22-scam"})
    assert rep.status_code == 200


def test_mock_interview_flow(client):
    q_resp = client.get("/api/interview/questions?roleId=python-developer")
    assert q_resp.status_code == 200
    questions = q_resp.get_json()["questions"]
    assert len(questions) >= 5

    eval_resp = client.post(
        "/api/interview",
        json={
            "sessionId": "test_sess",
            "roleId": "python-developer",
            "answers": [
                {
                    "questionId": q["id"],
                    "userAnswer": (
                        "Specifically, I built a scalable Python Flask backend with indexed SQLite "
                        "because decorators and immutable tuples helped keep routing clean."
                    ),
                    "timeSpentSeconds": 35,
                }
                for q in questions
            ],
        },
    )
    assert eval_resp.status_code == 200
    report = eval_resp.get_json()
    assert 1 <= report["overallScore"] <= 10
    assert len(report["strengths"]) == 3


def test_upload_security_magic_bytes_eicar_and_download(client):
    # Invalid binary signature rejected
    bad_bin = client.post(
        "/api/upload",
        data={"file": (io.BytesIO(b"\x00\x01\x02\x03\xff\xfe"), "evil.exe")},
        content_type="multipart/form-data",
    )
    assert bad_bin.status_code == 422

    # EICAR malware signature rejected
    eicar = client.post(
        "/api/upload",
        data={"file": (io.BytesIO(EICAR_SIGNATURE + b" hello"), "../../eicar.txt")},
        content_type="multipart/form-data",
    )
    assert eicar.status_code == 422
    assert eicar.get_json()["securityCheck"]["isMalwareClean"] is False

    # Valid plain text resume accepted + path traversal sanitized + downloadable
    valid = client.post(
        "/api/upload",
        data={"file": (io.BytesIO(b"Education: B.Tech CSE. Skills: Python, Flask, SQL."), "../../my resume.txt")},
        content_type="multipart/form-data",
    )
    assert valid.status_code == 200
    v_json = valid.get_json()
    assert v_json["securityCheck"]["sanitizedFilename"] == "my_resume.txt"
    assert "Python" in v_json["extractedText"]

    dl = client.get(v_json["signedUrl"])
    assert dl.status_code == 200
    assert b"Flask" in dl.data


def test_dpdp_controls_admin_flags_and_hybrid_retrieval(client):
    c_resp = client.post(
        "/api/dashboard/consent",
        json={"dataProcessing": True, "whatsappUpdates": True, "modelTraining": False},
    )
    assert c_resp.status_code == 200
    assert c_resp.get_json()["consents"]["whatsappUpdates"] is True

    exp = client.get("/api/dashboard/export")
    assert exp.status_code == 200
    exported = json.loads(exp.data.decode("utf-8"))
    assert exported["consents"]["whatsappUpdates"] is True

    flag_resp = client.post(
        "/api/admin/flags",
        json={"key": "lockAtsMistakes2and3", "value": False},
    )
    assert flag_resp.status_code == 200
    assert flag_resp.get_json()["featureFlags"]["lockAtsMistakes2and3"] is False

    retrieval = perform_hybrid_retrieval("python flask fastapi", target_role="python-developer", top_k=4)
    assert len(retrieval["chunks"]) == 4
    assert all(cid.startswith("res-") for cid in retrieval["citedIds"])


def test_static_assets_and_vercel_tmp_fallback(client, monkeypatch):
    css_resp = client.get("/static/css/styles.css")
    assert css_resp.status_code == 200
    js_resp = client.get("/static/js/app.js")
    assert js_resp.status_code == 200

    from careerpilot.config import resolve_instance_dir
    import tempfile

    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.delenv("CAREERPILOT_INSTANCE_DIR", raising=False)
    resolved = resolve_instance_dir()
    assert str(resolved).startswith(tempfile.gettempdir())
