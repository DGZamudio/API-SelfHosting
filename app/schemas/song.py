from enum import Enum
from typing import Generic, TypeVar

from pydantic import BaseModel, HttpUrl

T = TypeVar("T")

class SongCreate(BaseModel):
    url: HttpUrl

class SongRead(BaseModel):
    itm: str

class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int

class SongStatus(str, Enum):
    pending = "pending"
    downloaded = "downloaded"
    error = "error"

class PaginationParams(BaseModel):
    page     : int = 1
    page_size : int = 20
