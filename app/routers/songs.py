from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.schemas.song import SongCreate
from app.services import ytdlp_service, song_service
from app.database import get_db

router = APIRouter(
    prefix="/songs",
    tags=["songs"]
)

@router.post("/")
def add_song(song: SongCreate, db: Session = Depends(get_db)):
    metadata = ytdlp_service.get_song_metadata(song.url)
    result = song_service.add_song_from_metadata(db, metadata)
    if not result:
        raise HTTPException(status_code=409, detail="Esta canción ya existe en el registro")
    return result

@router.get("/")
def list_songs(db: Session = Depends(get_db)):
    return song_service.list_songs(db)

# @router.delete("/{song_id}")
# def delete_song(song_id: int):
#     return song_service.delete_song(song_id)