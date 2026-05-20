from pydantic import BaseModel
from typing import Optional, Dict, Any


class TemplateCreate(BaseModel):
    name: str
    aircraft_type: str
    difficulty: str
    config: Dict[str, Any]


class TemplateUpdate(BaseModel):
    name: Optional[str] = None
    aircraft_type: Optional[str] = None
    difficulty: Optional[str] = None
    config: Optional[Dict[str, Any]] = None


class TemplateOut(BaseModel):
    id: str
    name: str
    aircraft_type: str
    difficulty: str
    config: Dict[str, Any]
    is_builtin: bool = False
    created_by: Optional[str] = None
    created_at: Optional[str] = None

    class Config:
        from_attributes = True
