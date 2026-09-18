from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import URL_MUSIC

engine_music = create_engine(
    URL_MUSIC
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_music)

Base = declarative_base()

def get_music_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
