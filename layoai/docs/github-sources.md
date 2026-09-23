# GitHub sources used for structure decisions

- Connected account repository: `elkadeco/flask`
  - Flask + Gunicorn + Railway deployment skeleton.
- Official OpenAI repository: `openai/openai-agents-python`
  - Agent + Runner pattern.
  - SQLAlchemySession for persistent agent memory.
- Official Supabase repository: `supabase/supabase-py`
  - Server-side `auth.get_user(jwt)` identity verification.
- Official Flask-Babel repository: `python-babel/flask-babel`
  - Reference point for future server-rendered localization if/when the frontend moves from static catalogs.

No third-party code is copied wholesale. The scaffold uses public API patterns and keeps provider credentials server-side.
