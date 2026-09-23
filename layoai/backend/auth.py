from functools import wraps
from flask import g, jsonify, request
from supabase import create_client
from config import settings

_supabase = (
    create_client(settings.supabase_url, settings.supabase_publishable_key)
    if settings.supabase_url and settings.supabase_publishable_key
    else None
)

def _bearer_token():
    header = request.headers.get("Authorization", "")
    return header[7:].strip() if header.lower().startswith("bearer ") else None

def resolve_identity():
    if hasattr(g, "identity"):
        return g.identity
    token = _bearer_token()
    if not token or not _supabase:
        g.identity = {"authenticated": False, "user_id": None, "email": None}
        return g.identity
    try:
        response = _supabase.auth.get_user(token)
        user = getattr(response, "user", None)
        if not user:
            raise ValueError("No user")
        g.identity = {
            "authenticated": True,
            "user_id": str(user.id),
            "email": (getattr(user, "email", None) or "").lower() or None,
        }
    except Exception:
        g.identity = {"authenticated": False, "user_id": None, "email": None}
    return g.identity

def require_user(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        identity = resolve_identity()
        if not identity["authenticated"]:
            return jsonify({"error": "authentication_required"}), 401
        return fn(*args, **kwargs)
    return wrapper

def require_designer(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        identity = resolve_identity()
        if not identity["authenticated"]:
            return jsonify({"error": "authentication_required"}), 401
        if not identity["email"] or identity["email"] not in settings.designer_emails:
            return jsonify({"error": "designer_access_required"}), 403
        return fn(*args, **kwargs)
    return wrapper
