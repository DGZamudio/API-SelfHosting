from pydantic import BaseModel, HttpUrl
from datetime import datetime
from enum import Enum

class SongCreate(BaseModel):
    url: HttpUrl

class SongStatus(str, Enum):
    pending = "pending"
    downloaded = "downloaded"
    error = "error"