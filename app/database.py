import sqlite3
from app.config import DATABASE_PATH

class Database:
    def get_conn(self):
        return sqlite3.connect(DATABASE_PATH+"music.db")