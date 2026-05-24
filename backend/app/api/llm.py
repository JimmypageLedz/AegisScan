from fastapi import APIRouter

from app.config import settings
from app.schemas.llm import ModelListRead
from app.services.llm_service import list_available_models

router = APIRouter(prefix="/llm", tags=["llm"])

FALLBACK_MODELS = [
    "gpt-5.4",
    "gpt-5.4-mini",
    "gpt-5.5",
    "gpt-4.1",
    "gpt-4.1-mini",
]


def _fallback_models() -> list[str]:
    models = [settings.openai_model, *FALLBACK_MODELS]
    return list(dict.fromkeys(model for model in models if model))


@router.get("/models", response_model=ModelListRead)
def get_models():
    try:
        models = list_available_models()
    except RuntimeError as exc:
        return ModelListRead(
            models=_fallback_models(),
            default_model=settings.openai_model or None,
            source="fallback",
            warning=str(exc),
        )

    return ModelListRead(
        models=models,
        default_model=settings.openai_model or None,
        source="remote",
    )
