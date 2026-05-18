from pydantic import BaseModel
from typing import Any, Generic, TypeVar, List


T = TypeVar("T")


class ResponseModel(BaseModel, Generic[T]):
    code: int = 0
    message: str = "success"
    data: T | None = None

    class Config:
        arbitrary_types_allowed = True


class PaginatedResponse(BaseModel, Generic[T]):
    code: int = 0
    message: str = "success"
    data: List[Any] = []
    total: int = 0
    page: int = 1
    page_size: int = 20

    class Config:
        arbitrary_types_allowed = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
