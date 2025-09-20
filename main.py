import os
import sys
import importlib
import logging
from deltachat2 import events
from deltabot_cli import BotCli
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configurar logging
def setup_logging():
    level = logging.DEBUG if os.getenv("DEBUG", "0") == "1" else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%H:%M:%S",
    )

setup_logging()

# Crear instancia del bot
cli = BotCli("gemini_bot")

# Cargar plugins dinámicamente
def load_plugins():
    plugins_dir = os.path.join(os.path.dirname(__file__), 'plugins')
    sys.path.insert(0, plugins_dir)
    
    plugins = {}
    
    # Listar todos los archivos Python en la carpeta plugins
    for filename in os.listdir(plugins_dir):
        if filename.endswith('.py') and filename != '__init__.py':
            module_name = filename[:-3]  # Remover .py
            try:
                module = importlib.import_module(module_name)
                plugins[module_name] = module
                logging.info(f"Plugin cargado: {module_name}")
            except Exception as e:
                logging.error(f"Error cargando plugin {module_name}: {e}")
    
    return plugins

# Cargar todos los plugins
plugins = load_plugins()

# Registrar manejadores de eventos desde los plugins
@cli.on(events.NewMessage)
def handle_message(bot, accid, event):
    # Delegar el manejo de mensajes al plugin de comandos
    if 'commands' in plugins:
        plugins['commands'].handle_message(bot, accid, event)

if __name__ == "__main__":
    cli.start()
