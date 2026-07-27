import io
import os
from pathlib import Path

import requests
import yt_dlp
from fastapi import HTTPException
from mutagen.id3 import APIC, ID3, TALB, TIT2, TPE1, USLT, error
from PIL import Image
from pydantic import HttpUrl

from app.config import (
    SONGS_DOWNLOADS_FOLDER,
    TEMP_DOWNLOADS_FOLDER,
    THUMBNAILS_DOWNLOADS_FOLDER,
)
from app.utils import clean_filename, limpiar_archivo_parcial


def extract_metadata(song_info: dict, url: str | None = None, portada: str | None = None) -> dict:
    metadata = {}

    id_video = song_info.get('id')
    url = song_info.get("original_url")
    titulo = song_info.get('track', song_info.get('title'))
    artista = song_info.get('artist', song_info.get('uploader'))
    album = song_info.get('album', 'Álbum Desconocido')
    portada = portada if portada else song_info.get('thumbnail')

    metadata = {
        'video_id': id_video,
        'url': url,
        'title': titulo,
        'artist': artista,
        'album': album,
        'thumbnail':portada
    }

    return metadata

def select_thumbnail(portadas: list[dict]) -> str:
    max_res = -1
    portada_url = ""
    for portada in portadas:
        local_url = portada.get("url")
        response = requests.get(local_url)
        if response.status_code == 200:
            local_max = max(portada.get("height"), max_res)
            if local_max > max_res:
                max_res = max(portada.get("height"), max_res)
                portada_url = local_url

    return portada_url

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
            'quiet': True
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(str(url), download=False)
            download_type = "song"

            if bool(info.get('entries')):
                download_type = "album"
            
            songs_meta = []

            if download_type == "album":
                local_portada = select_thumbnail(info.get("thumbnails"))
                for cancion in info.get("entries"):
                    songs_meta.append(extract_metadata(cancion, portada=local_portada))
            else:
                songs_meta.append(extract_metadata(info, url=url))
        
        return {"metadata":songs_meta, "type":download_type}
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

def process_img(img_bytes: bytes, album_name: str, crop: bool = True) -> bytes:
    save_path = os.path.join(THUMBNAILS_DOWNLOADS_FOLDER, f"{clean_filename(album_name)}.jpg")
    pil_img = Image.open(io.BytesIO(img_bytes))
    pil_img = pil_img.convert("RGB")
    w, h = pil_img.size

    if crop and w != h:
        side = min(w, h)
        left = (w - side) // 2
        top = (h - side) // 2
        pil_img = pil_img.crop((left, top, left + side, top + side))

    buffer = io.BytesIO()
    pil_img.save(buffer, format="JPEG")
    bytes_finales = buffer.getvalue()

    with open(save_path, "wb") as f:
        f.write(bytes_finales)

    return bytes_finales

def add_thumbnail(audio_obj: ID3, image_bytes: bytes, mime: str = "image/jpeg"):
    audio_obj.add(
        APIC(
            encoding=3,
            mime=mime,
            type=3,
            desc="Cover",
            data=image_bytes
        )
    )
    
def get_lyrics(title: str, artist: str) -> str | None:
    params = {
        "track_name": title,
        "artist_name": artist,
    }
    response = requests.get("https://lrclib.net/api/search", params=params)
    response.raise_for_status()
    resultados = response.json()

    if not resultados:
        return None

    return resultados[0].get("plainLyrics")

def _procesar_metadata_y_tags(info: dict, save_path: str, portada_album: bytes | None = None) -> dict:
    """Descarga tags, carátula y letra para UNA canción ya descargada por yt-dlp."""
    id_video = info.get('id')
    archivo_inicial = os.path.join(save_path, f"{id_video}.mp3")

    titulo = info.get('track', info.get('title'))
    artista = info.get('artist', info.get('uploader'))
    album = info.get('album', 'Álbum Desconocido')
    portada_url = info.get('thumbnail')

    meta = {
        'video_id': id_video,
        'title': titulo,
        'artist': artista,
        'album': album,
        'thumbnail': portada_url
    }

    nombre_limpio = clean_filename(f"{titulo}.mp3")
    nombre_final = os.path.join(save_path, nombre_limpio)

    try:
        if os.path.exists(nombre_final):
            if os.path.exists(archivo_inicial):
                os.remove(archivo_inicial)
            return {'path': nombre_final, 'metadata': meta, 'errors': []}

        if os.path.exists(archivo_inicial):
            os.rename(archivo_inicial, nombre_final)
        else:
            raise FileNotFoundError()
    except Exception as e:
        limpiar_archivo_parcial()
        raise HTTPException(
            status_code=400,
            detail=f"No se pudo descargar la canción, intenta de nuevo, error:{e}"
        ) from e

    try:
        try:
            audio = ID3(nombre_final)
        except error:
            audio = ID3()
        errors = []

        try:
            audio.add(TIT2(encoding=3, text=titulo))
            audio.add(TPE1(encoding=3, text=artista))
            audio.add(TALB(encoding=3, text=album))
        except:
            errors.append('Error al agregar la metadata')

        try:
            if portada_album:
                add_thumbnail(audio, portada_album)
            else:
                thumbnail_path = thumbnail_exists(album)
                if thumbnail_path:
                    with thumbnail_path.open('rb') as image_bytes:
                        add_thumbnail(audio, image_bytes.read())
                else:
                    thumbnail_bytes = download_thumbnail(portada_url)
                    if thumbnail_bytes:
                        image_bytes = process_img(thumbnail_bytes, album)
                        add_thumbnail(audio, image_bytes)
        except:
            errors.append('Error al agregar la carátula')

        try:
            if titulo and artista:
                letra = get_lyrics(title=titulo, artist=artista)
                if letra:
                    audio.add(
                        USLT(encoding=3, lang="eng", desc="", text=letra)
                    )
        except:
            errors.append('Error al agregar la letra')

        audio.save(nombre_final)
        return {'path': nombre_final, 'metadata': meta, 'errors': errors}

    except Exception as e:
        raise Exception(f"Fallo procesando {titulo}: {e}") from e


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
        'quiet': True
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
    except Exception as e:
        limpiar_archivo_parcial()
        raise HTTPException(
            status_code=400,
            detail=f"No se pudo descargar la canción, intenta de nuevo, error:{e}"
        ) from e

    is_album = bool(info.get('entries'))

    if is_album:
        thumbnail_bytes = download_thumbnail(select_thumbnail(info.get("thumbnails")))
        album_name = info.get('title', 'Álbum Desconocido').replace("Album - ", "")
        portada_album = process_img(thumbnail_bytes, album_name) if thumbnail_bytes else None

        resultados = []
        for entrada in info.get("entries"):
            resultado = _procesar_metadata_y_tags(entrada, save_path, portada_album=portada_album)
            resultados.append(resultado)

        return {"type": "album", "results": resultados}

    else:
        resultado = _procesar_metadata_y_tags(info, save_path)
        return {"type": "song", **resultado}