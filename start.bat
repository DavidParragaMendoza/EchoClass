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

echo  ✅ Servidor iniciando en http://localhost:8000
echo  📝 Presiona Ctrl+C para detener
echo.

REM Iniciar servidor
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000
