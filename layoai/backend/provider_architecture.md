# Provider architecture

LayoAI core must not import provider SDKs directly.

Adapters implement the provider ports for:
- OpenAI managed Agents API
- OpenAI Agents SDK
- Supabase auth/data
- standard SQLAlchemy/PostgreSQL
- replaceable storage
- local geometry analysis

The managed OpenAI runtime is the preferred development runtime. The Agents SDK runtime is the later self-hosted migration path.

Provider selection is environment-driven. No client-facing route should change when a provider is replaced.
