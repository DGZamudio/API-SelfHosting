from typing import List
from sqlalchemy import bindparam, func, update
from sqlalchemy.orm import Session
from app.models.artist import Artist
from app.models.album import Album
from app.models.song import Song

def list_songs(db: Session, status: str | None = None):
    query = db.query(Song)
    if status:
        query = query.filter(Song.status == status)
    return query.all()

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

def mark_songs(
    db: Session,
    ids: List[str]
):
    result = db.execute(
        update(Song).where(Song.yt_video_id.in_(ids)).values(status="downloaded", downloaded_at=func.now())
    )
    db.commit()
    return result