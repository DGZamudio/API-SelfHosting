from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from app.database import Base

class Song(Base):
    __tablename__ = "songs"

    id = Column(Integer, primary_key=True)
    yt_video_id = Column(String, unique=True, nullable=False, index=True)
    title = Column(String, nullable=False)
    status = Column(String, default="pending")
    local_path = Column(String, nullable=True)
    source_url = Column(String, nullable=False)
    added_at = Column(DateTime, server_default=func.now())
    downloaded_at = Column(DateTime, nullable=True)

    artist_id = Column(Integer, ForeignKey("artists.id"))
    album_id = Column(Integer, ForeignKey("albums.id"))

    artist = relationship("Artist", back_populates="songs")
    album = relationship("Album", back_populates="songs")