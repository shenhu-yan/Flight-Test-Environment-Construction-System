from datetime import datetime

from pydantic import BaseModel


class UserCreate(BaseModel):
    username: str
    password: str
    global_role: str = "viewer"


class UserUpdate(BaseModel):
    username: str | None = None
    password: str | None = None
    global_role: str | None = None


class UserResponse(BaseModel):
    id: str
    username: str
    global_role: str
    created_at: datetime

    model_config = {"from_attributes": True}


class LoginRequest(BaseModel):
    username: str
    password: str
