import io
import os
import re

import requests
from mutagen.id3 import APIC, ID3, error
from PIL import Image


def process_and_embed_cover(mp3_path: str, image_url: str):
    """Descarga, recorta, guarda en la carpeta como cover.jpg e incrusta en el MP3."""
    try:
        album_folder = os.path.dirname(mp3_path)
        cover_path = os.path.join(album_folder, "cover.jpg")

        if os.path.exists(cover_path):
            with open(cover_path, "rb") as f:
                img_bytes = f.read()
        else:
            response = requests.get(image_url, timeout=10)
            response.raise_for_status()

            # Recortamos a 1:1 y redimensionamos
            img = Image.open(io.BytesIO(response.content)).convert("RGB")
            width, height = img.size
            min_dim = min(width, height)
            left = (width - min_dim) / 2
            top = (height - min_dim) / 2
            right = (width + min_dim) / 2
            bottom = (height + min_dim) / 2

            img_cropped = img.crop((left, top, right, bottom)).resize((600, 600), Image.Resampling.LANCZOS)

            img_byte_arr = io.BytesIO()
            img_cropped.save(img_byte_arr, format='JPEG', quality=85)
            img_bytes = img_byte_arr.getvalue()

            with open(cover_path, "wb") as f:
                f.write(img_bytes)

        audio = ID3(mp3_path)
        audio.add(
            APIC(
                encoding=3,
                mime='image/jpeg',
                type=3,
                desc='Cover',
                data=img_bytes
            )
        )
        audio.save()

    except Exception as e:
        print(f"Advertencia: No se pudo procesar la carátula para {mp3_path}: {e}")

def clean_filename(filename: str) -> str:
    """Elimina caracteres prohibidos en sistemas de archivos (especialmente Windows)"""
    return re.sub(r'[\\/*?:"<>|]', "", filename)

def limpiar_archivo_parcial(*rutas: str):
    for ruta in rutas:
        if ruta and os.path.exists(ruta):
            os.remove(ruta)
