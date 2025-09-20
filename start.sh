#!/bin/bash

# Script para ejecutar Gemini Bot en Render
# Las variables de entorno se configuran en el dashboard de Render

set -e  # Salir inmediatamente si cualquier comando falla

echo "🚀 Iniciando Gemini Bot..."
echo "📦 Comando: ${1:-'no especificado'}"
echo "📁 Directorio actual: $(pwd)"
echo "🐍 Versión de Python: $(python --version)"

# Nombre del archivo de backup (configurable por variable de entorno)
BACKUP_FILE="${BACKUP_FILE:-gembot.tar}"

# Función para importar backup
import_backup() {
    echo "📂 Buscando backup: $BACKUP_FILE"
    
    if [ -f "$BACKUP_FILE" ]; then
        echo "✅ Archivo de backup encontrado, importando..."
        echo "📊 Tamaño del backup: $(du -h "$BACKUP_FILE" | cut -f1)"
        
        if python main.py import "$BACKUP_FILE"; then
            echo "✅ Backup importado exitosamente"
        else
            echo "❌ Error al importar el backup"
            exit 1
        fi
    else
        echo "❌ Archivo de backup no encontrado: $BACKUP_FILE"
        echo "📋 Archivos en el directorio:"
        ls -la
        echo "💡 Asegúrate de que el archivo $BACKUP_FILE existe o configura BACKUP_FILE"
        exit 1
    fi
}

# Función para verificar dependencias
check_dependencies() {
    echo "🔍 Verificando dependencias..."
    if ! python -c "import deltachat; import requests; print('✅ Dependencias OK')" 2>/dev/null; then
        echo "❌ Dependencias de Python no satisfechas"
        echo "📦 Instalando dependencias..."
        pip install -r requirements.txt || {
            echo "❌ Error instalando dependencias"
            exit 1
        }
    fi
}

# Función para configurar el bot (ejecutar link)
configure_bot() {
    echo "🔗 Configurando bot con el comando 'link'..."
    
    if python main.py link; then
        echo "✅ Configuración completada exitosamente"
        return 0
    else
        echo "⚠️  La configuración con 'link' falló o no es necesaria"
        echo "ℹ️  Esto puede ser normal si la configuración ya existe"
        return 1
    fi
}

# Función para iniciar el servidor
start_server() {
    echo "🌐 Iniciando servidor Delta Chat..."
    echo "🤖 Iniciando Gemini Bot..."
    
    # Verificar dependencias primero
    check_dependencies
    
    # Configurar el bot antes de iniciar
    if configure_bot; then
        echo "✅ Bot configurado, iniciando servidor..."
    else
        echo "ℹ️  Iniciando servidor sin configuración adicional..."
    fi
    
    # Ejecutar el servidor
    exec python main.py serve
}

# Función para mostrar ayuda
show_help() {
    echo "Uso: $0 <comando>"
    echo "Comandos disponibles:"
    echo "  import  - Importar backup desde ${BACKUP_FILE}"
    echo "  serve   - Iniciar el servidor (comando por defecto)"
    echo "  help    - Mostrar esta ayuda"
    echo ""
    echo "Variables de entorno:"
    echo "  BACKUP_FILE - Nombre del archivo de backup (por defecto: gembot.tar)"
}

# Procesar argumentos
case "${1:-serve}" in  # 'serve' como comando por defecto
    "import")
        import_backup
        ;;
    "serve")
        start_server
        ;;
    "help"|"-h"|"--help")
        show_help
        ;;
    *)
        echo "❌ Comando no reconocido: $1"
        show_help
        exit 1
        ;;
esac
