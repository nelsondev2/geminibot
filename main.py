import os
import requests
import base64
import uuid
import time
from dotenv import load_dotenv
from deltachat2 import MsgData, events, ChatType
from deltabot_cli import BotCli
from argparse import Namespace
from deltachat2.bot import Bot  # para tipado en on_init

# Cargar API key desde .env
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

MODEL = "models/gemini-2.0-flash-preview-image-generation"
ENDPOINT = f"https://generativelanguage.googleapis.com/v1beta/{MODEL}:generateContent?key={API_KEY}"

cli = BotCli("gemini_image_bot")

# Variable para controlar mensajes antiguos
BOT_START_TIME = time.time()

# Texto de ayuda personalizado para GemImg
HELP = (
    "🤖 *GemImg Bot*\n\n"
    "Envíame texto para generar una imagen con Gemini.\n"
    "Ejemplos:\n"
    "- pirámide futurista al atardecer\n"
    "- retrato realista de un astronauta\n\n"
    "Comandos:\n"
    "`/help` → Muestra este mensaje\n"
    "(Cualquier otro comando será ignorado)"
)

def should_process_message(event):
    """Determina si el mensaje debe ser procesado (evita reprocesar mensajes antiguos)"""
    msg_age = time.time() - event.msg.timestamp
    return msg_age < 120  # Procesar solo mensajes de menos de 2 minutos

def mark_as_read(bot, accid, msg_id, chat_id):
    """Marca el mensaje como leído si es un chat individual"""
    try:
        chat = bot.rpc.get_basic_chat_info(accid, chat_id)
        if chat.chat_type == ChatType.SINGLE:
            bot.rpc.markseen_msgs(accid, [msg_id])
            bot.logger.debug(f"Mensaje {msg_id} marcado como leído")
    except Exception as e:
        bot.logger.error(f"Error marcando como leído: {e}")

# Configuración inicial del bot al arrancar
@cli.on_init
def on_init(bot: Bot, args: Namespace) -> None:
    for accid in bot.rpc.get_all_account_ids():
        bot.rpc.set_config(accid, "displayname", "GemImge")
        bot.rpc.set_config(accid, "skip_start_messages", "1")
        bot.rpc.set_config(accid, "selfstatus", HELP)
        bot.rpc.set_config(accid, "delete_device_after", str(60 * 60 * 24))  # 1 día

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
    # Ignorar mensajes antiguos al reiniciar el bot
    if not should_process_message(event):
        bot.logger.info(f"Ignorando mensaje antiguo: {event.msg.text[:50]}...")
        return

    prompt = event.msg.text.strip()
    if not prompt:
        return

    # Marcar como leído inmediatamente (solo en chats individuales)
    mark_as_read(bot, accid, event.msg.id, event.msg.chat_id)

    # Ignorar comandos, salvo /help
    if prompt.startswith("/"):
        if prompt.lower() == "/help":
            bot.rpc.send_msg(accid, event.msg.chat_id, MsgData(text=HELP))
        else:
            bot.logger.info(f"Ignorando comando: {prompt}")
        return

    bot.logger.info(f"Generando imagen para: {prompt}")
    
    # Enviar reacción de "procesando" (opcional)
    try:
        bot.rpc.send_reaction(accid, event.msg.id, ["⏳"])
    except:
        pass  # Si falla la reacción, continuar igual
    
    imagen_path, descripcion = generar_imagen(prompt)

    # Limpiar reacción de "procesando"
    try:
        bot.rpc.send_reaction(accid, event.msg.id, [])
    except:
        pass

    if imagen_path:
        bot.rpc.send_msg(accid, event.msg.chat_id, MsgData(
            text=descripcion or "Aquí tienes tu imagen:",
            file=imagen_path
        ))
        # Limpiar archivo temporal después de enviar
        try:
            os.remove(imagen_path)
        except:
            pass
    else:
        bot.rpc.send_msg(accid, event.msg.chat_id, MsgData(
            text=f"No se pudo generar la imagen. {descripcion or ''}"
        ))

if __name__ == "__main__":
    cli.start()
