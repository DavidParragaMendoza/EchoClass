#!/bin/bash

echo "========================================"
echo " Instalador - Transcriptor de Clases"
echo "========================================"
echo

echo "[1/5] Verificando Python..."
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python3 no está instalado"
    echo "Instálalo usando tu gestor de paquetes"
    exit 1
fi
python3 --version

echo
echo "[2/5] Verificando FFmpeg..."
if ! command -v ffmpeg &> /dev/null; then
    echo "ADVERTENCIA: FFmpeg no está instalado"
    echo "Ubuntu/Debian: sudo apt install ffmpeg"
    echo "macOS: brew install ffmpeg"
    read -p "Presiona Enter para continuar..."
fi

echo
echo "[3/5] Creando entorno virtual..."
cd backend
if [ -d "venv" ]; then
    echo "Entorno virtual ya existe, omitiendo..."
else
    python3 -m venv venv
fi

echo
echo "[4/5] Activando entorno e instalando dependencias..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "ERROR: Falló la instalación de dependencias"
    exit 1
fi

echo
echo "[5/5] Verificando Ollama..."
if ! command -v ollama &> /dev/null; then
    echo "ADVERTENCIA: Ollama no está instalado"
    echo "Descárgalo desde: https://ollama.ai"
    echo
    echo "Después de instalar, ejecuta:"
    echo "  ollama pull llama3"
    echo "  ollama serve"
    read -p "Presiona Enter para continuar..."
fi

echo
echo "========================================"
echo " Instalación Completada!"
echo "========================================"
echo
echo "Para iniciar el servidor:"
echo "  1. Ejecuta: ./start_server.sh"
echo "  2. Abre: frontend/index.html en tu navegador"
echo
echo "Asegúrate de que Ollama esté ejecutándose:"
echo "  ollama serve"
echo
