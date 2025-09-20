#!/bin/bash

# Script para ejecutar Gemini Bot en Render
# Las variables de entorno se configuran en el dashboard de Render

echo "🚀 Iniciando Gemini Bot..."
echo "📦 Comando: $1"

# Nombre del archivo de backup
BACKUP_FILE="gembot.tar.gz"

# Función para importar backup
import_backup() {
    if [ -f "$BACKUP_FILE" ]; then
        echo "📂 Importando backup: $BACKUP_FILE"
        python main.py import "$BACKUP_FILE"
    else
        echo "❌ Archivo de backup no encontrado: $BACKUP_FILE"
        echo "💡 Asegúrate de que el archivo $BACKUP_FILE existe en el directorio actual"
        exit 1
    fi
}

# Función para iniciar el servidor
start_server() {
    echo "🌐 Iniciando servidor Delta Chat..."
    echo "🤖 Iniciando Gemini Bot..."
    exec python main.py serve
}

# Procesar argumentos
case "$1" in
    "import")
        import_backup
        ;;
    "serve")
        start_server
        ;;
    "")
        echo "❌ Uso: $0 <comando>"
        echo "Comandos disponibles:"
        echo "  import  - Importar backup desde $BACKUP_FILE"
        echo "  serve   - Iniciar el servidor"
        exit 1
        ;;
    *)
        echo "❌ Comando no reconocido: $1"
        echo "Comandos disponibles:"
        echo "  import  - Importar backup desde $BACKUP_FILE"
        echo "  serve   - Iniciar el servidor"
        exit 1
        ;;
esac
