from datetime import datetime
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

class ArtistSchema(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

class AlbumSchema(BaseModel):
    id: int
    title: str
    artist: ArtistSchema | None = None
    songs: list[SongSchema] = []
    yt_playlist_id: str | None = None
    thumbnail: str | None = None

    class Config:
        from_attributes = True

class SongSchema(BaseModel):
    id: int
    yt_video_id: str | None = None
    title: str
    added_at: datetime | None = None
    status: SongStatus
    source_url: HttpUrl
    downloaded_at: datetime | None = None

    class Config:
        from_attributes = True
