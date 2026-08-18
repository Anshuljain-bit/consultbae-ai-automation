from __future__ import annotations

import uuid
from pathlib import Path

from flask import Flask, jsonify, request, send_file, send_from_directory
from flask_cors import CORS
from sqlalchemy import select
from werkzeug.utils import secure_filename

if __package__ is None or __package__ == "":
    import sys

    sys.path.append(str(Path(__file__).resolve().parent.parent))
    from backend.audio_analysis import analyze_audio
    from backend.config import BASE_DIR, FLASK_HOST, FLASK_PORT, MAX_UPLOAD_MB, UPLOAD_DIR
    from backend.db import Base, engine, session_scope
    from backend.models import AudioSubmission, Person, PersonPhone
    from backend.normalize import display_name, normalize_name, normalize_phone
else:
    from .audio_analysis import analyze_audio
    from .config import BASE_DIR, FLASK_HOST, FLASK_PORT, MAX_UPLOAD_MB, UPLOAD_DIR
    from .db import Base, engine, session_scope
    from .models import AudioSubmission, Person, PersonPhone
    from .normalize import display_name, normalize_name, normalize_phone


DIST_DIR = BASE_DIR / "frontend" / "dist"


def create_app() -> Flask:
    app = Flask(__name__, static_folder=str(DIST_DIR), static_url_path="")
    app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_MB * 1024 * 1024
    CORS(app)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)

    @app.get("/api/health")
    def health():
        return jsonify({"ok": True})

    @app.get("/api/submissions")
    def list_submissions():
        with session_scope() as session:
            submissions = session.scalars(select(AudioSubmission).order_by(AudioSubmission.created_at.desc())).all()
            return jsonify([serialize_submission(item) for item in submissions])

    @app.post("/api/submissions")
    def create_submission():
        name = display_name(request.form.get("name"))
        normalized = normalize_name(name)
        phone = normalize_phone(request.form.get("phone"))
        upload = request.files.get("audio")
        if not normalized or not name:
            return jsonify({"error": "Name is required."}), 400
        if not phone:
            return jsonify({"error": "A valid Indian phone number is required."}), 400
        if upload is None or upload.filename == "":
            return jsonify({"error": "Audio file is required."}), 400

        original_filename = secure_filename(upload.filename) or "audio-upload"
        suffix = Path(original_filename).suffix.lower() or ".webm"
        stored_filename = f"{uuid.uuid4().hex}{suffix}"
        storage_path = UPLOAD_DIR / stored_filename
        upload.save(storage_path)

        try:
            metrics = analyze_audio(storage_path)
        except Exception as exc:
            storage_path.unlink(missing_ok=True)
            return jsonify({"error": str(exc)}), 422

        with session_scope() as session:
            person = find_or_create_person(session, name=name, normalized_name=normalized, phone=phone)
            submission = AudioSubmission(
                person_id=person.id,
                name=name,
                normalized_name=normalized,
                phone_e164=phone,
                original_filename=original_filename,
                stored_filename=stored_filename,
                storage_path=str(storage_path),
                content_type=upload.content_type,
                **metrics,
            )
            session.add(submission)
            session.flush()
            payload = serialize_submission(submission)
        return jsonify(payload), 201

    @app.delete("/api/submissions/<int:submission_id>")
    def delete_submission(submission_id: int):
        with session_scope() as session:
            submission = session.get(AudioSubmission, submission_id)
            if not submission:
                return jsonify({"error": "Submission not found."}), 404
            storage_path = Path(submission.storage_path)
            session.delete(submission)

        storage_path.unlink(missing_ok=True)
        return jsonify({"deleted": True, "id": submission_id})

    @app.get("/api/audio/<int:submission_id>")
    def get_audio(submission_id: int):
        with session_scope() as session:
            submission = session.get(AudioSubmission, submission_id)
            if not submission:
                return jsonify({"error": "Audio not found."}), 404
            path = Path(submission.storage_path)
            if not path.exists():
                return jsonify({"error": "Stored audio file is missing."}), 404
            return send_file(path, mimetype=submission.content_type or "application/octet-stream")

    @app.get("/")
    def index():
        if DIST_DIR.exists():
            return send_from_directory(DIST_DIR, "index.html")
        return jsonify({"message": "Run the Vite dev server or build frontend/dist first."})

    @app.get("/<path:path>")
    def frontend(path: str):
        if DIST_DIR.exists() and (DIST_DIR / path).exists():
            return send_from_directory(DIST_DIR, path)
        if DIST_DIR.exists():
            return send_from_directory(DIST_DIR, "index.html")
        return jsonify({"message": "Frontend build not found."}), 404

    return app


def find_or_create_person(session, name: str, normalized_name: str, phone: str) -> Person:
    phone_match = session.scalar(select(PersonPhone).where(PersonPhone.phone_e164 == phone))
    if phone_match:
        person = phone_match.person
        if len(name) > len(person.full_name):
            person.full_name = name
        return person

    person = Person(
        full_name=name,
        normalized_name=normalized_name,
        primary_phone=phone,
    )
    session.add(person)
    session.flush()
    session.add(PersonPhone(person_id=person.id, phone_e164=phone))
    return person


def serialize_submission(submission: AudioSubmission) -> dict:
    return {
        "id": submission.id,
        "person_id": submission.person_id,
        "name": submission.name,
        "phone": submission.phone_e164,
        "original_filename": submission.original_filename,
        "audio_url": f"/api/audio/{submission.id}",
        "duration_seconds": submission.duration_seconds,
        "sample_rate_khz": submission.sample_rate_khz,
        "sample_rate_hz": submission.sample_rate_hz,
        "bitrate_kbps": submission.bitrate_kbps,
        "loudness_db": submission.loudness_db,
        "quality_estimate": submission.quality_estimate,
        "noise_estimate": submission.noise_estimate,
        "analysis_notes": submission.analysis_notes,
        "created_at": submission.created_at.isoformat() if submission.created_at else None,
    }


app = create_app()


if __name__ == "__main__":
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=True)
