from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class Playlist(Base):
    __tablename__ = "playlists"

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    yt_playlist_id = Column(String, unique=True, nullable=True)

    song_playlists = relationship("SongPlaylist", back_populates="playlist")
