from fastapi import (
    APIRouter,
    BackgroundTasks,
    Body,
    Depends,
    HTTPException,
    Path,
    Query,
)
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_music_db
from app.schemas.song import (
    AlbumSchema,
    ArtistSchema,
    PaginatedResponse,
    PaginationParams,
    SongCreate,
    SongSchema,
    SongStatus,
)
from app.services import song_service, ytdlp_service

router = APIRouter(
    prefix="/music",
    tags=["music"]
)

@router.post("/")
def add_music(
    song: SongCreate,
    background_tasks: BackgroundTasks,
    preview: bool = Query(False),
    db: Session = Depends(get_music_db)
):
    data = ytdlp_service.get_song_metadata(song.url)

    if preview:
        return {"type": data["type"], "result": None, "metadata": data["metadata"]}

    result = song_service.add_songs_from_metadata(
        db,
        data["metadata"],
        playlist=data["playlist"],
        yt_playlist_id=str(song.url) if data["type"] != "song" else None,
    )

    if not result:
        raise HTTPException(status_code=409, detail="Esta canción ya existe en el registro")

    background_tasks.add_task(ytdlp_service.background_download_task, data["metadata"])

    return {"type": data["type"], "result": result, "metadata": data["metadata"]}

@router.get("/songs", response_model=PaginatedResponse[SongSchema])
def list_songs(
    status: SongStatus | None = None,
    album: int | None = Query(None),
    page: int = Query(1),
    page_size: int = Query(20),
    db: Session = Depends(get_music_db)
):
    return song_service.list_songs(db, PaginationParams(page=page, page_size=page_size), status=status, album=album)

@router.get("/albums", response_model=PaginatedResponse[AlbumSchema])
def list_albums(
    page: int = Query(1),
    page_size: int = Query(20),
    db: Session = Depends(get_music_db)
):
    return song_service.list_albums(db, PaginationParams(page=page, page_size=page_size))

@router.get("/artists", response_model=PaginatedResponse[ArtistSchema])
def list_artists(
    page: int = Query(1),
    page_size: int = Query(20),
    db: Session = Depends(get_music_db)
):
    return song_service.list_artists(db, PaginationParams(page=page, page_size=page_size))

@router.get("/playlists")
def list_playlists(
    page: int = Query(1),
    page_size: int = Query(20),
    db: Session = Depends(get_music_db)
):
    return song_service.list_playlists(db, PaginationParams(page=page, page_size=page_size))

@router.get("/playlists/{playlist_id}")
def list_playlist_song(
    playlist_id: int = Path(...),
    db: Session = Depends(get_music_db)
):
    return song_service.get_playlist_songs(db, playlist_id)

@router.post("/playlists")
def add_playist(
    playlist_title: str = Query(...),
    songs: list[int] = Body(...),
    db: Session = Depends(get_music_db)
):
    playlist = song_service.get_or_create_playlist(db, playlist_title)
    if playlist:
        return song_service.add_songs_playlist(db, songs, playlist)

    return HTTPException(404, detail="Playlist no encontrada")

@router.post("/download")
def download_song(
    song: SongCreate
):
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
