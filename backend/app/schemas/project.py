from datetime import datetime

from pydantic import BaseModel


class ProjectCreate(BaseModel):
    name: str
    description: str | None = None


class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class ProjectResponse(BaseModel):
    id: str
    name: str
    description: str | None = None
    created_by: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MemberAdd(BaseModel):
    user_id: str
    role: str = "viewer"


class MemberResponse(BaseModel):
    id: str
    user_id: str
    project_id: str
    role: str

    model_config = {"from_attributes": True}
