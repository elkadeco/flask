# LayoAI modular scaffold v1.8

This branch adds a reviewable LayoAI application structure on top of the connected Flask/Railway repository.

## Reused from this repository
- Flask application boundary
- Gunicorn deployment
- Railway deployment pattern

## Added for LayoAI
- 15-locale registry with English fallback and RTL metadata
- Supabase bearer-token verification boundary
- Customer brief persistence contract
- Customer save/resume endpoints
- Room data model
- OpenAI Agents SDK intake route
- Persistent agent-session contract
- Designer-protected brief list
- Truthful health/readiness endpoint
- File-storage adapter boundary
- CI scaffold and architecture notes

This is a development scaffold, not production certification. No secrets are stored here.
