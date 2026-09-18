from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.orm import relationship

from app.database import Base


class SongPlaylist(Base):
    __tablename__ = "songs_playlists"

    id = Column(Integer, primary_key=True)

    song_id = Column(Integer, ForeignKey("songs.id"))
    playlist_id = Column(Integer, ForeignKey("playlists.id"))

    song = relationship("Song", back_populates="song_playlists")
    playlist = relationship("Playlist", back_populates="song_playlists")
