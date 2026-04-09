@echo off
chcp 65001 >nul
title EchoClass - Servidor

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

REM Activar entorno
call venv\Scripts\activate.bat

REM Forzar ejecución de Whisper en CPU (sin CUDA)
set "WHISPER_MODEL=large"
set "WHISPER_COMPUTE_TYPE=float32"

echo  ✅ Servidor iniciando en http://localhost:8000
echo  📝 Presiona Ctrl+C para detener
echo  ⚠️ Si Ctrl+C no responde, usa Ctrl+Break o cierra la ventana de terminal
echo.

REM Iniciar servidor
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000
