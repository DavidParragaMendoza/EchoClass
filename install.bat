@echo off
chcp 65001 >nul
title EchoClass - Instalador

echo.
echo  ╔═══════════════════════════════════════════╗
echo  ║         🎙️ EchoClass - Instalador         ║
echo  ╚═══════════════════════════════════════════╝
echo.

REM Verificar Python
echo [1/4] Verificando Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python no encontrado
    echo.
    echo    Descarga Python desde: https://www.python.org/downloads/
    echo    IMPORTANTE: Marca "Add Python to PATH" durante la instalación
    echo.
    pause
    exit /b 1
)
python --version
echo ✅ Python encontrado
echo.

REM Verificar FFmpeg
echo [2/4] Verificando FFmpeg...
ffmpeg -version >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️ FFmpeg no encontrado. Intentando instalar con winget...
    winget install FFmpeg --accept-package-agreements --accept-source-agreements
    if %errorlevel% neq 0 (
        echo.
        echo ❌ No se pudo instalar FFmpeg automáticamente
        echo    Instala manualmente: winget install FFmpeg
        echo    O descarga desde: https://ffmpeg.org/download.html
        echo.
        pause
    )
) else (
    echo ✅ FFmpeg encontrado
)
echo.

REM Crear entorno virtual e instalar dependencias
echo [3/4] Configurando entorno Python...
if exist venv (
    echo    Entorno virtual existente, actualizando...
) else (
    echo    Creando entorno virtual...
    python -m venv venv
)

call venv\Scripts\activate.bat
echo    Instalando dependencias...
python -m pip install --upgrade pip --quiet
python -m pip install -r requirements.txt --quiet

if %errorlevel% neq 0 (
    echo ❌ Error al instalar dependencias
    pause
    exit /b 1
)
echo ✅ Dependencias instaladas
echo.

REM Verificar/Instalar Ollama
echo [4/4] Verificando Ollama...
ollama --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️ Ollama no encontrado
    echo.
    echo    Descarga Ollama desde: https://ollama.ai
    echo    Después de instalar, ejecuta:
    echo      ollama pull qwen2.5:7b
    echo.
    pause
) else (
    echo ✅ Ollama encontrado
    echo    Verificando modelo qwen2.5:7b...
    ollama list 2>nul | findstr "qwen2.5:7b" >nul
    if %errorlevel% neq 0 (
        echo    Descargando modelo qwen2.5:7b (puede tomar unos minutos)...
        ollama pull qwen2.5:7b
    ) else (
        echo ✅ Modelo qwen2.5:7b disponible
    )
)

echo.
echo  ╔═══════════════════════════════════════════╗
echo  ║      ✅ Instalación Completada            ║
echo  ╚═══════════════════════════════════════════╝
echo.
echo  Para iniciar EchoClass:
echo    1. Ejecuta: start.bat
echo    2. Abre: http://localhost:8000
echo.
echo  Asegúrate de que Ollama esté ejecutándose:
echo    ollama serve
echo.
pause
