# LayoAI architecture mapping

## Shared Core
- Supabase authentication boundary
- customer/design-role separation
- multilingual registry with English fallback
- OpenAI Agents SDK server-side route
- SQLAlchemy persistence
- Railway deployment contract
- health/readiness reporting
- file-storage adapter boundary

## LayoAI app-specific modules
- architectural project-type taxonomy
- one-question-at-a-time brief
- adaptive answer suggestions
- room editor
- file metadata and future private storage
- customer save/resume portal
- designer brief review

## Protected boundary
Public discovery and local draft entry can work without registration.
Cloud save/resume, uploads and designer access require authenticated identity.

## Not LIVE in this scaffold
Production secrets, live OTP delivery, real file storage, full CRM, notifications,
rate limiting, backups, observability and release certification.
