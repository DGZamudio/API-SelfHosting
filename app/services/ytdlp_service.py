import os
import io
import requests
import yt_dlp
from pathlib import Path
from PIL import Image
from fastapi import HTTPException
from pydantic import HttpUrl
from mutagen.id3 import ID3, APIC, error
from mutagen.easyid3 import EasyID3
from app.config import FFMPEG_PATH, SONGS_DOWNLOADS_FOLDER, TEMP_DOWNLOADS_FOLDER, THUMBNAILS_DOWNLOADS_FOLDER

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
    
def thumbnail_exists(album_name: str) -> Path | None:
    local_path = os.path.join(THUMBNAILS_DOWNLOADS_FOLDER, f"{album_name}.jpg")
    thumbnail = Path(local_path)
    
    if thumbnail.exists():
        return thumbnail
    else:
        return None
    
def download_thumbnail(thumbnail_url: str | None) -> bytes | None:
    if not thumbnail_url:
        return
    response = requests.get(str(thumbnail_url))
    response.raise_for_status()
    
    return response.content

def process_img(img_bytes: bytes, album_name: str) -> bytes:
    pil_img = Image.open(io.BytesIO(img_bytes))
    pil_img = pil_img.convert("RGB")
    
    w, h = pil_img.size
    start_point = w//2-h//2
    portrait = (start_point, 0, start_point+h, h)
    recortada = pil_img.crop(portrait)

    save_path = os.path.join(THUMBNAILS_DOWNLOADS_FOLDER , f"{album_name.replace("/", "-")}.jpg")
    
    buffer = io.BytesIO()
    recortada.save(buffer, format="JPEG")
    bytes_finales = buffer.getvalue()

    with open(save_path, "wb") as f:
        f.write(bytes_finales)

    return bytes_finales

def add_thumbnail(ruta_mp3: str, image_bytes: bytes, mime: str = "image/jpeg"):
    try:
        audio = ID3(ruta_mp3)
    except error:
        audio = ID3()

    audio.add(
        APIC(
            encoding=3,
            mime=mime,
            type=3,
            desc="Cover",
            data=image_bytes
        )
    )
    audio.save(ruta_mp3)
    
def download_song(url: str, temp=False):
    save_path = TEMP_DOWNLOADS_FOLDER if temp else SONGS_DOWNLOADS_FOLDER
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
        portada = info.get('thumbnail')

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
        
        thumbnail_path = thumbnail_exists(album)
        
        if thumbnail_path:
            with thumbnail_path.open('rb') as image_bytes:
                add_thumbnail(nombre_final, image_bytes.read())
        else:
            thumbnail_bytes = download_thumbnail(portada)
            if thumbnail_bytes:
                image_bytes = process_img(thumbnail_bytes, album)
                add_thumbnail(nombre_final, image_bytes)
                
        return nombre_final
    except Exception as e:
        raise Exception(f"Fallo procesando {titulo}: {e}")