import os

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)

DATABASE_URL = os.getenv('DATABASE_URL', "postgresql+psycopg://dev:dev@localhost:5432/music")
DOWNLOADS_FOLDER = os.getenv('DOWNLOADS_FOLDER', os.path.join(PROJECT_ROOT, "downloads"))

TEMP_DOWNLOADS_FOLDER = os.path.join(DOWNLOADS_FOLDER, "temp")
SONGS_DOWNLOADS_FOLDER = os.path.join(DOWNLOADS_FOLDER, "songs")
THUMBNAILS_DOWNLOADS_FOLDER = os.path.join(DOWNLOADS_FOLDER, "thumbnails")
