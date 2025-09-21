import requests
import json
import time
import os
from dotenv import load_dotenv

# Cargar API Key desde archivo .env
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent?key={API_KEY}"

def call_gemini_api(messages, max_retries=3, initial_timeout=45):
    """Función mejorada con reintentos y tiempo de espera adaptable"""
    timeout = initial_timeout
    last_error = None

    for attempt in range(max_retries):
        try:
            response = requests.post(
                GEMINI_URL,
                headers={'Content-Type': 'application/json'},
                json={
                    "contents": messages,
                    "generationConfig": {
                        "temperature": 0.9,
                        "topP": 1,
                        "topK": 40
                    },
                    "safetySettings": [
                        {
                            "category": "HARM_CATEGORY_HARASSMENT",
                            "threshold": "BLOCK_ONLY_HIGH"
                        },
                        {
                            "category": "HARM_CATEGORY_HATE_SPEECH",
                            "threshold": "BLOCK_ONLY_HIGH"
                        },
                        {
                            "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                            "threshold": "BLOCK_ONLY_HIGH"
                        },
                        {
                            "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                            "threshold": "BLOCK_ONLY_HIGH"
                        }
                    ]
                },
                timeout=timeout
            )

            response.raise_for_status()
            result = response.json()

            if not result.get("candidates"):
                raise ValueError("La respuesta no contiene candidatos")

            first_candidate = result["candidates"][0]
            if not first_candidate.get("content"):
                raise ValueError("El candidato no contiene contenido")

            parts = first_candidate["content"].get("parts", [])
            if not parts:
                raise ValueError("No hay partes en el contenido")

            return parts[0].get("text", "No se pudo generar respuesta")

        except requests.exceptions.Timeout:
            last_error = f"Intento {attempt + 1}: Tiempo de espera agotado ({timeout}s)"
            print(last_error)
            timeout += 15
            if attempt < max_retries - 1:
                continue
            raise Exception(f"Tiempo de espera agotado después de {max_retries} intentos")

        except requests.exceptions.RequestException as e:
            last_error = f"Intento {attempt + 1}: Error de conexión - {str(e)}"
            print(last_error)
            if attempt < max_retries - 1:
                time.sleep(2)
                continue
            raise Exception(f"Error de conexión después de {max_retries} intentos: {str(e)}")

        except json.JSONDecodeError:
            last_error = f"Intento {attempt + 1}: Respuesta inválida (JSON malformado)"
            print(last_error)
            if attempt < max_retries - 1:
                continue
            raise Exception("Respuesta inválida del servidor (JSON malformado) después de varios intentos")

        except Exception as e:
            last_error = f"Intento {attempt + 1}: Error - {str(e)}"
            print(last_error)
            if attempt < max_retries - 1:
                continue
            raise Exception(f"Error al procesar la respuesta después de {max_retries} intentos: {str(e)}")

def check_gemini_status():
    """Verifica el estado del servicio Gemini"""
    try:
        response = requests.get(
            "https://generativelanguage.googleapis.com/v1beta/operations",
            params={'key': API_KEY},
            timeout=10
        )
        return response.status_code == 200
    except:
        return False
