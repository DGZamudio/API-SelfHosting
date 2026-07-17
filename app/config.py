import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)

FFMPEG_PATH = os.path.join(PROJECT_ROOT, "app", "services")
DATABASE_PATH = os.path.join(PROJECT_ROOT, "data", "music.db")
DOWNLOADS_FOLDER = os.path.join(PROJECT_ROOT, "downloads")
TEMP_DOWNLOADS_FOLDER = os.path.join(DOWNLOADS_FOLDER, "temp")

DATABASE_URL = f"sqlite:///{DATABASE_PATH}"