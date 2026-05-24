import json
from pathlib import Path
import tomllib

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AegisScan API"
    app_debug: bool = True
    database_url: str = "sqlite:///./aegisscan.db"
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"
    openai_api_key: str = ""
    openai_base_url: str = ""
    openai_model: str=""
    llm_mode: str = "mock"
    llm_timeout_seconds: int = 30

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()


def _load_codex_config() -> dict:
    codex_dir = Path.home() / ".codex"
    config_path = codex_dir / "config.toml"
    auth_path = codex_dir / "auth.json"

    data: dict = {
        "openai_api_key": "",
        "openai_base_url": "",
        "openai_model": "",
    }

    if config_path.exists():
        try:
            with config_path.open("rb") as file:
                config_data = tomllib.load(file)

            provider_name = config_data.get("model_provider")
            providers = config_data.get("model_providers", {})
            provider_config = providers.get(provider_name, {}) if provider_name else {}

            data["openai_base_url"] = provider_config.get("base_url", "") or ""
            data["openai_model"] = config_data.get("model", "") or ""
        except (OSError, tomllib.TOMLDecodeError):
            pass

    if auth_path.exists():
        try:
            with auth_path.open("r", encoding="utf-8") as file:
                auth_data = json.load(file)

            data["openai_api_key"] = auth_data.get("OPENAI_API_KEY", "") or ""
        except (OSError, json.JSONDecodeError):
            pass

    return data


_codex_config = _load_codex_config()

if not settings.openai_api_key:
    settings.openai_api_key = _codex_config.get("openai_api_key", "")

if not settings.openai_base_url:
    settings.openai_base_url = _codex_config.get("openai_base_url", "")

if not settings.openai_model:
    settings.openai_model = _codex_config.get("openai_model", "")
