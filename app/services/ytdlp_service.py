import os
from fastapi import HTTPException
from pydantic import HttpUrl
import yt_dlp
from mutagen.easyid3 import EasyID3

from app.config import DOWNLOADS_FOLDER, FFMPEG_PATH, TEMP_DOWNLOADS_FOLDER

def get_song_metadata(url: HttpUrl):
    try:
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': os.path.join(TEMP_DOWNLOADS_FOLDER, '%(id)s.%(ext)s'), 
            'ffmpeg_location': FFMPEG_PATH
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(str(url), download=False)
            id_video = info.get('id')

            titulo = info.get('track', info.get('title'))
            artista = info.get('artist', info.get('uploader'))
            album = info.get('album', 'Álbum Desconocido')
    
        
        meta = {
            'video_id': id_video,
            'url': url,
            'title': titulo,
            'artist': artista,
            'album': album    
        }
        
        return meta
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Hubo un error al obtener la canción: {e}")

def download_song(url: str, temp=False):
    save_path = TEMP_DOWNLOADS_FOLDER if temp else DOWNLOADS_FOLDER
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': os.path.join(save_path, '%(id)s.%(ext)s'), 
        'ffmpeg_location': FFMPEG_PATH
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        id_video = info.get('id')
        archivo_inicial = os.path.join(save_path,  f"{id_video}.mp3")

        titulo = info.get('track', info.get('title'))
        artista = info.get('artist', info.get('uploader'))
        album = info.get('album', 'Álbum Desconocido')
        
    nombre_final = os.path.join(save_path, f"{titulo}.mp3".replace("/", "-"))

    if os.path.exists(archivo_inicial):
        os.rename(archivo_inicial, nombre_final)
    else:
        raise FileNotFoundError()

    try:
        audio = EasyID3(nombre_final)
        audio['title'] = titulo
        audio['artist'] = artista
        audio['album'] = album
        audio.save()
        
        return nombre_final
    except Exception as e:
        raise e