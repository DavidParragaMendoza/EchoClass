# ============================================================
# EchoClass — RunPod Docker Image
# Base: NVIDIA CUDA 12.1 + cuDNN 8 + Ubuntu 22.04
# Incluye: Python 3.11, FFmpeg, faster-whisper (CUDA), Ollama
# ============================================================

FROM nvidia/cuda:12.1.0-cudnn8-runtime-ubuntu22.04

# ------------------------------------
# Variables de entorno base
# ------------------------------------
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    # Ollama descarga los modelos aquí dentro del pod
    OLLAMA_MODELS=/root/.ollama/models \
    # Whisper descarga los modelos aquí dentro del pod
    WHISPER_CACHE=/root/.cache/huggingface/hub

# ------------------------------------
# Dependencias del sistema + FFmpeg
# ------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
        python3.11 \
        python3.11-dev \
        python3-pip \
        python3.11-venv \
        ffmpeg \
        curl \
        wget \
        ca-certificates \
        git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Hacer python3.11 el default
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.11 1 \
    && update-alternatives --install /usr/bin/pip pip /usr/bin/pip3 1

# ------------------------------------
# Instalar Ollama
# ------------------------------------
RUN curl -fsSL https://ollama.com/install.sh | sh

# ------------------------------------
# Directorio de trabajo
# ------------------------------------
WORKDIR /app

# ------------------------------------
# Dependencias Python (capa separada para caché)
# ------------------------------------
COPY runpod/requirements-runpod.txt ./requirements.txt
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# ------------------------------------
# Código fuente de la aplicación
# ------------------------------------
COPY src/ ./src/
COPY static/ ./static/

# ------------------------------------
# Script de arranque
# ------------------------------------
COPY runpod/start.sh ./start.sh
RUN chmod +x ./start.sh

# ------------------------------------
# Puertos expuestos
# RunPod expone el puerto 8000 por defecto
# ------------------------------------
EXPOSE 8000

# ------------------------------------
# Comando de arranque
# ------------------------------------
CMD ["./start.sh"]
