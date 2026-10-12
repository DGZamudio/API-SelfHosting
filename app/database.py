from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import URL_MUSIC

engine_music = create_engine(
    URL_MUSIC,
    connect_args={"check_same_thread": False}
)

# Activar soporte de Foreign Keys en SQLite
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_music)

Base = declarative_base()

def get_music_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
