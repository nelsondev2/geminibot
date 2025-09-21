import os
import tempfile
from deltachat2 import MsgData
from deltachat2.transport import JsonRpcError
from . import image_generation

def isbotinchat(bot, accid, chatid):
    """Verifica si el bot sigue siendo miembro del chat"""
    try:
        members = bot.rpc.getchatcontacts(accid, chatid)
        return accid in members
    except JsonRpcError as e:
        print(f"Error verificando membresía del chat: {e}")
        return False
    except Exception as e:
        print(f"Error inesperado verificando membresía: {e}")
        return False

def handle_message(bot, accid, event):
    msg = event.msg
    chatid = msg.chatid
    text = msg.text.strip() if msg.text else ""

    # Comando para generar imagen
    if text.startswith("/imagen "):
        prompt = text[8:].strip()
        if not prompt:
            bot.rpc.sendmsg(accid, chatid, MsgData(text="❌ Debes proporcionar una descripción para la imagen. Ejemplo: /imagen un paisaje montañoso al atardecer"))
            return

        try:
            bot.rpc.sendmsg(accid, chatid, MsgData(text="🎨 Generando imagen..."))
            
            # Generar la imagen
            imagenpath, descripcion = image_generation.generar_imagen(prompt)

            if imagenpath and os.path.exists(imagenpath):
                # Enviar la imagen
                with open(imagenpath, 'rb') as f:
                    imagen_data = f.read()

                bot.rpc.sendmsg(
                    accid,
                    chatid,
                    MsgData(
                        file=imagen_data,
                        text=descripcion if descripcion else "Imagen generada por Gemini IA"
                    )
                )
                
                # Limpiar archivo temporal
                os.unlink(imagenpath)
            else:
                bot.rpc.sendmsg(accid, chatid, MsgData(text=f"❌ Error al generar la imagen: {descripcion}"))
                
        except Exception as e:
            error_msg = f"❌ Error al procesar el comando de imagen: {str(e)}"
            bot.rpc.sendmsg(accid, chatid, MsgData(text=error_msg))
        return

    # Comando de ayuda simplificado
    if text == "/help":
        help_text = """🤖 Gemini Bot - Comandos disponibles:

🖼️ Imágenes:
- /imagen <descripción> - Genera una imagen con IA

Ejemplo: /imagen un paisaje montañoso al atardecer
"""
        bot.rpc.sendmsg(accid, chatid, MsgData(text=help_text))
        return

    # Si es un mensaje normal (no comando)
    if text and not text.startswith('/'):
        try:
            # Verificar si el bot sigue en el chat
            if not isbotinchat(bot, accid, chatid):
                print(f"Bot ya no está en el chat {chatid}, ignorando mensaje")
                return
            
            # Enviar indicador de escritura
            bot.rpc.sendchataction(accid, chatid, "typing")
            
            # Respuesta simple para mensajes de texto
            respuesta = "🤖 Solo respondo al comando /imagen. Usa /help para ver los comandos disponibles."
            
            # Enviar respuesta
            bot.rpc.sendmsg(accid, chatid, MsgData(text=respuesta))

        except Exception as e:
            error_msg = f"❌ Error: {str(e)}"
            try:
                bot.rpc.sendmsg(accid, chatid, MsgData(text=error_msg))
            except JsonRpcError as inner_e:
                print(f"Error al enviar mensaje de error: {inner_e}")
