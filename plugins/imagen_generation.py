import os
import requests
import base64
import json
import uuid
import tempfile
from dotenv import load_dotenv

# Cargar API key desde .env
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

MODEL = "models/gemini-2.0-flash-preview-image-generation"
ENDPOINT = f"https://generativelanguage.googleapis.com/v1beta/{MODEL}:generateContent?key={API_KEY}"

def generar_imagen(prompt):
    if not API_KEY:
        return None, "❌ No se encontró la API key. Define GEMINI_API_KEY en tu archivo .env"

    payload = {
        "contents": [
            {"role": "user", "parts": [{"text": prompt}]}
        ],
        "generationConfig": {
            "responseModalities": ["TEXT", "IMAGE"]
        }
    }

    try:
        resp = requests.post(ENDPOINT, json=payload, timeout=30)
    except Exception as e:
        return None, f"❌ Error de conexión: {e}"

    if resp.status_code != 200:
        return None, f"Error: {resp.status_code} - {resp.text}"

    data = resp.json()

    texto_encontrado = False
    imagen_encontrada = False
    descripcion = ""
    imagen_path = None

    try:
        parts = data["candidates"][0]["content"]["parts"]

        # Mostrar texto descriptivo si existe
        for part in parts:
            if "text" in part:
                descripcion = part["text"]
                texto_encontrado = True

        # Buscar y guardar imagen
        for part in parts:
            inline_key = None
            if "inlineData" in part:
                inline_key = "inlineData"
            elif "inline_data" in part:
                inline_key = "inline_data"

            if inline_key:
                mime_type = part[inline_key].get("mimeType", part[inline_key].get("mime_type", ""))
                if mime_type.startswith("image/"):
                    extension = mime_type.split("/")[-1]
                    # Crear archivo temporal para la imagen
                    with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{extension}') as f:
                        imagen_path = f.name
                    image_base64 = part[inline_key]["data"]
                    image_bytes = base64.b64decode(image_base64)
                    with open(imagen_path, "wb") as f:
                        f.write(image_bytes)
                    imagen_encontrada = True
                    break

        if not imagen_encontrada:
            return None, "⚠️ No se encontró imagen en la respuesta."

        return imagen_path, descripcion

    except (KeyError, IndexError) as e:
        return None, f"❌ Error procesando la respuesta: {e}"
