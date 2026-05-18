from datetime import datetime

from pydantic import BaseModel


class ModelCreate(BaseModel):
    project_id: str
    name: str
    type: str
    description: str | None = None


class ModelUpdate(BaseModel):
    name: str | None = None
    type: str | None = None
    status: str | None = None
    description: str | None = None


class ModelResponse(BaseModel):
    id: str
    project_id: str
    name: str
    type: str
    status: str
    description: str | None = None
    current_version: int
    created_by: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ModelVersionResponse(BaseModel):
    id: str
    model_id: str
    version: int
    storage_path: str
    metadata: dict | None = None
    download_count: int
    created_at: datetime

    model_config = {"from_attributes": True}


class ModelVersionCreate(BaseModel):
    storage_path: str
    metadata: dict | None = None


class ModelDiffRequest(BaseModel):
    version_a: int
    version_b: int
