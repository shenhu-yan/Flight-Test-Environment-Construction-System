from pydantic import BaseModel
from typing import Optional, Dict, Any


class ModelCreate(BaseModel):
    project_id: str
    name: str
    type: str
    description: Optional[str] = None


class ModelOut(BaseModel):
    id: str
    project_id: str
    name: str
    type: str
    status: str
    description: Optional[str] = None
    current_version: str
    created_by: Optional[str] = None
    created_at: Optional[str] = None

    class Config:
        from_attributes = True


class ModelVersionOut(BaseModel):
    id: str
    model_id: str
    version: str
    storage_path: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    download_count: int = 0
    created_at: Optional[str] = None

    class Config:
        from_attributes = True
