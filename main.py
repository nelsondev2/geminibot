import os
import requests
import base64
import uuid
from dotenv import load_dotenv
from deltachat2 import MsgData, events
from deltabot_cli import BotCli

# Cargar API key desde .env
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

MODEL = "models/gemini-2.0-flash-preview-image-generation"
ENDPOINT = f"https://generativelanguage.googleapis.com/v1beta/{MODEL}:generateContent?key={API_KEY}"

cli = BotCli("gemini_image_bot")

def generar_imagen(prompt):
    """Genera imagen usando la API de Gemini sin proxies"""
    if not API_KEY:
        return None, "No se encontró la API key. Define GEMINI_API_KEY en tu archivo .env"

    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"responseModalities": ["TEXT", "IMAGE"]}
    }

    try:
        resp = requests.post(ENDPOINT, json=payload, timeout=30)
    except Exception as e:
        return None, f"Error de conexión: {e}"

    if resp.status_code != 200:
        return None, f"Error {resp.status_code}: {resp.text}"

    try:
        parts = resp.json()["candidates"][0]["content"]["parts"]
        descripcion = None
        imagen_path = None

        for part in parts:
            if "text" in part:
                descripcion = part["text"]

        for part in parts:
            inline_key = "inlineData" if "inlineData" in part else "inline_data" if "inline_data" in part else None
            if inline_key:
                mime_type = part[inline_key].get("mimeType", part[inline_key].get("mime_type", ""))
                if mime_type.startswith("image/"):
                    extension = mime_type.split("/")[-1]
                    nombre_archivo = f"imagen_{uuid.uuid4().hex}.{extension}"
                    image_bytes = base64.b64decode(part[inline_key]["data"])
                    with open(nombre_archivo, "wb") as f:
                        f.write(image_bytes)
                    imagen_path = nombre_archivo
                    break

        return imagen_path, descripcion

    except Exception as e:
        return None, f"Error procesando la respuesta: {e}"

# Evento: cuando llega un mensaje nuevo
@cli.on(events.NewMessage)
def responder_con_imagen(bot, accid, event):
    prompt = event.msg.text.strip()
    if not prompt:
        return

    bot.logger.info(f"Generando imagen para: {prompt}")
    imagen_path, descripcion = generar_imagen(prompt)

    if imagen_path:
        bot.rpc.send_msg(accid, event.msg.chat_id, MsgData(
            text=descripcion or "Aquí tienes tu imagen:",
            file=imagen_path
        ))
    else:
        bot.rpc.send_msg(accid, event.msg.chat_id, MsgData(
            text=f"No se pudo generar la imagen. {descripcion or ''}"
        ))

if __name__ == "__main__":
    cli.start()
