import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

def test_locale_contract():
    from config import DEFAULT_LOCALE, SUPPORTED_LOCALES
    assert DEFAULT_LOCALE == "en"
    assert SUPPORTED_LOCALES["ar"]["dir"] == "rtl"
    assert SUPPORTED_LOCALES["fa"]["dir"] == "rtl"
    assert SUPPORTED_LOCALES["ur"]["dir"] == "rtl"

def test_health_contract():
    from app import app
    client = app.test_client()
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.get_json()
    assert body["app"] == "LayoAI"
    assert "ai_configured" in body
    assert "auth_configured" in body
