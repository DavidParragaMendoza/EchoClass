@echo off
echo ========================================
echo  Instalador - Transcriptor de Clases
echo ========================================
echo.

echo [1/5] Verificando Python...
python --version
if %errorlevel% neq 0 (
    echo ERROR: Python no esta instalado
    echo Descargalo desde: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo.
echo [2/5] Verificando FFmpeg...
ffmpeg -version >nul 2>&1
if %errorlevel% neq 0 (
    echo ADVERTENCIA: FFmpeg no esta instalado
    echo Instala con: winget install FFmpeg
    echo O descarga desde: https://ffmpeg.org/download.html
    pause
)

echo.
echo [3/5] Creando entorno virtual...
cd backend
if exist venv (
    echo Entorno virtual ya existe, omitiendo...
) else (
    python -m venv venv
)

echo.
echo [4/5] Activando entorno e instalando dependencias...
call venv\Scripts\activate.bat
pip install --upgrade pip
pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo ERROR: Fallo la instalacion de dependencias
    pause
    exit /b 1
)

echo.
echo [5/5] Verificando Ollama...
ollama --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ADVERTENCIA: Ollama no esta instalado
    echo Descargalo desde: https://ollama.ai
    echo.
    echo Despues de instalar, ejecuta:
    echo   ollama pull llama3
    echo   ollama serve
    pause
)

echo.
echo ========================================
echo  Instalacion Completada!
echo ========================================
echo.
echo Para iniciar el servidor:
echo   1. Ejecuta: start_server.bat
echo   2. Abre: frontend\index.html en tu navegador
echo.
echo Asegurate de que Ollama este ejecutandose:
echo   ollama serve
echo.
pause
