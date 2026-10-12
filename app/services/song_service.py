from pydantic import HttpUrl
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session, joinedload, selectinload

from app.models.album import Album
from app.models.artist import Artist
from app.models.playlist import Playlist
from app.models.song import Song
from app.models.song_playlist import SongPlaylist
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

    albums = (
            query
            .options(
                joinedload(Album.artist),
                selectinload(Album.songs)
            )
            .offset(offset)
            .limit(pagination.page_size)
            .all()
        )

    return {
        "items": albums,
        "total": total,
        "page": pagination.page,
        "page_size": pagination.page_size,
    }

def list_artists(db: Session, pagination: PaginationParams):
    query = db.query(Artist)

    total = query.count()

    offset = (pagination.page - 1) * pagination.page_size
    artists = (
        query
        .offset(offset).limit(pagination.page_size)
        .all()
    )

    return {
        "items": artists,
        "total": total,
        "page": pagination.page,
        "page_size": pagination.page_size,
    }

def list_playlists(db: Session, pagination: PaginationParams):
    query = db.query(Playlist)

    total = query.count()

    offset = (pagination.page - 1) * pagination.page_size
    playlists = (
        query
        .offset(offset)
        .limit(pagination.page_size)
        .all()
    )

    return {
        "items": playlists,
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

def get_or_create_playlist(db: Session, title: str, yt_playlist_id: str | None = None) -> Playlist | None:
    if not title:
        return None
    playlist = db.query(Playlist).filter(Playlist.title == title).first()
    if playlist:
        return playlist
    playlist = Playlist(title=title, yt_playlist_id=yt_playlist_id)
    db.add(playlist)
    db.flush()
    return playlist

def get_playlist_songs(db: Session, playlist_id: int):
    playlist = db.query(Playlist).where(Playlist.id == playlist_id).first()

    if not playlist:
        return None

    stmt = select(Song).join(SongPlaylist, Song.id == SongPlaylist.song_id).where(SongPlaylist.playlist_id == playlist.id)
    songs = db.scalars(stmt).all()

    return songs

def add_songs_playlist(db: Session, songs_ids: list[int], playlist: Playlist):
    if not songs_ids:
        return []

    songs = db.scalars(select(Song).where(Song.id.in_(songs_ids))).all()

    new_relations = [
        SongPlaylist(playlist=playlist, song=song)
        for song in songs
    ]

    if new_relations:
        db.add_all(new_relations)
        db.commit()

    return new_relations


def add_songs_from_metadata(db: Session, songs: list[dict], yt_playlist_id: str | None = None, playlist: str | None = None) -> list[Song]:
    nuevas = []
    to_playlist = []
    playlist_obj = None

    if playlist:
        playlist_obj = get_or_create_playlist(db, playlist, yt_playlist_id=yt_playlist_id)

    for cancion in songs:
        existing = db.query(Song).filter(Song.yt_video_id == cancion["video_id"]).first()
        if existing:
            continue

        artist = get_or_create_artist(db, cancion["artist"])
        album = (
            get_or_create_album(db, cancion["album"], artist, yt_playlist_id=yt_playlist_id)
            if cancion.get("album")
            else None
        )

        song = Song(
            yt_video_id=cancion["video_id"],
            title=cancion["title"],
            artist=artist,
            album=album,
            source_url=str(cancion["url"]),
            status="pending"
        )

        nuevas.append(song)

        if playlist_obj:
            to_playlist.append(
                SongPlaylist(
                    song=song,
                    playlist=playlist_obj
                )
            )

    if nuevas:
        db.add_all(nuevas)
    if to_playlist:
        db.add_all(to_playlist)

    if nuevas or to_playlist:
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
