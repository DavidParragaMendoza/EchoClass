#!/bin/bash

echo "========================================"
echo " Iniciando Servidor de Transcripción"
echo "========================================"
echo

cd backend

if [ ! -d "venv" ]; then
    echo "ERROR: Entorno virtual no encontrado"
    echo "Ejecuta primero: ./install.sh"
    exit 1
fi

echo "Activando entorno virtual..."
source venv/bin/activate

echo
echo "Iniciando servidor FastAPI en http://localhost:8000"
echo
echo "IMPORTANTE:"
echo "- Asegúrate de que Ollama esté ejecutándose: ollama serve"
echo "- Abre frontend/index.html en tu navegador"
echo
echo "Presiona Ctrl+C para detener el servidor"
echo

python main.py
