from pydantic import BaseModel
from typing import Optional


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserCreate(BaseModel):
    username: str
    password: str
    global_role: str = "viewer"


class UserUpdate(BaseModel):
    username: Optional[str] = None
    global_role: Optional[str] = None


class UserOut(BaseModel):
    id: str
    username: str
    global_role: str
    created_at: Optional[str] = None

    class Config:
        from_attributes = True
