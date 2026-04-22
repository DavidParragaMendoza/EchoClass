@echo off
chcp 65001 >nul
title EchoClass - Servidor
cd /d "%~dp0"

echo.
echo  🎙️ EchoClass - Iniciando servidor...
echo.

REM Verificar entorno virtual
if not exist venv (
    echo ❌ Entorno virtual no encontrado
    echo    Ejecuta primero: install.bat
    pause
    exit /b 1
)

if not exist venv\Scripts\python.exe (
    echo ❌ Entorno virtual incompleto: falta venv\Scripts\python.exe
    echo    Ejecuta install.bat para repararlo
    pause
    exit /b 1
)

REM Verificar que el venv sea usable (evita rutas viejas de Python)
venv\Scripts\python.exe --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️ Entorno virtual incompatible o corrupto detectado. Recreando con el Python actual...
    rmdir /s /q venv
    python -m venv venv
    if %errorlevel% neq 0 (
        echo ❌ No se pudo recrear el entorno virtual
        echo    Verifica que `python --version` funcione y ejecuta install.bat
        pause
        exit /b 1
    )
)

REM Activar entorno
call venv\Scripts\activate.bat

REM Instalar dependencias si faltan (nuevo venv)
python -m pip show fastapi >nul 2>&1
if %errorlevel% neq 0 (
    echo    Instalando dependencias en el entorno virtual...
    python -m pip install --upgrade pip --quiet
    python -m pip install -r requirements.txt --quiet
    if %errorlevel% neq 0 (
        echo ❌ Error al instalar dependencias
        echo    Ejecuta install.bat para diagnostico completo
        pause
        exit /b 1
    )
)

REM Forzar máxima calidad de Whisper en GPU CUDA
set "WHISPER_DEVICE=cuda"
set "WHISPER_MODEL=large-v3"
set "WHISPER_COMPUTE_TYPE=float16"

echo  ✅ Servidor iniciando en http://localhost:8000
echo  📝 Presiona Ctrl+C para detener
echo  ⚠️ Si Ctrl+C no responde, usa Ctrl+Break o cierra la ventana de terminal
echo.

REM Iniciar servidor
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000
