"""Settings for the l2 workflow.

Override any field with an env var prefixed ``L2_``, e.g.
``L2_DEFAULT_MODEL=openai:gpt-5-mini``. ``.env`` is loaded here, on
first import, so every module that reads settings sees it.
"""

from functools import cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from workflows.practice.l2.models import SupportPriority

load_dotenv()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="L2_", extra="ignore")

    default_model: str = "openai:gpt-5.4"
    output_dir: Path = Path("var/output")

    # first-pass KB search (kb_lookup node)
    kb_lookup_limit: int = 3

    # fallback KB search (kb_search_agent node): max search_kb calls per ticket
    kb_agent_max_tool_calls: int = 3

    # human_action lane (build_triage_output): every condition must hold,
    # otherwise the ticket is marked needs_human_review
    action_min_category_confidence: float = 0.80
    action_min_priority_confidence: float = 0.70
    action_min_direct_articles: int = 1
    review_always_priorities: frozenset[SupportPriority] = frozenset(
        {SupportPriority.critical}
    )

    openai_api_key: SecretStr | None = Field(
        default=None, validation_alias="OPENAI_API_KEY"
    )


@cache
def get_settings() -> Settings:
    return Settings()
