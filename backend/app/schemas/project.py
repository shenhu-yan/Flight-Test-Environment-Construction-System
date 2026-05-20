from pydantic import BaseModel
from typing import Optional


class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class ProjectOut(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    created_by: Optional[str] = None
    created_at: Optional[str] = None

    class Config:
        from_attributes = True


class TaskCreate(BaseModel):
    name: str
    description: Optional[str] = None


class TaskUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class TaskOut(BaseModel):
    id: str
    project_id: str
    name: str
    description: Optional[str] = None
    created_by: Optional[str] = None
    created_at: Optional[str] = None

    class Config:
        from_attributes = True


class MemberAdd(BaseModel):
    user_id: str
    role: str = "viewer"
