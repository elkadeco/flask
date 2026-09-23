import asyncio
from pydantic import BaseModel, Field
from agents import Agent, Runner
from agents.extensions.memory import SQLAlchemySession
from config import settings

class IntakeReply(BaseModel):
    acknowledgment: str
    next_question: str
    suggestions: list[str] = Field(default_factory=list)
    field_id: str | None = None
    ready_for_review: bool = False

INSTRUCTIONS = """You are LayoAI, an architectural design-intake assistant.
Ask exactly one useful question at a time.
Prefer 2-6 short selectable suggestions before free typing.
Adapt to project type, locale, prior answers and contradictions.
Do not repeat known information.
Never invent dimensions, budget, dates, ownership, approvals or names.
Accept 'Not sure yet'.
Reply in the user's current message language.
Keep free text in the user's language.
"""

async def _run(message, session_id, project_type, locale, answers):
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured")
    kwargs = {
        "name": "LayoAI Intake",
        "instructions": INSTRUCTIONS,
        "output_type": IntakeReply,
    }
    if settings.openai_model:
        kwargs["model"] = settings.openai_model
    agent = Agent(**kwargs)
    session = SQLAlchemySession.from_url(
        session_id,
        url=settings.agent_database_url,
        create_tables=True,
        ensure_ascii=False,
    )
    prompt = str({
        "locale": locale,
        "project_type": project_type,
        "known_answers": answers,
        "user_message": message,
    })
    result = await Runner.run(agent, prompt, session=session)
    return result.final_output

def run_intake_agent_sync(**kwargs):
    return asyncio.run(_run(**kwargs))
