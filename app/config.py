import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv("../.env")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)

# Database
DB_MUSIC_NAME = "music_db"
DB_USERNAME = os.getenv('DB_USERNAME')
DB_PASSWORD = os.getenv('DB_PASSWORD')

def ensure_database_exists(db_name: str):
    """Se conecta a la DB por defecto 'postgres' y crea la nueva DB si no existe."""
    default_url = f"postgresql+psycopg2://{DB_USERNAME}:{DB_PASSWORD}@localhost:5432/postgres"

    engine = create_engine(
        default_url
    )

    with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        result = conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :dbname"),
            {"dbname": db_name}
        )
        if not result.scalar():
            conn.execute(text(f'CREATE DATABASE "{db_name}"'))

ensure_database_exists(DB_MUSIC_NAME)
URL_MUSIC = f"postgresql+psycopg2://{DB_USERNAME}:{DB_PASSWORD}@localhost:5432/{DB_MUSIC_NAME}"

# Folders
DOWNLOADS_FOLDER = os.getenv('DOWNLOADS_FOLDER', os.path.join(PROJECT_ROOT, "downloads"))
TEMP_DOWNLOADS_FOLDER = os.path.join(DOWNLOADS_FOLDER, "temp")
SONGS_DOWNLOADS_FOLDER = os.path.join(DOWNLOADS_FOLDER, "songs")
THUMBNAILS_DOWNLOADS_FOLDER = os.path.join(DOWNLOADS_FOLDER, "thumbnails")
