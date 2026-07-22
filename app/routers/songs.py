from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.schemas.song import SongCreate
from app.services import ytdlp_service, song_service
from app.database import get_db

router = APIRouter(
    prefix="/songs",
    tags=["songs"]
)

@router.post("/")
def add_song(song: SongCreate, preview: bool = Query(False), db: Session = Depends(get_db)):
    metadata = ytdlp_service.get_song_metadata(song.url)
    result = None
    if not preview:
        result = song_service.add_song_from_metadata(db, metadata)
        if not result:
            raise HTTPException(status_code=409, detail="Esta canción ya existe en el registro")
    return {'result':result, 'metadata':metadata}

@router.get("/")
def list_songs(db: Session = Depends(get_db)):
    return song_service.list_songs(db)

@router.post("/download")
def descargar_cancion(song: SongCreate):
    res = ytdlp_service.download_song(str(song.url), temp=True)
    if res.get('path'):
        return FileResponse(
            path=res['path'],
            media_type="audio/mpeg",
            filename=f"{res['metadata'].get('title')}.mp3"
        )
    else:
        raise HTTPException(status_code=400, detail="Hubo un error descargando la canción")