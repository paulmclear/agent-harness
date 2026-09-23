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

load_dotenv()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="L2_", extra="ignore")

    default_model: str = "openai:gpt-5.4"
    output_dir: Path = Path("var/output")

    # first-pass KB search (kb_lookup node)
    kb_lookup_limit: int = 3

    openai_api_key: SecretStr | None = Field(
        default=None, validation_alias="OPENAI_API_KEY"
    )


@cache
def get_settings() -> Settings:
    return Settings()
