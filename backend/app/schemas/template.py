from datetime import datetime

from pydantic import BaseModel


class TemplateCreate(BaseModel):
    name: str
    aircraft_type: str
    difficulty: str = "basic"
    config: dict


class TemplateUpdate(BaseModel):
    name: str | None = None
    aircraft_type: str | None = None
    difficulty: str | None = None
    config: dict | None = None


class TemplateResponse(BaseModel):
    id: str
    name: str
    aircraft_type: str
    difficulty: str
    config: dict
    is_builtin: bool
    created_by: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
