# LayoAI migration runbook

## Supabase to standard PostgreSQL / SQLAlchemy
1. Export client projects using the provider-neutral bundle contract.
2. Configure `DATABASE_URL`.
3. Switch `LAYO_DATA_PROVIDER=sqlalchemy`.
4. Import into the new store through a reviewed migration utility.
5. Compare project, room, geometry and file-metadata counts.
6. Keep the prior database read-only during the rollback window.

## OpenAI managed Agents API to Agents SDK
1. Keep `OPENAI_API_KEY` server-side.
2. Configure an application-owned `AGENT_DATABASE_URL`.
3. Switch `LAYO_AI_RUNTIME=agents_sdk`.
4. Keep project facts unchanged.
5. New conversations use LayoAI-owned session memory.
6. Historical managed session IDs may remain as audit references.
7. Run multilingual, geometry, validation and handoff regression tests before cutover.

## Hosting
LayoAI remains a conventional server application. Railway is an optional host, not a product dependency. The same app can later run on another WSGI/container/VM platform.
