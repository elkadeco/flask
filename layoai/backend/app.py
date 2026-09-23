from pathlib import Path
import hashlib
import re
import uuid
from flask import Flask, jsonify, request, send_from_directory
from dotenv import load_dotenv

load_dotenv()

from config import settings, SUPPORTED_LOCALES, DEFAULT_LOCALE
from auth import require_user, require_designer, resolve_identity
from supabase_rest import rest
from ai_agent import run_intake_agent_sync
from geometry import bp as geometry_bp

FRONTEND = (Path(__file__).resolve().parent.parent / "frontend").resolve()
app = Flask(__name__, static_folder=None)
app.config["SECRET_KEY"] = settings.secret_key
app.register_blueprint(geometry_bp)

def brief_expand(token, brief):
    bid = brief["id"]
    rooms = rest("GET", "layo_rooms", token, params={
        "select": "id,name,count,area,priority,notes",
        "brief_id": f"eq.{bid}",
        "order": "created_at.asc",
    }) or []
    files = rest("GET", "layo_uploads", token, params={
        "select": "id,filename,category,status,size_bytes,content_type,storage_path",
        "brief_id": f"eq.{bid}",
        "order": "created_at.asc",
    }) or []
    geometry = rest("GET", "layo_geometry_models", token, params={
        "select": "*",
        "brief_id": f"eq.{bid}",
        "order": "updated_at.desc",
    }) or []
    return {**brief, "rooms": rooms, "files": files, "geometry": geometry}

@app.get("/api/health")
def health():
    return jsonify({
        "ok": True,
        "app": "LayoAI",
        "auth_configured": True,
        "database_configured": True,
        "geometry_configured": True,
        "ai_configured": bool(settings.openai_api_key),
        "storage_configured": settings.storage_provider == "supabase",
    })

@app.get("/api/locales")
def locales():
    return jsonify({"default": DEFAULT_LOCALE, "locales": SUPPORTED_LOCALES})

@app.get("/api/briefs")
@require_user
def list_briefs():
    identity = resolve_identity()
    rows = rest("GET", "layo_briefs", identity["token"], params={
        "select": "*",
        "order": "updated_at.desc",
    }) or []
    return jsonify({"briefs": rows})

@app.post("/api/briefs")
@require_user
def create_brief():
    identity = resolve_identity()
    payload = request.get_json(silent=True) or {}
    body = {
        "owner_user_id": identity["user_id"],
        "project_type": payload.get("project_type"),
        "project_name": payload.get("project_name"),
        "locale": payload.get("locale") if payload.get("locale") in SUPPORTED_LOCALES else DEFAULT_LOCALE,
        "status": payload.get("status", "draft"),
        "answers": payload.get("answers") or {},
        "reviewed": bool(payload.get("reviewed")),
        "submission_consent": bool(payload.get("submission_consent")),
    }
    rows = rest("POST", "layo_briefs", identity["token"], json_body=body, prefer="return=representation") or []
    return jsonify(rows[0]), 201

@app.get("/api/briefs/<brief_id>")
@require_user
def get_brief(brief_id):
    identity = resolve_identity()
    rows = rest("GET", "layo_briefs", identity["token"], params={
        "select": "*", "id": f"eq.{brief_id}", "limit": "1"
    }) or []
    if not rows:
        return jsonify({"error": "not_found"}), 404
    return jsonify(brief_expand(identity["token"], rows[0]))

@app.patch("/api/briefs/<brief_id>")
@require_user
def update_brief(brief_id):
    identity = resolve_identity()
    payload = request.get_json(silent=True) or {}
    allowed = {
        key: payload[key]
        for key in ("project_type", "project_name", "locale", "status", "answers", "reviewed", "submission_consent")
        if key in payload
    }
    rows = rest("PATCH", "layo_briefs", identity["token"], params={"id": f"eq.{brief_id}"},
                json_body=allowed, prefer="return=representation") or []
    if not rows:
        return jsonify({"error": "not_found"}), 404
    return jsonify(rows[0])

@app.post("/api/briefs/<brief_id>/rooms")
@require_user
def add_room(brief_id):
    identity = resolve_identity()
    payload = request.get_json(silent=True) or {}
    name = (payload.get("name") or "").strip()
    if not name:
        return jsonify({"error": "room_name_required"}), 400
    body = {
        "brief_id": brief_id,
        "owner_user_id": identity["user_id"],
        "name": name,
        "count": payload.get("count"),
        "area": payload.get("area"),
        "priority": payload.get("priority") or "Must have",
        "notes": payload.get("notes"),
    }
    rows = rest("POST", "layo_rooms", identity["token"], json_body=body, prefer="return=representation") or []
    return jsonify(rows[0]), 201

@app.post("/api/uploads/prepare")
@require_user
def prepare_upload():
    identity = resolve_identity()
    payload = request.get_json(silent=True) or {}
    brief_id = str(payload.get("brief_id") or "")
    filename = str(payload.get("filename") or "file").strip()
    if not brief_id:
        return jsonify({"error": "brief_id_required"}), 400
    safe = re.sub(r"[^A-Za-z0-9._-]+", "_", filename)[:160] or "file"
    object_name = f"{identity['user_id']}/{brief_id}/{uuid.uuid4()}_{safe}"
    return jsonify({
        "bucket": settings.storage_bucket,
        "path": object_name,
        "max_upload_mb": settings.max_upload_mb,
        "upload_url": settings.supabase_url + "/storage/v1/object/" + settings.storage_bucket + "/" + object_name,
        "method": "POST",
    })

@app.post("/api/ai/intake")
def ai_intake():
    if not settings.openai_api_key:
        return jsonify({
            "error": "ai_not_configured",
            "fallback": "Continue with prepared choices; your draft remains available.",
        }), 503
    payload = request.get_json(silent=True) or {}
    message = (payload.get("message") or "").strip()
    if not message:
        return jsonify({"error": "message_required"}), 400
    identity = resolve_identity()
    raw = payload.get("session_id") or request.headers.get("X-Layo-Session") or "guest"
    session_id = (
        f"user:{identity['user_id']}:{raw}"
        if identity["authenticated"]
        else "guest:" + hashlib.sha256(raw.encode()).hexdigest()[:24]
    )
    try:
        reply = run_intake_agent_sync(
            message=message,
            session_id=session_id,
            project_type=payload.get("project_type"),
            locale=payload.get("locale") or DEFAULT_LOCALE,
            answers=payload.get("answers") or {},
        )
        return jsonify(reply.model_dump())
    except Exception as exc:
        return jsonify({
            "error": "ai_unavailable",
            "fallback": "Continue with prepared answer choices.",
            "detail": exc.__class__.__name__,
        }), 503

@app.get("/api/designer/briefs")
@require_designer
def designer_briefs():
    identity = resolve_identity()
    rows = rest("GET", "layo_briefs", identity["token"], params={
        "select": "id,project_type,project_name,locale,status,updated_at",
        "order": "updated_at.desc",
    }) or []
    return jsonify({"briefs": rows})

@app.get("/")
def index():
    target = FRONTEND / "index.html"
    if target.exists():
        return send_from_directory(FRONTEND, "index.html")
    return jsonify({"app": "LayoAI", "status": "live-integration-backend", "api": "/api/health"})

@app.get("/<path:path>")
def spa(path):
    target = FRONTEND / path
    if target.exists() and target.is_file():
        return send_from_directory(FRONTEND, path)
    index = FRONTEND / "index.html"
    if index.exists():
        return send_from_directory(FRONTEND, "index.html")
    return jsonify({"error": "frontend_not_bundled"}), 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
