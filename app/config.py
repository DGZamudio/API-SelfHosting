import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv("../.env")

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent

# Databases
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
os.makedirs(DATA_DIR, exist_ok=True)

# Music Database
DB_MUSIC_NAME = "music.db"
MUSIC_DB_PATH = os.path.join(DATA_DIR, DB_MUSIC_NAME)

URL_MUSIC = f"sqlite:///{MUSIC_DB_PATH}"

# Folders
DOWNLOADS_FOLDER = Path(os.getenv('DOWNLOADS_FOLDER', PROJECT_ROOT / "downloads"))
TEMP_DOWNLOADS_FOLDER = DOWNLOADS_FOLDER / "temp"
SONGS_DOWNLOADS_FOLDER = DOWNLOADS_FOLDER / "songs"
THUMBNAILS_DOWNLOADS_FOLDER = DOWNLOADS_FOLDER / "thumbnails"

# Crear carpetas automáticamente si no existen
for folder in [TEMP_DOWNLOADS_FOLDER, SONGS_DOWNLOADS_FOLDER, THUMBNAILS_DOWNLOADS_FOLDER]:
    folder.mkdir(parents=True, exist_ok=True)
