from datetime import datetime
from enum import Enum

from pydantic import BaseModel, HttpUrl


class SongCreate(BaseModel):
    url: HttpUrl

class SongStatus(str, Enum):
    pending = "pending"
    downloaded = "downloaded"
    error = "error"
