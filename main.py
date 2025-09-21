import os
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

# Cargar solo los plugins necesarios
def load_plugins():
    plugins = {}
    plugins_pkg = "plugins"

    # Lista fija de plugins a cargar
    plugin_list = ["commands", "image_generation"]

    for module_name in plugin_list:
        try:
            full_module_name = f"{plugins_pkg}.{module_name}"
            module = importlib.import_module(full_module_name)
            plugins[module_name] = module
            logging.info(f"Plugin cargado: {module_name}")
        except Exception as e:
            logging.error(f"Error cargando plugin {module_name}: {e}")

    return plugins

# Cargar los plugins seleccionados
plugins = load_plugins()

# Registrar manejadores de eventos desde commands.py
@cli.on(events.NewMessage)
def handle_message(bot, accid, event):
    if 'commands' in plugins:
        plugins['commands'].handle_message(bot, accid, event)

if __name__ == "__main__":
    cli.start()
