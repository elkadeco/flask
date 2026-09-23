from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True)
class Identity:
    authenticated: bool
    user_id: str | None = None
    email: str | None = None
    token: str | None = None


@dataclass
class AgentContext:
    message: str
    locale: str
    project_type: str | None
    answers: dict[str, Any]
    owner_user_id: str | None
    brief_id: str | None
    conversation_key: str
    external_session_id: str | None = None


@dataclass
class AgentReply:
    acknowledgment: str
    next_question: str
    suggestions: list[str] = field(default_factory=list)
    field_id: str | None = None
    ready_for_review: bool = False
    external_session_id: str | None = None
    runtime: str | None = None


class AuthPort(Protocol):
    def resolve(self, bearer_token: str | None) -> Identity: ...


class BriefRepositoryPort(Protocol):
    def list_briefs(self, identity: Identity) -> list[dict[str, Any]]: ...
    def create_brief(self, identity: Identity, payload: dict[str, Any]) -> dict[str, Any]: ...
    def get_brief(self, identity: Identity, brief_id: str) -> dict[str, Any] | None: ...
    def update_brief(self, identity: Identity, brief_id: str, payload: dict[str, Any]) -> dict[str, Any] | None: ...
    def add_room(self, identity: Identity, brief_id: str, payload: dict[str, Any]) -> dict[str, Any]: ...
    def add_geometry(self, identity: Identity, brief_id: str, payload: dict[str, Any]) -> dict[str, Any]: ...
    def export_user_bundle(self, identity: Identity) -> dict[str, Any]: ...


class AIOrchestratorPort(Protocol):
    runtime_name: str
    def respond(self, context: AgentContext) -> AgentReply: ...
    def health(self) -> dict[str, Any]: ...


class StoragePort(Protocol):
    def health(self) -> dict[str, Any]: ...


class GeometryPort(Protocol):
    def health(self) -> dict[str, Any]: ...
