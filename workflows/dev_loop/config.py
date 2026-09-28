"""Settings for the dev_loop workflow.

Override any field with an env var prefixed ``DEV_LOOP_``, e.g.
``DEV_LOOP_DEFAULT_MODEL=openai:gpt-5-mini``. ``.env`` is loaded here, on
first import, so every module that reads settings sees it.
"""

from functools import cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="DEV_LOOP_", extra="ignore")

    default_model: str = "openai:gpt-5.4"
    output_dir: Path = Path("var/output")

    openai_api_key: SecretStr | None = Field(
        default=None, validation_alias="OPENAI_API_KEY"
    )


@cache
def get_settings() -> Settings:
    return Settings()
