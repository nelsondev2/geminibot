import os
import time
import requests
import base64
import uuid
from dotenv import load_dotenv
from deltachat2 import MsgData, events
from deltabot_cli import BotCli

# Cargar API key
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

MODEL = "models/gemini-2.0-flash-preview-image-generation"
ENDPOINT = f"https://generativelanguage.googleapis.com/v1beta/{MODEL}:generateContent?key={API_KEY}"

# Marca de tiempo de arranque (para filtrar mensajes antiguos)
START_TIME = int(time.time())

# Directorio de datos persistente (montar volumen en Render en /data)
DATA_DIR = os.getenv("DATA_DIR", "/data/deltachat")

cli = BotCli("gemini_image_bot", data_dir=DATA_DIR)

def generar_imagen(prompt):
    """Genera imagen usando la API de Gemini."""
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

@cli.on(events.NewMessage)
def responder_con_imagen(bot, accid, event):
    # Filtrar mensajes antiguos
    if event.msg.timestamp < START_TIME:
        bot.logger.info(f"Ignorando mensaje antiguo: {event.msg.text}")
        bot.rpc.mark_seen(accid, event.msg.chat_id)
        return

    prompt = event.msg.text.strip() if event.msg.text else ""

    # Ignorar comandos
    if prompt.startswith("/"):
        if prompt.lower() == "/help":
            bot.rpc.send_msg(accid, event.msg.chat_id, MsgData(
                text=(
                    "🤖 *GemImg Bot*\n\n"
                    "Envíame texto para generar una imagen.\n"
                    "También puedes adjuntar una imagen como referencia junto con tu descripción.\n\n"
                    "Ejemplos:\n"
                    "- pirámide futurista al atardecer\n"
                    "- (imagen adjunta) + 'estilo acuarela'\n\n"
                    "Comandos:\n"
                    "`/help` → Muestra este mensaje"
                )
            ))
        bot.rpc.mark_seen(accid, event.msg.chat_id)
        return

    if not prompt:
        bot.rpc.mark_seen(accid, event.msg.chat_id)
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

    # ✅ Marcar como leído después de responder
    bot.rpc.mark_seen(accid, event.msg.chat_id)

if __name__ == "__main__":
    cli.start()
