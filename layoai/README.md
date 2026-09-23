# LayoAI live integration v1.9

This branch is now connected to the existing LayoAI Supabase project at the application-contract level.

## Live foundation completed
- Supabase project restored.
- Customer portal tables created with Row Level Security.
- Private `layoai-private` Storage bucket created with per-user folder policies.
- Email OTP-compatible authentication boundary.
- Customer brief cloud save/resume endpoints.
- Rooms and file metadata contracts.
- Server-side OpenAI Agents SDK intake endpoint with persistent session adapter.
- 15-language locale registry with English fallback and RTL metadata.
- Designer access remains allowlist-protected.
- Health endpoint truthfully reports readiness.

## Still needs deployment environment configuration
- Finish secure OpenAI API key setup and set `OPENAI_API_KEY` on the hosting service.
- Set `OPENAI_MODEL` after model/task evaluation.
- Add the approved designer email(s) to `DESIGNER_EMAIL_ALLOWLIST`.
- The current v1.9 wired visual shell is delivered separately as an artifact and should be copied to `layoai/frontend/index.html` in the deployment bundle.

SMS/WhatsApp verification is not enabled. No fake success state is used.
