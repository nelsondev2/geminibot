import os
import tempfile
import base64
import wave
import subprocess
import langid
import speech_recognition as sr
from gtts import gTTS
import requests
from dotenv import load_dotenv

# Cargar API Key desde archivo .env
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_TTS_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-tts:generateContent"

# Lista completa de voces preconstruidas disponibles en Gemini TTS con descripciones
GEMINI_VOICES_DETAILED = {
    "Kore": {"description": "Voz femenina firme y profesional", "gender": "femenina", "style": "firme"},
    "Puck": {"description": "Voz optimista y alegre", "gender": "femenina", "style": "optimista"},
    "Charon": {"description": "Voz informativa y clara", "gender": "masculina", "style": "informativa"},
    "Fenrir": {"description": "Voz con tono de excitabilidad", "gender": "masculina", "style": "excitada"},
    "Leda": {"description": "Voz juvenil y energética", "gender": "femenina", "style": "juvenil"},
    "Orus": {"description": "Voz firme y confiable", "gender": "masculina", "style": "firme"},
    "Aoede": {"description": "Voz suave y breezy", "gender": "femenina", "style": "suave"},
    "Callirrhoe": {"description": "Voz tranquila y calmada", "gender": "femenina", "style": "calmada"},
    "Autonoe": {"description": "Voz brillante y expresiva", "gender": "femenina", "style": "expresiva"},
    "Enceladus": {"description": "Voz con calidad respiratoria", "gender": "masculina", "style": "susurrante"},
    "Iapetus": {"description": "Voz clara y nítida", "gender": "masculina", "style": "clara"},
    "Umbriel": {"description": "Voz relajada y calmada", "gender": "masculina", "style": "relajada"},
    "Algieba": {"description": "Voz suave y delicada", "gender": "femenina", "style": "suave"},
    "Despina": {"description": "Voz suave y melodiosa", "gender": "femenina", "style": "suave"},
    "Erinome": {"description": "Voz clara y despejada", "gender": "femenina", "style": "clara"},
    "Algenib": {"description": "Voz arenosa y única", "gender": "masculina", "style": "única"},
    "Rasalgethi": {"description": "Voz informativa y clara", "gender": "masculina", "style": "informativa"},
    "Laomedeia": {"description": "Voz optimista y positiva", "gender": "femenina", "style": "optimista"},
    "Achernar": {"description": "Voz suave y agradable", "gender": "masculina", "style": "suave"},
    "Alnilam": {"description": "Voz firme y confiable", "gender": "masculina", "style": "firme"},
    "Schedar": {"description": "Voz par y equilibrada", "gender": "femenina", "style": "equilibrada"},
    "Gacrux": {"description": "Voz apropiada para contenido para mayores", "gender": "masculina", "style": "madura"},
    "Pulcherrima": {"description": "Voz hacia adelante y directa", "gender": "femenina", "style": "directa"},
    "Achird": {"description": "Voz amistosa y cercana", "gender": "masculina", "style": "amistosa"},
    "Zubenelgenubi": {"description": "Voz casual y relajada", "gender": "masculina", "style": "casual"},
    "Vindemiatrix": {"description": "Voz suave y tranquilizadora", "gender": "femenina", "style": "tranquilizadora"},
    "Sadachbia": {"description": "Voz animada y energética", "gender": "femenina", "style": "animada"},
    "Sadaltager": {"description": "Voz con tono de conocimiento", "gender": "masculina", "style": "sabia"},
    "Sulafat": {"description": "Voz cálida y acogedora", "gender": "femenina", "style": "cálida"},
    "Zephyr": {"description": "Voz iluminada y brillante", "gender": "femenina", "style": "brillante"}
}

# Lista simple de voces para validación
GEMINI_VOICES = list(GEMINI_VOICES_DETAILED.keys())

def get_voice_info(voice_name):
    """Obtiene información descriptiva de una voz específica"""
    if voice_name in GEMINI_VOICES_DETAILED:
        return GEMINI_VOICES_DETAILED[voice_name]["description"]
    return "Voz preconfigurada de Gemini TTS"

def text_to_audio_gtts(text, lang='es', slow=False):
    """Función de respaldo con gTTS"""
    try:
        tts = gTTS(text=text, lang=lang, slow=slow)
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as fp:
            temp_audio_path = fp.name
            tts.save(temp_audio_path)
        return temp_audio_path
    except Exception as e:
        print(f"Error en gTTS: {e}")
        return None

def text_to_audio_gemini(text, lang='es', slow=False, voice_name="Kore"):
    """Convierte texto a audio usando Gemini TTS API con respaldo de gTTS"""
    try:
        # Configuración de Gemini TTS
        config = {
            "api_key": API_KEY,
            "api_url": GEMINI_TTS_URL,
            "voice_name": voice_name,
            "timeout": (5, 60)
        }

        # Construir payload
        payload = {
            "contents": [{"parts": [{"text": text}]}],
            "generationConfig": {
                "responseModalities": ["AUDIO"],
                "speechConfig": {
                    "voiceConfig": {
                        "prebuiltVoiceConfig": {"voiceName": voice_name}
                    }
                }
            }
        }

        # Headers y URL
        headers = {"Content-Type": "application/json"}
        url = f'{config["api_url"]}?key={config["api_key"]}'

        # Realizar solicitud
        response = requests.post(url, headers=headers, json=payload, timeout=config["timeout"])
        response.raise_for_status()

        # Procesar respuesta
        data = response.json()
        audio_b64 = data["candidates"][0]["content"]["parts"][0]["inlineData"]["data"]
        pcm_bytes = base64.b64decode(audio_b64)

        # Crear WAV temporal
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as wav_fp:
            wav_path = wav_fp.name
            with wave.open(wav_path, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(24000)
                wf.writeframes(pcm_bytes)

        # Convertir a MP3
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as mp3_fp:
            mp3_path = mp3_fp.name
            subprocess.run([
                "ffmpeg", "-y", "-i", wav_path, mp3_path
            ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Limpiar archivo WAV temporal
        os.unlink(wav_path)
        return mp3_path

    except Exception as e:
        print(f"Gemini TTS falló, usando gTTS como respaldo: {e}")
        # Fallback a gTTS
        return text_to_audio_gtts(text, lang, slow)

def detect_language(text):
    """Detecta el idioma del texto"""
    try:
        lang, _ = langid.classify(text)
        return lang
    except Exception as e:
        print(f"Error detectando idioma: {e}")
        return 'es'  # Por defecto español

def convert_audio_to_wav(input_path, output_path):
    """Convierte cualquier formato de audio to WAV usando ffmpeg"""
    try:
        result = subprocess.run([
            'ffmpeg', '-y', '-i', input_path,
            '-acodec', 'pcm_s16le', '-ac', '1', '-ar', '16000',
            output_path
        ], capture_output=True, text=True, timeout=30)

        if result.returncode != 0:
            print(f"Error en conversión: {result.stderr}")
            return False
        return True
    except subprocess.TimeoutExpired:
        print("Tiempo de espera agotado en conversión de audio")
        return False
    except Exception as e:
        print(f"Error al convertir audio: {e}")
        return False

def audio_to_text(audio_path):
    """Convierte audio a texto usando speech_recognition"""
    try:
        recognizer = sr.Recognizer()

        # Verificar si necesita conversión
        file_ext = os.path.splitext(audio_path.lower())[1]
        needs_conversion = file_ext not in ['.wav']

        if needs_conversion:
            # Convertir a WAV primero
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_wav:
                temp_wav_path = temp_wav.name

            if not convert_audio_to_wav(audio_path, temp_wav_path):
                return None, "❌ Error al convertir el audio a formato compatible"

            audio_file_path = temp_wav_path
        else:
            audio_file_path = audio_path

        # Cargar el archivo de audio
        with sr.AudioFile(audio_file_path) as source:
            # Ajustar para el ruido ambiental
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            # Obtener el audio del archivo
            audio_data = recognizer.record(source)

        # Limpiar archivo temporal si se creó
        if needs_conversion and os.path.exists(audio_file_path):
            os.unlink(audio_file_path)

        # Intentar reconocimiento con Google Speech Recognition
        try:
            # Detectar idioma automáticamente o usar español por defecto
            text = recognizer.recognize_google(audio_data, language='es-ES')
            return text, None
        except sr.UnknownValueError:
            return None, "❌ No se pudo entender el audio. Asegúrate de que sea claro y en un idioma soportado."
        except sr.RequestError as e:
            return None, f"❌ Error en el servicio de reconocimiento: {e}"

    except Exception as e:
        # Limpiar archivo temporal en caso de error
        if 'temp_wav_path' in locals() and os.path.exists(temp_wav_path):
            os.unlink(temp_wav_path)
        return None, f"❌ Error al procesar el audio: {str(e)}"

def is_audio_file(filename):
    """Verifica si el archivo es un formato de audio soportado"""
    if not filename:
        return False
    SUPPORTED_AUDIO_FORMATS = ['.mp3', '.wav', '.m4a', '.ogg', '.flac', '.acc', '.aac']
    return any(filename.lower().endswith(ext) for ext in SUPPORTED_AUDIO_FORMATS)
