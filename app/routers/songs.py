from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.song import SongCreate
from app.services import song_service, ytdlp_service

router = APIRouter(
    prefix="/songs",
    tags=["songs"]
)

@router.post("/")
def add_song(song: SongCreate, background_tasks: BackgroundTasks, preview: bool = Query(False), db: Session = Depends(get_db)):
    data = ytdlp_service.get_song_metadata(song.url)

    if preview:
        return {"type": data["type"], "result": None, "metadata": data["metadata"]}

    background_tasks.add_task(ytdlp_service.download_song, str(song.url))

    if data["type"] == "album":
        result = song_service.add_songs_from_metadata(db, data["metadata"])
    else:
        result = song_service.add_song_from_metadata(db, data["metadata"][0])

    if not result:
        raise HTTPException(status_code=409, detail="Esta canción ya existe en el registro")

    return {"type": data["type"], "result": result, "metadata": data["metadata"]}

@router.get("/")
def list_songs(db: Session = Depends(get_db)):
    return song_service.list_songs(db)

@router.post("/download")
def descargar_cancion(song: SongCreate):
    res = ytdlp_service.download_song(str(song.url), temp=True)

    if res["type"] == "album":
        raise HTTPException(
            status_code=400,
            detail="Este endpoint solo descarga canciones individuales, no álbumes completos"
        )

    if not res.get("path"):
        raise HTTPException(status_code=400, detail="Hubo un error descargando la canción")

    return FileResponse(
        path=res["path"],
        media_type="audio/mpeg",
        filename=f"{res['metadata'].get('title')}.mp3"
    )
