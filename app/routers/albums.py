from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_music_db
from app.schemas.song import PaginationParams
from app.services import song_service

router = APIRouter(
    prefix="/albums",
    tags=["albums"]
)

@router.get("/")
def list_albums(
    pagination: PaginationParams,
    db: Session = Depends(get_music_db)
):
    return song_service.list_albums(db, pagination)
