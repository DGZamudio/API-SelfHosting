import os
import shutil
from pathlib import Path

import requests
import yt_dlp
from fastapi import HTTPException
from pydantic import HttpUrl

from app.config import SONGS_DOWNLOADS_FOLDER, TEMP_DOWNLOADS_FOLDER
from app.utils import clean_filename, limpiar_archivo_parcial


def get_lyrics(title: str, artist: str) -> str | None:
    """Busca letras sincronizadas o planas en LRCLIB."""
    try:
        params = {"track_name": title, "artist_name": artist}
        response = requests.get("https://lrclib.net/api/search", params=params, timeout=5)
        if response.status_code == 200:
            resultados = response.json()
            if resultados:
                return resultados[0].get("syncedLyrics") or resultados[0].get("plainLyrics")
    except Exception:
        pass
    return None


def extract_metadata(song_info: dict, url: str | None = None) -> dict:
    thumbnails = song_info.get('thumbnails', [])
    portada_url = song_info.get('thumbnail')

    if thumbnails:
        cuadradas = [t for t in thumbnails if t.get('width') and t.get('height') and t.get('width') == t.get('height')]

        if cuadradas:
            portada_url = max(cuadradas, key=lambda x: x.get('height', 0)).get('url')
        else:
            portada_url = max(thumbnails, key=lambda x: x.get('height', 0) or 0).get('url')

    # Retorna la metadata limpia
    return {
        'video_id': song_info.get('id'),
        'url': song_info.get('original_url', url),
        'title': song_info.get('track') or song_info.get('title') or "Título Desconocido",
        'artist': (
            song_info.get('artists')[0] if song_info.get('artists')
            else song_info.get('artist') or song_info.get('uploader') or "Artista Desconocido"
        ),
        'album': song_info.get('album') or 'Álbum Desconocido',
        'thumbnail': portada_url
    }

def get_song_metadata(url: HttpUrl):
    """Extrae rápidamente los metadatos sin descargar nada."""
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': 'in_playlist',
            'skip_download': True,
            'ignoreerrors': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(str(url), download=False)
            if not info:
                raise ValueError("No se obtuvo información de la URL.")

            is_playlist = 'entries' in info and bool(info.get('entries'))
            download_type = "album" if is_playlist else "song"
            songs_meta = []

            if is_playlist:
                for cancion in info.get("entries", []):
                    if cancion:
                        songs_meta.append(extract_metadata(cancion))
            else:
                songs_meta.append(extract_metadata(info, url=str(url)))

        return {"metadata": songs_meta, "type": download_type}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener metadata: {e}")


def _organizar_y_descargar_letra(info: dict, save_path: str) -> dict:
    """Mueve el MP3 a su carpeta final (/Artista/Álbum/) y genera el archivo .lrc."""
    id_video = info.get('id')
    archivo_inicial = os.path.join(TEMP_DOWNLOADS_FOLDER, f"{id_video}.mp3")

    titulo = info.get('track') or info.get('title') or "Canción Desconocida"

    # Extraer artista
    artists = info.get('artists')
    artista = artists[0] if artists else info.get('artist') or info.get('uploader') or "Artista Desconocido"

    album = info.get('album') or 'Álbum Desconocido'

    meta = {
        'video_id': id_video,
        'title': titulo,
        'artist': artista,
        'album': album,
        'thumbnail': info.get('thumbnail')
    }

    folder_path = os.path.join(save_path, clean_filename(artista), clean_filename(album))
    nombre_final = os.path.join(folder_path, f"{clean_filename(titulo)}.mp3")

    errors = []

    try:
        os.makedirs(folder_path, exist_ok=True)

        if os.path.exists(nombre_final):
            if os.path.exists(archivo_inicial):
                os.remove(archivo_inicial)
        elif os.path.exists(archivo_inicial):
            shutil.move(archivo_inicial, nombre_final)
        else:
            raise FileNotFoundError(f"No se encontró el archivo temporal: {archivo_inicial}")

    except Exception as e:
        limpiar_archivo_parcial()
        raise HTTPException(
            status_code=400,
            detail=f"Error al mover la canción al destino final: {e}"
        ) from e

    # Descarga de letra sincronizada externa (.lrc)
    try:
        letra = get_lyrics(title=titulo, artist=artista)
        if letra:
            lrc_path = os.path.splitext(nombre_final)[0] + ".lrc"
            with open(lrc_path, "w", encoding="utf-8") as lyric_file:
                lyric_file.write(letra)
    except Exception:
        errors.append('Error al obtener la letra .lrc')

    return {'path': nombre_final, 'metadata': meta, 'errors': errors}


def download_song(url: str, temp=False):
    save_path = TEMP_DOWNLOADS_FOLDER if temp else SONGS_DOWNLOADS_FOLDER

    ydl_opts = {
        'format': 'ba/b',
        'outtmpl': os.path.join(TEMP_DOWNLOADS_FOLDER, '%(id)s.%(ext)s'),
        'quiet': True,
        'no_warnings': True,

        # Optimización de descarga
        'concurrent_fragment_downloads': 5,
        'buffersize': 1024 * 16,
        'nocheckcertificate': True,

        # yt-dlp descarga, incrusta la portada, incrusta la metadata y BORRA la imagen temporal automáticamente
        'writethumbnail': True,
        'postprocessors': [
            {
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            },
            {
                'key': 'FFmpegMetadata',
                'add_metadata': True,
            },
            {
                'key': 'EmbedThumbnail',
                'already_have_thumbnail': False,
            }
        ],
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
    except Exception as e:
        limpiar_archivo_parcial()
        raise HTTPException(
            status_code=400,
            detail=f"No se pudo descargar la canción: {e}"
        ) from e

    is_album = 'entries' in info and bool(info.get('entries'))

    if is_album:
        resultados = []
        for entrada in info.get("entries", []):
            if entrada:
                resultado = _organizar_y_descargar_letra(entrada, save_path)
                resultados.append(resultado)
        return {"type": "album", "results": resultados}
    else:
        resultado = _organizar_y_descargar_letra(info, save_path)
        return {"type": "song", **resultado}
