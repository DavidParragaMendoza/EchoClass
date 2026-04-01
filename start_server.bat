@echo off
echo ========================================
echo  Iniciando Servidor de Transcripcion
echo ========================================
echo.

cd backend

if not exist venv (
    echo ERROR: Entorno virtual no encontrado
    echo Ejecuta primero: install.bat
    pause
    exit /b 1
)

echo Activando entorno virtual...
call venv\Scripts\activate.bat

echo.
echo Iniciando servidor FastAPI en http://localhost:8000
echo.
echo IMPORTANTE:
echo - Asegurate de que Ollama este ejecutandose: ollama serve
echo - Abre frontend\index.html en tu navegador
echo.
echo Presiona Ctrl+C para detener el servidor
echo.

python main.py
