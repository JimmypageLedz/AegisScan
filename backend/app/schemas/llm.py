from pydantic import BaseModel


class ModelListRead(BaseModel):
    models: list[str]
    default_model: str | None = None
    source: str = "remote"
    warning: str | None = None
