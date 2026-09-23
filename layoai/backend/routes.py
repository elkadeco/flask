import hashlib
from flask import Blueprint, jsonify, request
from sqlalchemy import select

from ai_agent import run_intake_agent_sync
from auth import require_designer, require_user, resolve_identity
from config import DEFAULT_LOCALE, SUPPORTED_LOCALES, settings
from db import Brief, Room, SessionLocal

bp = Blueprint("api", __name__)

def brief_json(brief):
    return {
        "id": brief.id,
        "project_type": brief.project_type,
        "project_name": brief.project_name,
        "locale": brief.locale,
        "status": brief.status,
        "answers": brief.answers or {},
        "reviewed": brief.reviewed,
        "submission_consent": brief.submission_consent,
        "rooms": [
            {
                "id": r.id, "name": r.name, "count": r.count,
                "area": r.area, "priority": r.priority, "notes": r.notes
            } for r in brief.rooms
        ],
        "updated_at": brief.updated_at.isoformat(),
    }

@bp.get("/api/health")
def health():
    return jsonify({
        "ok": True,
        "app": "LayoAI",
        "ai_configured": bool(settings.openai_api_key),
        "auth_configured": bool(settings.supabase_url and settings.supabase_publishable_key),
        "storage_configured": settings.storage_provider != "disabled",
    })

@bp.get("/api/locales")
def locales():
    return jsonify({"default": DEFAULT_LOCALE, "locales": SUPPORTED_LOCALES})

@bp.get("/api/briefs")
@require_user
def list_briefs():
    identity = resolve_identity()
    with SessionLocal() as db:
        items = db.scalars(
            select(Brief)
            .where(Brief.owner_user_id == identity["user_id"])
            .order_by(Brief.updated_at.desc())
        ).all()
        return jsonify({"briefs": [brief_json(item) for item in items]})

@bp.post("/api/briefs")
@require_user
def create_brief():
    identity = resolve_identity()
    payload = request.get_json(silent=True) or {}
    locale = payload.get("locale", DEFAULT_LOCALE)
    if locale not in SUPPORTED_LOCALES:
        locale = DEFAULT_LOCALE
    brief = Brief(
        owner_user_id=identity["user_id"],
        project_type=payload.get("project_type"),
        project_name=payload.get("project_name"),
        locale=locale,
        answers=payload.get("answers") or {},
    )
    with SessionLocal() as db:
        db.add(brief)
        db.commit()
        db.refresh(brief)
        return jsonify(brief_json(brief)), 201

@bp.patch("/api/briefs/<brief_id>")
@require_user
def update_brief(brief_id):
    identity = resolve_identity()
    payload = request.get_json(silent=True) or {}
    allowed = {"project_type", "project_name", "locale", "answers", "reviewed", "submission_consent", "status"}
    with SessionLocal() as db:
        brief = db.get(Brief, brief_id)
        if not brief or brief.owner_user_id != identity["user_id"]:
            return jsonify({"error": "not_found"}), 404
        for key in allowed:
            if key in payload:
                setattr(brief, key, payload[key])
        db.commit()
        db.refresh(brief)
        return jsonify(brief_json(brief))

@bp.post("/api/briefs/<brief_id>/rooms")
@require_user
def add_room(brief_id):
    identity = resolve_identity()
    payload = request.get_json(silent=True) or {}
    name = (payload.get("name") or "").strip()
    if not name:
        return jsonify({"error": "room_name_required"}), 400
    with SessionLocal() as db:
        brief = db.get(Brief, brief_id)
        if not brief or brief.owner_user_id != identity["user_id"]:
            return jsonify({"error": "not_found"}), 404
        room = Room(
            brief_id=brief.id,
            name=name,
            count=str(payload.get("count")) if payload.get("count") is not None else None,
            area=str(payload.get("area")) if payload.get("area") is not None else None,
            priority=payload.get("priority") or "Must have",
            notes=payload.get("notes"),
        )
        db.add(room)
        db.commit()
        db.refresh(brief)
        return jsonify(brief_json(brief)), 201

@bp.post("/api/ai/intake")
def ai_intake():
    if not settings.openai_api_key:
        return jsonify({
            "error": "ai_not_configured",
            "fallback": "Continue with prepared choices; preserve the user's draft."
        }), 503
    payload = request.get_json(silent=True) or {}
    message = (payload.get("message") or "").strip()
    if not message:
        return jsonify({"error": "message_required"}), 400
    identity = resolve_identity()
    raw_session = payload.get("session_id") or request.headers.get("X-Layo-Session") or "guest"
    if identity["authenticated"]:
        session_id = f"user:{identity['user_id']}:{raw_session}"
    else:
        digest = hashlib.sha256(raw_session.encode("utf-8")).hexdigest()[:24]
        session_id = f"guest:{digest}"
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

@bp.post("/api/uploads/prepare")
@require_user
def prepare_upload():
    if settings.storage_provider == "disabled":
        return jsonify({
            "status": "not_configured",
            "max_upload_mb": settings.max_upload_mb,
            "message": "Connect the approved storage adapter before enabling file bytes."
        }), 501
    return jsonify({"status": "adapter_required"}), 501

@bp.get("/api/designer/briefs")
@require_designer
def designer_briefs():
    with SessionLocal() as db:
        items = db.scalars(select(Brief).order_by(Brief.updated_at.desc())).all()
        return jsonify({"briefs": [brief_json(item) for item in items]})
