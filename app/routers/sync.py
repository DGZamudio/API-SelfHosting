from fastapi import APIRouter, BackgroundTasks, HTTPException, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from zipstream import ZipStream
from app.config import SONGS_DOWNLOADS_FOLDER
from app.schemas.song import SongCreate
from app.services import song_service, ytdlp_service
from app.database import get_db

router = APIRouter(
    prefix="/sync",
    tags=["sync"]
)

@router.get("/")
def sync_device(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    songs = song_service.list_songs(db, status="pending")
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