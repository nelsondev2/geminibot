import os
import tempfile
import time
from deltachat2 import MsgData, ChatType
from deltachat2.transport import JsonRpcError
from . import database, text_processing, audio_processing, image_generation

def is_bot_in_chat(bot, accid, chat_id):
    """Verifica si el bot sigue siendo miembro del chat"""
    try:
        members = bot.rpc.get_chat_contacts(accid, chat_id)
        return accid in members
    except JsonRpcError as e:
        print(f"Error verificando membresía del chat: {e}")
        return False
    except Exception as e:
        print(f"Error inesperado verificando membresía: {e}")
        return False

def handle_message(bot, accid, event):
    msg = event.msg
    chat_id = msg.chat_id
    text = msg.text.strip() if msg.text else ""

    # Verificar si es un archivo de audio
    if msg.file and msg.file_name and audio_processing.is_audio_file(msg.file_name):
        try:
            # Convertir audio a texto
            transcribed_text, error = audio_processing.audio_to_text(msg.file)

            if error:
                bot.rpc.send_msg(accid, chat_id, MsgData(text=error))
                return

            if not transcribed_text or transcribed_text.strip() == "":
                bot.rpc.send_msg(accid, chat_id, MsgData(text="❌ No se detectó texto en el audio. Asegúrate de que el audio sea claro y contenga voz."))
                return

            # Mostrar el texto transcribido
            bot.rpc.send_msg(
                accid,
                chat_id,
                MsgData(text=f"📝{transcribed_text}"))

            # Usar el texto transcribido como prompt para Gemini
            text = transcribed_text  # Continuar con el procesamiento normal

        except Exception as e:
            error_msg = f"❌ Error al procesar el audio: {str(e)}"
            bot.rpc.send_msg(accid, chat_id, MsgData(text=error_msg))
            return

    # Comando para mostrar voces disponibles
    if text == "/voices":
        try:
            # Obtener la voz actual configurada para este chat
            chat_data = database.get_chat_config(chat_id)
            current_lang = 'es'  # Fijo en español
            current_voice = chat_data[3] if chat_data and chat_data[3] else 'Kore'

            # Construir mensaje con la lista de voces
            voices_list = "🎙️ **Voces disponibles en Gemini TTS:**\n\n"

            for i, (voice, info) in enumerate(audio_processing.GEMINI_VOICES_DETAILED.items(), 1):
                current_indicator = " ✅" if voice == current_voice else ""
                voices_list += f"{i}. **{voice}**{current_indicator} - {info['description']} ({info['gender']}, {info['style']})\n"

            voices_list += f"\n🌍 **Idioma:** Español (fijo)\n"
            voices_list += f"🎵 **Voz actual:** {current_voice}\n"
            voices_list += "🔊 **Para cambiar de voz:** `/set_voice <nombre_voz>`\n"

            # Dividir el mensaje si es demasiado largo para Delta Chat
            if len(voices_list) > 2000:
                parts = [voices_list[i:i+2000] for i in range(0, len(voices_list), 2000)]
                for part in parts:
                    bot.rpc.send_msg(accid, chat_id, MsgData(text=part))
                    time.sleep(0.5)
            else:
                bot.rpc.send_msg(accid, chat_id, MsgData(text=voices_list))

        except Exception as e:
            error_msg = f"❌ Error al obtener la lista de voces: {str(e)}"
            bot.rpc.send_msg(accid, chat_id, MsgData(text=error_msg))
        return

    # Comando para configurar la voz específica
    if text.startswith("/set_voice "):
        voice_name = text[11:].strip()

        if voice_name not in audio_processing.GEMINI_VOICES:
            available_voices = ", ".join(list(audio_processing.GEMINI_VOICES_DETAILED.keys())[:8]) + "..."
            error_msg = f"❌ Voz no válida. Usa: `/set_voice <nombre_voz>`\n\n"
            error_msg += f"🎙️ Algunas voces disponibles: {available_voices}\n"
            error_msg += "📋 Ver todas las voces: `/voices`"
            bot.rpc.send_msg(accid, chat_id, MsgData(text=error_msg))
            return

        try:
            # Obtener información actual del chat
            chat_info = bot.rpc.get_basic_chat_info(accid, chat_id)
            chat_title = chat_info.name if chat_info.name else "Chat privado"
            
            # Actualizar configuración
            chat_data = database.get_chat_config(chat_id)
            if chat_data:
                prompt, audio_mode, textfile_mode, _ = chat_data
            else:
                prompt = 'Eres un asistente útil que responde de manera clara y concisa.'
                audio_mode = 0
                textfile_mode = 0
                
            database.save_chat_config(chat_id, chat_title, prompt, audio_mode, textfile_mode, voice_name)

            voice_info = audio_processing.get_voice_info(voice_name)
            success_msg = f"✅ Voz cambiada a: **{voice_name}**\n"
            success_msg += f"📝 {voice_info}\n\n"
            success_msg += "🔊 Prueba el modo audio con: `/audio on`"
            bot.rpc.send_msg(accid, chat_id, MsgData(text=success_msg))

        except Exception as e:
            error_msg = f"❌ Error al cambiar la voz: {str(e)}"
            bot.rpc.send_msg(accid, chat_id, MsgData(text=error_msg))
        return

    # Comando para activar/desactivar modo archivo de texto
    if text.startswith("/textfile "):
        mode = text[10:].strip().lower()

        if mode not in ["on", "off"]:
            try:
                bot.rpc.send_msg(
                    accid,
                    chat_id,
                    MsgData(text="❌ Uso incorrecto. Formato: `/textfile on|off`")
                )
            except JsonRpcError as e:
                print(f"Error al enviar mensaje: {e}")
            return

        textfile_mode = 1 if mode == "on" else 0

        try:
            # Obtener información actual del chat
            chat_info = bot.rpc.get_basic_chat_info(accid, chat_id)
            chat_title = chat_info.name if chat_info.name else "Chat privado"
            
            chat_data = database.get_chat_config(chat_id)
            if chat_data:
                prompt, audio_mode, _, voice_name = chat_data
            else:
                prompt = 'Eres un asistente útil que responde de manera clara y concisa.'
                audio_mode = 0
                voice_name = 'Kore'
                
            database.save_chat_config(chat_id, chat_title, prompt, audio_mode, textfile_mode, voice_name)

            bot.rpc.send_msg(
                accid,
                chat_id,
                MsgData(text=f"📄 Modo archivo de texto {'activado' if textfile_mode else 'desactivado'} correctamente.")
            )
        except JsonRpcError as e:
            print(f"Error al enviar confirmación de textfile: {e}")
        return

    # Comando para activar/desactivar audio
    if text.startswith("/audio "):
        mode = text[7:].strip().lower()

        if mode not in ["on", "off"]:
            try:
                bot.rpc.send_msg(
                    accid,
                    chat_id,
                    MsgData(text="❌ Uso incorrecto. Formato: `/audio on|off`")
                )
            except JsonRpcError as e:
                print(f"Error al enviar mensaje: {e}")
            return

        audio_mode = 1 if mode == "on" else 0

        try:
            # Obtener información actual del chat
            chat_info = bot.rpc.get_basic_chat_info(accid, chat_id)
            chat_title = chat_info.name if chat_info.name else "Chat privado"
            
            chat_data = database.get_chat_config(chat_id)
            if chat_data:
                prompt, _, textfile_mode, voice_name = chat_data
            else:
                prompt = 'Eres un asistente útil que responde de manera clara y concisa.'
                textfile_mode = 0
                voice_name = 'Kore'
                
            database.save_chat_config(chat_id, chat_title, prompt, audio_mode, textfile_mode, voice_name)

            bot.rpc.send_msg(
                accid,
                chat_id,
                MsgData(text=f"🔊 Modo audio {'activado' if audio_mode else 'desactivado'} correctamente.")
            )
        except JsonRpcError as e:
            print(f"Error al enviar confirmación de audio: {e}")
        return

    # Comando para limpiar historial
    if text == "/clear":
        try:
            database.clear_chat_history(chat_id)
            bot.rpc.send_msg(
                accid,
                chat_id,
                MsgData(text="🧹 Historial de conversación limpiado correctamente.")
            )
        except JsonRpcError as e:
            print(f"Error al limpiar historial: {e}")
        return

    # Comando para mostrar ayuda
    if text == "/help":
        help_text = """
🤖 **Gemini Bot - Comandos disponibles:**

📝 **Interacción:**
- Simplemente escribe tu mensaje para conversar con Gemini
- Responde a un mensaje para continuar la conversación

🎙️ **Audio:**
- Envía un mensaje de voz (formato MP3, WAV, M4A, etc.)
- `/audio on|off` - Activa/desactiva respuestas en audio
- `/voices` - Muestra todas las voces disponibles
- `/set_voice <nombre>` - Cambia la voz (ej: `/set_voice Kore`)

📄 **Archivos:**
- `/textfile on|off` - Guarda respuestas largas en archivos de texto

🖼️ **Imágenes:**
- `/imagen <descripción>` - Genera una imagen con IA

⚙️ **Configuración:**
- `/clear` - Limpia el historial de conversación
- `/help` - Muestra esta ayuda

🌐 **Idiomas:**
- El bot detecta automáticamente el idioma de tus mensajes
- Las respuestas se generan en el mismo idioma
        """
        try:
            bot.rpc.send_msg(accid, chat_id, MsgData(text=help_text))
        except JsonRpcError as e:
            print(f"Error al enviar ayuda: {e}")
        return

    # Comando para generar imagen
    if text.startswith("/imagen "):
        prompt = text[8:].strip()
        if not prompt:
            bot.rpc.send_msg(accid, chat_id, MsgData(text="❌ Debes proporcionar una descripción para la imagen. Ejemplo: `/imagen un paisaje montañoso al atardecer`"))
            return

        try:
            bot.rpc.send_msg(accid, chat_id, MsgData(text="🎨 Generando imagen..."))
            
            # Generar la imagen
            imagen_path, descripcion = image_generation.generar_imagen(prompt)
            
            if imagen_path and os.path.exists(imagen_path):
                # Enviar la imagen
                with open(imagen_path, 'rb') as f:
                    imagen_data = f.read()
                
                bot.rpc.send_msg(
                    accid,
                    chat_id,
                    MsgData(
                        file=imagen_data,
                        filename="imagen_generada.png",
                        text=descripcion if descripcion else "Imagen generada por Gemini IA"
                    )
                )
                
                # Limpiar archivo temporal
                os.unlink(imagen_path)
            else:
                bot.rpc.send_msg(accid, chat_id, MsgData(text=f"❌ Error al generar la imagen: {descripcion}"))
                
        except Exception as e:
            error_msg = f"❌ Error al procesar el comando de imagen: {str(e)}"
            bot.rpc.send_msg(accid, chat_id, MsgData(text=error_msg))
        return

    # Comando para mostrar información del chat
    if text == "/info":
        try:
            chat_info = bot.rpc.get_basic_chat_info(accid, chat_id)
            chat_type = "Grupo" if chat_info.chat_type == ChatType.GROUP else "Privado"
            
            chat_data = database.get_chat_config(chat_id)
            if chat_data:
                prompt, audio_mode, textfile_mode, voice_name = chat_data
                audio_status = "Activado" if audio_mode else "Desactivado"
                textfile_status = "Activado" if textfile_mode else "Desactivado"
            else:
                prompt = 'Eres un asistente útil que responde de manera clara y concisa.'
                audio_status = "Desactivado"
                textfile_status = "Desactivado"
                voice_name = 'Kore'

            info_text = f"""
💬 **Información del chat:**

📋 **Tipo:** {chat_type}
🏷️ **Nombre:** {chat_info.name if chat_info.name else 'Chat privado'}
🔊 **Modo audio:** {audio_status}
📄 **Modo archivo:** {textfile_status}
🎙️ **Voz:** {voice_name}
🌐 **Idioma:** Español (fijo)
💾 **Prompt personalizado:** {'Sí' if prompt != 'Eres un asistente útil que responde de manera clara y concisa.' else 'No'}
            """
            
            bot.rpc.send_msg(accid, chat_id, MsgData(text=info_text))
        except Exception as e:
            error_msg = f"❌ Error al obtener información: {str(e)}"
            bot.rpc.send_msg(accid, chat_id, MsgData(text=error_msg))
        return

    # Si es un mensaje normal (no comando)
    if text and not text.startswith('/'):
        try:
            # Verificar si el bot sigue en el chat
            if not is_bot_in_chat(bot, accid, chat_id):
                print(f"Bot ya no está en el chat {chat_id}, ignorando mensaje")
                return

            # Obtener configuración del chat
            chat_data = database.get_chat_config(chat_id)
            if chat_data:
                prompt, audio_mode, textfile_mode, voice_name = chat_data
            else:
                # Configuración por defecto
                chat_info = bot.rpc.get_basic_chat_info(accid, chat_id)
                chat_title = chat_info.name if chat_info.name else "Chat privado"
                prompt = 'Eres un asistente útil que responde de manera clara y concisa.'
                audio_mode = 0
                textfile_mode = 0
                voice_name = 'Kore'
                database.save_chat_config(chat_id, chat_title, prompt, audio_mode, textfile_mode, voice_name)

            # Guardar mensaje del usuario
            database.save_message(chat_id, text, "user")

            # Obtener historial de conversación
            history = database.get_chat_history(chat_id)
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
            bot.rpc.send_chat_action(accid, chat_id, "typing")

            # Llamar a la API de Gemini
            respuesta = text_processing.call_gemini_api(messages)

            # Guardar respuesta del asistente
            database.save_message(chat_id, respuesta, "assistant")

            # Verificar si está activado el modo archivo de texto para respuestas largas
            if textfile_mode and len(respuesta) > 1000:
                # Crear archivo temporal con la respuesta
                with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt', encoding='utf-8') as f:
                    f.write(respuesta)
                    temp_file_path = f.name

                # Enviar archivo de texto
                with open(temp_file_path, 'rb') as f:
                    file_data = f.read()

                bot.rpc.send_msg(
                    accid,
                    chat_id,
                    MsgData(
                        file=file_data,
                        filename="respuesta.txt",
                        text="📄 Respuesta guardada en archivo de texto (modo textfile activado)"
                    )
                )

                # Limpiar archivo temporal
                os.unlink(temp_file_path)

            # Verificar si está activado el modo audio
            elif audio_mode:
                # Generar audio
                audio_path = audio_processing.text_to_audio_gemini(respuesta, voice_name=voice_name)

                if audio_path and os.path.exists(audio_path):
                    # Enviar audio
                    with open(audio_path, 'rb') as f:
                        audio_data = f.read()

                    bot.rpc.send_msg(
                        accid,
                        chat_id,
                        MsgData(
                            file=audio_data,
                            filename="respuesta.mp3",
                            text="🔊 Escucha la respuesta en audio"
                        )
                    )

                    # Limpiar archivo temporal
                    os.unlink(audio_path)
                else:
                    # Fallback a texto si falla la generación de audio
                    bot.rpc.send_msg(accid, chat_id, MsgData(text=respuesta))

            else:
                # Enviar respuesta como texto normal
                bot.rpc.send_msg(accid, chat_id, MsgData(text=respuesta))

        except Exception as e:
            error_msg = f"❌ Error: {str(e)}"
            try:
                bot.rpc.send_msg(accid, chat_id, MsgData(text=error_msg))
            except JsonRpcError as inner_e:
                print(f"Error al enviar mensaje de error: {inner_e}")
