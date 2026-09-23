# LayoAI Provider Portability Contract v3.0

## Principle

**OpenAI manages intelligence; LayoAI owns the product, project facts, geometry, files, workflow state, and provider interfaces.**

No business-critical project record is authoritative only inside an OpenAI session, Supabase table, Railway service, or another vendor-specific resource.

## Current development phase

- AI provider: OpenAI
- AI runtime: OpenAI managed Agents API
- Data adapter: Supabase
- Auth adapter: Supabase
- Geometry: LayoAI geometry engine
- Storage: provider-neutral adapter boundary

## Exit path

Provider changes are configuration changes behind ports:

- `LAYO_AI_RUNTIME=managed_agents_api` — OpenAI manages the agent session/harness.
- `LAYO_AI_RUNTIME=agents_sdk` — the OpenAI Agents SDK runs inside LayoAI's own server.
- `LAYO_DATA_PROVIDER=supabase` — current Supabase REST/RLS adapter.
- `LAYO_DATA_PROVIDER=sqlalchemy` — standard SQL database, including PostgreSQL.
- `LAYO_AUTH_PROVIDER=supabase` — current auth adapter.
- `LAYO_STORAGE_PROVIDER=disabled|local|future-s3` — replaceable storage port.

Frontend API routes remain stable when providers change.

## Data ownership

Canonical LayoAI project data includes:
- client preferences
- briefs and answers
- rooms and spaces
- geometry and area verification
- file metadata
- submission and confirmation state

OpenAI session IDs are references, not the system of record.

The portable export contract is `LAYO-BUNDLE-1.0`.

## OpenAI migration

During development, the managed Agents API keeps session progress. LayoAI stores the external session ID as a reference.

For later independence, switch to the Agents SDK runtime and an application-owned session database. The frontend, core project schema, and client portal do not need redesign.
