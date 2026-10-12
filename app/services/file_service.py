import os
from datetime import datetime

from app.config import TEMP_DOWNLOADS_FOLDER
from app.models.song import Song


def create_m3u_playlist(songs: list[Song]):
    timestamp = datetime.microsecond
    playlist_path = os.path.join(TEMP_DOWNLOADS_FOLDER, f"{timestamp}.m3u")
    with open(playlist_path, "w", encoding="utf-8") as f:
        for song in songs:
            song_path = os.path.join(song.artist.name, song.album.title, f"{song.title}.mp3")
            f.write(f"{song_path}\n")

    return playlist_path
