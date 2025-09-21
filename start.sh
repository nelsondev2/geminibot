#!/bin/bash
set -e

PYTHON_BIN="${PYTHON_BIN:-python3}"
BACKUP_FILE="${BACKUP_FILE:-geminibot.tar}"

# Ir a la carpeta raíz del proyecto (donde está main.py)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "🚀 Iniciando Gemini Bot..."
echo "📁 Directorio actual: $(pwd)"
echo "🐍 Versión de Python: $($PYTHON_BIN --version)"

# 1️⃣ Importar backup
echo "📂 Importando backup: $BACKUP_FILE"
$PYTHON_BIN -m main import "$BACKUP_FILE"

# 2️⃣ Ejecutar link y capturar el enlace
echo "🔗 Ejecutando link..."
LINK_OUTPUT="$($PYTHON_BIN -m main link)"
echo "$LINK_OUTPUT"

LINK_URL=$(echo "$LINK_OUTPUT" | grep -Eo 'https://.*')
if [ -n "$LINK_URL" ]; then
    echo "========================================"
    echo "📌 ENLACE PARA ABRIR EN DELTA CHAT:"
    echo "$LINK_URL"
    echo "========================================"
fi

# 3️⃣ Iniciar servidor
echo "🌐 Iniciando servidor..."
exec $PYTHON_BIN -m main serve
