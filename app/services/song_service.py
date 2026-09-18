from sqlalchemy import func, update
from sqlalchemy.orm import Session

from app.models.album import Album
from app.models.artist import Artist
from app.models.song import Song
from app.schemas.song import PaginationParams, SongStatus


def list_songs(db: Session, pagination: PaginationParams | None = None, status: SongStatus | None = None): #response_model=PaginatedResponse[SongRead]
    query = db.query(Song)

    if status:
        query = query.filter(Song.status == status)

    total = query.count()

    songs = None

    if pagination:
        offset = (pagination.page - 1) * pagination.page_size
        songs = query.offset(offset).limit(pagination.page_size).all()
    else:
        songs = query.all()

    return {
        "items": songs,
        "total": total,
        "page": pagination.page if pagination else -1,
        "page_size": pagination.page_size if pagination else -1,
    }

def list_albums(db: Session, pagination: PaginationParams):
    query = db.query(Album)

    total = query.count()

    offset = (pagination.page - 1) * pagination.page_size
    albums = query.offset(offset).limit(pagination.page_size).all()

    return {
        "items": albums,
        "total": total,
        "page": pagination.page,
        "page_size": pagination.page_size,
    }

def get_song_by_url(db: Session, url):
    song = db.query(Song).filter(Song.source_url == url).first()
    return song

def get_or_create_artist(db: Session, name: str) -> Artist:
    artist = db.query(Artist).filter(Artist.name == name).first()
    if artist:
        return artist
    artist = Artist(name=name)
    db.add(artist)
    db.flush()
    return artist


def get_or_create_album(db: Session, title: str, artist: Artist, yt_playlist_id: str | None) -> Album | None:
    if not title:
        return None
    album = db.query(Album).filter(Album.title == title, Album.artist_id == artist.id).first()
    if album:
        return album
    album = Album(title=title, artist=artist, yt_playlist_id=yt_playlist_id)
    db.add(album)
    db.flush()
    return album


def add_song_from_metadata(
    db: Session,
    metadata: dict
) -> Song | None:
    existing = db.query(Song).filter(Song.yt_video_id == metadata["video_id"]).first()
    if existing:
        return None

    artist = get_or_create_artist(db, metadata["artist"])
    album = get_or_create_album(db, metadata["album"], artist, yt_playlist_id=None) if metadata["album"] else None

    song = Song(
        yt_video_id=metadata["video_id"],
        title=metadata["title"],
        artist=artist,
        album=album,
        source_url=str(metadata["url"]),
        status="pending"
    )
    db.add(song)
    db.commit()
    db.refresh(song)
    return song

def add_songs_from_metadata(db: Session, songs: list[dict]) -> list[Song]:
    nuevas = []
    for cancion in songs:
        existing = db.query(Song).filter(Song.yt_video_id == cancion["video_id"]).first()
        if existing:
            continue

        artist = get_or_create_artist(db, cancion["artist"])
        album = (
            get_or_create_album(db, cancion["album"], artist, yt_playlist_id=None)
            if cancion.get("album")
            else None
        )

        nuevas.append(
            Song(
                yt_video_id=cancion["video_id"],
                title=cancion["title"],
                artist=artist,
                album=album,
                source_url=str(cancion["url"]),
                status="pending",
            )
        )

    if nuevas:
        db.add_all(nuevas)
        db.commit()
        for song in nuevas:
            db.refresh(song)

    return nuevas

def mark_songs(
    db: Session,
    ids: list[str],
    status: SongStatus = SongStatus.downloaded
):
    valores = {"status": status.value}

    if status == SongStatus.downloaded:
            valores["downloaded_at"] = func.now()

    _ = db.execute(
        update(Song).where(Song.yt_video_id.in_(ids)).values(**valores)
    )
    db.commit()
