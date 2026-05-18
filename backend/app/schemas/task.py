from datetime import datetime

from pydantic import BaseModel


class TaskCreate(BaseModel):
    name: str
    description: str | None = None


class TaskUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class TaskResponse(BaseModel):
    id: str
    project_id: str
    name: str
    description: str | None = None
    created_by: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
