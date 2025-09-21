import os
import tempfile
from deltachat2 import MsgData
from deltachat2.transport import JsonRpcError
from . import database, image_generation

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

    # Si es un mensaje normal (no comando)
    if text and not text.startswith('/'):
        try:
            # Verificar si el bot sigue en el chat
            if not isbotinchat(bot, accid, chatid):
                print(f"Bot ya no está en el chat {chatid}, ignorando mensaje")
                return
            
            # Obtener configuración del chat
            chatdata = database.getchatconfig(chatid)
            if not chatdata:
                # Configuración por defecto
                chatinfo = bot.rpc.getbasicchatinfo(accid, chatid)
                chattitle = chatinfo.name if chatinfo.name else "Chat privado"
                prompt = 'Eres un asistente útil que responde de manera clara y concisa.'
                audiomode = 0
                textfilemode = 0
                voicename = 'Kore'
                database.savechatconfig(chatid, chattitle, prompt, audiomode, textfilemode, voicename)
            
            # Guardar mensaje del usuario
            database.savemessage(chatid, text, "user")
            
            # Obtener historial de conversación
            history = database.getchathistory(chatid)
            messages = []

            # Construir mensajes para la API
            messages.append({"role": "user", "parts": [{"text": prompt}]})

            # Agregar historial (en orden inverso)
            for content, role in reversed(history):
                if role == "user":
                    messages.append({"role": "user", "parts": [{"text": content}]})
                else:
                    messages.append({"role": "model", "parts": [{"text": content}]})

            # Agregar el mensaje actual
            messages.append({"role": "user", "parts": [{"text": text}]})

            # Enviar indicador de escritura
            bot.rpc.sendchataction(accid, chatid, "typing")

            # Llamar a la API de Gemini (deberías importar textprocessing si lo necesitas)
            # respuesta = textprocessing.callgemini_api(messages)
            
            # Para este ejemplo, solo confirmamos recepción del mensaje
            respuesta = "✅ Mensaje recibido. Funcionalidad de texto desactivada, solo imágenes disponibles."
            
            # Guardar respuesta del asistente
            database.savemessage(chatid, respuesta, "assistant")
            
            # Enviar respuesta
            bot.rpc.sendmsg(accid, chatid, MsgData(text=respuesta))

        except Exception as e:
            error_msg = f"❌ Error: {str(e)}"
            try:
                bot.rpc.sendmsg(accid, chatid, MsgData(text=error_msg))
            except JsonRpcError as inner_e:
                print(f"Error al enviar mensaje de error: {inner_e}")
