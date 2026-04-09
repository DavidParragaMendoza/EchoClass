@echo off
chcp 65001 >nul
title EchoClass - Instalador

echo.
echo  ╔═══════════════════════════════════════════╗
echo  ║         🎙️ EchoClass - Instalador        ║
echo  ╚═══════════════════════════════════════════╝
echo.

if "%TERM_PROGRAM%"=="vscode" (
    echo ⚠️ ADVERTENCIA: Estas ejecutando este instalador dentro de la terminal de VS Code.
    echo    Esto puede causar problemas al actualizar variables de entorno ^(como PATH para FFmpeg^).
    echo    Se recomienda encarecidamente cerrar esta terminal y ejecutar "install.bat"
    echo    desde una ventana externa normal de CMD o PowerShell.
    echo.
    pause
)

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

python -c "import sys; sys.exit(0 if (3, 9) <= sys.version_info < (3, 14) else 1)" >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Version de Python no compatible
    python --version
    echo.
    echo    EchoClass requiere Python 3.9 a 3.13 ^(3.14 es muy reciente y da problemas^)
    echo    Recomendado: Python 3.11 o 3.12
    echo    Descarga: https://www.python.org/downloads/
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
    winget install --id Gyan.FFmpeg -e --accept-package-agreements --accept-source-agreements
    ffmpeg -version >nul 2>&1
    if %errorlevel% neq 0 (
        winget list --id Gyan.FFmpeg -e >nul 2>&1
        if %errorlevel% equ 0 (
            echo ✅ FFmpeg instalado con winget
            echo    Reinicia la terminal para que PATH se actualice
        ) else (
            echo.
            echo ❌ No se pudo instalar FFmpeg automáticamente
            echo    Instala manualmente: winget install --id Gyan.FFmpeg -e
            echo    O descarga desde: https://ffmpeg.org/download.html
            echo.
            pause
            exit /b 1
        )
    ) else (
        echo ✅ FFmpeg encontrado
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
    if %errorlevel% neq 0 (
        echo ❌ Error al crear el entorno virtual
        echo    Verifica que Python sea 3.9-3.13 y vuelve a intentar
        pause
        exit /b 1
    )
)

call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo ❌ No se pudo activar el entorno virtual
    pause
    exit /b 1
)
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
