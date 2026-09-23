import os
from dataclasses import dataclass

SUPPORTED_LOCALES = {
    "en": {"name": "English", "dir": "ltr"},
    "ar": {"name": "العربية", "dir": "rtl"},
    "fa": {"name": "فارسی", "dir": "rtl"},
    "es": {"name": "Español", "dir": "ltr"},
    "fr": {"name": "Français", "dir": "ltr"},
    "de": {"name": "Deutsch", "dir": "ltr"},
    "it": {"name": "Italiano", "dir": "ltr"},
    "pt": {"name": "Português", "dir": "ltr"},
    "ru": {"name": "Русский", "dir": "ltr"},
    "tr": {"name": "Türkçe", "dir": "ltr"},
    "zh-CN": {"name": "简体中文", "dir": "ltr"},
    "ja": {"name": "日本語", "dir": "ltr"},
    "ko": {"name": "한국어", "dir": "ltr"},
    "hi": {"name": "हिन्दी", "dir": "ltr"},
    "ur": {"name": "اردو", "dir": "rtl"},
}
DEFAULT_LOCALE = "en"

@dataclass(frozen=True)
class Settings:
    secret_key: str = os.getenv("SECRET_KEY", "dev-only-change-me")
    supabase_url: str = os.getenv("SUPABASE_URL", "https://tcthfufpqfzfuzjoycma.supabase.co")
    supabase_publishable_key: str = os.getenv("SUPABASE_PUBLISHABLE_KEY", "sb_publishable_WGjEJesxClMtNJPgDwXbyg_tGs6HdGK")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "")
    agent_database_url: str = os.getenv("AGENT_DATABASE_URL", "sqlite+aiosqlite:///layoai_agent_sessions.db")
    designer_email_allowlist: str = os.getenv("DESIGNER_EMAIL_ALLOWLIST", "")
    storage_provider: str = os.getenv("STORAGE_PROVIDER", "supabase")
    storage_bucket: str = os.getenv("STORAGE_BUCKET", "layoai-private")
    max_upload_mb: int = int(os.getenv("MAX_UPLOAD_MB", "20"))

    @property
    def designer_emails(self):
        return {x.strip().lower() for x in self.designer_email_allowlist.split(",") if x.strip()}

settings = Settings()
