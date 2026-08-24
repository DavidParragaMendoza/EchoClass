#!/bin/bash
# ============================================================
# EchoClass — Script de arranque del pod de RunPod
#
# Secuencia:
#   1. Verificar GPU disponible
#   2. Iniciar servidor Ollama en background
#   3. Esperar a que Ollama esté listo
#   4. Descargar modelo LLM (qwen2.5:7b) si no está en cache
#   5. Levantar servidor FastAPI (EchoClass)
# ============================================================

set -e  # Salir si cualquier comando falla

# ------------------------------------
# Colores para logs
# ------------------------------------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # Sin color

log() { echo -e "${BLUE}[EchoClass]${NC} $1"; }
ok()  { echo -e "${GREEN}[✓]${NC} $1"; }
warn(){ echo -e "${YELLOW}[⚠]${NC} $1"; }
err() { echo -e "${RED}[✗]${NC} $1"; }

# ------------------------------------
# 1. Verificar GPU
# ------------------------------------
log "Verificando GPU..."
if nvidia-smi &>/dev/null; then
    ok "GPU detectada:"
    nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
else
    warn "GPU no detectada — Whisper correrá en CPU (más lento)"
fi

# ------------------------------------
# 2. Iniciar Ollama en background
# ------------------------------------
log "Iniciando servidor Ollama en background..."
ollama serve &
OLLAMA_PID=$!
ok "Ollama iniciado (PID: $OLLAMA_PID)"

# ------------------------------------
# 3. Esperar a que Ollama esté listo
# ------------------------------------
log "Esperando a que Ollama esté listo..."
MAX_RETRIES=30
RETRY_COUNT=0

until curl -sf http://localhost:11434/api/tags > /dev/null 2>&1; do
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
        err "Ollama no respondió después de ${MAX_RETRIES} intentos"
        exit 1
    fi
    echo "  Intento $RETRY_COUNT/$MAX_RETRIES — esperando 2s..."
    sleep 2
done
ok "Ollama listo en http://localhost:11434"

# ------------------------------------
# 4. Descargar modelo LLM
# ------------------------------------
OLLAMA_MODEL="${OLLAMA_MODEL:-qwen2.5:7b}"
log "Verificando modelo Ollama: '$OLLAMA_MODEL'..."

if ollama list | grep -q "$OLLAMA_MODEL"; then
    ok "Modelo '$OLLAMA_MODEL' ya está disponible en cache"
else
    log "Descargando modelo '$OLLAMA_MODEL' (puede tardar varios minutos en el primer arranque)..."
    ollama pull "$OLLAMA_MODEL"
    ok "Modelo '$OLLAMA_MODEL' descargado"
fi

# ------------------------------------
# 5. Configuración del servidor
# ------------------------------------
export WHISPER_MODEL="${WHISPER_MODEL:-large-v3}"
export WHISPER_DEVICE="${WHISPER_DEVICE:-cuda}"
export WHISPER_COMPUTE_TYPE="${WHISPER_COMPUTE_TYPE:-float16}"
export WHISPER_LANGUAGE="${WHISPER_LANGUAGE:-es}"
export OLLAMA_MODEL="$OLLAMA_MODEL"
export OLLAMA_URL="http://localhost:11434"
export SERVER_HOST="0.0.0.0"
export SERVER_PORT="${SERVER_PORT:-8000}"

log "Configuración del servidor:"
echo "  WHISPER_MODEL      = $WHISPER_MODEL"
echo "  WHISPER_DEVICE     = $WHISPER_DEVICE"
echo "  WHISPER_COMPUTE_TYPE = $WHISPER_COMPUTE_TYPE"
echo "  OLLAMA_MODEL       = $OLLAMA_MODEL"
echo "  SERVER_PORT        = $SERVER_PORT"

# ------------------------------------
# 6. Iniciar servidor FastAPI (EchoClass)
# ------------------------------------
log "🚀 Iniciando EchoClass en 0.0.0.0:${SERVER_PORT}..."
cd /app
exec python -m uvicorn src.main:app \
    --host 0.0.0.0 \
    --port "${SERVER_PORT}" \
    --log-level info
