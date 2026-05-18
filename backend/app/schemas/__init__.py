from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ResponseModel(BaseModel, Generic[T]):
    code: int = 0
    message: str = "success"
    data: T | None = None


class PaginatedResponse(BaseModel, Generic[T]):
    code: int = 0
    message: str = "success"
    data: list[T] = []
    total: int = 0
    page: int = 1
    page_size: int = 20


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
