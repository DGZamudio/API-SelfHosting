import os
import re

def clean_filename(filename: str) -> str:
    """Elimina caracteres prohibidos en sistemas de archivos (especialmente Windows)"""
    return re.sub(r'[\\/*?:"<>|]', "", filename)

def limpiar_archivo_parcial(*rutas: str):
    for ruta in rutas:
        if ruta and os.path.exists(ruta):
            os.remove(ruta)