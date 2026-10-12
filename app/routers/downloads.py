import os

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Path, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from starlette.responses import FileResponse
from zipstream import ZipStream

from app.config import SONGS_DOWNLOADS_FOLDER
from app.database import get_music_db
from app.schemas.song import SongStatus
from app.services import song_service, ytdlp_service
from app.services.file_service import create_m3u_playlist

router = APIRouter(
    prefix="/downloads",
    tags=["downloads"]
)

@router.get("/music")
def sync_device(background_tasks: BackgroundTasks, db: Session = Depends(get_music_db)):
    songs = song_service.list_songs(db, status=SongStatus.pending).get("items", [])
    yt_ids = []

    for song in songs:
        ytdlp_service.download_song(str(song.source_url))
        yt_ids.append(str(song.yt_video_id))

    zs = ZipStream.from_path(SONGS_DOWNLOADS_FOLDER)

    background_tasks.add_task(song_service.mark_songs, db, yt_ids)

    return StreamingResponse(
        iter(zs),
        media_type="application/zip",
        headers={
            "Content-Disposition": "attachment; filename=sync.zip",
            "Content-Length": str(len(zs)),
            "Last-Modified": zs.last_modified.strftime('%Y-%m-%d %H:%M:%S')
        }
    )

@router.get("/playlists/{playlist_id}")
def download_playlist(
    background_tasks: BackgroundTasks,
    playlist_id: int = Path(...),
    playlist_name: str = Query(...),
    db: Session = Depends(get_music_db)
):
    songs = song_service.get_playlist_songs(db, playlist_id)

    if not songs:
        return HTTPException(404, detail="No se encontraron canciónes")

    m3u_path = create_m3u_playlist(list(songs))

    background_tasks.add_task(os.remove, m3u_path)

    return FileResponse(
        path=m3u_path,
        media_type="audio/x-mpegurl",
        filename=f"{playlist_name}.m3u",
        background=background_tasks
    )
